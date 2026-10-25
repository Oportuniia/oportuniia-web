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


@pytest.mark.parametrize('hold,expected',[(False,'APPROVED'),(True,'EXCEPTION')])
def test_profile_edit_rechecks_but_never_lifts_admin_hold(system,monkeypatch,hold,expected):
    c,db,mail=system;login(c,mail)
    subject=db.raw.web_users.find_one({})['subject_id']
    db.raw.web_access_reviews.insert_one({'subject_id':subject,'revoked':hold,'identity_status':'REJECTED' if hold else 'VERIFIED'})
    payload={'account_kind':'inversor','subject_type':'PF','full_name':'Fixture','email':'one@example.com'}
    r=c.post('/api/investor/profile-draft',json=payload)
    assert r.status_code==200,r.text
    draft=db.raw.web_profile_drafts.find_one({'subject_id':subject})
    db.raw.web_personal_documents.insert_one({'subject_id':subject,'document_id':'d','sha256':'abc','scan_state':'CLEAN','category':'identity'})
    monkeypatch.setattr(automatic,'missing_profile_fields',lambda p:[])
    monkeypatch.setattr(automatic,'server_read',lambda *a:evidence())
    assert asyncio.run(automatic.process_profile(db,draft))==expected
    review=db.raw.web_access_reviews.find_one({'subject_id':subject})
    assert review['revoked'] is hold
    if not hold:
        assert review['pbc_status']=='PENDING'
        assert 'automatic_recheck_revision' not in review
    assert db.raw.web_operation_grants.count_documents({})==0


def test_admin_hold_during_reader_is_not_overwritten(system,monkeypatch):
    c,db,mail=system;login(c,mail)
    subject=db.raw.web_users.find_one({})['subject_id']
    draft={'subject_id':subject,'revision':'new','state':'PENDING_REVIEW','profile':{'subject_type':'PF'}}
    db.raw.web_profile_drafts.insert_one(draft)
    db.raw.web_access_reviews.insert_one({'subject_id':subject,'revoked':True,'automatic_recheck_revision':'new'})
    db.raw.web_personal_documents.insert_one({'subject_id':subject,'document_id':'d','sha256':'abc','scan_state':'CLEAN','category':'identity'})
    monkeypatch.setattr(automatic,'missing_profile_fields',lambda p:[])
    def read(*args):
        db.raw.web_access_reviews.update_one({'subject_id':subject},{'$set':{'revoked':True},'$unset':{'automatic_recheck_revision':''}})
        return evidence()
    monkeypatch.setattr(automatic,'server_read',read)
    assert asyncio.run(automatic.process_profile(db,draft))=='EXCEPTION'
    assert db.raw.web_access_reviews.find_one({'subject_id':subject})['revoked']
    assert db.raw.web_notifications.count_documents({'title':'Alta aprobada'})==0

@pytest.mark.parametrize('subject_type',['PF','PJ'])
def test_complete_profile_approval_and_dossier_with_real_field_rules(system,monkeypatch,subject_type):
    c,db,mail=system;login(c,mail)
    subject=db.raw.web_users.find_one({})['subject_id']
    profile={'account_kind':'inversor','subject_type':subject_type,'full_name':'Ana Garcia Lopez','email':'one@example.com','tax_id':'12345678Z','birth_date':'1980-01-01','fiscal_address':'Calle Prueba','fiscal_address_number':'1','address':'Calle Prueba','address_number':'1','municipality':'Madrid','province':'Madrid','region':'Madrid','country':'ES','nationality':'ES','professional_activity':'Prueba','consents':{k:True for k in ('privacy','truthfulness','no_commitment','terms')}}
    if subject_type=='PJ':profile.update(company_name='Empresa Ensayo SL',company_tax_id='B12345674',registered_address='Calle Prueba',registered_address_number='1',representative='Ana Garcia Lopez',representative_id='12345678Z',representative_position='Administrador')
    assert automatic.missing_profile_fields(profile)==[]
    assert c.post('/api/investor/profile-draft',json=profile).status_code==200
    draft=db.raw.web_profile_drafts.find_one({'subject_id':subject})
    text='DOCUMENTO NACIONAL DE IDENTIDAD\nAPELLIDOS\nGARCIA LOPEZ\nNOMBRE\nANA\n12345678Z\n01/01/1980\nVALIDEZ 01/01/2090'
    texts={'identity':text,'fiscal':'AGENCIA TRIBUTARIA\nIDENTIFICACION FISCAL\nEMPRESA ENSAYO SL\nB12345674'}
    for kind in (['identity','fiscal'] if subject_type=='PJ' else ['identity']):
        db.raw.web_personal_documents.insert_one({'subject_id':subject,'document_id':kind,'sha256':kind,'scan_state':'CLEAN','created_at':datetime.now(timezone.utc)})
    monkeypatch.setattr(automatic,'server_read',lambda row,p:evaluate_text(texts[row['document_id']],.99,p))
    assert asyncio.run(automatic.process_profile(db,draft))=='APPROVED'
    access=c.get('/api/investor/access').json()
    assert access['identity_status']=='VERIFIED' and access['dossier_status']=='APPROVED'
    assert access['pbc_status']=='PENDING' and not access['premium']
    assert db.raw.web_operation_grants.count_documents({})==0
    kinds={k for d in db.raw.web_personal_documents.find({'review_state':'APPROVED'}) for k in d['document_kinds']}
    assert kinds==({'representative_identity','company_tax_document'} if subject_type=='PJ' else {'identity'})


def test_inline_labels_and_spaced_number_are_read_without_fuzzy_identity_matching():
    text='DOCUMENTO NACIONAL DE IDENTIDAD\nAPELLIDOS: GARCIA LOPEZ\nNOMBRE: ANA\n12345678 Z\n01/01/1980\nVALIDEZ 01/01/2090'
    profile={'subject_type':'PF','full_name':'Ana Garcia Lopez','tax_id':'12345678Z','birth_date':'1980-01-01'}
    result=evaluate_text(text,.99,profile)
    assert result['name_matches'] and result['number_matches']
    assert not evaluate_text(text,.99,{**profile,'full_name':'Ana Garcia'})['name_matches']
    assert not evaluate_text(text+'\n87654321X',.99,profile)['number_matches']


def test_new_reader_version_retries_old_failures_but_keeps_current_limit(monkeypatch):
    db=DB();draft={'subject_id':'fixture','revision':'r','state':'PENDING_REVIEW','profile':{'subject_type':'PF'}}
    db.raw.web_users.insert_one({'subject_id':'fixture','active':True,'email_verified':True})
    db.raw.web_profile_drafts.insert_one(draft)
    db.raw.web_personal_documents.insert_one({'subject_id':'fixture','document_id':'d','sha256':'a','scan_state':'CLEAN','server_read_failures':2,'server_read_failure_version':automatic.READER_VERSION-1})
    monkeypatch.setattr(automatic,'missing_profile_fields',lambda p:[])
    attempts=[]
    def failed(*args):attempts.append(1);raise ValueError('fixture')
    monkeypatch.setattr(automatic,'server_read',failed)
    for _ in range(3):asyncio.run(automatic.process_profile(db,draft))
    assert len(attempts)==2
    assert db.raw.web_personal_documents.find_one({})['server_read_failure_version']==automatic.READER_VERSION
    assert db.raw.web_access_reviews.count_documents({})==0
