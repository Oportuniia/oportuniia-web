"""Private MI OPORTUNIIA account area. No legal case files or cross-user queries.

The caller MUST supply an authenticated WEB actor from the server-side session.
Personal documents remain in dedicated Mongo collections and a separate private
R2 bucket; no document bytes or cloud keys appear in list responses.
"""
from __future__ import annotations
from datetime import datetime, timezone
from fastapi import HTTPException

ALLOWED_STATES = {"PENDING", "AVAILABLE", "QUARANTINED", "REJECTED"}


def safe_profile(actor: dict) -> dict:
    return {
        "actor_id": actor["actor_id"],
        "role": actor["role"],
        "validation_state": actor["validation_state"],
        "public_code": actor.get("public_code"),
        "email": actor["email"],
        "email_verified": bool(actor.get("email_verified")),
    }


def safe_document(row: dict) -> dict:
    return {key: row.get(key) for key in (
        "file_id", "display_name", "mime", "size", "status", "created_at",
        "updated_at", "document_kind"
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
