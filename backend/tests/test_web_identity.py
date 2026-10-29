"""Account lifecycle and cross-user authorization; no network or real mail."""
import re
from datetime import timedelta

import mongomock
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

import investor_access
import web_identity as identity
import web_workspace
import web_secondfactor


class Cursor:
    def __init__(self, c): self.c = c
    def sort(self, *a): self.c = self.c.sort(*a); return self
    async def to_list(self, n): return list(self.c)[:n]


class Collection:
    def __init__(self, c): self.c = c
    def find(self, *a, **kw): return Cursor(self.c.find(*a, **kw))
    async def find_one(self, *a, **kw): return self.c.find_one(*a, **kw)
    async def find_one_and_update(self, *a, **kw): return self.c.find_one_and_update(*a, **kw)
    async def insert_one(self, *a, **kw): return self.c.insert_one(*a, **kw)
    async def update_one(self, *a, **kw): return self.c.update_one(*a, **kw)
    async def update_many(self, *a, **kw): return self.c.update_many(*a, **kw)
    async def delete_many(self, *a, **kw): return self.c.delete_many(*a, **kw)
    async def create_index(self, *a, **kw): return self.c.create_index(*a, **kw)


class DB:
    def __init__(self): self.raw = mongomock.MongoClient(tz_aware=True).db
    def __getattr__(self, k): return Collection(self.raw[k])


@pytest.fixture
def system(monkeypatch):
    for k, v in {"WEB_IDENTITY_MODE": "web_sessions", "WEB_REQUIRE_MFA": "false", "WEB_PUBLIC_ORIGIN": "https://portal.test", "WEB_REGISTRATION_ENABLED": "true",
                 "WEB_PRIVACY_VERSION": "TEST-1", "WEB_TERMS_VERSION": "TEST-1", "WEB_SMTP_HOST": "test.invalid", "WEB_HOSTING_SMTP_AVAILABLE": "true", "WEB_SMTP_USER": "test",
                 "WEB_SMTP_PASSWORD": "test-not-real", "WEB_MAIL_FROM": "test@example.invalid"}.items(): monkeypatch.setenv(k, v)
    db = DB(); app = FastAPI(); app.state.web_db = db; router = APIRouter(prefix="/api")
    identity.register_identity_routes(router, db); investor_access.register_investor_routes(router, db); web_workspace.register_workspace_routes(router, db); web_secondfactor.register_secondfactor_routes(router, db); app.include_router(router)
    mail = []
    async def send(to, title, body): mail.append((to, title, body))
    monkeypatch.setattr(identity, "send_transactional", send)
    import asyncio
    asyncio.run(identity.ensure_indexes(db))
    client = TestClient(app, base_url="https://portal.test", headers={"Origin": "https://portal.test"})
    return client, db, mail


PASSWORD = "Ficticio-Seguro-2030!"


def signup(c, mail, email="one@example.com"):
    result = c.post("/api/account/register", json={"name": "Usuario ficticio", "email": email, "password": PASSWORD, "account_kind": "inversor", "accept_privacy": True, "accept_terms": True})
    assert result.status_code == 202, result.text
    return re.search(r"#verify=([^\s]+)", mail[-1][2]).group(1)


