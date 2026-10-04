"""Notification plans only: NO external delivery and NO private file disclosure.

Operational offer deadlines are transactional and separate from marketing
preferences. Optional Premium document reminders require current verified
subscription, explicit reminder consent and a declared next review date.
A trusted worker decides delivery and records provider receipts atomically.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone


def _aware(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("UTC-aware datetime required")
    return value.astimezone(timezone.utc)


def offer_deadline_notifications(offer: dict, *, now: datetime) -> list[dict]:
    """Produce deterministic reminder keys, never declare delivery."""
    current=_aware(now)
    if offer.get("state") != "AWAITING_DOCUMENTS" or offer.get("documents_verified_at"):
        return []
    deadline=_aware(offer["document_deadline"])
    if current >= deadline:
        return []
    start=_aware(offer["notice_delivered_at"])
    if deadline-start != timedelta(hours=72):
        raise ValueError("document deadline does not match three-day protocol")
    if current < start:
        return []
    remaining=deadline-current
    result=[]
    for hours in (48,24):
        threshold=deadline-timedelta(hours=hours)
        if threshold <= current < deadline:
            result.append({
                "key":f"offer:{offer['offer_id']}:deadline-{hours}h",
                "kind":"OFFER_DOCUMENT_DEADLINE",
                "offer_id":offer["offer_id"],
                "actor_id":offer["actor_id"],
                "threshold_hours":hours,
                "deadline":deadline,
                "transactional":True,
                "redact_attachment_details":True,
            })
    # Scheduler calls repeatedly: stable keys let delivery outbox deduplicate.
    return result


def premium_document_review_reminder(document: dict, subscription: dict,
                                     preferences: dict, *, now: datetime) -> dict | None:
    """No inferred expiry: owner must explicitly set the next review date."""
    current=_aware(now)
    if not preferences or preferences.get("document_reminders") is not True:
        return None
    actor=document.get("actor_id")
    if not actor or subscription.get("actor_id") != actor:
        return None
    if not (subscription.get("status") == "ACTIVE" and
            subscription.get("source_verified") is True and
            _aware(subscription["valid_from"]) <= current <
            _aware(subscription["expires_at"])):
        return None
    if document.get("status") != "AVAILABLE" or document.get("review_reminders") is not True:
        return None
    target=document.get("next_review_at")
    if not isinstance(target, datetime):
        return None
    review_at=_aware(target)
    # Premium notices are intentionally limited to a configurable 7-day window.
    if not review_at-timedelta(days=7) <= current <= review_at:
        return None
    file_id=document.get("file_id")
    if not file_id:
        return None
    return {
        "key":f"premium:{actor}:{file_id}:{review_at.isoformat()}:7d",
        "kind":"PREMIUM_DOCUMENT_REVIEW",
        "actor_id":actor,
        "file_id":file_id,
        "review_at":review_at,
        "transactional":False,
        # Only general reminder in emails; never attach or name identity files.
        "redact_attachment_details":True,
    }
