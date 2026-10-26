"""Master-only operational dashboard. Whitelisted records, no document contents."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from fastapi import Request, Query
from web_accounts import administrator
from investor_access import premium_period_active
from web_identity import audit

SOURCES = {
 'users': ('web_users','created_at', 'Usuarios'),
 'recommendations': ('web_recommendations','created_at','Recomendaciones'),
 'views': ('web_recommendations','viewed_at','Fichas consultadas'),
 'reservations': ('web_reservations','created_at','Reservas'),
 'payments': ('web_checkout_intents','paid_at','Pagos confirmados'),
 'work': ('web_message_threads','created_at','Solicitudes y consultas'),
 'reports': ('web_management_reports','sent_at','Resúmenes históricos'),
}
FIELDS={'subject_id':1,'name':1,'username':1,'role':1,'account_kind':1,'active':1,'created_at':1,'sender_id':1,'investor_id':1,'op_ref':1,'channel':1,'viewed_at':1,'state':1,'status':1,'kind':1,'paid_at':1,'sent_at':1,'start':1,'end':1,'body_summary':1,'campaign_id':1,'provider':1}

def stamp(value):
 try:
  d=value if isinstance(value,datetime) else datetime.fromisoformat(str(value).replace('Z','+00:00'))
  return d.replace(tzinfo=timezone.utc) if not d.tzinfo else d
 except (ValueError,TypeError): return None

async def data(db,days):
 now=datetime.now(timezone.utc); start=now-timedelta(days=days); previous=start-timedelta(days=days)
 result={'generated_at':now.isoformat(),'days':days,'metrics':[],'series':{},'limited':False}
 for key,(collection,date,label) in SOURCES.items():
  query={'purge_completed':{'$ne':True}} if key=='users' else {'state':'PAID'} if key=='payments' else {}
  rows=await getattr(db,collection).find(query,FIELDS).to_list(10001)
  result['limited'] |= len(rows)>10000
  rows=rows[:10000]; current=[]; prior=0; series=Counter()
  for row in rows:
   d=stamp(row.get(date))
   if d and start<=d<=now:
    current.append(row);series[d.date().isoformat()]+=1
   elif d and previous<=d<start:prior+=1
  result['metrics'].append({'key':key,'label':label,'value':len(current),'previous':prior,'undated':sum(stamp(r.get(date)) is None for r in rows)})
  result['series'][key]=dict(sorted(series.items()))
 users=await db.web_users.find({'active':True,'purge_completed':{'$ne':True},'role':{'$ne':'superadmin'}},{'subject_id':1,'account_kind':1}).to_list(10001)
 ent=await db.web_entitlements.find({'product':'PREMIUM','active':True}).to_list(10001)
 prof=await db.web_professionals.find({'active':True}).to_list(10001)
 from investor_access import future
 included={p['_id'] for p in prof if p.get('kind')=='suscriptor' and future(p.get('valid_until'))}
 active={e['subject_id']:e for e in ent if premium_period_active(e)}
 result['segments']={'premium_paid':sum(u['subject_id'] in active and active[u['subject_id']].get('provider')!='MASTER_TEST' for u in users),'premium_test':sum(u['subject_id'] in active and active[u['subject_id']].get('provider')=='MASTER_TEST' for u in users),'premium_included':sum(u['subject_id'] in included and u['subject_id'] not in active for u in users),'standard':sum(u['subject_id'] not in active and u['subject_id'] not in included for u in users)}
 result['profiles']=dict(Counter(u.get('account_kind','Sin clasificar') for u in users))
 result['technical']=await db.web_technical_minutes.find({'minute':{'$gte':start.isoformat()}},{'_id':0}).sort('minute',-1).to_list(1500)
 result['coverage']=['Los periodos son ventanas móviles; se comparan con el periodo anterior de igual duración.','Premium indica derechos vigentes, no facturación ni aprobación del expediente.','Los registros sin fecha no se atribuyen a ningún periodo.','No hay seguimiento público de visitantes ni campañas conectado todavía.','Los tiempos técnicos miden la respuesta de la API, no la carga visual de la página.']
 return result

def register_control_routes(router,db):
 @router.get('/account/control')
 async def dashboard(request:Request, days:int=Query(7,ge=1,le=366)):
  await administrator(request,db)
  return await data(db,days)
 @router.get('/account/control/records')
 async def records(request:Request,category:str='users',days:int=Query(7,ge=1,le=366),offset:int=Query(0,ge=0,le=10000)):
  await administrator(request,db)
  from investor_access import fail
  if category not in SOURCES:fail('invalid_category',422)
  collection,date,_=SOURCES[category]; query={'state':'PAID'} if category=='payments' else {'purge_completed':{'$ne':True}} if category=='users' else {}
  rows=await getattr(db,collection).find(query,FIELDS).to_list(10001)
  end=datetime.now(timezone.utc);start=end-timedelta(days=days)
  selected=[r for r in rows[:10000] if stamp(r.get(date)) and start<=stamp(r.get(date))<=end]
  selected.sort(key=lambda r:stamp(r[date]),reverse=True)
  for r in selected:
   r['id']=str(r.pop('_id',''))
  return {'items':selected[offset:offset+50],'total':len(selected),'limited':len(rows)>10000}
 @router.post('/account/control/rafa-premium')
 async def test_premium(request:Request):
  actor=await administrator(request,db)
  user=await db.web_users.find_one({'username':'rafa.querol','active':True,'role':{'$ne':'superadmin'}})
  from investor_access import fail
  if not user:fail('account_not_found',404)
  existing=await db.web_entitlements.find_one({'subject_id':user['subject_id'],'product':'PREMIUM','active':True})
  if existing and premium_period_active(existing):return {'already_active':True}
  now=datetime.now(timezone.utc);end=now+timedelta(days=30)
  await db.web_entitlements.update_one({'subject_id':user['subject_id'],'product':'PREMIUM'},{'$set':{'subject_id':user['subject_id'],'product':'PREMIUM','active':True,'provider':'MASTER_TEST','valid_from':now.isoformat(),'valid_until':end.isoformat(),'granted_by':actor['subject_id']}},upsert=True)
  await audit(db,actor['subject_id'],'premium_test_granted:'+user['subject_id'])
  return {'valid_until':end.isoformat(),'charged':False}

# Aggregate technical counters only: no IP, query string, body or user identifier.
import asyncio
import time
technical_bucket = {}
async def flush_technical(db):
 global technical_bucket
 snapshot=technical_bucket;technical_bucket={}
 try:
  for minute,values in snapshot.items():
   await db.web_technical_minutes.update_one({'_id':minute},{'$set':{'minute':minute},'$inc':values},upsert=True)
  await db.web_technical_minutes.delete_many({'minute':{'$lt':(datetime.now(timezone.utc)-timedelta(days=366)).isoformat()}})
 except Exception:
  pass  # Monitoring never blocks access; lost samples are not reconstructed.

def install_technical(app,db):
 @app.middleware('http')
 async def measured(request,call_next):
  started=time.monotonic();status=500
  try:
   response=await call_next(request);status=response.status_code;return response
  finally:
   if db is not None and request.url.path.startswith('/api/') and not request.url.path.startswith('/api/account/control'):
    minute=datetime.now(timezone.utc).replace(second=0,microsecond=0).isoformat()
    bucket=technical_bucket.setdefault(minute,{'requests':0,'errors':0,'duration_ms':0})
    bucket['requests']+=1;bucket['errors']+=int(status>=500);bucket['duration_ms']+=round((time.monotonic()-started)*1000)
    if len(technical_bucket)>1:
     await flush_technical(db)
