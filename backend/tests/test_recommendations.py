import asyncio
from fastapi import APIRouter
from test_web_identity import system, login
import web_recommendations as rec
import web_workers


def setup(system, monkeypatch):
    c, db, mail = system
    login(c, mail)
    sender = db.raw.web_users.find_one({})['subject_id']
    db.raw.web_professionals.insert_one({'_id': sender, 'kind': 'suscriptor', 'active': True, 'valid_until': '2099-01-01T00:00:00Z'})
    db.raw.web_users.insert_one({'subject_id': 'client', 'name': 'Cliente ficticio', 'email': 'client@example.invalid', 'active': True, 'email_verified': True})
    db.raw.web_client_links.insert_one({'_id': 'client', 'professional_id': sender, 'investor_id': 'client', 'state': 'ACCEPTED'})
    db.raw.web_profile_drafts.insert_one({'subject_id': 'client', 'profile': {'phone': '+34600000000'}})
    db.raw.web_operation_bindings.insert_one({'public_ref': 'OP-TEST', 'publication_approved': True, 'catalog_reference_safe': True})
    db.raw.web_share_summaries.insert_one({'_id': 'OP-TEST', 'op_ref': 'OP-TEST', 'title': 'Prueba', 'approved': True, 'internal_id': 'SECRET', 'provider': 'SECRET', 'location': 'Madrid'})
    async def context(*args): return {'premium': True, 'stage': 2, 'grant': {'permissions': ['CATALOG']}}
    monkeypatch.setattr(rec, 'context', context)
    router = APIRouter(prefix='/api'); rec.register_recommendation_routes(router, db); c.app.include_router(router)
    return c, db, sender


def share(c, channel='email', ids=None):
    return c.post('/api/professional/recommendations', json={'op_ref': 'OP-TEST', 'investor_ids': ids or ['client'], 'channel': channel})


def test_share_is_recipient_bound_safe_and_idempotent(system, monkeypatch):
    c, db, sender = setup(system, monkeypatch)
    a=share(c); assert a.status_code == 200, a.text
    assert share(c).json() == a.json()
    assert db.raw.web_email_outbox.count_documents({}) == 1
    ident=a.json()['items'][0]['id']
    result=c.get('/api/professional/recommendations/'+ident)
    assert result.status_code == 200
    assert 'SECRET' not in result.text and 'provider' not in result.text
    assert 'Uso personal' in result.json()['watermark']
    from fastapi import HTTPException
    try: asyncio.run(rec.authorized_share(db, ident, 'stranger'))
    except HTTPException as e: assert e.status_code == 404
    else: raise AssertionError('Cross-account disclosure')
    assert db.raw.web_entitlements.count_documents({}) == 0


def test_no_arbitrary_recipient_or_browser_role(system, monkeypatch):
    c,db,sender=setup(system,monkeypatch)
    assert share(c,ids=['stranger']).status_code == 404
    db.raw.web_client_links.update_one({}, {'$set': {'state': 'PENDING'}})
    assert share(c).status_code == 403
    assert db.raw.web_recommendations.count_documents({}) == 0
    db.raw.web_professionals.delete_many({})
    assert share(c).status_code == 403


def test_revocation_and_expiry_block_access_and_mail(system, monkeypatch):
    c,db,sender=setup(system,monkeypatch)
    ident=share(c).json()['items'][0]['id']
    assert c.post('/api/professional/recommendations/'+ident+'/revoke',json={}).status_code==200
    assert c.get('/api/professional/recommendations/'+ident).status_code==404
    monkeypatch.setattr(web_workers,'mail_ready',lambda:True)
    async def never(*args): raise AssertionError('Revoked mail must not send')
    monkeypatch.setattr(web_workers,'send_transactional',never)
    assert not asyncio.run(web_workers.dispatch_email_once(db,rec.SCOPE))['submitted']
    assert db.raw.web_email_outbox.find_one({})['state']=='SKIPPED_REVOKED_OR_PREFERENCE'


def test_mail_identifies_sender_and_private_link_only(system, monkeypatch):
    c,db,sender=setup(system,monkeypatch)
    share(c)
    sent=[]
    monkeypatch.setattr(web_workers,'mail_ready',lambda:True)
    async def send(*args):sent.append(args)
    monkeypatch.setattr(web_workers,'send_transactional',send)
    assert asyncio.run(web_workers.dispatch_email_once(db,rec.SCOPE))['submitted']
    assert sent[0][0]=='client@example.invalid'
    assert 'Usuario ficticio' in sent[0][1] and '#ficha/' in sent[0][2]
    assert 'SECRET' not in str(sent)
    assert not asyncio.run(web_workers.dispatch_email_once(db,rec.SCOPE))['processed']


