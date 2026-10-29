from test_web_identity import system, login
from web_dossier import name_mismatch

def prepare(system, state='CLEAN'):
    c,db,mail=system
    login(c,mail)
    subject=db.raw.web_users.find_one()['subject_id']
    db.raw.web_profile_drafts.insert_one({'subject_id':subject,'profile':{'full_name':'Antonio García'}})
    db.raw.web_personal_documents.insert_one({'subject_id':subject,'document_id':'doc','scan_state':state,'dossier_state':'AWAITING_CONFIRMATION'})
    return c,db

def payload(**kw):
    return {'kinds':['identity'],'detected_name':'ANTONIO GARCIA','identity_answer':'matches','confirmed':True,**kw}

def test_confirmation_files_without_approving_identity(system):
    c,db=prepare(system)
    r=c.post('/api/investor/personal-documents/doc/confirm',json=payload())
    assert r.status_code==200,r.text
    d=db.raw.web_personal_documents.find_one()
    assert d['dossier_state']=='FILED' and d['review_state']=='PENDING'
    assert d['operational_evidence'] is False

def test_discrepancy_cannot_be_accepted_as_matching(system):
    c,db=prepare(system)
    r=c.post('/api/investor/personal-documents/doc/confirm',json=payload(detected_name='José García'))
    assert r.status_code==422
    r=c.post('/api/investor/personal-documents/doc/confirm',json=payload(detected_name='José García',explanation='Documento del representante, revisar.'))
    assert r.status_code==200 and r.json()['dossier_state']=='DISCREPANCY'

def test_unclean_never_confirmed(system):
    c,db=prepare(system,'QUARANTINED')
    assert c.post('/api/investor/personal-documents/doc/confirm',json=payload()).status_code==409

def test_unknown_document_not_evidence(system):
    c,db=prepare(system)
    r=c.post('/api/investor/personal-documents/doc/confirm',json=payload(kinds=['other']))
    assert r.json()['dossier_state']=='TEMPORARY'
    assert db.raw.web_personal_documents.find_one()['temporary_until']

def test_owner_boundary(system):
    c,db=prepare(system)
    db.raw.web_personal_documents.update_one({}, {'$set':{'subject_id':'another'}})
    assert c.post('/api/investor/personal-documents/doc/confirm',json=payload()).status_code==404

def test_names_compare_accents_and_order():
    assert not name_mismatch('Antonio García','GARCIA ANTONIO')
    assert name_mismatch('Antonio García','José García')

def test_temporary_expiry_removes_bytes_and_blocks_reconfirmation(system,monkeypatch):
    import asyncio
    from datetime import datetime,timedelta,timezone
    from types import SimpleNamespace
    import web_personal_storage
    from web_dossier import expire_temporary
    c,db=prepare(system)
    db.raw.web_personal_documents.update_one({}, {'$set':{'dossier_state':'TEMPORARY','temporary_until':datetime.now(timezone.utc)-timedelta(days=1),'storage_backend':'r2-aesgcm','storage_bucket':'test-private','storage_key':'test/doc'}})
    assert c.post('/api/investor/personal-documents/doc/confirm',json=payload()).status_code==404
    calls=[]
    monkeypatch.setattr(web_personal_storage,'client',lambda *a:SimpleNamespace(delete_object=lambda **kw:calls.append(kw)))
    asyncio.run(expire_temporary(db))
    assert calls==[{'Bucket':'test-private','Key':'test/doc'}]
    assert db.raw.web_personal_documents.find_one()['deleted'] is True
    assert c.post('/api/investor/personal-documents/doc/confirm',json=payload()).status_code==404
