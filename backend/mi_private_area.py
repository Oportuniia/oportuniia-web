"""Private MI OPORTUNIIA account area. No legal case files or cross-user queries.

The caller MUST supply an authenticated WEB actor from the server-side session.
Personal documents remain in dedicated Mongo collections and a separate private
R2 bucket; no document bytes or cloud keys appear in list responses.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from mi_notification_center import cancel_pending_optional

ALLOWED_STATES = {"PENDING", "AVAILABLE", "QUARANTINED", "REJECTED"}


def safe_profile(actor: dict) -> dict:
    return {
        "actor_id": actor["actor_id"],
        "role": actor["role"],
        "validation_state": actor["validation_state"],
        "public_code": actor.get("public_code"),
        "email": actor["email"],
        "email_verified": bool(actor.get("email_verified")),
        "document_reminders": actor.get("document_reminders") is True,
    }


def safe_document(row: dict) -> dict:
    return {key: row.get(key) for key in (
        "file_id", "display_name", "mime", "size", "status", "created_at",
        "updated_at", "document_kind", "review_reminders", "next_review_at"
    )}


async def private_documents(db, actor: dict, *, limit: int = 50):
    if not actor or not actor.get("actor_id"):
        raise HTTPException(401, "Sesión necesaria")
    if not 1 <= limit <= 100:
        raise HTTPException(422, "Límite inválido")
    cursor = db.mi_user_files.find(
        {"actor_id": actor["actor_id"], "status": {"$in": sorted(ALLOWED_STATES)}},
        {"_id": 0, "storage_key": 0, "scan_details": 0},
    ).sort("created_at", -1).limit(limit)
    return [safe_document(row) async for row in cursor]


async def profile_update(db, actor: dict, *, preferred_name: str):
    if not actor or not actor.get("actor_id"):
        raise HTTPException(401, "Sesión necesaria")
    clean = preferred_name.strip()
    if not 1 <= len(clean) <= 100 or any(ord(c) < 32 for c in clean):
        raise HTTPException(422, "Nombre no válido")
    await db.mi_actors.update_one(
        {"actor_id": actor["actor_id"], "validation_state": {"$in": ["PENDING", "VERIFIED"]}},
        {"$set": {"preferred_name": clean, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"preferred_name": clean}


async def set_document_reminder_consent(db, actor: dict, *, enabled: bool):
    """Document-specific Premium opt-in; does not affect essential offer notices."""
    if not actor or not actor.get("actor_id"):
        raise HTTPException(401, "Sesión necesaria")
    if type(enabled) is not bool:
        raise HTTPException(422, "Consentimiento no válido")
    now = datetime.now(timezone.utc)
    result = await db.mi_actors.update_one(
        {"actor_id": actor["actor_id"], "validation_state": {"$in": ["PENDING", "VERIFIED"]}},
        {"$set": {"document_reminders": enabled, "document_reminders_updated_at": now,
                  "updated_at": now}},
    )
    if result.matched_count != 1:
        raise HTTPException(403, "Cuenta no disponible")
    if not enabled:
        await cancel_pending_optional(db,actor_id=actor["actor_id"],now=now)
    return {"document_reminders": enabled}


async def set_document_review_date(db, actor: dict, *, file_id: str,
                                   next_review_at: datetime | None):
    """Owner-scoped review schedule, NOT a legal document expiry date.

    Caller must verify current Premium entitlement before allowing date edits.
    Clearing a date also clears that file's reminder opt-in.
    """
    import re
    if not actor or not actor.get("actor_id"):
        raise HTTPException(401, "Sesión necesaria")
    if not isinstance(file_id, str) or not re.fullmatch(r"[0-9a-f]{32}", file_id):
        raise HTTPException(404, "Documento no encontrado")
    now = datetime.now(timezone.utc)
    if next_review_at is not None:
        if not isinstance(next_review_at, datetime) or next_review_at.tzinfo is None:
            raise HTTPException(422, "Fecha y zona horaria obligatorias")
        next_review_at = next_review_at.astimezone(timezone.utc)
        if next_review_at <= now or next_review_at > now + timedelta(days=730):
            raise HTTPException(422, "Selecciona una fecha futura dentro de los próximos dos años")
    update = {"$set": {
        "review_reminders": next_review_at is not None,
        "updated_at": now,
    }}
    if next_review_at is not None:
        update["$set"]["next_review_at"] = next_review_at
    else:
        update["$unset"] = {"next_review_at": ""}
    result = await db.mi_user_files.update_one(
        {"actor_id": actor["actor_id"], "file_id": file_id,
         "status": "AVAILABLE", "scan_verdict": "CLEAN"},
        update,
    )
    if result.matched_count != 1:
        raise HTTPException(404, "Documento privado verificado no encontrado")
    # Changing the date or removing it invalidates old queued reminder keys.
    await cancel_pending_optional(db,actor_id=actor["actor_id"],
                                  file_id=file_id,now=now)
    return {"file_id": file_id,
            "review_reminders": next_review_at is not None,
            "next_review_at": next_review_at}
