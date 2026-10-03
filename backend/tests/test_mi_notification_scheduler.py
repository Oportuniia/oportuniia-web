from datetime import datetime, timedelta, timezone

import pytest
from pymongo.errors import DuplicateKeyError

from mi_notification_scheduler import (
    schedule_notifications, schedule_offer_reminders, schedule_premium_reviews,
)

NOW = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)
ACTOR = "mi_owner"


class Cursor:
    def __init__(self, rows):
        self.rows = rows
    def sort(self, *_args):
        return self
    def limit(self, n):
        self.rows = self.rows[:n]
        return self
    def __aiter__(self):
        self._rows = iter(self.rows)
        return self
    async def __anext__(self):
        try:
            return next(self._rows)
        except StopIteration:
            raise StopAsyncIteration


class Find:
    def __init__(self, rows):
        self.rows = rows
    def find(self, query, projection):
        assert "_id" in projection and projection["_id"] == 0
        if "document_deadline" in query:
            assert query["documents_verified_at"] == {"$exists": False}
            assert query["notice_delivery_ref"] == {"$exists": True}
        if "next_review_at" in query:
            assert query["scan_verdict"] == "CLEAN"
            assert query["review_reminders"] is True
        return Cursor(self.rows)
    async def find_one(self, query, _projection=None):
        for row in self.rows:
            if all(row.get(k) == v for k, v in query.items()
                   if not isinstance(v, dict)):
                return row
        return None


class Outbox:
    def __init__(self):
        self.saved = {}
    async def insert_one(self, item):
        if item["key"] in self.saved:
            raise DuplicateKeyError("duplicate notification")
        self.saved[item["key"]] = item.copy()


def database(offers=(), documents=(), actors=(), entitlements=()):
    return type("DB", (), {
        "mi_offers": Find(list(offers)),
        "mi_user_files": Find(list(documents)),
        "mi_actors": Find(list(actors)),
        "mi_premium_entitlements": Find(list(entitlements)),
        "mi_notification_outbox": Outbox(),
    })()


def approved_offer():
    return {
        "offer_id": "o1", "actor_id": ACTOR, "state": "AWAITING_DOCUMENTS",
        "notice_delivery_ref": "proved-notice",
        "notice_delivered_at": NOW-timedelta(hours=24),
        "document_deadline": NOW+timedelta(hours=48),
    }


def test_record():
    return {
        "actor_id": ACTOR, "file_id": "f"*32, "status": "AVAILABLE",
        "scan_verdict": "CLEAN", "review_reminders": True,
        "next_review_at": NOW+timedelta(days=4),
    }


def premium_actor():
    return {"actor_id": ACTOR, "email_verified": True,
            "validation_state": "VERIFIED", "document_reminders": True}


def premium_subscription():
    return {"actor_id": ACTOR, "status": "ACTIVE",
            "source_verified": True,
            "valid_from": NOW-timedelta(days=1),
            "expires_at": NOW+timedelta(days=30)}


@pytest.mark.asyncio
async def test_combined_scheduler_deduplicates_across_repeated_runs():
    db = database(offers=[approved_offer()], documents=[test_record()],
                  actors=[premium_actor()], entitlements=[premium_subscription()])
    first = await schedule_notifications(db, now=NOW)
    assert first["offer"]["queued"] == 1
    assert first["premium"]["queued"] == 1
    second = await schedule_notifications(db, now=NOW)
    assert second["offer"]["queued"] == 0
    assert second["premium"]["queued"] == 0
    assert len(db.mi_notification_outbox.saved) == 2
    assert all("email" not in row and "display_name" not in row
               for row in db.mi_notification_outbox.saved.values())


@pytest.mark.asyncio
async def test_missing_premium_consent_or_entitlement_creates_nothing():
    db = database(documents=[test_record()],
                  actors=[{**premium_actor(), "document_reminders": False}],
                  entitlements=[premium_subscription()])
    result = await schedule_premium_reviews(db, now=NOW)
    assert result["queued"] == 0
    db = database(documents=[test_record()], actors=[premium_actor()],
                  entitlements=[{**premium_subscription(), "source_verified": False}])
    result = await schedule_premium_reviews(db, now=NOW)
    assert result["queued"] == 0


@pytest.mark.asyncio
async def test_invalid_and_uncommunicated_offers_are_skipped():
    bad = {**approved_offer(), "notice_delivery_ref": None}
    result = await schedule_offer_reminders(database(offers=[bad]), now=NOW)
    assert result["queued"] == 0


@pytest.mark.asyncio
async def test_worker_rejects_unbounded_batches_and_naive_dates():
    with pytest.raises(ValueError):
        await schedule_premium_reviews(database(), now=NOW, limit=9999)
    with pytest.raises(ValueError):
        await schedule_offer_reminders(database(), now=NOW.replace(tzinfo=None))
