import asyncio
import hashlib
import hmac
import io
import json
import time
from datetime import timedelta
from types import SimpleNamespace

from test_web_identity import system, login
from test_investor_access import complete_profile
import web_identity
import web_review
import web_payments
import web_workers


class Object(dict):
    def __getattr__(self, key): return self[key]


def test_human_review_requires_mfa_allowlist_evidence_and_revision(system, monkeypatch):
    c, db, mail = system; login(c, mail)
    # Routes are added to this isolated test app, not exposed by a demo role.
    web_review.register_review_routes(c.app.router, db)
    # Prefix is absent for routes directly attached to the test app router.
    path = '/staff/reviews'
    assert c.get(path).status_code == 403
    subject = c.get('/api/account/session').json()['user']['subject_id']
    monkeypatch.setenv('WEB_REVIEWER_SUBJECT_IDS', subject)
    assert c.get(path).status_code == 403
    db.raw.web_users.update_one({'subject_id': subject}, {'$set': {'mfa_enabled': True}})
    db.raw.web_sessions.update_many({}, {'$set': {'mfa_verified': True}})
    db.raw.web_users.insert_one({'subject_id': 'investor-b', 'email': 'b@example.com', 'active': True, 'email_verified': True})
    db.raw.web_profile_drafts.insert_one({'subject_id': 'investor-b', 'revision': 'r1', 'state': 'PENDING_REVIEW', 'profile': complete_profile()})
    db.raw.web_personal_documents.insert_one({'subject_id': 'investor-b', 'document_id': 'id-b', 'category': 'identity', 'scan_state': 'QUARANTINED'})
    payload = {'expected_revision': 'r1', 'decision': 'APPROVE', 'reason': 'Identidad y documentación contrastadas por el equipo.', 'reviewed_document_ids': ['id-b'], 'identity_contrasted': True, 'dossier_contrasted': True}
    assert c.post(path+'/'+subject, json=payload).status_code == 403
    assert c.post(path+'/investor-b', json=payload).status_code == 409
    db.raw.web_personal_documents.update_one({}, {'$set': {'scan_state': 'CLEAN'}})
    assert c.post(path+'/investor-b', json={**payload, 'reviewed_document_ids': ['other-id']}).status_code == 422
    assert c.post(path+'/investor-b', json={**payload, 'expected_revision': 'stale'}).status_code == 409
    result = c.post(path+'/investor-b', json=payload)
    assert result.status_code == 200, result.text
    assert result.json()['operation_access_granted'] is False
    ctx = asyncio.run(__import__('investor_access').context(db, 'investor-b'))
    assert ctx['stage'] == 2 and ctx['premium'] is False
    db.raw.web_profile_drafts.update_one({'subject_id': 'investor-b'}, {'$set': {'revision': 'r2'}})
    assert asyncio.run(__import__('investor_access').context(db, 'investor-b'))['stage'] == 0


def fake_stripe():
    checkouts = {}; subscriptions = {}; created = []
    def create(params, options):
        ident = 'cs_'+options['idempotency_key']
        checkout = Object(id=ident, url='https://checkout.stripe.com/c/test', expires_at=int(time.time()+3600), client_reference_id=params['client_reference_id'], payment_status='unpaid', subscription='sub_1' if params['mode']=='subscription' else None, customer='cus_1')
        checkouts[ident] = checkout; created.append((params, options)); return checkout
    def update_sub(ident, params): subscriptions[ident].update(params); return subscriptions[ident]
    client = SimpleNamespace(v1=SimpleNamespace(prices=SimpleNamespace(retrieve=lambda p: Object(currency='eur', unit_amount=100000, recurring={'interval': 'month', 'interval_count': 1})), checkout=SimpleNamespace(sessions=SimpleNamespace(create=create, retrieve=lambda ident: checkouts[ident])), subscriptions=SimpleNamespace(retrieve=lambda ident: subscriptions[ident], update=update_sub)))
    subscriptions['sub_1'] = Object(id='sub_1', status='active', cancel_at_period_end=False, items={'data': [Object(price={'id': 'price_monthly'}, current_period_end=int(time.time()+86400))]})
    return client, checkouts, subscriptions, created


def test_checkout_idempotence_server_price_and_no_browser_activation(system, monkeypatch):
    c, db, mail = system; login(c, mail)
    subject = c.get('/api/account/session').json()['user']['subject_id']
    client, checkouts, subs, created = fake_stripe()
    monkeypatch.setattr(web_payments, 'provider', lambda: client)
    monkeypatch.setenv('WEB_STRIPE_PREMIUM_MONTHLY_PRICE', 'price_monthly')
    monkeypatch.setenv('WEB_PREMIUM_TERMS_VERSION', 'TEST-1')
    assert c.post('/api/investor/premium/checkout', json={'plan': 'monthly'}).status_code == 403
    asyncio.run(web_payments.create_checkout(db, subject, 'PREMIUM'))
    asyncio.run(web_payments.create_checkout(db, subject, 'PREMIUM'))
    assert len(created) == 1 and created[0][0]['line_items'] == [{'price': 'price_monthly', 'quantity': 1}]
    assert db.raw.web_entitlements.count_documents({}) == 0
    intent = db.raw.web_checkout_intents.find_one({})
    assert asyncio.run(web_payments.confirm_intent(db, client, intent)) is False
    checkouts[intent['session_id']]['payment_status'] = 'paid'
    assert asyncio.run(web_payments.confirm_intent(db, client, intent)) is True
    assert db.raw.web_entitlements.find_one({})['active'] is True
    # Payment cannot verify a pending dossier or unlock actual Premium access.
    assert c.get('/api/investor/access').json()['premium'] is False


