"""Provider-neutral subscription bridge for MI OPORTUNIIA.

Trusted billing middleware calls this bridge with a signed JSON event; users
CANNOT self-grant Premium. Customer->WEB actor mappings must first be verified
by operations and persisted separately in mi_subscription_links. No provider
or paid plan is presumed until configured and tested.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError


def _configured_secret() -> bytes:
    if os.getenv("MI_BILLING_BRIDGE_ENABLED") != "1":
        raise HTTPException(503, "Sincronización de suscripciones desactivada")
    secret = os.getenv("MI_BILLING_BRIDGE_SECRET", "")
    if len(secret) < 48:
        raise HTTPException(503, "Firma de suscripciones no configurada")
    return secret.encode("utf-8")


def verify_signed_event(raw: bytes, *, timestamp: str, signature: str,
                        now: datetime | None = None) -> dict:
    """Reject replays, stale events and invalid signatures, before parsing."""
    secret = _configured_secret()
    if len(raw) > 8192 or not timestamp.isdigit():
        raise HTTPException(400, "Evento de suscripción inválido")
    moment = now or datetime.now(timezone.utc)
    if abs(moment.timestamp() - int(timestamp)) > 300:
        raise HTTPException(401, "Firma caducada")
    expected = hmac.new(secret, timestamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
    if not re.fullmatch(r"[a-f0-9]{64}", signature) or not hmac.compare_digest(signature, expected):
        raise HTTPException(401, "Firma de suscripción no válida")
    try:
        event = json.loads(raw)
    except (UnicodeError, ValueError):
        raise HTTPException(400, "Evento JSON inválido")
    if not isinstance(event, dict):
        raise HTTPException(400, "Evento inválido")
    return event


def _timestamp(value: str) -> datetime:
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError("Timezone required")
        return date.astimezone(timezone.utc)
    except (AttributeError, ValueError) as exc:
        raise HTTPException(422, "Fecha de suscripción inválida") from exc


async def apply_signed_event(db, event: dict) -> dict:
    # A billing middleware is trusted only to report subscription state; it
    # cannot decide the WEB actor or override independently verified identity.
    if event.get("schema") != "mi-billing-v1" or event.get("plan") != "PREMIUM":
        raise HTTPException(422, "Contrato de suscripción no soportado")
    event_id = event.get("event_id")
    customer = event.get("customer_id")
    status = event.get("status")
    if not isinstance(event_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,120}", event_id):
        raise HTTPException(422, "Identificador de evento inválido")
    if not isinstance(customer, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,120}", customer):
        raise HTTPException(422, "Identificador de cliente inválido")
    if status not in ("ACTIVE", "CANCELLED", "EXPIRED", "PAST_DUE"):
        raise HTTPException(422, "Estado no autorizado")
    effective_at = _timestamp(event.get("effective_at"))
    expires_at = _timestamp(event.get("expires_at"))
    if expires_at <= effective_at:
        raise HTTPException(422, "Periodo de suscripción inválido")
    mapping = await db.mi_subscription_links.find_one(
        {"provider_customer_id": customer, "verified": True},
    )
    if not mapping:
        # Never create user mappings or grant Premium from a webhook.
        raise HTTPException(409, "Vinculación de facturación sin verificar")
    try:
        await db.mi_billing_events.insert_one({
            "_id": event_id, "customer_hash": hashlib.sha256(customer.encode()).hexdigest(),
            "received_at": datetime.now(timezone.utc),
        })
    except DuplicateKeyError:
        return {"status": "already_processed"}
    actor_id = mapping["actor_id"]
    # Only apply newer effective state, preventing delayed events from
    # resurrecting a cancelled account.
    updated = await db.mi_premium_entitlements.update_one(
        {"actor_id": actor_id, "$or": [
            {"event_at": {"$lt": effective_at}}, {"event_at": {"$exists": False}},
        ]},
        {"$set": {
            "actor_id": actor_id, "status": status, "valid_from": effective_at,
            "expires_at": expires_at, "event_at": effective_at,
            "source_verified": True, "source": "signed_billing_bridge",
        }},
        upsert=False,
    )
    if not updated.matched_count:
        existing = await db.mi_premium_entitlements.find_one({"actor_id": actor_id})
        if not existing:
            # This is a verified first event, linked by operations. Start from
            # empty row without letting a race overwrite a newer event.
            try:
                await db.mi_premium_entitlements.insert_one({
                    "actor_id": actor_id, "status": status, "valid_from": effective_at,
                    "expires_at": expires_at, "event_at": effective_at,
                    "source_verified": True, "source": "signed_billing_bridge",
                })
            except DuplicateKeyError:
                return {"status": "concurrent_event_review_required"}
    return {"status": "recorded"}


async def ensure_subscription_indexes(db):
    await db.mi_subscription_links.create_index("provider_customer_id", unique=True)
    await db.mi_premium_entitlements.create_index("actor_id", unique=True)
