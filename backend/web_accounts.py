"""WEB-owned administrator accounts. No privilege is derived from a username."""
import os
import re
import uuid
from datetime import timedelta

from fastapi import Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pymongo.errors import DuplicateKeyError

from web_identity import (audit, denied, hash_password, now, rate_limit,
                          resolve_session, safe_user)


async def bootstrap_accounts(db):
    # Explicit operator secrets only. Existing credentials and roles are immutable here.
    for prefix, username, email, role in (
        ("WEB_ADMIN", "rafamaster", "info@oportuniia.com", "superadmin"),
        ("WEB_USER", "rafa.querol", "rafa.querol77@gmail.com", "user"),
    ):
        password = os.getenv(prefix + "_INITIAL_PASSWORD", "")
        if not password or await db.web_users.find_one({"$or": [{"username": username}, {"email": email}]}):
            continue
        stamp = now()
        try:
            await db.web_users.insert_one({"subject_id": str(uuid.uuid4()),
                "username": username, "name": username, "email": email,
                "recovery_email": "info@oportuniia.com", "role": role,
                "account_kind": "inversor", "active": True,
                "email_verified": True, "activation_method": "authorized_operator_secret",
                "password_hash": await hash_password(password), "session_version": 0,
                "must_change_password": True,
                "initial_password_expires_at": stamp + timedelta(hours=24), "created_at": stamp})
        except DuplicateKeyError:
            pass


async def administrator(request, db):
    user, session = await resolve_session(request, db)
    if user.get("role") != "superadmin": denied("administrator_required")
    if not user.get("mfa_enabled") or not session.get("mfa_verified"):
        denied("administrator_second_factor_required")
    return user


class NewAccount(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=1, max_length=180)
    email: EmailStr
    recovery_email: EmailStr
    role: str = "user"
    initial_password: str = Field(min_length=11, max_length=72)


class InitialPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    initial_password: str = Field(min_length=11, max_length=72)


def register_account_admin_routes(router, db):
    @router.get("/staff/accounts")
    async def accounts(request: Request):
        await administrator(request, db)
        rows = await db.web_users.find({}, {"_id": 0, "subject_id": 1, "name": 1,
            "username": 1, "email": 1, "recovery_email": 1, "role": 1,
            "active": 1, "must_change_password": 1}).to_list(500)
        return {"items": rows}

    @router.post("/staff/accounts", status_code=201)
    async def create(payload: NewAccount, request: Request):
        actor = await administrator(request, db)
        await rate_limit(db, request, "admin-create", actor["subject_id"])
        username = payload.username.strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,79}", username): denied("invalid_username", 422)
        if payload.role not in {"superadmin", "user"}: denied("invalid_role", 422)
        stamp = now()
        user = {"subject_id": str(uuid.uuid4()), "username": username,
            "name": payload.name.strip(), "email": str(payload.email).lower(),
            "recovery_email": str(payload.recovery_email).lower(), "role": payload.role,
            "account_kind": "inversor", "active": True, "email_verified": True,
            "activation_method": "authenticated_administrator", "created_at": stamp,
            "password_hash": await hash_password(payload.initial_password), "session_version": 0,
            "must_change_password": True, "initial_password_expires_at": stamp + timedelta(hours=24)}
        try: await db.web_users.insert_one(user)
        except DuplicateKeyError: denied("account_identifier_already_exists", 409)
        await audit(db, actor["subject_id"], "ADMIN_ACCOUNT_CREATED:" + user["subject_id"])
        return {"user": safe_user(user)}

    @router.post("/staff/accounts/{subject}/initial-password")
    async def reset(subject: str, payload: InitialPassword, request: Request):
        actor = await administrator(request, db)
        await rate_limit(db, request, "admin-reset", actor["subject_id"])
        if subject == actor["subject_id"]: denied("use_own_password_change", 409)
        result = await db.web_users.update_one({"subject_id": subject, "active": True}, {"$set": {
            "password_hash": await hash_password(payload.initial_password), "must_change_password": True,
            "initial_password_expires_at": now() + timedelta(hours=24)}, "$inc": {"session_version": 1}})
        if not result.matched_count: denied("account_not_found", 404)
        await db.web_sessions.update_many({"subject_id": subject}, {"$set": {"revoked": True}})
        await audit(db, actor["subject_id"], "ADMIN_PASSWORD_RESET:" + subject)
        return {"updated": True, "must_change_password": True}

    @router.delete("/staff/accounts/{subject}")
    async def remove(subject: str, request: Request):
        actor = await administrator(request, db)
        if subject == actor["subject_id"]: denied("cannot_delete_own_administrator", 409)
        result = await db.web_users.update_one({"subject_id": subject, "active": True}, {
            "$set": {"active": False, "disabled_at": now()}, "$inc": {"session_version": 1}})
        if not result.matched_count: denied("account_not_found", 404)
        await db.web_sessions.update_many({"subject_id": subject}, {"$set": {"revoked": True}})
        await audit(db, actor["subject_id"], "ADMIN_ACCOUNT_DISABLED:" + subject)
        return {"disabled": True, "records_preserved": True}
