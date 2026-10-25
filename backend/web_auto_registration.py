"""Automatic website registration based on server-read document consistency.
Does not verify authenticity or grant operation-specific/AML permissions.
Browser declarations can never create the trusted evidence used here.
"""
import asyncio
import base64
import json
import subprocess
import sys
import uuid
from datetime import datetime,timedelta,timezone
from pathlib import Path
from pymongo.errors import DuplicateKeyError
from investor_access import missing_profile_fields
from web_dossier import expired
from web_personal_storage import read

def server_read(row,profile):
    from web_document_processing import document_processing_slot
    with document_processing_slot:
        return _server_read(row,profile)

def _server_read(row,profile):
    raw=read(row)  # decrypt and verify original SHA-256 before any parser
    payload=json.dumps({'data':base64.b64encode(raw).decode(),'profile':profile}).encode()
    result=subprocess.run([sys.executable,str(Path(__file__).with_name('web_document_reader.py'))],input=payload,
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=120,check=True)
    if len(result.stdout)>16000:raise ValueError('reader_output_limit')
    return json.loads(result.stdout)

def qualifies(results,company):
    clean=[r for r in results if r.get('legible') and not r.get('fictitious')]
    identity=any(all(r.get(k) for k in ('identity','name_matches','number_matches','birth_matches','expiry_read_and_valid')) for r in clean)
    return identity and (not company or any(r.get('fiscal') and r.get('company_matches') for r in clean))

async def process_profile(db,draft):
    subject=draft['subject_id'];revision=draft.get('revision');profile=draft.get('profile',{})
    if not revision or missing_profile_fields(profile):return 'WAITING_DETAILS'
    user=await db.web_users.find_one({'subject_id':subject,'active':True,'email_verified':True})
    if not user or user.get('role')=='superadmin':return 'SKIPPED'
    blocked_keys=[{'subject_id':subject},{'email':user['email']}]+[{'tax_id':value} for value in (profile.get('tax_id'),profile.get('company_tax_id')) if value]
    if await db.web_registration_blocks.find_one({'$or':blocked_keys, 'active':True}):return 'EXCEPTION'
    current=await db.web_access_reviews.find_one({'subject_id':subject}) or {}
    if current.get('revoked'):return 'EXCEPTION'
    if current.get('profile_revision')==revision and not current.get('revoked') and current.get('dossier_status')=='APPROVED':return 'ALREADY_APPROVED'
    docs=await db.web_personal_documents.find({'subject_id':subject,'scan_state':'CLEAN','deleted':{'$ne':True}}).sort('created_at',-1).to_list(10)
    results=[];ids=[]
    for doc in docs:
        if expired(doc):continue
        evidence=doc.get('server_reading',{})
        if evidence.get('profile_revision')!=revision or evidence.get('sha256')!=doc.get('sha256'):
            if doc.get('server_read_failures',0)>=2:continue
            try:result=await asyncio.to_thread(server_read,doc,profile)
            except Exception:
                await db.web_personal_documents.update_one({'_id':doc['_id']},{'$inc':{'server_read_failures':1},'$set':{'server_read_state':'RETRY_OR_EXCEPTION'}})
                continue
            evidence={**result,'profile_revision':revision,'sha256':doc['sha256'],'at':datetime.now(timezone.utc)}
            await db.web_personal_documents.update_one({'_id':doc['_id'],'sha256':doc['sha256']},{'$set':{'server_reading':evidence,'server_read_state':'COMPLETE'}})
        results.append(evidence);ids.append(doc['document_id'])
    if not qualifies(results,profile.get('subject_type')=='PJ'):
        await db.web_profile_drafts.update_one({'subject_id':subject,'revision':revision},{'$set':{'automatic_state':'NEEDS_CORRECTION_OR_EXCEPTION'}})
        return 'EXCEPTION'
    stamp=datetime.now(timezone.utc);decision='automatic:'+subject+':'+revision
    # Stable identity and revision prevent duplicate events. Access checks compare
    # the saved revision on every request, so later edits invalidate this result.
    await db.web_registration_decisions.update_one({'_id':decision},{'$setOnInsert':{'subject_id':subject,'revision':revision,'at':stamp,'basis':'SERVER_DOCUMENT_CONSISTENCY','authenticity_verified':False,'documents':ids}},upsert=True)
    await db.web_verified_profiles.update_one({'subject_id':subject,'version':decision},{'$setOnInsert':{'profile':profile,'created_at':stamp,'verification_basis':'SERVER_DOCUMENT_CONSISTENCY'}},upsert=True)
    await db.web_access_reviews.update_one({'subject_id':subject},{'$set':{'profile_version':decision,'profile_revision':revision,'profile_complete':True,'documents_complete':True,'identity_status':'VERIFIED','dossier_status':'APPROVED','pbc_status':'PENDING','revoked':False,'valid_until':(stamp+timedelta(days=90)).isoformat(),'verification_basis':'SERVER_DOCUMENT_CONSISTENCY','authenticity_verified':False}},upsert=True)
    await db.web_profile_drafts.update_one({'subject_id':subject,'revision':revision},{'$set':{'state':'REVIEWED','automatic_state':'APPROVED'}})
    for document_id,evidence in zip(ids,results):
        kinds=[]
        if qualifies([evidence],False):kinds.append('representative_identity' if profile.get('subject_type')=='PJ' else 'identity')
        if profile.get('subject_type')=='PJ' and evidence.get('legible') and evidence.get('fiscal') and evidence.get('company_matches') and not evidence.get('fictitious'):kinds.append('company_tax_document')
        if kinds:
            await db.web_personal_documents.update_one({'subject_id':subject,'document_id':document_id,'scan_state':'CLEAN','deleted':{'$ne':True}},{'$set':{'review_state':'APPROVED','dossier_state':'FILED','document_kinds':kinds,'review_decision_id':decision,'operational_evidence':True}})
    await db.web_notifications.update_one({'id':decision},{'$setOnInsert':{'subject_id':subject,'title':'Alta aprobada','body':'La documentación coincide con tu perfil. Tu alta está aprobada. Los permisos de cada operación se gestionan por separado.','read':False,'created_at':stamp}},upsert=True)
    return 'APPROVED'

async def run(db):
    stamp=datetime.now(timezone.utc);token=str(uuid.uuid4())
    try:
        claimed=await db.web_job_leases.update_one({'_id':'automatic-registration','$or':[{'until':{'$lte':stamp}},{'until':{'$exists':False}}]}, {'$set':{'until':stamp+timedelta(minutes=25),'token':token}},upsert=True)
    except DuplicateKeyError:return
    if not (claimed.modified_count or claimed.upserted_id):return
    try:
        drafts=await db.web_profile_drafts.find({'state':'PENDING_REVIEW'}).sort('auto_checked_at',1).to_list(1)
        for draft in drafts:
            try:
                result=await process_profile(db,draft)
                status={'auto_last_result':result,'auto_error_type':None}
            except Exception as error:
                # A malformed old profile must not starve every later account.
                status={'auto_last_result':'PROCESSING_ERROR','auto_error_type':type(error).__name__}
            await db.web_profile_drafts.update_one({'subject_id':draft['subject_id'],'revision':draft.get('revision')},{'$set':{'auto_checked_at':stamp,**status}})
    finally:
        await db.web_job_leases.update_one({'_id':'automatic-registration','token':token},{'$set':{'until':datetime.now(timezone.utc)}})

async def worker(db):
    while True:
        try:await run(db)
        except Exception:pass
        await asyncio.sleep(30)
