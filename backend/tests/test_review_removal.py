from test_web_identity import system
from test_web_dossier import prepare
import web_review

def test_removal_requires_mfa_is_recoverable_and_does_not_restore_approval(system):
    c,db=prepare(system)
    web_review.register_review_routes(c.app.router,db,prefix='/account/reviews')
    db.raw.web_users.update_one({}, {'$set':{'role':'superadmin'}})
    db.raw.web_personal_documents.update_one({}, {'$set':{'subject_id':'other','review_state':'APPROVED'}})
    db.raw.web_access_reviews.insert_one({'subject_id':'other','revoked':False,'documents_complete':True})
    url='/account/reviews/other/documents/doc/removal'
    body={'removed':True,'reason':'Documento duplicado de prueba.'}
    assert c.post(url,json=body).status_code==403
    db.raw.web_users.update_one({}, {'$set':{'mfa_enabled':True}})
    db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':True}})
    assert c.post(url,json=body).status_code==200
    assert db.raw.web_personal_documents.find_one()['deleted']
    assert db.raw.web_access_reviews.find_one()['revoked']
    assert c.post(url,json={**body,'removed':False}).status_code==200
    assert not db.raw.web_personal_documents.find_one()['deleted']
    assert db.raw.web_access_reviews.find_one()['revoked']
    assert db.raw.web_document_review_events.count_documents({})==2
    assert c.post(url,json={**body,'removed':False}).status_code==409
