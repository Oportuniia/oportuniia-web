import hashlib
import io
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import mongomock
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
import investor_access as gateway

FUTURE = (datetime.now(timezone.utc)+timedelta(days=30)).isoformat()
PAST = (datetime.now(timezone.utc)-timedelta(days=1)).isoformat()

class Cursor:
    def __init__(self, cursor): self.cursor=cursor
    async def to_list(self, limit): return list(self.cursor)[:limit]
class Collection:
    def __init__(self, collection): self.collection=collection
    async def find_one(self, *a, **kw): return self.collection.find_one(*a, **kw)
    def find(self, *a, **kw): return Cursor(self.collection.find(*a, **kw))
    async def insert_one(self, *a, **kw): return self.collection.insert_one(*a, **kw)
    async def update_one(self, *a, **kw): return self.collection.update_one(*a, **kw)
class DB:
    def __init__(self): self.db=mongomock.MongoClient().db
    def __getattr__(self, name): return Collection(self.db[name])

def setup_client(authenticated=True):
    db=DB();app=FastAPI();router=APIRouter(prefix='/api');gateway.register_investor_routes(router,db);app.include_router(router)
    if authenticated: app.dependency_overrides[gateway.authenticated_subject]=lambda:'investor-a'
    return TestClient(app),db

def seed(db,product='PC',stage=2,premium=False):
    db.db.web_access_reviews.insert_one({'subject_id':'investor-a','identity_status':'VERIFIED' if stage else 'PENDING','dossier_status':'APPROVED' if stage>=2 else 'PENDING','pbc_status':'CLEARED','valid_until':FUTURE})
    db.db.web_operation_grants.insert_one({'subject_id':'investor-a','op_ref':'OP-123','permissions':[product],'dossier_authorized':True,'pbc_status':'CLEARED','can_reserve':True,'valid_until':FUTURE})
    if premium: db.db.web_entitlements.insert_one({'subject_id':'investor-a','product':'PREMIUM','active':True,'valid_until':FUTURE})
    data=b'%PDF-1.4\nsynthetic test document\n%%EOF'
    db.db.web_operation_documents.insert_one({'op_ref':'OP-123','document_id':'doc-1','product':product,'owner':'LEGAL' if product=='LEGAL' else 'PRESENTACION','approved':True,'public_reference_safe':True,'minimum_stage':1 if product=='PC' else 2,'storage_key':'approved/provider-secret.pdf','mime':'application/pdf','sha256':hashlib.sha256(data).hexdigest()})
    return data

def test_absent_auth_provider_is_closed_even_with_forged_role(monkeypatch):
    for key in ['WEB_AUTH_ISSUER','WEB_AUTH_AUDIENCE','WEB_AUTH_JWKS_URL']:monkeypatch.delenv(key,raising=False)
    c,_=setup_client(False)
    for path in ['/api/investor/access','/api/investor/operations/OP-123/documents','/api/investor/operations/OP-123/documents/doc-1']:
        assert c.get(path,headers={'X-Role':'premium','Authorization':'Bearer pretend-cleared'}).status_code==503

def test_pending_identity_and_premium_payment_do_not_unlock_documents():
    c,db=setup_client();seed(db,stage=0,premium=True)
    assert c.get('/api/investor/access').json()['premium'] is True
    assert c.get('/api/investor/operations/OP-123/documents').json()['items']==[]
    assert c.get('/api/investor/operations/OP-123/documents/doc-1').status_code==403

def test_profile_submission_never_validates_or_sets_investor_modality():
    c,db=setup_client();payload={'account_kind':'inversor','subject_type':'PJ','full_name':'Ficticio','company_name':'Entidad ficticia','collaborator_model':'A'}
    assert c.post('/api/investor/profile-draft',json=payload).status_code==422
    payload['collaborator_model']='';assert c.post('/api/investor/profile-draft',json=payload).json()['access_granted'] is False
    assert db.db.web_access_reviews.count_documents({})==0
    assert c.post('/api/investor/profile-draft',json={**payload,'identity_status':'VERIFIED'}).status_code==422

def test_album_requires_both_verified_dossier_and_separate_premium():
    c,db=setup_client();seed(db,'RF',stage=2,premium=False)
    assert c.get('/api/investor/operations/OP-123/documents/doc-1').status_code==403
    db.db.web_entitlements.insert_one({'subject_id':'investor-a','product':'PREMIUM','active':True,'valid_until':FUTURE})
    result=c.get('/api/investor/operations/OP-123/documents').json();assert len(result['items'])==1
    assert 'storage_key' not in str(result) and 'provider-secret' not in str(result)

