"""Read-only, metadata-only observation of sovereign application records.
Never starts work or treats a transport receipt as business completion.
"""
from __future__ import annotations
import asyncio, hmac, os, time
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request

MODULE_COLLECTIONS = {
 'CORE': ['jobs','trace_events','m2m_outbox'],
 'IA': ['m2m_core_inbox','jobs','assets','m2m_outbox','m2m_inbox'],
 'LEGAL': ['m2m_direct_ia_inbox','legal_operation_trace','legal_operation_results','legal_result_returns','m2m_outbox','m2m_inbox'],
 'APP': ['m2m_inbox','m2m_outbox','properties','reports','field_mission_results','post_field_results','post_field_outputs'],
 'VISUAL': ['inbound_receipts','operations','photos','m2m_presentation_outbox'],
 'WEB': ['presentation_web_drafts','presentation_web_active','presentation_web_published'],
}
REF_KEYS = ('id','event_id','correlation_id','internal_id','job_id','portfolio_id','portfolio_reference','perimeter_id','perimeter_ref','operation_id','op_reference','output_id','report_id','mission_id','property_id','provenance_reference','source_output_id','id_interno','id_tecnico','ref_oportuniia','activo_id','field_mission_id')
CONTAINERS = ('payload','business_ref','source_references','l1_ref','traceability','source','metadata','provenance')
SAFE_KEYS = ('status','state','business_status','event_type','relationship','stage','phase','step','consumer','producer','target','created_at','updated_at','timestamp','received_at','completed_at','acked_at','next_attempt_at','attempt','attempt_count','work_status','publication_state','estado','total_discard','recorded_at','occurred_at')

def now(): return datetime.now(timezone.utc).isoformat()

def references(doc):
    found=set()
    def visit(value, depth=0):
        if not isinstance(value,dict) or depth>3: return
        for key in REF_KEYS:
            val=value.get(key)
            if isinstance(val,(str,int)) and 0<len(str(val))<=180:
                found.add(str(val))
                if key=='provenance_reference' and str(val).startswith('job:'): found.add(str(val)[4:])
        for key in CONTAINERS: visit(value.get(key),depth+1)
    visit(doc)
    return sorted(found)

def clean(doc, collection, module):
    item={k:doc[k].isoformat() if isinstance(doc[k],datetime) else doc[k] for k in SAFE_KEYS if isinstance(doc.get(k),(str,int,float,bool,datetime))}
    item.update(collection=collection,module=module,refs=references(doc))
    item['internal_id']=str(doc.get('internal_id') or '')
    item['record_id']=str(doc.get('id') or doc.get('event_id') or doc.get('internal_id') or doc.get('_id') or '')
    item['kind']='transport' if 'm2m' in collection or collection=='inbound_receipts' else ('history' if collection=='trace_events' else 'business')
    if module=='LEGAL' and collection=='legal_operation_results':
        item['state']='DISCARDED' if doc.get('total_discard') is True else doc.get('work_status','PENDING')
    if module=='WEB':
        item['state']=doc.get('publication_state','PENDING')
    if module=='VISUAL' and collection=='photos':
        version=next((v for v in doc.get('versions',[]) if v.get('id')==doc.get('current_version_id')),None)
        item['state']='DONE' if version and version.get('state')=='aprobada' else 'PENDING'
    if module=='IA' and collection=='assets':
        computed=doc.get('computed') or {}
        item['score']=computed.get('score_global')
        item['secondary_score']=computed.get('acuerdo_score')
        item['classification']=computed.get('clasificacion_v2') or computed.get('clasificacion')
        item['state']='ERROR' if computed.get('error_status')=='EXCLUIDO_POR_ERROR' else ('DONE' if computed else 'PENDING')
    return item

async def mongo_snapshot(db,module):
    projection={'_id':1,**{k:1 for k in REF_KEYS+SAFE_KEYS}}
    for container in CONTAINERS:
        for key in REF_KEYS: projection[f'{container}.{key}']=1
    if module=='IA':
        for key in ('score_global','acuerdo_score','clasificacion_v2','clasificacion','error_status'): projection['computed.'+key]=1
    if module=='VISUAL':
        projection.update({'current_version_id':1,'versions.id':1,'versions.state':1})
    async def read(collection):
        rows=await db[collection].find({},projection).sort('_id',-1).limit(1001).to_list(1001)
        return [clean(x,collection,module) for x in rows[:1000]],len(rows)>1000
    results=await asyncio.gather(*(read(c) for c in MODULE_COLLECTIONS[module]))
    return {'module':module,'observed_at':now(),'complete':not any(x[1] for x in results),'records':[r for x in results for r in x[0]]}

def build_router(module, db_factory=None, snapshot=None):
    router=APIRouter(prefix='/api/control-observer',tags=['internal-read-only-control'])
    cache={'at':0,'data':None}; lock=asyncio.Lock()
    @router.get('/snapshot')
    async def read_snapshot(request:Request):
        secret=os.environ.get('CONTROL_OBSERVER_KEY','')
        if not secret: raise HTTPException(503,'CONTROL_OBSERVER_NOT_CONFIGURED')
        if not hmac.compare_digest(request.headers.get('X-Control-Observer-Key',''),secret): raise HTTPException(401,'Unauthorized')
        async with lock:
            if time.monotonic()-cache['at']<(60 if module=='PRESENTACION' else 10) and cache['data']: return cache['data']
            data=await snapshot() if snapshot else await mongo_snapshot(db_factory(),module)
            cache.update(at=time.monotonic(),data=data)
            return data
    return router