def login(c, mail, email="one@example.com"):
    token = signup(c, mail, email)
    assert c.post("/api/account/verify-email", json={"token": token}).status_code == 200
    r = c.post("/api/account/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    c.headers["X-CSRF-Token"] = c.cookies.get(identity.CSRF_COOKIE)
    return r


def test_signup_verify_login_logout_and_cookie_policy(system):
    c, db, mail = system
    token = signup(c, mail)
    assert mail[-1][1] == "Confirma tu correo y prepara tu acceso a OPORTUNIIA"
    assert "Crear tu cuenta es gratuito" in mail[-1][2]
    assert "Humanizamos la deuda." in mail[-1][2]
    assert c.post("/api/account/login", json={"email": "one@example.com", "password": PASSWORD}).status_code == 401
    assert c.post("/api/account/verify-email", json={"token": token}).json()["identity_verified"] is False
    assert c.post("/api/account/verify-email", json={"token": token}).status_code == 400
    r = c.post("/api/account/login", json={"email": "one@example.com", "password": PASSWORD})
    assert r.status_code == 200
    cookies = r.headers.get_list("set-cookie")
    assert any(identity.SESSION_COOKIE in x and "HttpOnly" in x and "Secure" in x and "SameSite=lax" in x for x in cookies)
    assert "password_hash" not in str(r.json()) and "token" not in r.json()
    row = db.raw.web_sessions.find_one({})
    assert row["token_hash"] != c.cookies.get(identity.SESSION_COOKIE) and len(row["token_hash"]) == 64
    assert c.get("/api/investor/access").json()["stage"] == 0
    assert c.post("/api/account/logout", json={}).status_code == 403
    c.headers["X-CSRF-Token"] = c.cookies.get(identity.CSRF_COOKIE)
    assert c.post("/api/account/logout", json={}).status_code == 200
    assert c.get("/api/account/session").status_code == 401


def test_origin_csrf_forged_role_and_disabled_user(system):
    c, db, mail = system; login(c, mail)
    assert c.post("/api/investor/premium/checkout", json={}, headers={"Origin": "https://evil.test", "X-Role": "premium"}).status_code == 403
    assert c.post("/api/investor/premium/checkout", json={}, headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert c.post("/api/investor/premium/checkout", json={}, headers={"X-Role": "premium"}).status_code == 403
    db.raw.web_users.update_one({}, {"$set": {"active": False}})
    assert c.get("/api/account/session").status_code == 401


def test_session_idle_absolute_and_version_revocation(system):
    c, db, mail = system; login(c, mail)
    db.raw.web_sessions.update_one({}, {"$set": {"last_seen": identity.now()-timedelta(minutes=31)}})
    assert c.get("/api/account/session").status_code == 401
    db.raw.web_sessions.update_one({}, {"$set": {"last_seen": identity.now(), "expires_at": identity.now()-timedelta(seconds=1)}})
    assert c.get("/api/account/session").status_code == 401
    db.raw.web_sessions.update_one({}, {"$set": {"expires_at": identity.now()+timedelta(hours=1)}})
    db.raw.web_users.update_one({}, {"$inc": {"session_version": 1}})
    assert c.get("/api/account/session").status_code == 401


def test_reset_single_use_and_revokes_other_tokens(system):
    c, db, mail = system; login(c, mail)
    assert c.post("/api/account/forgot-password", json={"email": "one@example.com"}).status_code == 202
    token = re.search(r"#reset=([^\s]+)", mail[-1][2]).group(1)
    assert c.post("/api/account/reset-password", json={"token": token, "password": "Nueva-Clave-Ficticia!"}).status_code == 200
    assert c.get("/api/account/session").status_code == 401
    assert c.post("/api/account/reset-password", json={"token": token, "password": "Otra-Clave-Ficticia!"}).status_code == 400
    assert c.post("/api/account/login", json={"email": "one@example.com", "password": PASSWORD}).status_code == 401
    assert c.post("/api/account/login", json={"email": "one@example.com", "password": "Nueva-Clave-Ficticia!"}).status_code == 200


def test_expired_links_and_generic_account_responses(system):
    c, db, mail = system; token = signup(c, mail)
    db.raw.web_identity_tokens.update_one({}, {"$set": {"expires_at": identity.now()-timedelta(minutes=1)}})
    assert c.post("/api/account/verify-email", json={"token": token}).status_code == 400
    payload = {"name": "Otra", "email": "one@example.com", "password": PASSWORD, "account_kind": "inversor", "accept_privacy": True, "accept_terms": True}
    assert c.post("/api/account/register", json=payload).json() == identity.REGISTRATION_MAIL
    assert c.post("/api/account/forgot-password", json={"email": "absent@example.com"}).json() == identity.GENERIC_MAIL
    assert len(mail) == 2


def test_shared_rate_limit_and_password_byte_boundary(system):
    c, db, mail = system
    for _ in range(8): assert c.post("/api/account/login", json={"email": "absent@example.com", "password": PASSWORD}).status_code == 401
    assert c.post("/api/account/login", json={"email": "absent@example.com", "password": PASSWORD}).status_code == 429
    payload = {"name": "Prueba", "email": "wide@example.com", "password": "á"*40, "account_kind": "inversor", "accept_privacy": True, "accept_terms": True}
    assert c.post("/api/account/register", json=payload).status_code == 422


def test_registration_requires_mail_and_legal_config(system, monkeypatch):
    c, db, mail = system
    monkeypatch.delenv("WEB_PRIVACY_VERSION")
    assert c.get("/api/account/config").json()["registration_enabled"] is False
    assert c.post("/api/account/register", json={"name": "Test", "email": "new@example.com", "password": PASSWORD, "account_kind": "inversor", "accept_privacy": True, "accept_terms": True}).status_code == 503
    assert db.raw.web_users.count_documents({}) == 0


def test_workspace_isolation_notifications_and_upload_gate(system):
    c, db, mail = system; login(c, mail)
    subject = c.get("/api/account/session").json()["user"]["subject_id"]
    db.raw.web_notifications.insert_many([{"id": "mine", "subject_id": subject, "title": "Mía", "read": False}, {"id": "other", "subject_id": "other-user", "title": "Ajena", "read": False}])
    db.raw.web_profile_drafts.insert_one({"subject_id": "other-user", "profile": {"tax_id": "NEVER-EXPOSE"}})
    data = c.get("/api/investor/workspace").json()
    assert [n["id"] for n in data["notifications"]] == ["mine"] and "NEVER-EXPOSE" not in str(data)
    assert c.post("/api/investor/notifications/other/read", json={}).status_code == 404
    assert c.post("/api/investor/notifications/mine/read", json={}).status_code == 200
    assert c.get("/api/investor/personal-documents/other-file").status_code == 404
    assert c.post("/api/investor/personal-documents", data={"category": "identity"}, files={"file": ("fake.pdf", b"%PDF-1.4 fake", "application/pdf")}).status_code == 503


def test_quarantine_uses_private_server_keys_and_does_not_grant_access(system, monkeypatch):
    c, db, mail = system; login(c, mail)
    for key, value in {"WEB_PERSONAL_UPLOADS_ENABLED": "true", "WEB_PERSONAL_BUCKET": "test-private", "WEB_PERSONAL_KMS_KEY_ID": "test-kms"}.items(): monkeypatch.setenv(key, value)
    objects = []
    class Store:
        def put_object(self, **kwargs): objects.append(kwargs)
    monkeypatch.setattr(web_workspace.web_personal_storage, "client", lambda *args: Store())
    result = c.post("/api/investor/personal-documents", data={"category": "identity"}, files={"file": ("../../SECRET.pdf", b"%PDF-1.4 fake", "application/pdf")})
    assert result.status_code == 200, result.text
    assert objects[0]["ServerSideEncryption"] == "aws:kms" and "SECRET" not in objects[0]["Key"]
    ident = result.json()["document_id"]
    assert c.get("/api/investor/personal-documents/"+ident).status_code == 409
    assert c.get("/api/investor/access").json()["stage"] == 0
    assert db.raw.web_access_reviews.count_documents({}) == 0
    assert c.post("/api/investor/personal-documents", data={"category": "identity"}, files={"file": ("fake.pdf", b"<script>bad</script>", "application/pdf")}).status_code == 415


def test_mfa_enrollment_required_replay_and_single_use_recovery(system, monkeypatch):
    import pyotp
    from cryptography.fernet import Fernet
    c, db, mail = system; login(c, mail)
    monkeypatch.setenv("WEB_REQUIRE_MFA", "true")
    monkeypatch.setenv("WEB_FACTOR_ENCRYPTION_KEY", Fernet.generate_key().decode())
    assert c.get("/api/investor/workspace").status_code == 200
    db.raw.web_users.update_one({}, {"$set": {"role": "superadmin"}})
    assert c.get("/api/investor/workspace").status_code == 403
    enroll = c.post("/api/account/second-factor/enroll", json={})
    assert enroll.status_code == 200, enroll.text
    secret = enroll.json()["secret"]
    assert "<svg" in enroll.json()["qr_svg"]
    assert "otpauth://" not in enroll.json()["qr_svg"]
    assert c.get("/api/account/config").json()["require_mfa"] is False
    assert secret not in str(db.raw.web_users.find_one({}))
    totp = pyotp.TOTP(secret)
    confirmed = c.post("/api/account/second-factor/confirm", json={"code": totp.now()})
    assert confirmed.status_code == 200, confirmed.text
    codes = confirmed.json()["recovery_codes"]
    assert codes[0] not in str(db.raw.web_users.find_one({}))
    assert c.get("/api/account/session").status_code == 401
    challenge = c.post("/api/account/login", json={"email": "one@example.com", "password": PASSWORD}).json()["challenge"]
    # Enrollment code may not be replayed as a login code.
    assert c.post("/api/account/second-factor/complete", json={"challenge": challenge, "code": totp.now()}).status_code == 401
    assert c.post("/api/account/second-factor/complete", json={"challenge": challenge, "code": codes[0]}).status_code == 200
    assert c.get("/api/investor/workspace").status_code == 200
    assert c.post("/api/account/second-factor/complete", json={"challenge": challenge, "code": codes[1]}).status_code == 401
    new = c.post("/api/account/login", json={"email": "one@example.com", "password": PASSWORD}).json()["challenge"]
    assert c.post("/api/account/second-factor/complete", json={"challenge": new, "code": codes[0]}).status_code == 401
    assert c.post("/api/account/second-factor/complete", json={"challenge": new, "code": totp.at(identity.now().timestamp()+30)}).status_code == 200


def test_mfa_attempt_limit_and_challenge_expiry(system, monkeypatch):
    import pyotp
    from cryptography.fernet import Fernet
    c, db, mail = system; login(c, mail)
    key = Fernet.generate_key(); monkeypatch.setenv("WEB_FACTOR_ENCRYPTION_KEY", key.decode())
    db.raw.web_users.update_one({}, {"$set": {"mfa_enabled": True, "mfa_secret": Fernet(key).encrypt(pyotp.random_base32().encode()).decode(), "mfa_last_counter": 0}})
    challenge = c.post("/api/account/login", json={"email": "one@example.com", "password": PASSWORD}).json()["challenge"]
    for _ in range(5): assert c.post("/api/account/second-factor/complete", json={"challenge": challenge, "code": "invalid"}).status_code == 401
    assert db.raw.web_login_challenges.find_one({})["attempts"] == 5
    assert c.post("/api/account/second-factor/complete", json={"challenge": challenge, "code": "invalid"}).status_code == 401