def test_whatsapp_no_automatic_send_and_requires_international_phone(system, monkeypatch):
    c,db,sender=setup(system,monkeypatch)
    r=share(c,'whatsapp');assert r.status_code==200,r.text
    assert r.json()['items'][0]['whatsapp_url'].startswith('https://wa.me/34600000000?text=')
    assert db.raw.web_email_outbox.count_documents({})==0
    assert db.raw.web_recommendations.find_one({}).get('viewed_at') is None
    db.raw.web_profile_drafts.update_one({'subject_id':'client'},{'$set':{'profile.phone':'600000000'}})
    assert share(c,'whatsapp').status_code==422


def test_preferences_csrf_and_summary_permission(system, monkeypatch):
    c,db,sender=setup(system,monkeypatch)
    db.raw.web_workspace_settings.insert_one({'subject_id':'client','operation_alerts':False})
    assert share(c).status_code==409
    db.raw.web_workspace_settings.delete_many({})
    c.headers['X-CSRF-Token']='wrong'
    assert share(c).status_code==403
    from web_identity import CSRF_COOKIE
    c.headers['X-CSRF-Token']=c.cookies.get(CSRF_COOKIE)
    db.raw.web_share_summaries.update_one({}, {'$set':{'approved':False}})
    assert share(c).status_code==404


def test_admin_configuration_not_available_to_investor(system, monkeypatch):
    c,db,sender=setup(system,monkeypatch)
    assert c.post('/api/account/professionals',json={'subject_id':sender,'kind':'suscriptor','active':True,'valid_until':'2099-01-01T00:00:00Z'}).status_code==403
    assert c.post('/api/account/client-links',json={'professional_id':sender,'investor_id':'client'}).status_code==403


def test_subscriber_does_not_require_collaborator_model():
    from investor_access import missing_profile_fields
    assert 'collaborator_model' not in missing_profile_fields({'account_kind':'suscriptor'})
    assert 'collaborator_model' in missing_profile_fields({'account_kind':'colaborador'})


def test_recipient_can_read_reply_but_stranger_cannot(system, monkeypatch):
    c,db,sender=setup(system,monkeypatch)
    ident=share(c).json()['items'][0]['id']
    from investor_access import authenticated_subject
    c.app.dependency_overrides[authenticated_subject]=lambda:'client'
    assert c.get('/api/professional/recommendations/'+ident).status_code==200
    assert db.raw.web_recommendations.find_one({})['viewed_at']
    payload={'body':'Me interesa esta operación ficticia','event_id':'reply-test-123'}
    assert c.post('/api/professional/recommendations/'+ident+'/reply',json=payload).status_code==200
    assert c.post('/api/professional/recommendations/'+ident+'/reply',json=payload).status_code==200
    assert db.raw.web_recommendation_messages.count_documents({})==1
    c.app.dependency_overrides[authenticated_subject]=lambda:'stranger'
    assert c.get('/api/professional/recommendations/'+ident).status_code==404
    assert c.post('/api/professional/recommendations/'+ident+'/reply',json=payload).status_code==404
    c.app.dependency_overrides[authenticated_subject]=lambda:'client'
    db.raw.web_recommendations.update_one({}, {'$set':{'valid_until':'2000-01-01T00:00:00Z'}})
    assert c.get('/api/professional/recommendations/'+ident).status_code==404


def test_revoked_link_and_source_grant_close_existing_summary(system, monkeypatch):
    c,db,sender=setup(system,monkeypatch)
    ident=share(c).json()['items'][0]['id']
    async def no_catalog(*args):return {'premium':True,'stage':2,'grant':{'permissions':[]}}
    monkeypatch.setattr(rec,'context',no_catalog)
    assert c.get('/api/professional/recommendations/'+ident).status_code==403
    db.raw.web_client_links.update_one({}, {'$set':{'state':'REVOKED'}})
    assert c.get('/api/professional/recommendations/'+ident).status_code==403


def test_subscriber_free_premium_requires_active_period_and_verification(system, monkeypatch):
    c,db,sender=setup(system,monkeypatch)
    import investor_access
    async def eligible(*args):return {'can_contract':True}
    monkeypatch.setattr(investor_access,'contracting_eligibility',eligible)
    assert asyncio.run(investor_access.context(db,sender))['premium'] is True
    db.raw.web_professionals.update_one({}, {'$set':{'valid_until':'2000-01-01T00:00:00Z'}})
    assert asyncio.run(investor_access.context(db,sender))['premium'] is False
    db.raw.web_professionals.update_one({}, {'$set':{'valid_until':'2099-01-01T00:00:00Z'}})
    async def incomplete(*args):return {'can_contract':False}
    monkeypatch.setattr(investor_access,'contracting_eligibility',incomplete)
    assert asyncio.run(investor_access.context(db,sender))['premium'] is False
