"""Account lifecycle owned by this application; no external identity provider."""
import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlencode, quote
from urllib.request import Request as URLRequest, urlopen

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

log = logging.getLogger(__name__)


def password_valid(password):
    if len(password) < 12 or len(password.encode("utf-8")) > 72:
        raise HTTPException(422, "Usa al menos 12 caracteres y como máximo 72 bytes")


def require_password_change(user, path):
    allowed = {"/api/accounts/me", "/api/accounts/password", "/api/auth/me", "/api/auth/logout", "/api/auth/change-password"}
    if user.get("must_change_password") and path.rstrip("/") not in allowed:
        raise HTTPException(403, {"code": "password_change_required", "message": "Debes cambiar tu contraseña inicial"})


def utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


async def resolve_identifier(collection, identifier):
    key = identifier.strip().casefold()
    user = await collection.find_one({"username_key": key})
    if not user:
        user = await collection.find_one({"username": {"$regex": "^" + re.escape(key) + "$", "$options": "i"}})
    if not user and "@" in key and await collection.count_documents({"email": key}) == 1:
        user = await collection.find_one({"email": key})
    return user


def check_initial_expiry(user):
    expires = user.get("temporary_password_expires_at")
    if user.get("must_change_password") and expires and utc(expires) <= datetime.now(timezone.utc):
        raise HTTPException(403, "La contraseña inicial ha caducado. Recupera tu contraseña")


