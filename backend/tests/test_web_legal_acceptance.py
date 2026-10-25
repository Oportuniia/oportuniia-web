from test_web_identity import system, signup, login, PASSWORD
from web_legal_acceptance import bundle

def payload(**kw):
    return dict(name='Persona ficticia',email='legal@example.com',password=PASSWORD,account_kind='inversor',accept_privacy=True,accept_terms=True,legal_bundle_id=bundle()['id'],**kw)

def test_new_signup_stores_exact_copy_and_sends_it(system):
    c,db,mail=system
    assert c.post('/api/account/register',json=payload()).status_code==202
    row=db.raw.web_users.find_one({'email':'legal@example.com'})
    assert row['acceptance']['snapshot']==bundle()
    assert all(d['text'] in mail[-1][2] for d in bundle()['documents'])
    assert c.get('/api/account/legal-receipt').status_code==401

def test_stale_or_missing_acceptance_does_not_create_account(system):
    c,db,mail=system
    p=payload();p['legal_bundle_id']='0'*64
    assert c.post('/api/account/register',json=p).status_code==409
    p=payload();p['accept_terms']=False
    assert c.post('/api/account/register',json=p).status_code==422
    assert db.raw.web_users.count_documents({})==0
    assert not mail

def test_own_copy_only_and_legacy_not_reconstructed(system):
    c,db,mail=system
    login(c,mail)
    assert c.get('/api/account/legal-receipt').json()['has_snapshot'] is False
    row=db.raw.web_users.find_one({'email':'one@example.com'})
    db.raw.web_users.update_one({'_id':row['_id']},{'$set':{'acceptance.snapshot':bundle()}})
    result=c.get('/api/account/legal-receipt?subject_id=other').json()
    assert result['has_snapshot'] is True
    assert bundle()['documents'][0]['text'] in result['text']

def test_duplicate_registration_preserves_first_acceptance(system):
    c,db,mail=system
    assert c.post('/api/account/register',json=payload()).status_code==202
    before=db.raw.web_users.find_one({'email':'legal@example.com'})['acceptance']
    assert c.post('/api/account/register',json=payload()).status_code==202
    assert db.raw.web_users.find_one({'email':'legal@example.com'})['acceptance']==before
