from fastapi import APIRouter
from test_web_identity import system, login, Cursor
from web_team_messages import register_team_message_routes
import asyncio
from web_team_messages import NEW_REPLY_SCOPE
from investor_access import TeamReply, save_team_reply
import web_workers


def setup(system, monkeypatch):
    c, db, mail = system
    login(c, mail)
    monkeypatch.setattr(Cursor, 'skip', lambda self, n: Cursor(self.c.skip(n)), raising=False)
    monkeypatch.setattr(Cursor, 'limit', lambda self, n: Cursor(self.c.limit(n)), raising=False)
    router = APIRouter(prefix='/api'); register_team_message_routes(router, db); c.app.include_router(router)
    return c, db


def master(db):
    db.raw.web_users.update_one({}, {'$set': {'role': 'superadmin', 'mfa_enabled': True}})
    db.raw.web_sessions.update_many({}, {'$set': {'mfa_verified': True}})


def test_inbox_requires_real_master_mfa_and_csrf(system, monkeypatch):
    c, db = setup(system, monkeypatch)
    ident = c.post('/api/investor/messages', json={'body': 'Petición ficticia'}).json()['thread_id']
    payload = {'thread_id': ident, 'event_id': 'event-1', 'body': 'Respuesta ficticia'}
    assert c.get('/api/account/team-messages', headers={'X-Role': 'superadmin'}).status_code == 403
    assert c.post('/api/account/team-messages/reply', json=payload).status_code == 403
    master(db)
    db.raw.web_sessions.update_many({}, {'$set': {'mfa_verified': False}})
    assert c.get('/api/account/team-messages').status_code == 403
    db.raw.web_sessions.update_many({}, {'$set': {'mfa_verified': True}})
    assert c.post('/api/account/team-messages/reply', json=payload, headers={'X-CSRF-Token': 'wrong'}).status_code == 403


def test_request_reply_visible_once_with_notification_and_mail_queue(system, monkeypatch):
    c, db = setup(system, monkeypatch)
    ident = c.post('/api/investor/messages', json={'body': 'Petición ficticia'}).json()['thread_id']
    master(db)
    data = c.get('/api/account/team-messages').json()
    assert data['items'][0]['thread_id'] == ident and data['next_offset'] is None
    payload = {'thread_id': ident, 'event_id': 'event-1', 'body': 'Respuesta ficticia'}
    assert c.post('/api/account/team-messages/reply', json=payload).json()['saved']
    assert c.post('/api/account/team-messages/reply', json=payload).json()['idempotent']
    assert c.post('/api/account/team-messages/reply', json={**payload, 'body': 'Otro texto'}).status_code == 409
    messages = c.get('/api/investor/messages').json()['items'][0]['messages']
    assert len(messages) == 2 and messages[-1]['body'] == payload['body']
    assert db.raw.web_email_outbox.count_documents({}) == 1
    assert db.raw.web_notifications.count_documents({'id': 'event-1'}) == 1


def test_inactive_recipient_not_exposed_or_contacted(system, monkeypatch):
    c, db = setup(system, monkeypatch); master(db)
    db.raw.web_users.insert_one({'subject_id': 'closed', 'active': False, 'name': 'Private'})
    db.raw.web_message_threads.insert_one({'thread_id': 'closed-thread', 'subject_id': 'closed', 'messages': [], 'updated_at': '2030'})
    assert c.get('/api/account/team-messages').json()['items'] == []
    assert c.post('/api/account/team-messages/reply', json={'thread_id': 'closed-thread', 'event_id': 'x', 'body': 'No enviar'}).status_code == 404
    assert db.raw.web_email_outbox.count_documents({}) == 0


def test_only_new_master_replies_send_and_old_retry_stays_excluded(system, monkeypatch):
    c, db = setup(system, monkeypatch)
    ident = c.post('/api/investor/messages', json={'body': 'Consulta ficticia'}).json()['thread_id']
    old = TeamReply(thread_id=ident, event_id='old-event', body='Respuesta anterior')
    asyncio.run(save_team_reply(db, old))
    master(db)
    assert c.post('/api/account/team-messages/reply', json=old.model_dump()).status_code == 200
    assert db.raw.web_email_outbox.find_one({'_id': 'old-event'}).get('notification_scope') is None
    new = {'thread_id': ident, 'event_id': 'new-event', 'body': 'Respuesta nueva'}
    assert c.post('/api/account/team-messages/reply', json=new).status_code == 200
    sent = []
    async def send(*args): sent.append(args)
    monkeypatch.setattr(web_workers, 'mail_ready', lambda: True)
    monkeypatch.setattr(web_workers, 'send_transactional', send)
    assert asyncio.run(web_workers.dispatch_email_once(db, NEW_REPLY_SCOPE))['submitted']
    assert not asyncio.run(web_workers.dispatch_email_once(db, NEW_REPLY_SCOPE))['processed']
    assert len(sent) == 1
    assert 'Respuesta nueva' not in sent[0][2]
    assert db.raw.web_email_outbox.find_one({'_id': 'old-event'})['state'] == 'PENDING_EMAIL_PROVIDER'


def test_new_reply_respects_recipient_opt_out(system, monkeypatch):
    c, db = setup(system, monkeypatch)
    ident = c.post('/api/investor/messages', json={'body': 'Consulta ficticia'}).json()['thread_id']
    subject = db.raw.web_users.find_one({})['subject_id']
    db.raw.web_workspace_settings.insert_one({'subject_id': subject, 'email_copies': False})
    master(db)
    c.post('/api/account/team-messages/reply', json={'thread_id': ident, 'event_id': 'no-mail', 'body': 'Respuesta privada'})
    monkeypatch.setattr(web_workers, 'mail_ready', lambda: True)
    async def forbidden(*args): raise AssertionError('Must not send')
    monkeypatch.setattr(web_workers, 'send_transactional', forbidden)
    assert not asyncio.run(web_workers.dispatch_email_once(db, NEW_REPLY_SCOPE))['submitted']
    assert db.raw.web_email_outbox.find_one({'_id': 'no-mail'})['state'] == 'SKIPPED_ACCOUNT_OR_PREFERENCE'
