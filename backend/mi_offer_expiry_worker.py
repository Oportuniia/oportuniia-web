"""Atomic deadline expiry for independently approved and notified WEB offers.

A private scheduler (n8n or a worker) may call expire_due_once when the
actual offer/notice/document systems have been commissioned. No public API
and no direct edits to sovereign PRESENTACIÓN publication state. Expiry
creates an action-pending marker for staff/CRM synchronization.

Each offer embeds a minimal expiry event and version increase in the SAME
atomic Mongo update; an upload only counts if the approved required
document packet has been verified server-side and recorded first.
"""
from __future__ import annotations
from datetime import datetime, timezone


async def expire_due_once(db, *, now: datetime, limit: int = 50) -> list[str]:
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("aware timestamp required")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("invalid worker limit")
    at=now.astimezone(timezone.utc)
    cursor=db.mi_offers.find(
        {"state":"AWAITING_DOCUMENTS", "document_deadline":{"$lt":at},
         "documents_verified_at":{"$exists":False}},
        {"_id":0,"offer_id":1,"version":1},
    ).sort("document_deadline",1).limit(limit)
    candidates=[row async for row in cursor]
    expired=[]
    for row in candidates:
        # One atomic CAS prevents competing workers from expiring twice, or
        # overriding a successfully verified document handoff.
        updated=await db.mi_offers.find_one_and_update(
            {"offer_id":row["offer_id"],"version":row["version"],
             "state":"AWAITING_DOCUMENTS","document_deadline":{"$lt":at},
             "documents_verified_at":{"$exists":False}},
            {"$set":{"state":"EXPIRED","expired_at":at,
                     "operations_review_pending":True},
             "$inc":{"version":1},
             "$push":{"events":{"kind":"DOCS_DEADLINE_EXPIRED",
                                "at":at,"previous_version":row["version"]}}},
        )
        if updated:
            expired.append(row["offer_id"])
    return expired