def test_webhook_signature_mode_and_duplicate_receipts(system, monkeypatch):
    c, db, mail = system
    web_payments.register_payment_routes(c.app.router, db)
    client, *_ = fake_stripe()
    monkeypatch.setattr(web_payments, 'provider', lambda: client)
    monkeypatch.setenv('WEB_STRIPE_SECRET_KEY', 'sk_test_not-real')
    monkeypatch.setenv('WEB_STRIPE_WEBHOOK_SECRET', 'whsec_not-real')
    raw = json.dumps({'id': 'evt_test', 'type': 'customer.subscription.deleted', 'livemode': False, 'data': {'object': {'id': 'sub_1', 'customer': 'cus_1'}}}).encode()
    stamp = str(int(time.time())); signature = hmac.new(b'whsec_not-real', stamp.encode()+b'.'+raw, hashlib.sha256).hexdigest()
    headers = {'Stripe-Signature': 't='+stamp+',v1='+signature, 'Content-Type': 'application/json'}
    db.raw.web_entitlements.insert_one({'subject_id': 'a', 'provider': 'STRIPE', 'customer_id': 'cus_1', 'product': 'PREMIUM', 'active': True})
    assert c.post('/payments/stripe/webhook', content=raw).status_code == 400
    assert c.post('/payments/stripe/webhook', content=raw, headers=headers).status_code == 200
    assert c.post('/payments/stripe/webhook', content=raw, headers=headers).status_code == 200
    assert db.raw.web_payment_events.count_documents({}) == 1 and db.raw.web_entitlements.find_one({})['active'] is False


def test_mail_preferences_and_scanning_do_not_approve_identity(system, monkeypatch):
    c, db, mail = system; login(c, mail)
    subject = c.get('/api/account/session').json()['user']['subject_id']
    db.raw.web_email_outbox.insert_one({'subject_id': subject, 'state': 'PENDING_EMAIL_PROVIDER', 'event_id': 'event-1'})
    delivered = []
    async def deliver(*args): delivered.append(args)
    monkeypatch.setattr(web_workers, 'send_transactional', deliver)
    assert asyncio.run(web_workers.dispatch_email_once(db))['submitted'] is True
    assert asyncio.run(web_workers.dispatch_email_once(db))['processed'] is False
    assert db.raw.web_email_outbox.find_one({})['state'] == 'SUBMITTED_TO_SMTP'
    for k, v in {'WEB_PERSONAL_UPLOADS_ENABLED': 'true', 'WEB_PERSONAL_BUCKET': 'test', 'WEB_PERSONAL_KMS_KEY_ID': 'test', 'WEB_CLAMAV_PRIVATE_HOST': 'private-scanner'}.items(): monkeypatch.setenv(k, v)
    data = b'%PDF-1.4 FICTICIO'
    db.raw.web_personal_documents.insert_one({'subject_id': subject, 'document_id': 'd', 'storage_key': 'test', 'scan_state': 'QUARANTINED', 'sha256': hashlib.sha256(data).hexdigest()})
    monkeypatch.setattr(__import__('web_personal_storage'), 'client', lambda *args: SimpleNamespace(get_object=lambda **kw: {'Body': io.BytesIO(data)}))
    monkeypatch.setattr(web_workers, 'scan_bytes', lambda data: 'CLEAN')
    assert asyncio.run(web_workers.scan_document_once(db))['scan_state'] == 'CLEAN'
    assert c.get('/api/investor/access').json()['stage'] == 0 and db.raw.web_access_reviews.count_documents({}) == 0


def test_signed_webempresa_bridge_and_no_redirects(system, monkeypatch):
    _, _, _ = system
    import requests
    monkeypatch.setenv('WEB_MAIL_BRIDGE_URL', 'https://mail-host.example/bridge.php')
    monkeypatch.setenv('WEB_MAIL_BRIDGE_KEY', 'synthetic-key-'*5)
    captured = []
    def send(url, **kwargs):
        captured.append(kwargs)
        headers, raw = kwargs['headers'], kwargs['data']
        expected = hmac.new(('synthetic-key-'*5).encode(), headers['X-OPP-Mail-Timestamp'].encode()+b'.'+headers['X-OPP-Mail-Nonce'].encode()+b'.'+raw, hashlib.sha256).hexdigest()
        assert expected == headers['X-OPP-Mail-Signature'] and kwargs['allow_redirects'] is False
        return SimpleNamespace(status_code=200, json=lambda: {'accepted': True})
    monkeypatch.setattr(requests, 'post', send)
    # Replace the fixture's no-network stub with the module's original implementation.
    import importlib
    source = __import__('pathlib').Path(web_identity.__file__).read_text()
    # Capture a clean module object without changing account routes already registered.
    spec = importlib.util.spec_from_file_location('mail_adapter_test', web_identity.__file__)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    asyncio.run(module.send_transactional('qa@example.com', 'Prueba ficticia', 'Mensaje ficticio'))
    assert len(captured) == 1


def test_body_size_is_limited_before_parsing():
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    from web_security import BodyLimitMiddleware
    app = FastAPI(); app.add_middleware(BodyLimitMiddleware)
    @app.post('/api/account/test')
    async def route(request: Request): return {'bytes': len(await request.body())}
    client = TestClient(app)
    assert client.post('/api/account/test', content=b'x'*70000).status_code == 413
    assert client.post('/api/account/test', content=iter([b'x'*40000,b'x'*40000])).status_code == 413
