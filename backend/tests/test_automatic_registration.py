import asyncio
from datetime import datetime,timezone
import pytest
from test_web_identity import system,DB,login
import web_auto_registration as automatic
import web_digest as digest
from web_document_reader import evaluate_text

def evidence(**changes):
    return dict(legible=True,identity=True,name_matches=True,number_matches=True,birth_matches=True,expiry_read_and_valid=True,fictitious=False,**changes)

def test_consistency_does_not_accept_missing_fields_or_fictitious_files():
    good=evidence()
    assert automatic.qualifies([good],False)
    for key in ('legible','name_matches','number_matches','birth_matches','expiry_read_and_valid'):
        assert not automatic.qualifies([{**good,key:False}],False)
    assert not automatic.qualifies([{**good,'fictitious':True}],False)
    assert not automatic.qualifies([good],True)
    assert automatic.qualifies([good,{'legible':True,'fiscal':True,'company_matches':True}],True)

def test_name_must_be_exact_not_a_substring():
    text='DOCUMENTO NACIONAL DE IDENTIDAD\nGARCIA<<JOSEFINA\n12345678Z\nVALIDEZ 01/01/2090\n01/01/1980'
    profile={'full_name':'Jose Garcia','tax_id':'12345678Z','birth_date':'1980-01-01'}
    assert not evaluate_text(text,.99,profile)['name_matches']
    profile['full_name']='Josefina Garcia'
    assert evaluate_text(text,.99,profile)['name_matches']

def test_browser_classification_cannot_approve_and_server_evidence_can(monkeypatch):
    db=DB();subject='fixture';revision='r1'
    draft={'subject_id':subject,'revision':revision,'state':'PENDING_REVIEW','profile':{'subject_type':'PF'}}
    db.raw.web_users.insert_one({'subject_id':subject,'email':'fictional@example.invalid','active':True,'email_verified':True})
    db.raw.web_profile_drafts.insert_one(draft)
    db.raw.web_personal_documents.insert_one({'subject_id':subject,'document_id':'d','sha256':'abc','scan_state':'CLEAN','dossier_state':'FILED','quality':'READABLE','document_kinds':['identity']})
    monkeypatch.setattr(automatic,'missing_profile_fields',lambda p:[])
    monkeypatch.setattr(automatic,'server_read',lambda *a:{**evidence(),'name_matches':False})
    assert asyncio.run(automatic.process_profile(db,draft))=='EXCEPTION'
    assert db.raw.web_access_reviews.count_documents({})==0
    db.raw.web_personal_documents.update_one({}, {'$unset':{'server_reading':''}})
    monkeypatch.setattr(automatic,'server_read',lambda *a:evidence())
    assert asyncio.run(automatic.process_profile(db,draft))=='APPROVED'
    assert db.raw.web_access_reviews.find_one()['pbc_status']=='PENDING'
    assert db.raw.web_access_reviews.find_one()['authenticity_verified'] is False
    assert db.raw.web_operation_grants.count_documents({})==0
    assert asyncio.run(automatic.process_profile(db,draft))=='ALREADY_APPROVED'
    assert db.raw.web_registration_decisions.count_documents({})==1

def test_founder_entitlement_requires_specific_account_and_keeps_mfa(system):
    c,db,mail=system;login(c,mail)
    db.raw.web_users.update_one({}, {'$set':{'username':'rafamaster','email':'info@oportuniia.com','role':'user'}})
    assert c.get('/api/investor/access').json()['founder_access'] is False
    db.raw.web_users.update_one({}, {'$set':{'role':'superadmin'}})
    assert c.get('/api/investor/access').status_code==403
    db.raw.web_users.update_one({}, {'$set':{'mfa_enabled':True}})
    db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':True}})
    r=c.get('/api/investor/access').json()
    assert r['founder_access'] and r['premium'] and r['dossier_status']=='NOT_REQUIRED'
    assert r['contracting']['documents_verified'] is False
    db.raw.web_users.update_one({}, {'$set':{'username':'another-admin'}})
    assert c.get('/api/investor/access').json()['founder_access'] is False

def test_digest_deduplicates_sends_aggregate_not_documents(monkeypatch):
    db=DB();sent=[]
    async def send(*args):sent.append(args)
    monkeypatch.setattr(digest,'send_transactional',send)
    now=datetime(2026,10,26,8,tzinfo=timezone.utc)
    db.raw.web_users.insert_one({'subject_id':'x','name':'DO NOT EMAIL NAME','created_at':datetime(2026,10,25,12,tzinfo=timezone.utc),'email_verified':True})
    db.raw.web_profile_drafts.insert_one({'subject_id':'x','profile':{'subject_type':'PJ','province':'Barcelona'}})
    asyncio.run(digest.tick(db,now));asyncio.run(digest.tick(db,now))
    assert len(sent)==2 and all(m[0]=='info@oportuniia.com' for m in sent)
    assert 'Altas registradas: 1' in sent[0][2]
    assert all('DO NOT EMAIL NAME' not in m[2] for m in sent)
    assert 'Barcelona' in sent[1][2]

def test_digest_period_uses_madrid_calendar_across_dst():
    start,end=digest.period(datetime(2026,10,26,8,tzinfo=timezone.utc))
    assert (end-start).total_seconds()==25*3600

def test_failed_profile_does_not_block_queue(monkeypatch):
    db=DB()
    for name in ('bad','good'):
        db.raw.web_profile_drafts.insert_one({'subject_id':name,'revision':'r','state':'PENDING_REVIEW'})
    seen=[]
    async def process(db,draft):
        seen.append(draft['subject_id'])
        if draft['subject_id']=='bad':raise ValueError('fixture')
        return 'WAITING_DETAILS'
    monkeypatch.setattr(automatic,'process_profile',process)
    asyncio.run(automatic.run(db));asyncio.run(automatic.run(db))
    assert seen==['bad','good']
    assert db.raw.web_profile_drafts.find_one({'subject_id':'bad'})['auto_last_result']=='PROCESSING_ERROR'
