import asyncio
from test_web_identity import system, login
from test_web_dossier import prepare
import web_review_mail as mailer

def test_readable_dni_fills_requirement_without_approving(system):
    c,db=prepare(system)
    r=c.post('/api/investor/personal-documents/doc/analysis',json={'kinds':['identity'],'detected_name':'ANTONIO GARCIA','quality':'READABLE'})
    assert r.status_code==200,r.text
    assert r.json()['dossier_state']=='FILED'
    assert db.raw.web_personal_documents.find_one()['operational_evidence'] is False
    assert db.raw.web_review_mail.count_documents({'state':'PENDING'})==1
    c.post('/api/investor/personal-documents/doc/analysis',json={'kinds':['identity'],'quality':'READABLE'})
    assert db.raw.web_review_mail.count_documents({})==1

def test_missing_name_is_not_misreported_as_bad_quality(system):
    c,db=prepare(system)
    r=c.post('/api/investor/personal-documents/doc/analysis',json={'kinds':['identity'],'quality':'READABLE'})
    assert r.json()['dossier_state']=='FILED'
    assert db.raw.web_personal_documents.find_one()['identity_read_status']=='REVIEW_REQUIRED'

def test_unreadable_does_not_fill_requirement(system):
    c,db=prepare(system)
    r=c.post('/api/investor/personal-documents/doc/analysis',json={'kinds':['identity'],'quality':'UNREADABLE'})
    assert r.json()['dossier_state']=='QUALITY_REJECTED'
    assert db.raw.web_review_mail.count_documents({})==0

def test_unnecessary_document_stays_temporary(system):
    c,db=prepare(system)
    r=c.post('/api/investor/personal-documents/doc/analysis',json={'kinds':['constitution'],'quality':'READABLE'})
    assert r.json()['dossier_state']=='TEMPORARY'

def test_company_identity_matches_its_requirement(system):
    c,db=prepare(system)
    db.raw.web_profile_drafts.update_one({}, {'$set':{'profile.subject_type':'PJ','profile.representative':'Antonio García'}})
    r=c.post('/api/investor/personal-documents/doc/analysis',json={'kinds':['identity'],'detected_name':'Antonio Garcia','quality':'READABLE'})
    assert r.json()['document_kinds']==['representative_identity']
    assert c.get('/api/investor/workspace').json()['required_documents']==['company_tax_document','representative_identity']

def test_mismatched_name_stays_unfiled(system):
    c,db=prepare(system)
    r=c.post('/api/investor/personal-documents/doc/analysis',json={'kinds':['identity'],'detected_name':'Jose Garcia','quality':'READABLE'})
    assert r.json()['dossier_state']=='DISCREPANCY'

def test_notice_to_info_has_no_document_or_identity_data_and_does_not_repeat(system,monkeypatch):
    c,db=prepare(system);sent=[]
    async def send(*args):sent.append(args)
    monkeypatch.setattr(mailer,'send_transactional',send)
    c.post('/api/investor/personal-documents/doc/analysis',json={'kinds':['identity'],'quality':'READABLE'})
    assert asyncio.run(mailer.dispatch(db)) is True
    assert asyncio.run(mailer.dispatch(db)) is False
    assert len(sent)==1 and sent[0][0]=='info@oportuniia.com'
    assert 'revision-cuentas.html#' in sent[0][2]
    assert 'Antonio' not in sent[0][2]

def test_notice_failure_is_queued_for_retry(system,monkeypatch):
    c,db=prepare(system)
    async def send(*args):raise RuntimeError('temporary provider failure')
    monkeypatch.setattr(mailer,'send_transactional',send)
    c.post('/api/investor/personal-documents/doc/analysis',json={'kinds':['identity'],'quality':'READABLE'})
    assert asyncio.run(mailer.dispatch(db)) is False
    assert db.raw.web_review_mail.find_one()['state']=='RETRY'

def test_received_backfill_deduplicates_identical_bytes(system):
    c,db=prepare(system)
    row=db.raw.web_personal_documents.find_one()
    db.raw.web_personal_documents.update_one({}, {'$set':{'sha256':'a'*64}})
    db.raw.web_personal_documents.insert_one({**{k:v for k,v in row.items() if k!='_id'},'document_id':'copy','sha256':'a'*64})
    asyncio.run(mailer.sync_received(db));asyncio.run(mailer.sync_received(db))
    assert db.raw.web_review_mail.count_documents({})==1

def test_superadmin_still_requires_mfa_and_manual_classification_never_approves(system):
    import web_review
    c,db=prepare(system)
    web_review.register_review_routes(c.app.router,db)
    web_review.register_review_routes(c.app.router,db,prefix='/account/reviews')
    db.raw.web_users.update_one({}, {'$set':{'role':'superadmin'}})
    assert c.get('/staff/reviews').status_code==403
    assert c.get('/account/reviews').status_code==403
    db.raw.web_users.update_one({}, {'$set':{'mfa_enabled':True}})
    db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':True}})
    assert c.get('/staff/reviews').status_code==200
    assert c.get('/account/reviews').status_code==200
    db.raw.web_personal_documents.update_one({}, {'$set':{'subject_id':'other-account','dossier_state':'READ_ERROR'}})
    r=c.post('/staff/reviews/other-account/documents/doc/classify',json={'kind':'identity','legible':True,'reason':'Original ficticio comprobado durante la prueba.'})
    assert r.status_code==200,r.text
    assert r.json()['identity_approved'] is False
    d=db.raw.web_personal_documents.find_one()
    assert d['dossier_state']=='FILED' and d['operational_evidence'] is False
