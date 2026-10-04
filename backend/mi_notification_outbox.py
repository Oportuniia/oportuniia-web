"""Private notification outbox for MI OPORTUNIIA.

No network delivery here. A trusted worker can queue deterministic notices and
reserve them atomically. Provider delivery receipts MUST be saved by a separate
authenticated transport adapter. Ambiguous timeouts require reconciliation,
not blind retry, to avoid duplicated or falsely recorded notifications.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

KINDS={"OFFER_DOCUMENT_DEADLINE", "PREMIUM_DOCUMENT_REVIEW", "PREMIUM_PAYROLL_REMINDER"}
LEASE=timedelta(minutes=10)


def _utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    return value.astimezone(timezone.utc)


async def ensure_outbox_indexes(db):
    await db.mi_notification_outbox.create_index("key", unique=True)
    await db.mi_notification_outbox.create_index([("state", 1), ("created_at", 1)])


async def enqueue(db, planned: dict, *, now: datetime) -> bool:
    """Idempotently store no-content notice; no email or file metadata."""
    at=_utc(now)
    kind=planned.get("kind")
    key=planned.get("key")
    actor_id=planned.get("actor_id")
    if kind not in KINDS or not isinstance(key, str) or not 8<=len(key)<=220:
        raise ValueError("invalid notification kind or key")
    if not isinstance(actor_id, str) or not actor_id.startswith("mi_"):
        raise ValueError("invalid actor")
    if planned.get("redact_attachment_details") is not True:
        raise ValueError("privacy flag required")
    # Only allowlist safe fields; no email, identity numbers or document name.
    doc={"key":key, "actor_id":actor_id, "kind":kind,
         "state":"PENDING", "created_at":at, "attempts":0}
    if kind=="OFFER_DOCUMENT_DEADLINE":
        if planned.get("threshold_hours") not in (24,48):
            raise ValueError("unsupported notification schedule")
        doc["offer_id"]=planned["offer_id"]
        doc["deadline"]=_utc(planned["deadline"])
        doc["threshold_hours"]=planned["threshold_hours"]
    elif kind=="PREMIUM_DOCUMENT_REVIEW":
        doc["file_id"]=planned["file_id"]
        doc["review_at"]=_utc(planned["review_at"])
    else:
        doc["signal_id"]=planned["signal_id"]
        doc["calendar_version"]=planned["calendar_version"]
        doc["event_at"]=_utc(planned["event_at"])
        doc["notify_at"]=_utc(planned["notify_at"])
    try:
        await db.mi_notification_outbox.insert_one(doc)
        return True
    except DuplicateKeyError:
        return False


async def claim_one(db, *, worker_id: str, now: datetime):
    """Single-worker claim; no reuse of an ambiguous SMTP attempt."""
    if not worker_id or len(worker_id)>80:
        raise ValueError("worker identity required")
    at=_utc(now)
    return await db.mi_notification_outbox.find_one_and_update(
        {"state":"PENDING"},
        {"$set":{"state":"CLAIMED", "worker_id":worker_id,
                 "claimed_at":at, "lease_expires_at":at+LEASE},
         "$inc":{"attempts":1}},
        sort=[("created_at",1)], return_document=ReturnDocument.AFTER,
    )


async def mark_sent(db, *, key: str, worker_id: str, receipt: str, now: datetime):
    if not receipt or len(receipt)>180:
        raise ValueError("verified provider receipt required")
    at=_utc(now)
    result=await db.mi_notification_outbox.update_one(
        {"key":key,"state":"CLAIMED","worker_id":worker_id,
         "lease_expires_at":{"$gte":at}},
        {"$set":{"state":"SENT","provider_receipt":receipt,"sent_at":at},
         "$unset":{"worker_id":"","lease_expires_at":""}},
    )
    return result.modified_count==1


async def mark_uncertain(db, *, key: str, worker_id: str, now: datetime):
    """Transport timeout: reconcile by provider receipt, do not auto-resend."""
    at=_utc(now)
    result=await db.mi_notification_outbox.update_one(
        {"key":key,"state":"CLAIMED","worker_id":worker_id},
        {"$set":{"state":"RECONCILE","uncertain_at":at},
         "$unset":{"worker_id":"","lease_expires_at":""}},
    )
    return result.modified_count==1


async def cancel_pending(db, *, key: str, reason: str, now: datetime):
    """Cancel if documents were received, Premium revoked or user opted out."""
    if reason not in ("DOCUMENTS_RECEIVED","OFFER_EXPIRED",
                      "PREMIUM_EXPIRED","OPT_OUT","DOCUMENT_UPDATED"):
        raise ValueError("invalid cancellation reason")
    at=_utc(now)
    result=await db.mi_notification_outbox.update_one(
        {"key":key,"state":"PENDING"},
        {"$set":{"state":"CANCELLED","cancel_reason":reason,"cancelled_at":at}},
    )
    return result.modified_count==1


async def cancel_claimed(db, *, key: str, worker_id: str, reason: str,
                         now: datetime):
    """Withdraw a claimed notice if live eligibility is revoked pre-send."""
    if reason not in ("NOT_ELIGIBLE", "DOCUMENTS_RECEIVED", "OPT_OUT",
                      "PREMIUM_EXPIRED", "DOCUMENT_UPDATED"):
        raise ValueError("invalid claimed cancellation reason")
    at=_utc(now)
    result=await db.mi_notification_outbox.update_one(
        {"key":key,"state":"CLAIMED","worker_id":worker_id,
         "lease_expires_at":{"$gte":at}},
        {"$set":{"state":"CANCELLED","cancel_reason":reason,
                 "cancelled_at":at},
         "$unset":{"worker_id":"","lease_expires_at":""}},
    )
    return result.modified_count==1