def test_other_investor_or_expired_permission_cannot_download():
    c,db=setup_client();seed(db)
    db.db.web_operation_grants.update_one({}, {'$set':{'subject_id':'investor-b'}})
    assert c.get('/api/investor/operations/OP-123/documents/doc-1').status_code==403
    db.db.web_operation_grants.update_one({}, {'$set':{'subject_id':'investor-a','valid_until':PAST}})
    assert c.get('/api/investor/operations/OP-123/documents').json()['items']==[]

def test_authorized_bytes_are_verified_and_reference_safe(monkeypatch):
    c,db=setup_client();data=seed(db)
    monkeypatch.setenv('WEB_DOCUMENTS_PRIVATE_BUCKET','private-test-bucket')
    import boto3
    monkeypatch.setattr(boto3,'client',lambda *_:SimpleNamespace(get_object=lambda **kw:{'ContentLength':len(data),'Body':io.BytesIO(data)}))
    r=c.get('/api/investor/operations/OP-123/documents/doc-1?view=1')
    assert r.status_code==200 and r.content==data
    assert r.headers['content-disposition']=='inline; filename="OP-123_PC.pdf"'
    assert r.headers['cache-control']=='private, no-store'
    assert db.db.web_access_audit.count_documents({'action':'DOCUMENT_READ'})==1
    db.db.web_operation_documents.update_one({}, {'$set':{'sha256':'0'*64}})
    assert c.get('/api/investor/operations/OP-123/documents/doc-1').status_code==503

def test_legal_requires_dossier_permission_and_pbc_clearance():
    c,db=setup_client();seed(db,'LEGAL')
    db.db.web_access_reviews.update_one({}, {'$set':{'pbc_status':'PENDING'}})
    assert c.get('/api/investor/operations/OP-123/documents').json()['items']==[]

def test_document_from_wrong_owner_is_never_listed():
    c,db=setup_client();seed(db)
    db.db.web_operation_documents.update_one({}, {'$set':{'owner':'OTHER'}})
    assert c.get('/api/investor/operations/OP-123/documents').json()['items']==[]

def test_reservation_is_closed_without_readiness_and_without_payment_provider():
    c,db=setup_client();seed(db)
    assert c.post('/api/investor/operations/OP-123/checkout',json={'modality':'A'}).status_code==403
    db.db.operation_readiness_snapshots.insert_one({'investor_id':'investor-a','operation_id':'OP-123','modality':'A','can_contract':True,'received_at':'2026-10-14','valid_until':FUTURE})
    assert c.post('/api/investor/operations/OP-123/checkout',json={'modality':'A'}).json()['detail']['code']=='payment_gateway_not_activated'
    assert c.post('/api/investor/operations/OP-123/checkout',json={'modality':'A','price':1,'pbc_cleared':True}).status_code==422

def test_presentation_metadata_resolves_public_reference_without_disclosing_internal_identity():
    c,db=setup_client();seed(db);db.db.web_operation_documents.delete_many({})
    db.db.web_operation_bindings.insert_one({'public_ref':'OP-123','internal_id':'FUND-SECRET-REF','publication_approved':True,'documents_reference_safe':True,'catalog_reference_safe':True})
    db.db.presentation_web_published.insert_one({'internal_id':'FUND-SECRET-REF','publication_state':'PUBLISHED','item':{'source_output_id':'web_'+'a'*24,'documents':{'PC':{'status':'READY','checksum':'b'*64}}}})
    result=c.get('/api/investor/operations/OP-123/documents').json()
    assert len(result['items'])==1 and result['items'][0]['product']=='PC'
    assert 'FUND-SECRET' not in str(result) and 'web_'+'a'*24 not in str(result)

def test_oidc_validates_signature_issuer_audience_and_expiry(monkeypatch):
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    private=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
    public=key.public_key()
    monkeypatch.setenv('WEB_AUTH_ISSUER','https://identity.example.invalid/')
    monkeypatch.setenv('WEB_AUTH_AUDIENCE','oportuniia-web')
    monkeypatch.setenv('WEB_AUTH_JWKS_URL','https://identity.example.invalid/jwks')
    monkeypatch.setattr(gateway,'_jwks',lambda _:SimpleNamespace(get_signing_key_from_jwt=lambda _:SimpleNamespace(key=public)))
    c,_=setup_client(False);now=datetime.now(timezone.utc)
    claims={'sub':'investor-a','iss':'https://identity.example.invalid/','aud':'oportuniia-web','iat':now,'exp':now+timedelta(minutes=5)}
    valid=jwt.encode(claims,private,algorithm='RS256')
    assert c.get('/api/investor/access',headers={'Authorization':'Bearer '+valid}).status_code==200
    for changes in [{'aud':'other-app'},{'iss':'https://attacker.invalid/'},{'exp':now-timedelta(seconds=10)}]:
        token=jwt.encode({**claims,**changes},private,algorithm='RS256')
        assert c.get('/api/investor/access',headers={'Authorization':'Bearer '+token}).status_code==401
    wrong_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    token=jwt.encode(claims,wrong_key,algorithm='RS256')
    assert c.get('/api/investor/access',headers={'Authorization':'Bearer '+token}).status_code==401

