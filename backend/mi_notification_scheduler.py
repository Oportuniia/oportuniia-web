"""Sandbox notification scheduler: plan operational and Premium notices.

A trusted cron/n8n runner calls this only against WEB's private database. No
HTTP endpoint and no SMTP side effects. Every proposed notification passes
through the privacy-minimal unique-key outbox; recipient and live eligibility
are independently resolved immediately before external delivery.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mi_document_notifications import (
    offer_deadline_notifications,
    premium_document_review_reminder,
)
from mi_notification_outbox import enqueue


def _now(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("timezone-aware scheduling timestamp required")
    return value.astimezone(timezone.utc)


def _limit(value):
    if type(value) is not int or not 1 <= value <= 100:
        raise ValueError("bounded worker batch required")
    return value


async def schedule_offer_reminders(db, *, now: datetime, limit: int = 50) -> dict:
    """Only preapproved and actually notified offers may generate notices."""
    at = _now(now)
    count = _limit(limit)
    cursor = db.mi_offers.find(
        {
            "state": "AWAITING_DOCUMENTS",
            "notice_delivery_ref": {"$exists": True},
            "documents_verified_at": {"$exists": False},
            "document_deadline": {"$gt": at, "$lte": at + timedelta(hours=48)},
        },
        {"_id": 0, "offer_id": 1, "actor_id": 1, "state": 1,
         "document_deadline": 1, "notice_delivered_at": 1,
         "notice_delivery_ref": 1, "documents_verified_at": 1},
    ).sort("document_deadline", 1).limit(count)
    eligible = queued = 0
    async for offer in cursor:
        # A corrupted/migrated record must not stop the other notifications.
        try:
            planned = offer_deadline_notifications(offer, now=at)
        except (KeyError, TypeError, ValueError):
            continue
        for notice in planned:
            eligible += 1
            if await enqueue(db, notice, now=at):
                queued += 1
    return {"kind": "OFFER_DOCUMENT_DEADLINE",
            "eligible": eligible, "queued": queued}


async def schedule_premium_reviews(db, *, now: datetime, limit: int = 50) -> dict:
    """Use an explicitly saved review date, verified Premium and current opt-in.

    Never scan document bytes, infer expiration or expose private filenames in
    the outbox. Invalid docs are skipped rather than triggering broad scans.
    """
    at = _now(now)
    count = _limit(limit)
    cursor = db.mi_user_files.find(
        {
            "status": "AVAILABLE",
            "scan_verdict": "CLEAN",
            "review_reminders": True,
            "next_review_at": {"$gte": at, "$lte": at + timedelta(days=7)},
        },
        {"_id": 0, "actor_id": 1, "file_id": 1, "status": 1,
         "review_reminders": 1, "next_review_at": 1},
    ).sort("next_review_at", 1).limit(count)
    eligible = queued = 0
    actors = {}
    entitlements = {}
    async for document in cursor:
        actor_id = document.get("actor_id")
        if not isinstance(actor_id, str) or not actor_id.startswith("mi_"):
            continue
        if actor_id not in actors:
            actors[actor_id] = await db.mi_actors.find_one(
                {"actor_id": actor_id, "email_verified": True,
                 "validation_state": "VERIFIED", "document_reminders": True},
                {"_id": 0, "actor_id": 1, "document_reminders": 1},
            )
        if not actors[actor_id]:
            continue
        if actor_id not in entitlements:
            entitlements[actor_id] = await db.mi_premium_entitlements.find_one(
                {"actor_id": actor_id, "status": "ACTIVE",
                 "source_verified": True,
                 "valid_from": {"$lte": at}, "expires_at": {"$gt": at}},
                {"_id": 0, "actor_id": 1, "status": 1, "source_verified": 1,
                 "valid_from": 1, "expires_at": 1},
            )
        entitlement = entitlements[actor_id]
        if not entitlement:
            continue
        try:
            notice = premium_document_review_reminder(
                document, entitlement, actors[actor_id], now=at,
            )
        except (ValueError, KeyError, TypeError):
            continue
        if notice:
            eligible += 1
            if await enqueue(db, notice, now=at):
                queued += 1
    return {"kind": "PREMIUM_DOCUMENT_REVIEW",
            "eligible": eligible, "queued": queued}


async def schedule_notifications(db, *, now: datetime, limit: int = 50) -> dict:
    """One iteration; caller owns configuration, pacing, and observability."""
    return {
        "offer": await schedule_offer_reminders(db, now=now, limit=limit),
        "premium": await schedule_premium_reviews(db, now=now, limit=limit),
    }
