"""TOTP second factor. Encrypted secrets, replay prevention, one-use recovery.
MFA does not replace identity review or operation authorization.
"""
import hmac
import os
import secrets
from datetime import timedelta

import pyotp
import qrcode
import qrcode.image.svg
from cryptography.fernet import Fernet
from pymongo import ReturnDocument
from pydantic import BaseModel, ConfigDict, Field
from fastapi import Request, Response

from web_identity import now, digest, denied, require_origin, resolve_session, rate_limit, audit


def cipher():
    try: return Fernet(os.environ["WEB_FACTOR_ENCRYPTION_KEY"].encode())
    except Exception: denied("second_factor_not_configured", 503)


def code_counter(secret, code):
    if len(code) != 6 or not code.isdigit(): return None
    current = int(now().timestamp()) // 30
    totp = pyotp.TOTP(secret)
    for counter in (current, current-1, current+1):
        if hmac.compare_digest(totp.at(counter*30), code): return counter
    return None


async def challenge(db, user):
    raw = secrets.token_urlsafe(32)
    await db.web_login_challenges.insert_one({"_id": digest(raw), "subject_id": user["subject_id"], "version": user.get("session_version", 0),
        "expires_at": now()+timedelta(minutes=5), "attempts": 0, "used": False})
    return {"second_factor_required": True, "challenge": raw}


async def verify_factor(db, user, code):
    try: secret = cipher().decrypt(user["mfa_secret"].encode()).decode()
    except Exception: denied("second_factor_unavailable", 503)
    counter = code_counter(secret, code)
    if counter is not None:
        result = await db.web_users.update_one({"subject_id": user["subject_id"], "session_version": user.get("session_version", 0), "mfa_last_counter": {"$lt": counter}}, {"$set": {"mfa_last_counter": counter}})
        return bool(result.matched_count)
    recovery_hash = digest(code)
    result = await db.web_users.update_one({"subject_id": user["subject_id"], "session_version": user.get("session_version", 0), "mfa_recovery_hashes": recovery_hash}, {"$pull": {"mfa_recovery_hashes": recovery_hash}})
    return bool(result.matched_count)


class Code(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=6, max_length=80)


class Complete(Code):
    challenge: str = Field(min_length=32, max_length=200)


def register_secondfactor_routes(router, db):
    @router.post("/account/second-factor/enroll")
    async def enroll(request: Request):
        user, session = await resolve_session(request, db)
        if user.get("mfa_enabled"): denied("second_factor_already_enabled", 409)
        if session["created_at"] < now()-timedelta(minutes=5): denied("fresh_login_required", 401)
        secret = pyotp.random_base32()
        encrypted = cipher().encrypt(secret.encode()).decode()
        await db.web_users.update_one({"subject_id": user["subject_id"], "mfa_enabled": {"$ne": True}}, {"$set": {"mfa_pending": encrypted, "mfa_pending_until": now()+timedelta(minutes=10)}})
        uri = pyotp.TOTP(secret).provisioning_uri(name=user["email"], issuer_name="OPORTUNIIA")
        qr = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathFillImage, border=4)
        return {"secret": secret, "uri": uri, "qr_svg": qr.to_string(encoding="unicode")}

    @router.post("/account/second-factor/confirm")
    async def confirm(payload: Code, request: Request):
        user, _ = await resolve_session(request, db)
        await rate_limit(db, request, "mfa-enroll", user["email"])
        if user.get("mfa_enabled") or not user.get("mfa_pending_until") or user["mfa_pending_until"] <= now(): denied("invalid_or_expired_link", 400)
        secret = cipher().decrypt(user["mfa_pending"].encode()).decode()
        counter = code_counter(secret, payload.code)
        if counter is None: denied("invalid_second_factor", 401)
        recovery = [secrets.token_hex(12) for _ in range(8)]
        updated = await db.web_users.update_one({"subject_id": user["subject_id"], "mfa_pending": user["mfa_pending"], "mfa_enabled": {"$ne": True}},
            {"$set": {"mfa_enabled": True, "mfa_secret": user["mfa_pending"], "mfa_last_counter": counter, "mfa_recovery_hashes": [digest(c) for c in recovery]},
             "$unset": {"mfa_pending": "", "mfa_pending_until": ""}, "$inc": {"session_version": 1}})
        if not updated.matched_count: denied("factor_enrollment_conflict", 409)
        await db.web_sessions.update_many({"subject_id": user["subject_id"]}, {"$set": {"revoked": True}})
        await audit(db, user["subject_id"], "MFA_ENABLED_SESSIONS_REVOKED")
        return {"enabled": True, "recovery_codes": recovery, "sign_in_required": True}

    @router.post("/account/second-factor/complete")
    async def complete(payload: Complete, request: Request, response: Response):
        from web_identity import issue_session, safe_user
        require_origin(request)
        await rate_limit(db, request, "mfa-login")
        row = await db.web_login_challenges.find_one_and_update({"_id": digest(payload.challenge), "used": False, "expires_at": {"$gt": now()}, "attempts": {"$lt": 5}}, {"$inc": {"attempts": 1}}, return_document=ReturnDocument.AFTER)
        if not row: denied("invalid_or_expired_link", 401)
        user = await db.web_users.find_one({"subject_id": row["subject_id"], "active": True, "email_verified": True, "mfa_enabled": True, "session_version": row["version"]})
        if not user or not await verify_factor(db, user, payload.code): denied("invalid_second_factor", 401)
        result = await db.web_login_challenges.update_one({"_id": row["_id"], "used": False}, {"$set": {"used": True}})
        if not result.modified_count: denied("invalid_or_expired_link", 401)
        await issue_session(db, user, response, mfa_verified=True)
        return {"user": safe_user(user)}

