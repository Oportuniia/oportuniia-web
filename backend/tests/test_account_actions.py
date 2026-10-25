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
