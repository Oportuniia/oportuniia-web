"""WEB-owned accounts. Reuses APP's opaque, hashed, revocable session model.

No CORE admin identity, browser roles or uploaded files confer investor rights.
Public activation is closed until database, HTTPS origin, mail and legal versions
have been explicitly configured. Mail adapter is transactional SMTP with TLS.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import secrets
import smtplib
import ssl
import uuid
import json
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlparse

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

SESSION_COOKIE = "__Host-opp_session"
CSRF_COOKIE = "__Host-opp_csrf"
SESSION_HOURS = 12
IDLE_MINUTES = 30
REGISTRATION_MAIL = {"accepted": True, "message": "Te hemos enviado un correo para confirmar tu dirección. Revisa también la carpeta de spam. Después podrás completar tu perfil y aportar los documentos. El alta definitiva quedará pendiente de revisión y aprobación por OPORTUNIIA."}
GENERIC_MAIL = {"accepted": True, "message": "Si procede, recibirás instrucciones en tu correo."}
# A constant-cost unsuccessful password check; not a credential or seeded user.
_DUMMY_HASH = bcrypt.hashpw(secrets.token_bytes(32), bcrypt.gensalt(rounds=12))


def now():
    return datetime.now(timezone.utc)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def denied(code, status=403):
    raise HTTPException(status, detail={"code": code})


def enabled():
    return os.getenv("WEB_IDENTITY_MODE") == "web_sessions"


def public_origin():
    value = os.getenv("WEB_PUBLIC_ORIGIN", "").rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.username or parsed.password or parsed.query or parsed.fragment:
        denied("secure_public_origin_not_configured", 503)
    return value


def require_origin(request):
    if request.headers.get("origin") != public_origin():
        denied("untrusted_origin")
    if request.method not in {"GET", "HEAD"} and not request.headers.get("content-type", "").lower().startswith("application/json"):
        # Multipart uploads use a dedicated call that validates CSRF separately.
        denied("json_content_type_required", 415)


def mail_ready():
    if os.getenv("WEB_MAIL_TRANSPORT") == "gmail":
        from web_gmail import ready
        return ready()
    bridge = os.getenv("WEB_MAIL_BRIDGE_URL", "")
    if bridge:
        return urlparse(bridge).scheme == "https" and len(os.getenv("WEB_MAIL_BRIDGE_KEY", "")) >= 40
    if os.getenv("WEB_HOSTING_SMTP_AVAILABLE") != "true": return False
    return all(os.getenv(k, "").strip() for k in ("WEB_SMTP_HOST", "WEB_SMTP_USER", "WEB_SMTP_PASSWORD", "WEB_MAIL_FROM")) and os.getenv("WEB_SMTP_TLS", "starttls") in {"starttls", "ssl"}


def registration_ready():
    return enabled() and os.getenv("WEB_REGISTRATION_ENABLED") == "true" and mail_ready() and all(os.getenv(k, "").strip() for k in ("WEB_PRIVACY_VERSION", "WEB_TERMS_VERSION"))


def safe_user(user):
    return {k: user.get(k) for k in ("subject_id", "name", "email", "email_verified", "account_kind", "mfa_enabled", "username", "role", "must_change_password")}


async def ensure_indexes(db):
    await db.web_users.create_index("email", unique=True, partialFilterExpression={"email": {"$type": "string"}})
    await db.web_users.create_index("subject_id", unique=True, partialFilterExpression={"subject_id": {"$type": "string"}})
    await db.web_users.create_index("username", unique=True, partialFilterExpression={"username": {"$type": "string"}})
    await db.web_sessions.create_index("token_hash", unique=True)
    await db.web_sessions.create_index("expires_at", expireAfterSeconds=0)
    await db.web_identity_tokens.create_index("token_hash", unique=True)
    await db.web_identity_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.web_profile_drafts.create_index("subject_id", unique=True)
    await db.web_verified_profiles.create_index([("subject_id", 1), ("version", 1)], unique=True)
    await db.web_entitlements.create_index([("subject_id", 1), ("product", 1)], unique=True)
    await db.web_notifications.create_index([("subject_id", 1), ("id", 1)], unique=True)
    await db.web_reservations.create_index("checkout_request_id", unique=True, partialFilterExpression={"checkout_request_id": {"$type": "string"}})
    await db.web_login_challenges.create_index("expires_at", expireAfterSeconds=0)
    await db.web_auth_limits.create_index("expires_at", expireAfterSeconds=0)


async def rate_limit(db, request, action, email=""):
    # Atomic and shared across workers; no trusted X-Forwarded-For from the client.
    timestamp = now()
    ip = request.client.host if request.client else "unknown"
    for scope, value, maximum in (("ip", ip, 40), ("email", email.lower(), 8)):
        if not value:
            continue
        bucket = int(timestamp.timestamp()) // 900
        ident = digest(f"{action}:{scope}:{value}:{bucket}")
        record = await db.web_auth_limits.find_one_and_update({"_id": ident}, {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": timestamp + timedelta(minutes=30)}}, upsert=True, return_document=ReturnDocument.AFTER)
        if record["count"] > maximum:
            denied("too_many_attempts", 429)


async def audit(db, subject, event):
    await db.web_security_audit.insert_one({"id": str(uuid.uuid4()), "subject_id": subject, "event": event, "at": now()})


async def send_transactional(recipient, subject, body):
    if not mail_ready():
        denied("transactional_mail_not_configured", 503)
    def deliver():
        if os.getenv("WEB_MAIL_TRANSPORT") == "gmail":
            from web_gmail import deliver as gmail_deliver
            gmail_deliver(recipient, subject, body)
            return
        bridge = os.getenv("WEB_MAIL_BRIDGE_URL", "")
        if bridge:
            import requests
            raw = json.dumps({"to": recipient, "subject": subject, "body": body}, ensure_ascii=False, separators=(",", ":")).encode()
            stamp, nonce = str(int(time.time())), secrets.token_hex(16)
            signature = hmac.new(os.environ["WEB_MAIL_BRIDGE_KEY"].encode(), stamp.encode()+b"."+nonce.encode()+b"."+raw, hashlib.sha256).hexdigest()
            result = requests.post(bridge, data=raw, headers={"Content-Type": "application/json", "X-OPP-Mail-Timestamp": stamp, "X-OPP-Mail-Nonce": nonce, "X-OPP-Mail-Signature": signature}, timeout=20, allow_redirects=False)
            if result.status_code != 200 or result.json().get("accepted") is not True: raise RuntimeError("mail_bridge_unavailable")
            return
        message = EmailMessage()
        message["From"] = os.environ["WEB_MAIL_FROM"]
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        from web_mail_templates import html_alternative
        message.add_alternative(html_alternative(body), subtype="html")
        tls = os.getenv("WEB_SMTP_TLS", "starttls")
        cls = smtplib.SMTP_SSL if tls == "ssl" else smtplib.SMTP
        port = int(os.getenv("WEB_SMTP_PORT", "465" if tls == "ssl" else "587"))
        options = {"timeout": 15}
        if tls == "ssl":
            options["context"] = ssl.create_default_context()
        with cls(os.environ["WEB_SMTP_HOST"], port, **options) as smtp:
            if tls == "starttls":
                smtp.starttls(context=ssl.create_default_context())
            smtp.login(os.environ["WEB_SMTP_USER"], os.environ["WEB_SMTP_PASSWORD"])
            smtp.send_message(message)
    try:
        await asyncio.to_thread(deliver)
    except Exception:
        # Do not expose SMTP errors, recipients or verification tokens.
        denied("transactional_mail_temporarily_unavailable", 503)


async def mail_token(db, user, purpose):
    raw = secrets.token_urlsafe(32)
    timestamp = now()
    await db.web_identity_tokens.insert_one({"token_hash": digest(raw), "subject_id": user["subject_id"], "purpose": purpose,
        "version": user.get("session_version", 0), "expires_at": timestamp + timedelta(minutes=30), "used": False})
    # Fragment tokens do not enter HTTP access logs or referrer headers.
    link = public_origin()+"/cuenta#"+purpose+"="+raw
    if purpose == "verify":
        from web_mail_templates import registration_confirmation
        title, body = registration_confirmation(user.get("name", ""), link)
    else:
        title = "Restablece tu contraseña · OPORTUNIIA"
        body = "Restablece tu contraseña en este enlace de un solo uso (30 minutos):\n\n"+link+"\n\nSi no lo has solicitado, ignora este mensaje."
    await send_transactional(user.get("recovery_email") or user["email"], title, body)


async def consume_token(db, raw, purpose):
    record = await db.web_identity_tokens.find_one_and_update({"token_hash": digest(raw), "purpose": purpose, "used": False, "expires_at": {"$gt": now()}}, {"$set": {"used": True}}, return_document=ReturnDocument.BEFORE)
    if not record:
        denied("invalid_or_expired_link", 400)
    return record


def validate_password(password):
    # Existing ecosystem uses bcrypt. Reject its truncation boundary explicitly.
    if len(password) < 11 or len(password.encode("utf-8")) > 72:
        denied("password_requires_11_characters_maximum_72_bytes", 422)


async def hash_password(password):
    validate_password(password)
    return (await asyncio.to_thread(bcrypt.hashpw, password.encode(), bcrypt.gensalt(rounds=12))).decode()


async def resolve_session(request: Request, db, *, check_csrf=True):
    if not enabled():
        denied("web_identity_not_activated", 503)
    token = request.cookies.get(SESSION_COOKIE, "")
    if not 32 <= len(token) <= 200:
        denied("authentication_required", 401)
    stamp = now()
    session = await db.web_sessions.find_one({"token_hash": digest(token), "revoked": False, "expires_at": {"$gt": stamp}, "last_seen": {"$gt": stamp-timedelta(minutes=IDLE_MINUTES)}})
    if not session:
        denied("invalid_or_expired_session", 401)
    user = await db.web_users.find_one({"subject_id": session["subject_id"], "active": True, "email_verified": True})
    if not user or user.get("session_version", 0) != session.get("version", 0):
        denied("session_revoked", 401)
    if user.get("must_change_password") and request.url.path not in {"/api/account/change-password", "/api/account/logout", "/api/account/session"}:
        denied("initial_password_change_required", 403)
    if check_csrf and request.method not in {"GET", "HEAD", "OPTIONS"}:
        # Content type is validated by each endpoint; uploads remain multipart.
        if request.headers.get("origin") != public_origin():
            denied("untrusted_origin")
        csrf, header = request.cookies.get(CSRF_COOKIE, ""), request.headers.get("x-csrf-token", "")
        if not csrf or not hmac.compare_digest(csrf, header) or not hmac.compare_digest(digest(csrf), session.get("csrf_hash", "")):
            denied("csrf_required")
    await db.web_sessions.update_one({"_id": session["_id"], "revoked": False}, {"$set": {"last_seen": stamp}})
    request.state.web_user = user
    request.state.web_session = session
    return user, session


async def issue_session(db, user, response, mfa_verified=False):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    stamp = now()
    await db.web_sessions.insert_one({"token_hash": digest(token), "csrf_hash": digest(csrf), "subject_id": user["subject_id"], "version": user.get("session_version", 0),
        "mfa_verified": mfa_verified, "revoked": False, "created_at": stamp, "last_seen": stamp, "expires_at": stamp+timedelta(hours=SESSION_HOURS)})
    response.set_cookie(SESSION_COOKIE, token, secure=True, httponly=True, samesite="lax", path="/", max_age=SESSION_HOURS*3600)
    response.set_cookie(CSRF_COOKIE, csrf, secure=True, httponly=False, samesite="strict", path="/", max_age=SESSION_HOURS*3600)
    await audit(db, user["subject_id"], "LOGIN_MFA" if mfa_verified else "LOGIN")


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=1, max_length=180)
    password: str = Field(min_length=1, max_length=200)


class Signup(Credentials):
    email: EmailStr = Field(max_length=180)
    name: str = Field(min_length=1, max_length=180)
    account_kind: str
    accept_privacy: bool
    accept_terms: bool


class MailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=180)


class LinkToken(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=200)


class Reset(LinkToken):
    password: str = Field(min_length=11, max_length=200)


def register_identity_routes(router: APIRouter, db):
    @router.get("/account/config")
    async def config():
        catalog_state = "error"
        if db is not None:
            try:
                ids = await db.web_operation_bindings.distinct("internal_id", {"publication_approved": True, "catalog_reference_safe": True})
                published = await db.presentation_web_published.find_one({"internal_id": {"$in": ids}, "publication_state": "PUBLISHED"}, {"_id": 1}) if ids else None
                catalog_state = "available" if published else "empty"
            except Exception:
                # A database failure is never presented as an empty catalogue.
                catalog_state = "error"
        return {"catalog_state": catalog_state,"early_access": os.getenv("WEB_EARLY_ACCESS", "true").strip().lower() in {"1", "true", "yes", "on"}, "identity_enabled": enabled(), "recovery_enabled": enabled() and mail_ready(), "registration_enabled": registration_ready(), "require_mfa": False, "mfa_required_roles": ["superadmin"], "mode": "web_sessions" if enabled() else "unavailable"}

    @router.post("/account/register", status_code=202)
    async def register(payload: Signup, request: Request):
        require_origin(request)
        if not registration_ready():
            denied("registration_not_activated", 503)
        if payload.account_kind not in {"inversor", "colaborador"} or not payload.accept_privacy or not payload.accept_terms:
            denied("registration_requirements_missing", 422)
        email = str(payload.email).strip().lower()
        await rate_limit(db, request, "register", email)
        hashed = await hash_password(payload.password)
        user = {"subject_id": str(uuid.uuid4()), "email": email, "name": payload.name.strip(), "password_hash": hashed, "account_kind": payload.account_kind,
            "active": True, "email_verified": False, "session_version": 0, "created_at": now(), "acceptance": {"privacy": os.environ["WEB_PRIVACY_VERSION"], "terms": os.environ["WEB_TERMS_VERSION"], "accepted_at": now()}}
        try:
            await db.web_users.insert_one(user)
        except DuplicateKeyError:
            existing = await db.web_users.find_one({"email": email})
            if existing and existing.get("active") and not existing.get("email_verified"):
                await mail_token(db, existing, "verify")
            else:
                await send_transactional(email, "Tu solicitud de acceso a OPORTUNIIA",
                    "Hemos recibido tu solicitud. Si ya confirmaste tu correo, puedes iniciar sesión en "
                    + public_origin() + "/cuenta. Si necesitas ayuda con tu acceso, contacta con OPORTUNIIA. "
                    "El alta definitiva requiere revisión y aprobación de tu documentación.")
            return REGISTRATION_MAIL
        await audit(db, user["subject_id"], "ACCOUNT_CREATED_PENDING_EMAIL")
        await mail_token(db, user, "verify")
        return REGISTRATION_MAIL

    @router.post("/account/verify-email")
    async def verify(payload: LinkToken, request: Request):
        require_origin(request)
        if not enabled(): denied("web_identity_not_activated", 503)
        await rate_limit(db, request, "verify")
        token = await consume_token(db, payload.token, "verify")
        result = await db.web_users.update_one({"subject_id": token["subject_id"], "active": True, "session_version": token["version"]}, {"$set": {"email_verified": True, "email_verified_at": now()}})
        if not result.matched_count: denied("invalid_or_expired_link", 400)
        await audit(db, token["subject_id"], "EMAIL_VERIFIED")
        return {"verified": True, "identity_verified": False, "premium": False}

    @router.post("/account/resend-verification", status_code=202)
    async def resend(payload: MailRequest, request: Request):
        require_origin(request)
        if not registration_ready(): denied("registration_not_activated", 503)
        email = str(payload.email).strip().lower()
        await rate_limit(db, request, "verify-mail", email)
        user = await db.web_users.find_one({"email": email, "active": True, "email_verified": False})
        if user: await mail_token(db, user, "verify")
        return GENERIC_MAIL

    @router.post("/account/login")
    async def login(payload: Credentials, request: Request, response: Response):
        require_origin(request)
        if not enabled(): denied("web_identity_not_activated", 503)
        email = str(payload.email).strip().lower()
        await rate_limit(db, request, "login", email)
        user = await db.web_users.find_one({"$or": [{"email": email}, {"username": email}]})
        candidate = payload.password.encode()
        try: valid = len(candidate) <= 72 and await asyncio.to_thread(bcrypt.checkpw, candidate, (user or {}).get("password_hash", _DUMMY_HASH.decode()).encode())
        except (ValueError, TypeError): valid = False
        if not valid or not user or not user.get("active") or not user.get("email_verified"):
            denied("invalid_credentials_or_unverified_email", 401)
        if user.get("must_change_password") and user.get("initial_password_expires_at", now()) <= now():
            denied("initial_password_expired", 401)
        if user.get("mfa_enabled"):
            from web_secondfactor import challenge
            return await challenge(db, user)
        await issue_session(db, user, response)
        return {"user": safe_user(user)}

    @router.get("/account/session")
    async def session(request: Request):
        user, _ = await resolve_session(request, db)
        return {"user": safe_user(user)}

    @router.post("/account/logout")
    async def logout(request: Request, response: Response):
        user, session = await resolve_session(request, db)
        await db.web_sessions.update_one({"_id": session["_id"]}, {"$set": {"revoked": True}})
        for cookie in (SESSION_COOKIE, CSRF_COOKIE): response.delete_cookie(cookie, path="/", secure=True, samesite="lax")
        await audit(db, user["subject_id"], "LOGOUT")
        return {"signed_out": True}

    @router.post("/account/forgot-password", status_code=202)
    async def forgot(payload: MailRequest, request: Request):
        require_origin(request)
        if not enabled() or not mail_ready(): denied("account_recovery_not_activated", 503)
        email = str(payload.email).strip().lower()
        await rate_limit(db, request, "forgot", email)
        user = await db.web_users.find_one({"$or": [{"email": email}, {"username": email}], "active": True, "email_verified": True})
        if user: await mail_token(db, user, "reset")
        return GENERIC_MAIL

    @router.post("/account/reset-password")
    async def reset(payload: Reset, request: Request):
        require_origin(request)
        if not enabled(): denied("web_identity_not_activated", 503)
        await rate_limit(db, request, "reset")
        hashed = await hash_password(payload.password)
        token = await consume_token(db, payload.token, "reset")
        result = await db.web_users.update_one({"subject_id": token["subject_id"], "active": True, "session_version": token["version"]}, {"$set": {"password_hash": hashed, "password_changed_at": now(), "must_change_password": False}, "$inc": {"session_version": 1}})
        if not result.matched_count: denied("invalid_or_expired_link", 400)
        await db.web_sessions.update_many({"subject_id": token["subject_id"]}, {"$set": {"revoked": True}})
        await audit(db, token["subject_id"], "PASSWORD_RESET_ALL_SESSIONS_REVOKED")
        return {"changed": True, "sign_in_required": True}



class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=11, max_length=200)


def register_password_change_routes(router, db):
    @router.post("/account/change-password")
    async def change(payload: PasswordChange, request: Request):
        user, _ = await resolve_session(request, db)
        await rate_limit(db, request, "change-password", user["subject_id"])
        candidate = payload.current_password.encode()
        try:
            valid = len(candidate) <= 72 and await asyncio.to_thread(bcrypt.checkpw, candidate, user["password_hash"].encode())
        except (ValueError, TypeError):
            valid = False
        if not valid: denied("invalid_current_password", 401)
        if hmac.compare_digest(payload.current_password.encode(), payload.new_password.encode()): denied("new_password_must_differ", 422)
        hashed = await hash_password(payload.new_password)
        result = await db.web_users.update_one({"subject_id": user["subject_id"], "session_version": user.get("session_version", 0)}, {"$set": {"password_hash": hashed, "password_changed_at": now(), "must_change_password": False}, "$unset": {"initial_password_expires_at": ""}, "$inc": {"session_version": 1}})
        if not result.matched_count: denied("session_revoked", 401)
        await db.web_sessions.update_many({"subject_id": user["subject_id"]}, {"$set": {"revoked": True}})
        await audit(db, user["subject_id"], "PASSWORD_CHANGED_ALL_SESSIONS_REVOKED")
        return {"changed": True, "sign_in_required": True}

