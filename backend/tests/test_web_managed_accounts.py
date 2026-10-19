import asyncio
from datetime import timedelta

from fastapi import APIRouter
import web_identity as identity
import web_accounts
from test_web_identity import system, login, PASSWORD


def routes(c, db):
    router = APIRouter(prefix="/api")
    identity.register_password_change_routes(router, db)
    web_accounts.register_account_admin_routes(router, db)
    c.app.include_router(router)


def test_username_login_and_forced_change_restricts_private_data(system):
    c, db, mail = system
    login(c, mail)
    routes(c, db)
    db.raw.web_users.update_one({}, {'$set': {'username': 'rafa.querol',
        'must_change_password': True, 'initial_password_expires_at': identity.now()+timedelta(hours=1)}})
    assert c.get('/api/investor/access').status_code == 403
    r = c.post('/api/account/login', json={'email': 'RAFA.QUEROL', 'password': PASSWORD})
    assert r.status_code == 200 and r.json()['user']['must_change_password']
    c.headers['X-CSRF-Token'] = c.cookies.get(identity.CSRF_COOKIE)
    endpoint = '/api/account/change-password'
    assert c.post(endpoint, json={'current_password': 'wrong', 'new_password': 'Otra-Clave-2026!'}).status_code == 401
    assert c.post(endpoint, json={'current_password': PASSWORD, 'new_password': PASSWORD}).status_code == 422
    assert c.post(endpoint, json={'current_password': PASSWORD, 'new_password': 'Otra-Clave-2026!'}).status_code == 200
    assert c.get('/api/account/session').status_code == 401
    assert db.raw.web_users.find_one({})['must_change_password'] is False


def test_expired_initial_password_is_rejected(system):
    c, db, mail = system
    login(c, mail)
    db.raw.web_users.update_one({}, {'$set': {'must_change_password': True,
        'initial_password_expires_at': identity.now()-timedelta(seconds=1)}})
    assert c.post('/api/account/login', json={'email': 'one@example.com', 'password': PASSWORD}).status_code == 401


def test_administrator_is_server_role_and_mfa_not_username(system):
    c, db, mail = system
    login(c, mail)
    routes(c, db)
    db.raw.web_users.update_one({}, {'$set': {'username': 'rafamaster', 'role': 'user'}})
    assert c.get('/api/staff/accounts', headers={'X-Role': 'superadmin'}).status_code == 403
    db.raw.web_users.update_one({}, {'$set': {'role': 'superadmin'}})
    assert c.get('/api/staff/accounts').status_code == 403
    db.raw.web_users.update_one({}, {'$set': {'mfa_enabled': True}})
    db.raw.web_sessions.update_many({}, {'$set': {'mfa_verified': True}})
    assert c.get('/api/staff/accounts').status_code == 200
    assert 'password_hash' not in c.get('/api/staff/accounts').text


def test_administrator_creates_resets_and_disables_without_deleting_data(system):
    c, db, mail = system
    login(c, mail)
    routes(c, db)
    own = db.raw.web_users.find_one({})['subject_id']
    db.raw.web_users.update_one({}, {'$set': {'role': 'superadmin', 'mfa_enabled': True}})
    db.raw.web_sessions.update_many({}, {'$set': {'mfa_verified': True}})
    payload = {'username': 'new.person', 'name': 'Persona', 'email': 'person@example.com',
        'recovery_email': 'recovery@example.com', 'role': 'user', 'initial_password': 'Temporal-2026!'}
    r = c.post('/api/staff/accounts', json=payload)
    assert r.status_code == 201, r.text
    assert 'Temporal-2026!' not in r.text and 'password_hash' not in r.text
    subject = r.json()['user']['subject_id']
    assert c.post('/api/staff/accounts', json=payload).status_code == 409
    db.raw.web_sessions.insert_one({'subject_id': subject, 'revoked': False})
    assert c.post('/api/staff/accounts/'+subject+'/initial-password', json={'initial_password': 'Nueva-Temporal-2026!'}).status_code == 200
    assert db.raw.web_sessions.find_one({'subject_id': subject})['revoked']
    assert c.delete('/api/staff/accounts/'+own).status_code == 409
    assert c.delete('/api/staff/accounts/'+subject).status_code == 200
    assert db.raw.web_users.find_one({'subject_id': subject})['active'] is False


def test_bootstrap_never_replaces_an_existing_account(system, monkeypatch):
    c, db, mail = system
    login(c, mail, 'info@oportuniia.com')
    original = db.raw.web_users.find_one({})
    monkeypatch.setenv('WEB_ADMIN_INITIAL_PASSWORD', 'Diferente-Temporal-2026!')
    monkeypatch.delenv('WEB_USER_INITIAL_PASSWORD', raising=False)
    asyncio.run(web_accounts.bootstrap_accounts(db))
    unchanged = db.raw.web_users.find_one({'subject_id': original['subject_id']})
    assert unchanged['password_hash'] == original['password_hash']
    assert unchanged.get('role') == original.get('role')
