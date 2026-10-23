import hashlib
import io
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
import web_quarantine as q
from test_web_identity import system, login
from fastapi import APIRouter


DATA = b'%PDF-1.4\nFICTICIO'


@pytest.fixture
def record():
    return {'size': len(DATA), 'mime': 'application/pdf', 'sha256': hashlib.sha256(DATA).hexdigest(),
            'quarantine_bucket': 'test-private', 'quarantine_key': 'incoming/test', 'quarantine_version': 'v1'}


@pytest.mark.parametrize('verdict,expected', [(None,'QUARANTINED'),('NO_THREATS_FOUND','CLEAN'),
    ('THREATS_FOUND','INFECTED'),('UNSUPPORTED','REJECTED'),('FAILED','SCAN_FAILED'),
    ('ACCESS_DENIED','SCAN_FAILED'),('unknown','QUARANTINED')])
def test_only_explicit_clean_is_accepted(record,monkeypatch,verdict,expected):
    def tags(**kw):
        assert kw['VersionId']=='v1'
        return {'VersionId':'v1','TagSet': [{'Key':'GuardDutyMalwareScanStatus','Value':verdict}] if verdict else []}
    monkeypatch.setattr(q,'client',lambda:SimpleNamespace(head_object=lambda **kw:{'ContentLength':len(DATA),'ContentType':'application/pdf','VersionId':'v1'},get_object_tagging=tags))
    assert q.inspect_scan(record)==('v1',expected)


@pytest.mark.parametrize('state',['INFECTED','QUARANTINED','SCAN_FAILED','REJECTED'])
def test_unscanned_or_infected_bytes_never_read(record,monkeypatch,state):
    monkeypatch.setattr(q,'inspect_scan',lambda row:('v1',state))
    monkeypatch.setattr(q,'client',lambda:pytest.fail('must not read bytes'))
    with pytest.raises(ValueError): q.promote(record)


def test_exact_clean_version_promoted(record,monkeypatch):
    monkeypatch.setattr(q,'inspect_scan',lambda row:('v1','CLEAN'))
    def get(**kw):
        assert kw['VersionId']=='v1'
        return {'Body':io.BytesIO(DATA)}
    monkeypatch.setattr(q,'client',lambda:SimpleNamespace(get_object=get))
    writes=[]
    monkeypatch.setattr(q.storage,'write',lambda data,row:writes.append(data))
    q.promote(record)
    assert writes==[DATA]


def test_changed_bytes_cannot_promote(record,monkeypatch):
    monkeypatch.setattr(q,'inspect_scan',lambda row:('v1','CLEAN'))
    monkeypatch.setattr(q,'client',lambda:SimpleNamespace(get_object=lambda **kw:{'Body':io.BytesIO(b'WRONG')}))
    monkeypatch.setattr(q.storage,'write',lambda *a:pytest.fail('corrupt bytes must not be saved'))
    with pytest.raises(ValueError): q.promote(record)


def test_version_change_cannot_promote(record,monkeypatch):
    monkeypatch.setattr(q,'inspect_scan',lambda row:('v2','CLEAN'))
    monkeypatch.setattr(q,'client',lambda:pytest.fail('must not read changed version'))
    with pytest.raises(ValueError): q.promote(record)


def test_original_over_limit_rejected():
    with pytest.raises(ValidationError):
        q.UploadIntent(category='identity',mime='application/pdf',size=q.MAX_BYTES+1,sha256='a'*64)


def test_presigned_policy_binds_size_checksum_and_short_expiry(record,monkeypatch):
    def sign(bucket,key,**kw):
        assert bucket=='test-private' and key=='incoming/test'
        assert kw['ExpiresIn']==300
        assert ['content-length-range',len(DATA),len(DATA)] in kw['Conditions']
        assert {'x-amz-checksum-sha256':kw['Fields']['x-amz-checksum-sha256']} in kw['Conditions']
        assert 'tagging' not in kw['Fields']
        return {'url':'https://example.invalid','fields':kw['Fields']}
    monkeypatch.setattr(q,'client',lambda:SimpleNamespace(generate_presigned_post=sign))
    assert q.signed_upload(record)['url']=='https://example.invalid'


def test_routes_keep_subject_and_scan_authority_on_server(system,monkeypatch):
    c,db,mail=system
    router=APIRouter(prefix='/api');q.register_quarantine_routes(router,db);c.app.include_router(router)
    monkeypatch.setattr(q,'configured',lambda:True)
    monkeypatch.setenv('WEB_QUARANTINE_BUCKET','test-private')
    monkeypatch.setattr(q,'signed_upload',lambda row:{'url':'https://test.invalid','fields':{}})
    body={'category':'identity','mime':'application/pdf','size':len(DATA),'sha256':hashlib.sha256(DATA).hexdigest()}
    assert c.post('/api/investor/personal-documents/upload-intent',json=body).status_code==401
    login(c,mail)
    assert c.post('/api/investor/personal-documents/upload-intent',json={**body,'scan_state':'CLEAN'}).status_code==422
    assert c.post('/api/investor/personal-documents/upload-intent',json=body,headers={'X-CSRF-Token':'wrong'}).status_code==403
    result=c.post('/api/investor/personal-documents/upload-intent',json=body)
    assert result.status_code==200,result.text
    ident=result.json()['document_id']
    row=db.raw.web_personal_documents.find_one({'document_id':ident})
    assert row['scan_state']=='QUARANTINED' and row['review_state']=='PENDING'
    db.raw.web_personal_documents.insert_one({**{k:v for k,v in row.items() if k!='_id'},'document_id':'other-doc','subject_id':'other-user'})
    assert c.post('/api/investor/personal-documents/other-doc/scan-status',json={}).status_code==404
    monkeypatch.setattr(q,'inspect_scan',lambda row:('version-1','INFECTED'))
    monkeypatch.setattr(q,'promote',lambda row:pytest.fail('infected document must not be promoted'))
    assert c.post(f'/api/investor/personal-documents/{ident}/scan-status',json={}).json()['scan_state']=='INFECTED'
    assert db.raw.web_access_reviews.count_documents({})==0
