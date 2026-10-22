"""Registration always attempts delivery; it never approves identity."""
from test_web_identity import system, signup, PASSWORD
import web_identity


def payload():
    return dict(name="Persona ficticia", email="one@example.com", password=PASSWORD,
                account_kind="inversor", accept_privacy=True, accept_terms=True)


def test_retry_sends_again_without_duplicate_account_or_new_password(system):
    client, db, mail = system
    signup(client, mail)
    original = db.raw.web_users.find_one({})["password_hash"]
    result = client.post('/api/account/register', json=payload())
    assert result.status_code == 202
    assert len(mail) == 2
    assert db.raw.web_users.count_documents({}) == 1
    assert db.raw.web_users.find_one({})['password_hash'] == original
    assert db.raw.web_users.find_one({})['email_verified'] is False


def test_verified_account_gets_message_without_reopening_identity(system):
    client, db, mail = system
    token = signup(client, mail)
    client.post('/api/account/verify-email', json={'token': token})
    result = client.post('/api/account/register', json=payload())
    assert result.json() == web_identity.REGISTRATION_MAIL
    assert len(mail) == 2
    assert db.raw.web_users.find_one({})['email_verified'] is True
    assert db.raw.web_access_reviews.count_documents({}) == 0


def test_delivery_failure_is_not_reported_as_sent(system, monkeypatch):
    client, db, mail = system
    async def failed(*args):
        web_identity.denied('transactional_mail_temporarily_unavailable', 503)
    monkeypatch.setattr(web_identity, 'send_transactional', failed)
    assert client.post('/api/account/register', json=payload()).status_code == 503
    assert len(mail) == 0
    assert db.raw.web_users.find_one({})['email_verified'] is False
