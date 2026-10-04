"""Distributed Mongo rate limiter for MI OPORTUNIIA authentication endpoints.

Raw emails and IP addresses never enter limiter collection. Intentionally
rejects missing secret or database errors rather than bypassing protections.
"""
import hashlib
import hmac
import os
import time
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from pymongo import ReturnDocument


def _key(action, subject):
    secret = os.getenv("MI_RATE_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(503, "Protección antiabuso no configurada")
    return hmac.new(secret.encode(), (action + ":" + subject).encode(),
                    hashlib.sha256).hexdigest()


async def throttle(db, *, action, subject, limit, seconds):
    if not subject:
        raise HTTPException(403, "Identidad de red no disponible")
    now = datetime.now(timezone.utc)
    bucket = int(time.time() // seconds)
    digest = _key(action, subject)
    key = f"{action}:{digest}:{bucket}"
    try:
        row = await db.mi_rate_limits.find_one_and_update(
            {"_id": key},
            {"$inc": {"count": 1},
             "$setOnInsert": {"expires_at": now + timedelta(seconds=seconds * 2)}},
            upsert=True, return_document=ReturnDocument.AFTER,
        )
    except Exception as exc:
        # Fail closed if the counter cannot be persisted.
        raise HTTPException(503, "Protección antiabuso temporalmente no disponible") from exc
    if row["count"] > limit:
        raise HTTPException(429, "Demasiados intentos. Inténtalo más tarde")


async def auth_throttle(db, request, *, action, email="", per_ip=10, per_email=5):
    # Trusted deployment network configuration must provide accurate request.client.
    ip = request.client.host if request.client else ""
    await throttle(db, action=action + ":ip", subject=ip, limit=per_ip, seconds=900)
    if email:
        await throttle(db, action=action + ":email", subject=email.lower(),
                       limit=per_email, seconds=900)


async def ensure_rate_indexes(db):
    await db.mi_rate_limits.create_index("expires_at", expireAfterSeconds=0)