def send_recovery_email(email, token, username):
    # Google Workspace outbound: scope gmail.send only. Never expose credentials.
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh = os.environ.get("GMAIL_REFRESH_TOKEN")
    sender = os.environ.get("GMAIL_SENDER")
    app_url = (os.environ.get("PUBLIC_APP_URL") or os.environ.get("WEB_PUBLIC_URL", "")).rstrip("/")
    if not all((client_id, client_secret, refresh, sender, app_url)):
        log.error("Account recovery email is not configured")
        return False
    try:
        body = urlencode({"grant_type": "refresh_token", "client_id": client_id,
                          "client_secret": client_secret, "refresh_token": refresh}).encode()
        req = URLRequest("https://oauth2.googleapis.com/token", data=body)
        with urlopen(req, timeout=15) as response:
            access = json.load(response)["access_token"]
        message = EmailMessage()
        message["From"] = sender
        message["To"] = email
        message["Subject"] = "OPORTUNIIA · Restablecer contraseña"
        message.set_content(f"Cuenta: {username}\n\nEl enlace es de un solo uso y caduca en 30 minutos:\n{app_url}/cuenta/recuperar?token={quote(token)}\n\nSi no lo solicitaste, ignora este correo.")
        data = json.dumps({"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}).encode()
        req = URLRequest("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", data=data,
                         headers={"Authorization": "Bearer " + access, "Content-Type": "application/json"})
        with urlopen(req, timeout=20) as response:
            return bool(json.load(response).get("id"))
    except Exception as exc:
        log.error("Account recovery email failed (%s)", type(exc).__name__)
        return False


class CreateAccount(BaseModel):
    username: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9._@+-]+$")
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    role: str
    password: str = Field(min_length=12, max_length=256)


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class InitialPassword(BaseModel):
    password: str = Field(min_length=12, max_length=256)


class Recover(BaseModel):
    username: str = Field(min_length=1, max_length=254)
    email: EmailStr


class ResetPassword(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


def build_accounts_router(db, current_user, hash_password, verify_password, *,
                          roles, admin_role, id_field="id", version_field="token_version",
                          version_default=0, active_field="active", name_field="name"):
    router = APIRouter(prefix="/api/accounts", tags=["accounts"])
    collection = db.users

    def query(user_id):
        if id_field == "_id":
            if not ObjectId.is_valid(user_id):
                raise HTTPException(404, "Usuario no encontrado")
            return {"_id": ObjectId(user_id)}
        return {id_field: user_id}

    def uid(doc):
        return str(doc.get(id_field, doc.get("id", "")))

    def public(doc):
        return {"id": uid(doc), "username": doc.get("username", ""), "email": doc.get("email", ""),
                "name": doc.get(name_field, ""), "role": doc.get("role"),
                "active": doc.get(active_field, True), "must_change_password": doc.get("must_change_password", False)}

    async def admin(user=Depends(current_user)):
        if user.get("role") != admin_role:
            raise HTTPException(403, "Solo administradores")
        return user

    async def audit(actor, action, target):
        await db.account_audit.insert_one({"actor_id": str(actor["id"]), "action": action,
                                            "target_id": target, "created_at": datetime.now(timezone.utc)})

    async def replace_password(doc, password, initial):
        password_valid(password)
        values = {"password_hash": hash_password(password), "must_change_password": initial,
                  version_field: int(doc.get(version_field, version_default)) + 1}
        if initial:
            values["temporary_password_expires_at"] = datetime.now(timezone.utc) + timedelta(hours=24)
        update = {"$set": values}
        if not initial:
            update["$unset"] = {"temporary_password_expires_at": ""}
        result = await collection.update_one({**query(uid(doc)), "password_hash": doc["password_hash"]}, update)
        if not result.modified_count:
            raise HTTPException(409, "La cuenta ha cambiado. Inicia sesión de nuevo")
        await db.account_reset_tokens.delete_many({"user_id": uid(doc)})

    @router.get("/me")
    async def me(user=Depends(current_user)):
        doc = await collection.find_one(query(user["id"]))
        if not doc:
            raise HTTPException(401, "Sesión no válida")
        return public(doc)

    @router.get("/users")
    async def users(actor=Depends(admin)):
        return [public(doc) for doc in await collection.find({}).to_list(500)]

    @router.post("/users")
    async def create(payload: CreateAccount, actor=Depends(admin)):
        password_valid(payload.password)
        if payload.role not in roles:
            raise HTTPException(422, "Rol no válido")
        if await resolve_identifier(collection, payload.username):
            raise HTTPException(409, "Ese usuario ya existe")
        if await collection.find_one({"email": str(payload.email).lower()}):
            raise HTTPException(409, "Ese correo ya está asociado a una cuenta")
        doc = {"username": payload.username.strip(), "username_key": payload.username.strip().casefold(),
               "email": str(payload.email).lower(), name_field: payload.name.strip(), "role": payload.role,
               "password_hash": hash_password(payload.password), "must_change_password": True,
               "temporary_password_expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
               active_field: True, version_field: version_default, "created_at": datetime.now(timezone.utc).isoformat()}
        doc["username_norm"] = payload.username.strip().casefold()
        doc["email_norm"] = str(payload.email).lower()
        if id_field != "_id":
            doc[id_field] = str(uuid.uuid4())
        result = await collection.insert_one(doc)
        if id_field == "_id":
            doc["_id"] = result.inserted_id
        await audit(actor, "CREATE_USER", uid(doc))
        return public(doc)

    @router.post("/users/{user_id}/password")
    async def issue_initial(user_id: str, payload: InitialPassword, actor=Depends(admin)):
        if user_id == actor["id"]:
            raise HTTPException(400, "Utiliza Cambiar mi contraseña")
        doc = await collection.find_one(query(user_id))
        if not doc:
            raise HTTPException(404, "Usuario no encontrado")
        await replace_password(doc, payload.password, True)
        await audit(actor, "ISSUE_INITIAL_PASSWORD", user_id)
        return {"ok": True}

    @router.delete("/users/{user_id}")
    async def delete(user_id: str, actor=Depends(admin)):
        if user_id == actor["id"]:
            raise HTTPException(400, "No puedes eliminar tu propia cuenta")
        if not await collection.find_one(query(user_id)):
            raise HTTPException(404, "Usuario no encontrado")
        await collection.delete_one(query(user_id))
        await db.account_reset_tokens.delete_many({"user_id": user_id})
        await audit(actor, "DELETE_USER", user_id)
        return {"ok": True}

    @router.post("/password")
    async def change(payload: ChangePassword, actor=Depends(current_user)):
        doc = await collection.find_one(query(actor["id"]))
        if not doc or not verify_password(payload.current_password, doc.get("password_hash", "")):
            raise HTTPException(400, "Contraseña actual incorrecta")
        if verify_password(payload.new_password, doc["password_hash"]):
            raise HTTPException(400, "La nueva contraseña debe ser distinta")
        await replace_password(doc, payload.new_password, False)
        await audit(actor, "CHANGE_PASSWORD", actor["id"])
        return {"ok": True, "message": "Contraseña cambiada. Inicia sesión de nuevo"}

    @router.post("/recovery/request")
    async def recover(payload: Recover, request: Request):
        message = {"message": "Si los datos coinciden, recibirás un enlace de recuperación"}
        source = request.client.host if request.client else "unknown"
        bucket = int(time.time()) // 900
        key = hashlib.sha256(f"{source}:{bucket}".encode()).hexdigest()
        limiter = await db.account_reset_limits.find_one_and_update({"_id": key},
            {"$inc": {"count": 1}, "$set": {"expires_at": datetime.now(timezone.utc) + timedelta(minutes=30)}},
            upsert=True, return_document=True)
        if limiter and limiter.get("count", 0) > 5:
            return message
        doc = await resolve_identifier(collection, payload.username)
        if not doc or not doc.get(active_field, True) or doc.get("email") != str(payload.email).lower():
            return message
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        await db.account_reset_tokens.insert_one({"token_hash": digest, "user_id": uid(doc),
            "version": int(doc.get(version_field, version_default)), "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30)})
        sent = await asyncio.to_thread(send_recovery_email, doc["email"], token, doc.get("username", payload.username))
        if not sent:
            await db.account_reset_tokens.delete_one({"token_hash": digest})
        return message

    @router.post("/recovery/confirm")
    async def reset(payload: ResetPassword):
        password_valid(payload.new_password)
        digest = hashlib.sha256(payload.token.encode()).hexdigest()
        record = await db.account_reset_tokens.find_one_and_delete({"token_hash": digest, "expires_at": {"$gt": datetime.now(timezone.utc)}})
        if not record:
            raise HTTPException(400, "El enlace ha caducado o ya se ha utilizado")
        doc = await collection.find_one(query(record["user_id"]))
        if not doc or not doc.get(active_field, True) or int(doc.get(version_field, version_default)) != record["version"]:
            raise HTTPException(400, "El enlace ya no es válido")
        await replace_password(doc, payload.new_password, False)
        return {"ok": True}

    return router


async def ensure_account_indexes(db):
    await db.users.create_index("username_key", unique=True, sparse=True)
    await db.account_reset_tokens.create_index("token_hash", unique=True)
    await db.account_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.account_reset_limits.create_index("expires_at", expireAfterSeconds=0)
