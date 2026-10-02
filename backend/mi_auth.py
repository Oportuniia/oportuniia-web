"""MI OPORTUNIIA account lifecycle; disabled unless explicitly configured.

Independent of LEGAL and GHL. HTTPS cookie auth with server-side Mongo
sessions. Creating a personal profile does NOT grant PDF permissions.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import re
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import bcrypt
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from personal_user_registry import ROLES, ensure_registry_indexes, normalize_email, approve_and_assign, public_actor
from mi_private_area import safe_profile, private_documents, profile_update
from mi_premium_service import premium_inspect, premium_confirm, premium_photo_inspect, premium_photo_confirm
from mi_private_upload import upload_intent, confirm_upload
from mi_rate_limit import auth_throttle, ensure_rate_indexes
from mi_private_download import signed_private_download

router = APIRouter(prefix="/api/mi", tags=["MI OPORTUNIIA"])
COOKIE = "mi_session"
VERIFY_HOURS = 24
SESSION_HOURS = 12


def _enabled():
    if os.getenv("MI_AUTH_ENABLED") != "1":
        raise HTTPException(503, "El registro privado todavía no está habilitado")


def _now():
    return datetime.now(timezone.utc)


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _same_origin(request: Request):
    """Block cross-origin mutation regardless of cookie SameSite mode."""
    origin = request.headers.get("origin")
    allowed = os.getenv("MI_PUBLIC_ORIGIN", "").rstrip("/")
    if not allowed or not origin or not hmac.compare_digest(origin.rstrip("/"), allowed):
        raise HTTPException(403, "Origen no autorizado")


def _password(password: str) -> bytes:
    if not 12 <= len(password) <= 72 or len(password.encode()) > 72:
        raise ValueError("Longitud de contraseña no válida")
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))


def _check_password(password: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed)
    except (ValueError, TypeError):
        return False


class Signup(BaseModel):
    email: str
    password: str
    role: str
    terms_version: str = Field(min_length=2, max_length=64)
    privacy_accepted: bool


class Login(BaseModel):
    email: str
    password: str


class RecoveryRequest(BaseModel):
    email: str


class RecoveryComplete(BaseModel):
    token: str = Field(min_length=30, max_length=150)
    new_password: str


class TokenIn(BaseModel):
    token: str = Field(min_length=30, max_length=150)


class Approval(BaseModel):
    actor_id: str


class ProfileChange(BaseModel):
    preferred_name: str = Field(min_length=1, max_length=100)


class FileIntent(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    mime: str
    size: int = Field(ge=1, le=25 * 1024 * 1024)


class PhotoConfirm(BaseModel):
    kind: str


class PdfConfirm(BaseModel):
    groups: list[dict] = Field(min_length=1, max_length=100)


def _smtp_send(email: str, token: str):
    host = os.getenv("MI_SMTP_HOST")
    user = os.getenv("MI_SMTP_USER")
    password = os.getenv("MI_SMTP_PASSWORD")
    sender = os.getenv("MI_SMTP_FROM")
    base = os.getenv("MI_PUBLIC_ORIGIN", "").rstrip("/")
    if not all((host, user, password, sender, base)):
        raise RuntimeError("SMTP configuration missing")
    msg = EmailMessage()
    msg["Subject"] = "Confirma tu correo · OPORTUNIIA"
    msg["From"] = sender
    msg["To"] = email
    msg.set_content(
        "Confirma tu registro de MI OPORTUNIIA con este código personal:\n\n"
        + token + "\n\n"
        + "Introdúcelo únicamente en " + base
        + ". Caduca en 24 horas. Si no has solicitado el registro, ignora este mensaje."
    )
    with smtplib.SMTP(host, int(os.getenv("MI_SMTP_PORT", "587")), timeout=15) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(user, password)
        smtp.send_message(msg)


def _smtp_reset(email: str, token: str):
    host = os.getenv("MI_SMTP_HOST")
    user = os.getenv("MI_SMTP_USER")
    password = os.getenv("MI_SMTP_PASSWORD")
    sender = os.getenv("MI_SMTP_FROM")
    if not all((host, user, password, sender)):
        raise RuntimeError("SMTP configuration missing")
    msg = EmailMessage()
    msg["Subject"] = "Recuperación de acceso · OPORTUNIIA"
    msg["From"] = sender
    msg["To"] = email
    msg.set_content(
        "Has solicitado restablecer tu contraseña de MI OPORTUNIIA. "
        "Introduce este código únicamente en nuestra web oficial:\n\n"
        + token + "\n\nCaduca en 30 minutos. Si no lo solicitaste, ignora este mensaje."
    )
    with smtplib.SMTP(host, int(os.getenv("MI_SMTP_PORT", "587")), timeout=15) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(user, password)
        smtp.send_message(msg)


def register_routes(db):
    @router.post("/auth/register", status_code=202)
    async def register(payload: Signup, request: Request):
        _enabled()
        _same_origin(request)
        if payload.role not in ROLES or not payload.privacy_accepted:
            raise HTTPException(422, "Perfil o consentimiento no válido")
        # The authoritative legal version comes from WEB, not a client claim.
        expected_terms = os.getenv("MI_TERMS_VERSION", "")
        if not expected_terms:
            raise HTTPException(503, "Condiciones de registro no configuradas")
        if not hmac.compare_digest(payload.terms_version, expected_terms):
            raise HTTPException(409, "Las condiciones han cambiado; actualiza el formulario")
        try:
            email = normalize_email(payload.email)
            hashed = _password(payload.password)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        if not all(os.getenv(k) for k in ("MI_SMTP_HOST","MI_SMTP_USER","MI_SMTP_PASSWORD","MI_SMTP_FROM")):
            raise HTTPException(503, "Servicio de confirmación no configurado")
        await auth_throttle(db, request, action="register", email=email,
                            per_ip=12, per_email=3)
        token = secrets.token_urlsafe(32)
        now = _now()
        actor = {
            "actor_id": "mi_" + secrets.token_hex(16),
            "role": payload.role, "email": email,
            "password_hash": hashed.decode(),
            "validation_state": "PENDING", "email_verified": False,
            "public_code": None, "verify_hash": _digest(token),
            "verify_expires": now + timedelta(hours=VERIFY_HOURS),
            "terms_version": payload.terms_version, "privacy_accepted_at": now,
            "created_at": now, "updated_at": now,
        }
        try:
            await db.mi_actors.insert_one(actor)
        except DuplicateKeyError:
            # Do not reveal whether the address exists.
            return {"status": "check_email"}
        try:
            await asyncio.to_thread(_smtp_send, email, token)
        except Exception:
            # Never leave an unverifiable account due to delivery failure.
            await db.mi_actors.delete_one({"actor_id": actor["actor_id"], "email_verified": False})
            raise HTTPException(503, "No se pudo enviar la confirmación; inténtalo de nuevo")
        return {"status": "check_email"}

    @router.post("/auth/resend")
    async def resend_verification(payload: RecoveryRequest, request: Request):
        _enabled()
        _same_origin(request)
        generic = {"status": "if_registered_check_email"}
        try:
            email = normalize_email(payload.email)
        except ValueError:
            return generic
        await auth_throttle(db, request, action="resend", email=email,
                            per_ip=8, per_email=2)
        actor = await db.mi_actors.find_one({
            "email": email, "email_verified": False, "validation_state": "PENDING",
        })
        if not actor:
            return generic
        if not all(os.getenv(k) for k in ("MI_SMTP_HOST", "MI_SMTP_USER", "MI_SMTP_PASSWORD", "MI_SMTP_FROM")):
            raise HTTPException(503, "Servicio de correo no configurado")
        token = secrets.token_urlsafe(32)
        now = _now()
        await db.mi_actors.update_one(
            {"actor_id": actor["actor_id"], "email_verified": False},
            {"$set": {"verify_hash": _digest(token),
                      "verify_expires": now + timedelta(hours=VERIFY_HOURS),
                      "updated_at": now}},
        )
        try:
            await asyncio.to_thread(_smtp_send, email, token)
        except Exception:
            raise HTTPException(503, "Servicio de correo temporalmente no disponible")
        return generic

    @router.post("/auth/verify")
    async def verify(payload: TokenIn, request: Request):
        _enabled()
        _same_origin(request)
        await auth_throttle(db, request, action="verify", per_ip=20)
        now = _now()
        actor = await db.mi_actors.find_one_and_update(
            {"verify_hash": _digest(payload.token), "verify_expires": {"$gt": now},
             "email_verified": False, "validation_state": "PENDING"},
            {"$set": {"email_verified": True, "updated_at": now},
             "$unset": {"verify_hash": "", "verify_expires": ""}},
            return_document=ReturnDocument.AFTER,
        )
        if not actor:
            raise HTTPException(400, "Código inválido o caducado")
        return {"status": "email_verified", "next": "pending_validation"}

    @router.post("/auth/recovery/request")
    async def recovery_request(payload: RecoveryRequest, request: Request):
        _enabled()
        _same_origin(request)
        generic = {"status": "if_registered_check_email"}
        try:
            email = normalize_email(payload.email)
        except ValueError:
            return generic
        await auth_throttle(db, request, action="recover", email=email,
                            per_ip=8, per_email=3)
        actor = await db.mi_actors.find_one({"email": email, "email_verified": True,
                     "validation_state": {"$in": ["PENDING", "VERIFIED"]}})
        if not actor:
            return generic
        if not all(os.getenv(k) for k in ("MI_SMTP_HOST", "MI_SMTP_USER", "MI_SMTP_PASSWORD", "MI_SMTP_FROM")):
            raise HTTPException(503, "Servicio de correo no configurado")
        # The public route also requires a distributed per-IP/account rate limiter
        # before MI_AUTH_ENABLED is set to 1.
        token = secrets.token_urlsafe(32)
        now = _now()
        await db.mi_actors.update_one(
            {"actor_id": actor["actor_id"]},
            {"$set": {"reset_hash": _digest(token),
                      "reset_expires": now + timedelta(minutes=30),
                      "updated_at": now}},
        )
        try:
            await asyncio.to_thread(_smtp_reset, email, token)
        except Exception:
            await db.mi_actors.update_one(
                {"actor_id": actor["actor_id"], "reset_hash": _digest(token)},
                {"$unset": {"reset_hash": "", "reset_expires": ""}},
            )
            raise HTTPException(503, "Servicio temporalmente no disponible")
        return generic

    @router.post("/auth/recovery/complete")
    async def recovery_complete(payload: RecoveryComplete, request: Request):
        _enabled()
        _same_origin(request)
        try:
            new_hash = _password(payload.new_password).decode()
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        await auth_throttle(db, request, action="reset", per_ip=10)
        actor = await db.mi_actors.find_one_and_update(
            {"reset_hash": _digest(payload.token), "reset_expires": {"$gt": _now()},
             "email_verified": True,
             "validation_state": {"$in": ["PENDING", "VERIFIED"]}},
            {"$set": {"password_hash": new_hash, "updated_at": _now()},
             "$unset": {"reset_hash": "", "reset_expires": ""}},
            return_document=ReturnDocument.AFTER,
        )
        if not actor:
            raise HTTPException(400, "Código inválido o caducado")
        await db.mi_sessions.delete_many({"actor_id": actor["actor_id"]})
        return {"status": "password_updated_all_sessions_revoked"}

    @router.post("/auth/login")
    async def login(payload: Login, request: Request, response: Response):
        _enabled()
        _same_origin(request)
        try:
            email = normalize_email(payload.email)
        except ValueError:
            raise HTTPException(401, "Credenciales inválidas")
        # Role is not selected from client. Duplicate email between profiles
        # requires one single role per email, enforced below by registration.
        await auth_throttle(db, request, action="login", email=email,
                            per_ip=30, per_email=10)
        actor = await db.mi_actors.find_one({"email": email})
        stored = actor.get("password_hash", "") if actor else ""
        if not stored or not _check_password(payload.password, stored.encode()):
            raise HTTPException(401, "Credenciales inválidas")
        if not actor.get("email_verified") or actor.get("validation_state") in ("SUSPENDED", "REJECTED"):
            raise HTTPException(403, "Cuenta pendiente o no disponible")
        raw = secrets.token_urlsafe(32)
        now = _now()
        await db.mi_sessions.insert_one({
            "session_hash": _digest(raw), "actor_id": actor["actor_id"],
            "created_at": now, "expires_at": now + timedelta(hours=SESSION_HOURS)
        })
        response.set_cookie(COOKIE, raw, secure=True, httponly=True, samesite="strict",
                            max_age=SESSION_HOURS * 3600, path="/")
        return {"actor": public_actor(actor), "email_verified": True}

    async def _session(request: Request):
        raw = request.cookies.get(COOKIE, "")
        if not raw or len(raw) > 200:
            raise HTTPException(401, "Sesión requerida")
        row = await db.mi_sessions.find_one({
            "session_hash": _digest(raw), "expires_at": {"$gt": _now()}
        })
        if not row:
            raise HTTPException(401, "Sesión caducada")
        actor = await db.mi_actors.find_one({"actor_id": row["actor_id"]})
        if not actor or not actor.get("email_verified") or actor["validation_state"] not in ("PENDING", "VERIFIED"):
            raise HTTPException(403, "Cuenta no disponible")
        return actor

    @router.get("/auth/me")
    async def me(request: Request):
        _enabled()
        actor = await _session(request)
        return {"actor": public_actor(actor), "email_verified": True}

    @router.get("/private/profile")
    async def private_profile(request: Request):
        _enabled()
        actor = await _session(request)
        return {"profile": {**safe_profile(actor),
                            "preferred_name": actor.get("preferred_name", "")}}

    @router.patch("/private/profile")
    async def change_private_profile(payload: ProfileChange, request: Request):
        _enabled()
        _same_origin(request)
        actor = await _session(request)
        return await profile_update(db, actor, preferred_name=payload.preferred_name)

    @router.get("/private/documents")
    async def list_private_documents(request: Request, limit: int = 50):
        _enabled()
        actor = await _session(request)
        return {"documents": await private_documents(db, actor, limit=limit)}

    @router.get("/private/documents/{file_id}/download")
    async def download_private_document(file_id: str, request: Request, response: Response):
        _enabled()
        actor = await _session(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return await signed_private_download(db, actor, file_id)

    @router.post("/private/documents/upload-intent")
    async def private_upload_intent(payload: FileIntent, request: Request):
        _enabled()
        _same_origin(request)
        actor = await _session(request)
        return await upload_intent(db, actor, name=payload.display_name,
                                   mime=payload.mime, size=payload.size)

    @router.post("/private/documents/{file_id}/confirm")
    async def private_confirm_file(file_id: str, request: Request):
        _enabled()
        _same_origin(request)
        actor = await _session(request)
        return await confirm_upload(db, actor, file_id)

    @router.post("/private/premium/image/{file_id}/inspect")
    async def inspect_private_image(file_id: str, request: Request):
        _enabled()
        _same_origin(request)
        actor = await _session(request)
        return await premium_photo_inspect(db, actor, file_id)

    @router.post("/private/premium/image/{file_id}/confirm")
    async def confirm_private_image(file_id: str, payload: PhotoConfirm, request: Request):
        _enabled()
        _same_origin(request)
        actor = await _session(request)
        return await premium_photo_confirm(db, actor, file_id, payload.kind)

    @router.post("/private/premium/pdf/{file_id}/inspect")
    async def inspect_private_pdf(file_id: str, request: Request):
        _enabled()
        _same_origin(request)
        actor = await _session(request)
        return await premium_inspect(db, actor, file_id)

    @router.post("/private/premium/pdf/{file_id}/confirm")
    async def confirm_private_pdf(file_id: str, payload: PdfConfirm, request: Request):
        _enabled()
        _same_origin(request)
        actor = await _session(request)
        return await premium_confirm(db, actor, file_id, payload.groups)

    @router.post("/auth/logout-all")
    async def logout_everywhere(request: Request, response: Response):
        _enabled()
        _same_origin(request)
        actor = await _session(request)
        await db.mi_sessions.delete_many({"actor_id": actor["actor_id"]})
        response.delete_cookie(COOKIE, path="/", secure=True,
                               httponly=True, samesite="strict")
        return {"status": "all_sessions_revoked"}

    @router.post("/auth/logout")
    async def logout(request: Request, response: Response):
        _enabled()
        _same_origin(request)
        raw = request.cookies.get(COOKIE, "")
        if raw:
            await db.mi_sessions.delete_one({"session_hash": _digest(raw)})
        response.delete_cookie(COOKIE, path="/", secure=True, httponly=True, samesite="strict")
        return {"status": "logged_out"}

    @router.post("/admin/approve")
    async def approve(payload: Approval, request: Request):
        _enabled()
        _same_origin(request)
        admin_token = os.getenv("MI_ADMIN_BOOTSTRAP_TOKEN", "")
        if len(admin_token) < 32 or not hmac.compare_digest(
            request.headers.get("x-mi-admin-token", ""), admin_token
        ):
            raise HTTPException(403, "Autorización administrativa requerida")
        actor = await db.mi_actors.find_one({"actor_id": payload.actor_id})
        if not actor or not actor.get("email_verified"):
            raise HTTPException(409, "Cuenta sin correo confirmado")
        try:
            approved = await approve_and_assign(db, actor_id=payload.actor_id, reviewer_id="mi_bootstrap_admin")
        except (ValueError, PermissionError) as exc:
            raise HTTPException(409, str(exc)) from exc
        return {"actor": approved}

    return router


def register_index_lifecycle(db):
    """Explicitly called only after activation against intended database."""
    async def _indexes():
        await ensure_registry_indexes(db)
        await ensure_rate_indexes(db)
        # Prevent multiple roles sharing an email until unified account design.
        await db.mi_actors.create_index("email", unique=True)
        await db.mi_sessions.create_index("session_hash", unique=True)
        await db.mi_sessions.create_index("expires_at", expireAfterSeconds=0)
        await db.mi_actors.create_index("reset_hash", unique=True,
            partialFilterExpression={"reset_hash": {"$type": "string"}})
        await db.mi_actors.create_index("verify_hash", unique=True,
            partialFilterExpression={"verify_hash": {"$type": "string"}})
    return _indexes