def test_message_threads_are_subject_bound_and_reply_email_is_explicitly_pending(monkeypatch):
    c,db=setup_client();db.db.web_message_threads.insert_one({'thread_id':'other','subject_id':'investor-b','messages':[{'body':'private-other'}]})
    assert c.get('/api/investor/messages').json()['items']==[]
    thread=c.post('/api/investor/messages',json={'op_ref':'OP-123','body':'Consulta ficticia'}).json()['thread_id']
    reply={'thread_id':thread,'event_id':'reply-1','body':'Respuesta ficticia'}
    assert c.post('/api/m2m/investor/replies',json=reply).status_code==503
    monkeypatch.setenv('WEB_MESSAGES_M2M_KEY','test-only-key')
    assert c.post('/api/m2m/investor/replies',json=reply).status_code==401
    headers={'X-OPORTUNIIA-Messages-Key':'test-only-key'}
    result=c.post('/api/m2m/investor/replies',json=reply,headers=headers)
    assert result.status_code==200 and result.json()['email_sent'] is False
    assert c.post('/api/m2m/investor/replies',json=reply,headers=headers).json()['idempotent'] is True
    assert db.db.web_email_outbox.count_documents({})==1
    assert len(db.db.web_message_threads.find_one({'thread_id':thread})['messages'])==2
    assert c.post('/api/m2m/investor/replies',json={**reply,'body':'Conflicting reply'},headers=headers).status_code==409

def test_offer_uses_verified_profile_snapshot_not_an_editable_draft():
    c,db=setup_client();seed(db)
    db.db.web_operation_grants.update_one({}, {'$push':{'permissions':'PREPARE_OFFER'}})
    assert c.get('/api/investor/operations/OP-123/offer-draft').status_code==409
    db.db.web_access_reviews.update_one({}, {'$set':{'profile_version':'verified-1'}})
    db.db.web_verified_profiles.insert_one({'subject_id':'investor-a','version':'verified-1','profile':{'full_name':'Verified fictitious investor','subject_type':'PF'}})
    db.db.web_profile_drafts.insert_one({'subject_id':'investor-a','profile':{'full_name':'Unreviewed replacement'}})
    result=c.get('/api/investor/operations/OP-123/offer-draft').json()
    assert result['applicant']['full_name']=='Verified fictitious investor'
    assert result['signed'] is False and result['submitted_to_provider'] is False

def test_document_reference_safety_requires_explicit_review():
    c,db=setup_client();seed(db)
    db.db.web_operation_documents.update_one({}, {'$unset':{'public_reference_safe':''}})
    assert c.get('/api/investor/operations/OP-123/documents').json()['items']==[]

def test_private_catalogue_requires_review_and_returns_only_assigned_public_references():
    c,db=setup_client();seed(db)
    db.db.web_operation_grants.update_one({}, {'$push':{'permissions':'CATALOG'}})
    db.db.web_operation_bindings.insert_one({'public_ref':'OP-123','internal_id':'PROVIDER-SECRET','publication_approved':True,'catalog_reference_safe':True})
    db.db.presentation_web_published.insert_one({'internal_id':'PROVIDER-SECRET','publication_state':'PUBLISHED','item':{'universe':'judicial','title':'Approved synthetic title','internal_id':'PROVIDER-SECRET','documents':{'private':'secret'},'source_output_id':'hidden'}})
    result=c.get('/api/investor/opportunities').json()
    assert result['items'][0]['op_ref']=='OP-123'
    assert 'PROVIDER-SECRET' not in str(result) and 'source_output_id' not in str(result) and 'documents' not in str(result)
    assert c.get('/api/investor/opportunities?universe=acuerdos').status_code==403
    db.db.web_access_reviews.update_one({}, {'$set':{'identity_status':'PENDING'}})
    assert c.get('/api/investor/opportunities').status_code==403
