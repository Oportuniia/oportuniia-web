"""Daily and weekly aggregate emails. No DNI, names or individual file notices."""
from collections import Counter
from datetime import datetime,timedelta,timezone,time
from zoneinfo import ZoneInfo
from pymongo.errors import DuplicateKeyError
from web_identity import send_transactional

MADRID=ZoneInfo('Europe/Madrid')
def period(now,weekly=False):
    local=now.astimezone(MADRID)
    end=local.date()-timedelta(days=local.weekday()) if weekly else local.date()
    begin=end-timedelta(days=7 if weekly else 1)
    return datetime.combine(begin,time(),MADRID).astimezone(timezone.utc),datetime.combine(end,time(),MADRID).astimezone(timezone.utc)

async def report(db,start,end,weekly=False):
    users=await db.web_users.find({'created_at':{'$gte':start,'$lt':end},'role':{'$ne':'superadmin'}},{'_id':0,'subject_id':1,'email_verified':1}).to_list(10001)
    limited=len(users)>10000;users=users[:10000]
    ids=[u['subject_id'] for u in users]
    drafts=await db.web_profile_drafts.find({'subject_id':{'$in':ids}},{'_id':0,'subject_id':1,'profile.subject_type':1,'profile.country':1,'profile.province':1,'profile.municipality':1,'state':1,'automatic_state':1}).to_list(10000)
    by_id={d['subject_id']:d for d in drafts}
    counts=Counter((by_id.get(i,{}).get('profile',{}).get('subject_type') or 'Sin completar') for i in ids)
    states=Counter(by_id.get(i,{}).get('automatic_state') or by_id.get(i,{}).get('state') or 'Sin perfil' for i in ids)
    lines=[f"Periodo: {start.astimezone(MADRID):%d/%m/%Y} a {(end-timedelta(seconds=1)).astimezone(MADRID):%d/%m/%Y}",
        f"Altas registradas: {len(users)}"+(' (informe limitado a 10.000; consultar administración)' if limited else ''),
        f"Correo confirmado: {sum(bool(u.get('email_verified')) for u in users)}",
        'Tipos: '+', '.join(f'{k}: {v}' for k,v in sorted(counts.items())),
        'Estado actual de estas altas: '+', '.join(f'{k}: {v}' for k,v in sorted(states.items()))]
    if weekly:
        for key,label in [('country','Países'),('province','Provincias'),('municipality','Municipios')]:
            counter=Counter(str(by_id.get(i,{}).get('profile',{}).get(key) or 'Sin completar') for i in ids)
            lines.append(label+' (datos declarados): '+', '.join(f'{k}: {v}' for k,v in counter.most_common(20)))
        payments=await db.web_checkout_intents.find({'state':'PAID','paid_at':{'$gte':start,'$lt':end}},{'_id':0,'kind':1}).to_list(10001)
        lines.append('Pagos confirmados de Premium/reservas: '+str(len(payments))+' (no equivalen a compraventas).')
        lines.append('Compraventas por zona: pendiente de disponer de una fuente de cierres de compraventa confirmados. No se infiere a partir de altas ni reservas.')
        lines.append('La procedencia refleja el perfil actual de las altas del periodo, no geolocalización ni seguimiento individual.')
    lines.append('Consulta perfiles y excepciones en https://oportuniia.com/revision-cuentas.html')
    return '\n\n'.join(lines)

async def tick(db,now=None):
    now=now or datetime.now(timezone.utc);local=now.astimezone(MADRID)
    if local.hour<8:return
    for weekly in (False,True):
        start,end=period(now,weekly);ident=('weekly:' if weekly else 'daily:')+end.isoformat()
        existing=await db.web_management_reports.find_one({'_id':ident})
        if existing and (existing.get('state') not in {'RETRY'} or existing.get('next_attempt',now)>now):continue
        token=now.isoformat()
        try:
            claimed=await db.web_management_reports.update_one({'_id':ident,'state':{'$nin':['SENT','SENDING']}}, {'$set':{'state':'SENDING','claimed_at':now,'token':token},'$inc':{'attempts':1}},upsert=True)
        except DuplicateKeyError:continue
        if not (claimed.modified_count or claimed.upserted_id):continue
        try:
            body=await report(db,start,end,weekly)
            await send_transactional('info@oportuniia.com','OPORTUNIIA · '+('Informe semanal' if weekly else 'Resumen diario')+' de altas',body)
            await db.web_management_reports.update_one({'_id':ident,'token':token},{'$set':{'state':'SENT','sent_at':now,'start':start,'end':end}})
        except Exception:
            record=await db.web_management_reports.find_one({'_id':ident}) or {}
            await db.web_management_reports.update_one({'_id':ident,'token':token},{'$set':{'state':'RETRY' if record.get('attempts',0)<5 else 'FAILED','next_attempt':now+timedelta(minutes=10)}})
