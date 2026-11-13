"""72 elapsed hours from explicit reservation approval; never initiates a charge."""
import asyncio
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo
from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError
from web_accounts import administrator
from web_identity import now, resolve_session, send_transactional, public_origin, audit
from investor_access import fail
from web_dossier import LABELS, expired

class Approval(BaseModel):
    model_config = ConfigDict(extra='forbid')
    required_documents: list[str] = Field(min_length=1,max_length=6)
    confirmation: str

async def outstanding(db,row,verified=True):
    docs=await db.web_personal_documents.find({'subject_id':row['subject_id'],'deleted':{'$ne':True},
        'scan_state':'CLEAN','dossier_state':'FILED','created_at':{'$lte':row['deadline_at']}}).to_list(100)
    supplied={k for d in docs if not expired(d) and not d.get('identity_discrepancy') and (not verified or d.get('review_state')=='APPROVED') for k in d.get('document_kinds',[])}
    return [k for k in row['required_documents'] if k not in supplied]

async def advance(db,row,stamp=None):
    stamp=stamp or now()
    if row['state'] not in ('ACTIVE','INITIAL_REVIEW_PENDING','DOCUMENTS_COMPLETE'):return row
    reservation=await db.web_reservations.find_one({'checkout_request_id':row['_id']})
    if reservation and reservation.get('state') in ('CANCELLED','REFUNDED','REJECTED'):
        await db.web_reservation_protocols.update_one({'_id':row['_id'],'state':row['state']},{'$set':{'state':'CANCELLED','checked_at':stamp}})
        return await db.web_reservation_protocols.find_one({'_id':row['_id']})
    if row['state']=='DOCUMENTS_COMPLETE':return row
    missing=await outstanding(db,row)
    awaiting_review=bool(missing) and not await outstanding(db,row,verified=False)
    # Initial requirements are fixed at approval. Later compliance requests do not reopen this clock.
    state='DOCUMENTS_COMPLETE' if not missing else ('INITIAL_REVIEW_PENDING' if awaiting_review else ('EXPIRED' if stamp>=row['deadline_at'] else 'ACTIVE'))
    await db.web_reservation_protocols.update_one({'_id':row['_id'],'state':row['state']},
        {'$set':{'state':state,'missing_documents':missing,'checked_at':stamp}})
    return await db.web_reservation_protocols.find_one({'_id':row['_id']})

