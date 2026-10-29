from test_web_identity import system, login
import web_review


def setup(system):
    c,db,mail=system
    login(c,mail)
    db.raw.web_users.update_one({}, {'$set':{'role':'superadmin','mfa_enabled':True}})
    db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':True}})
    db.raw.web_users.insert_one({'subject_id':'target','name':'Prueba','email':'target@example.com','active':True,'email_verified':True})
    db.raw.web_profile_drafts.insert_one({'subject_id':'target','revision':'r1','profile':{'tax_id':'12-345-a'},'state':'PENDING_REVIEW'})
    db.raw.web_access_reviews.insert_one({'subject_id':'target','revoked':False})
    web_review.register_review_routes(c.app.router,db,prefix='/account/reviews')
    return c,db


def action(c,kind,phrase,subject='target'):
    return c.post('/account/reviews/'+subject+'/account-action',json={'action':kind,'confirmation':phrase,'reason':'Actuación ficticia para comprobar los controles.'})


def test_remove_restore_confirmation_and_no_auto_approval(system):
    c,db=setup(system)
    assert action(c,'REMOVE','si').status_code==422
    assert not db.raw.web_users.find_one({'subject_id':'target'}).get('dossier_removed')
    assert action(c,'REMOVE','ELIMINAR EXPEDIENTE').status_code==200
    assert db.raw.web_users.find_one({'subject_id':'target'})['dossier_removed']
    assert db.raw.web_access_reviews.find_one({'subject_id':'target'})['revoked']
    assert action(c,'RESTORE','RESTAURAR EXPEDIENTE').status_code==200
    assert not db.raw.web_users.find_one({'subject_id':'target'})['dossier_removed']
    assert db.raw.web_access_reviews.find_one({'subject_id':'target'})['revoked']
    assert len(c.get('/account/reviews/history/restrictions').json()['items'])==2


def test_block_normalized_identity_register_and_unblock(system):
    import asyncio
    from web_access_restrictions import blocked
    c,db=setup(system)
    assert action(c,'BLOCK','VETAR ACCESO').status_code==200
    assert asyncio.run(blocked(db,{'email':'TARGET@example.com'}))
    assert asyncio.run(blocked(db,{'email':'new@example.com'},{'tax_id':'12345A'}))
    assert not asyncio.run(blocked(db,{'email':'unrelated@example.com'},{'full_name':'Prueba'}))
    r=c.post('/api/account/register',json={'name':'Prueba','email':'target@example.com','password':'Contraseña-prueba-222!','account_kind':'inversor','accept_privacy':True,'accept_terms':True})
    assert r.status_code==403
    assert action(c,'UNBLOCK','LEVANTAR VETO').status_code==200
    assert not asyncio.run(blocked(db,{'email':'new@example.com'},{'tax_id':'12345A'}))
    assert db.raw.web_account_events.count_documents({})==2


def test_mfa_self_and_master_protected(system):
    c,db=setup(system)
    own=db.raw.web_users.find_one({'role':'superadmin'})['subject_id']
    assert action(c,'REMOVE','ELIMINAR EXPEDIENTE',own).status_code==403
    db.raw.web_users.update_one({'subject_id':'target'},{'$set':{'role':'superadmin'}})
    assert action(c,'BLOCK','VETAR ACCESO').status_code==403
    db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':False}})
    assert action(c,'REMOVE','ELIMINAR EXPEDIENTE').status_code==403
    assert c.get('/account/reviews/history/restrictions').status_code==403


def test_restriction_revokes_existing_session(system):
    c,db,mail=system
    login(c,mail)
    db.raw.web_users.update_one({}, {'$set':{'access_blocked':True}})
    assert c.get('/api/account/session').status_code==403


def test_permanent_purge_cannot_restore_and_keeps_veto(system, monkeypatch):
    import web_dossier_purge
    c,db=setup(system)
    db.raw.web_personal_documents.insert_one({'subject_id':'target','document_id':'doc','storage_key':'one'})
    db.raw.web_workspace_settings.insert_one({'subject_id':'target','photo':'private-photo'})
    db.raw.web_registration_blocks.insert_one({'owner_subject_id':'target','active':True})
    erased=[]
    monkeypatch.setattr(web_dossier_purge,'erase_objects',lambda row:erased.append(row['document_id']))
    assert action(c,'PURGE','si').status_code==422
    assert action(c,'PURGE','ELIMINAR EXPEDIENTE').status_code==200
    assert erased==['doc']
    for collection in ('web_personal_documents','web_profile_drafts','web_workspace_settings'):
        assert db.raw[collection].count_documents({'subject_id':'target'})==0
    assert db.raw.web_users.find_one({'subject_id':'target'})['purge_completed']
    assert db.raw.web_registration_blocks.find_one({'owner_subject_id':'target'})['active']
    assert action(c,'RESTORE','RESTAURAR EXPEDIENTE').status_code==404
    assert c.get('/account/reviews/target').status_code==404


def test_storage_failure_is_retryable_not_false_success(system, monkeypatch):
    import web_dossier_purge
    c,db=setup(system)
    db.raw.web_personal_documents.insert_one({'subject_id':'target','document_id':'doc'})
    def failed(row): raise RuntimeError('storage unavailable')
    monkeypatch.setattr(web_dossier_purge,'erase_objects',failed)
    assert action(c,'PURGE','ELIMINAR EXPEDIENTE').status_code==503
    assert not db.raw.web_users.find_one({'subject_id':'target'})['active']
    assert db.raw.web_personal_documents.count_documents({'subject_id':'target'})==1
    assert action(c,'RESTORE','RESTAURAR EXPEDIENTE').status_code==409
    monkeypatch.setattr(web_dossier_purge,'erase_objects',lambda row:None)
    assert action(c,'PURGE','ELIMINAR EXPEDIENTE').status_code==200


def test_purge_requires_mfa_and_protects_master(system):
    c,db=setup(system)
    own=db.raw.web_users.find_one({'role':'superadmin'})['subject_id']
    assert action(c,'PURGE','ELIMINAR EXPEDIENTE',own).status_code==403
    db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':False}})
    assert action(c,'PURGE','ELIMINAR EXPEDIENTE').status_code==403


def test_erasure_only_deletes_exact_object_versions(monkeypatch):
    import web_dossier_purge as purge
    deleted=[]
    class Client:
        def get_paginator(self, name): return self
        def paginate(self, **kwargs):
            return [{'Versions':[{'Key':'incoming/one','VersionId':'v1'},{'Key':'incoming/one-other','VersionId':'v2'}],
                     'DeleteMarkers':[{'Key':'incoming/one','VersionId':'v3'}]}]
        def delete_object(self, **kwargs): deleted.append(kwargs)
    monkeypatch.setattr(purge.quarantine,'client',lambda:Client())
    purge.erase_objects({'quarantine_bucket':'private','quarantine_key':'incoming/one'})
    assert [x['VersionId'] for x in deleted]==['v1','v3']
