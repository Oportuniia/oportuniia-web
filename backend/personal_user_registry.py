"""MI OPORTUNIIA: sovereign user registry and permanent public codes.

Infrastructure service only. There are deliberately NO HTTP routes:
register/approve/import must be invoked exclusively by trusted WEB backend
after real identity, verification and administrative authorization are wired.
GHL subscribers and OPORTUNIIAPP collaborators are different populations.
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone

from pymongo import ASCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

ROLES = {"INVERSOR": "INV", "COLABORADOR": "COL"}
STATES = {"PENDING", "VERIFIED", "REJECTED", "SUSPENDED"}
CODE_PATTERN = re.compile(r"^OI-(INV|COL)-[0-9]{6,}$")


def normalize_email(value: str) -> str:
    email = (value or "").strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("invalid email")
    return email


def public_actor(actor: dict) -> dict:
    """No internal DB ID, documents, approval evidence, or migration metadata."""
    return {key: actor.get(key) for key in
            ("actor_id", "role", "validation_state", "public_code", "created_at")}


async def ensure_registry_indexes(db) -> None:
    """Run only in isolated sandbox until production migration is approved."""
    await db.mi_actors.create_index([("actor_id", ASCENDING)], unique=True)
    await db.mi_actors.create_index([("email", ASCENDING), ("role", ASCENDING)], unique=True)
    await db.mi_actors.create_index([("public_code", ASCENDING)],
                                    unique=True, partialFilterExpression={"public_code": {"$type": "string"}})
    await db.mi_code_sequences.create_index([("role", ASCENDING)], unique=True)
    await db.mi_approval_events.create_index([("actor_id", ASCENDING), ("at", ASCENDING)])


async def register_pending(db, *, email: str, role: str) -> dict:
    """Create a PENDING actor. Caller MUST ensure consent and anti-abuse limits."""
    if role not in ROLES:
        raise ValueError("unsupported WEB registry role")
    clean_email = normalize_email(email)
    now = datetime.now(timezone.utc)
    actor = {
        "actor_id": "mi_" + secrets.token_hex(16),
        "email": clean_email,
        "role": role,
        "validation_state": "PENDING",
        "public_code": None,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await db.mi_actors.insert_one(actor)
    except DuplicateKeyError as exc:
        raise ValueError("actor already registered for this role") from exc
    return public_actor(actor)


async def approve_and_assign(db, *, actor_id: str, reviewer_id: str) -> dict:
    """Trusted admin-only operation. Approval and code assignment are idempotent.

    Reserve code in actor in a single compare-and-set. A failed CAS may skip
    a sequence number, but can never assign it to a different actor.
    """
    if not re.fullmatch(r"mi_[0-9a-f]{32}", actor_id):
        raise ValueError("invalid actor ID")
    if not reviewer_id or len(reviewer_id.strip()) < 6:
        raise ValueError("reviewer identity required")
    actor = await db.mi_actors.find_one({"actor_id": actor_id})
    if not actor:
        raise ValueError("unknown actor")
    if actor["validation_state"] == "VERIFIED" and actor.get("public_code"):
        return public_actor(actor)
    if actor["validation_state"] != "PENDING" or actor.get("public_code"):
        raise PermissionError("actor cannot be approved from current state")
    prefix = ROLES.get(actor["role"])
    if not prefix:
        raise ValueError("invalid actor role")
    seq = await db.mi_code_sequences.find_one_and_update(
        {"role": actor["role"]}, {"$inc": {"next": 1}},
        upsert=True, return_document=ReturnDocument.AFTER,
    )
    code = f"OI-{prefix}-{seq['next']:06d}"
    now = datetime.now(timezone.utc)
    updated = await db.mi_actors.find_one_and_update(
        {"actor_id": actor_id, "validation_state": "PENDING", "public_code": None},
        {"$set": {"validation_state": "VERIFIED", "public_code": code, "updated_at": now,
                  "reviewed_by": reviewer_id}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        # Another authorized worker won the CAS; never overwrite their result.
        winner = await db.mi_actors.find_one({"actor_id": actor_id})
        if winner and winner["validation_state"] == "VERIFIED" and winner.get("public_code"):
            return public_actor(winner)
        raise RuntimeError("concurrent approval or changed state; review required")
    await db.mi_approval_events.insert_one(
        {"actor_id": actor_id, "reviewer_id": reviewer_id,
         "action": "VERIFIED_CODE_ASSIGNED", "at": now, "code": code}
    )
    return public_actor(updated)


def validate_legacy_code(code: str, expected_role: str) -> str:
    """Do NOT import legacy codes unless their real GHL scheme is confirmed."""
    if expected_role not in ROLES or not isinstance(code, str):
        raise ValueError("unknown legacy role/code")
    if not CODE_PATTERN.fullmatch(code) or not code.startswith(f"OI-{ROLES[expected_role]}-"):
        raise ValueError("legacy code scheme not confirmed: mapping required")
    return code