async def tick(db,stamp=None):
    stamp=stamp or now()
    rows=await db.web_reservation_protocols.find({'state':{'$in':['ACTIVE','INITIAL_REVIEW_PENDING','DOCUMENTS_COMPLETE']}}).to_list(1000)
    for row in rows:
        row=await advance(db,row,stamp)
        if row['state']!='ACTIVE':continue
        user=await db.web_users.find_one({'subject_id':row['subject_id'],'active':True,'email_verified':True})
        if not user:continue
        from web_access_restrictions import blocked
        if await blocked(db,user):continue
        day=int((stamp-row['approved_at']).total_seconds()//86400)
        if day not in (0,1,2):continue
        # Only the current reminder is issued after downtime; no burst of old mail.
        ident='reservation:'+row['_id']+':'+str(day)
        title='Reserva aprobada · empieza tu plazo de 72 horas' if day==0 else 'Recuerda completar la documentación de tu reserva'
        body='Tu reserva '+row['op_ref']+' tiene documentación pendiente. Fecha límite: '+row['deadline_at'].astimezone(ZoneInfo('Europe/Madrid')).strftime('%d/%m/%Y a las %H:%M (Madrid)')+'. Consulta los documentos y el tiempo restante en tu espacio privado.'
        await db.web_notifications.update_one({'subject_id':row['subject_id'],'id':ident},
            {'$setOnInsert':{'title':title,'body':body,'read':False,'created_at':stamp,'protocol_id':row['_id']}},upsert=True)
        try:
            await db.web_protocol_mail.insert_one({'_id':ident,'protocol_id':row['_id'],'state':'SENDING','created_at':stamp})
        except DuplicateKeyError:continue
        # Recheck immediately before submission; completion/cancellation stops mail.
        current=await db.web_reservation_protocols.find_one({'_id':row['_id']})
        current=await advance(db,current,stamp)
        if current['state']!='ACTIVE':
            await db.web_protocol_mail.update_one({'_id':ident},{'$set':{'state':'CANCELLED'}})
            continue
        try:
            await send_transactional(user['email'],title,body+'\n\n'+public_origin()+'/mi-oportuniia#recordatorios')
        except Exception:
            # Ambiguous delivery is not retried blindly. Visible to Master.
            await db.web_protocol_mail.update_one({'_id':ident},{'$set':{'state':'DELIVERY_UNCONFIRMED'}})
        else:
            await db.web_protocol_mail.update_one({'_id':ident},{'$set':{'state':'SUBMITTED','submitted_at':stamp}})
    # Active reminders disappear from the inbox when fulfilled, cancelled or expired.
    finished=await db.web_reservation_protocols.find({'state':{'$ne':'ACTIVE'}}).to_list(1000)
    for row in finished:
        await db.web_notifications.update_many({'subject_id':row['subject_id'],'protocol_id':row['_id']},
            {'$set':{'read':True,'resolved':True}})

async def worker(db):
    while True:
        try:await tick(db)
        except Exception:logging.getLogger(__name__).exception('reservation_protocol_tick_failed')
        await asyncio.sleep(60)

def register_protocol_routes(router,db):
    @router.get('/account/reservation-protocols')
    async def mine(request:Request):
        user,_=await resolve_session(request,db)
        rows=await db.web_reservation_protocols.find({'subject_id':user['subject_id']}).to_list(100)
        items=[]
        for row in rows:
            row=await advance(db,row)
            items.append({k:row.get(k) for k in ('op_ref','state','approved_at','deadline_at','required_documents','missing_documents')})
        return {'items':items,'labels':LABELS,'server_time':now()}

    @router.get('/account/reservation-protocols/manage')
    async def management(request:Request):
        await administrator(request,db)
        rows=await db.web_reservations.find({'state':{'$in':['PAID_PENDING_OPERATION_REVIEW','APPROVED']}}).to_list(500)
        result=[]
        for row in rows:
            ident=row.get('checkout_request_id')
            if not ident:continue
            protocol=await db.web_reservation_protocols.find_one({'_id':ident})
            if protocol:protocol=await advance(db,protocol)
            result.append({'reservation_id':ident,'op_ref':row.get('op_ref'),'subject_id':row.get('subject_id'),
                'protocol':{k:protocol.get(k) for k in ('state','deadline_at','missing_documents')} if protocol else None})
        mails=await db.web_protocol_mail.find({'state':{'$in':['SENDING','DELIVERY_UNCONFIRMED']}},{'_id':0,'protocol_id':1,'state':1}).to_list(100)
        return {'items':result,'labels':{k:v for k,v in LABELS.items() if k!='other'},'mail_incidents':mails,'server_time':now()}

    @router.post('/account/reservation-protocols/{reservation_id}/approve')
    async def approve(reservation_id:str,payload:Approval,request:Request):
        actor=await administrator(request,db)
        if payload.confirmation!='APROBAR RESERVA':fail('explicit_reservation_approval_required',422)
        if any(k not in LABELS or k=='other' for k in payload.required_documents):fail('invalid_required_documents',422)
        row=await db.web_reservations.find_one({'checkout_request_id':reservation_id,'state':{'$in':['PAID_PENDING_OPERATION_REVIEW','APPROVED']}})
        if not row or row.get('currency')!='EUR' or row.get('amount_received_minor')!=500000 or not row.get('payment_reference'):
            fail('confirmed_5000_eur_reservation_required',409)
        user=await db.web_users.find_one({'subject_id':row['subject_id'],'active':True,'email_verified':True})
        from web_access_restrictions import blocked
        if not user or await blocked(db,user):fail('account_access_restricted')
        stamp=now()
        protocol={'_id':reservation_id,'subject_id':row['subject_id'],'op_ref':row['op_ref'],'state':'ACTIVE',
            'approved_at':stamp,'deadline_at':stamp+timedelta(hours=72),'approved_by':actor['subject_id'],
            'required_documents':list(dict.fromkeys(payload.required_documents))}
        try:await db.web_reservation_protocols.insert_one(protocol)
        except DuplicateKeyError:
            existing=await db.web_reservation_protocols.find_one({'_id':reservation_id})
            return {'already_approved':True,'deadline_at':existing['deadline_at']}
        await db.web_reservations.update_one({'checkout_request_id':reservation_id},{'$set':{'state':'APPROVED','approved_at':stamp}})
        await audit(db,actor['subject_id'],'RESERVATION_APPROVED_72H:'+reservation_id)
        return {'approved':True,'deadline_at':protocol['deadline_at']}
