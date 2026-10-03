from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
from mi_private_area import safe_profile, safe_document, private_documents, profile_update, set_document_reminder_consent, set_document_review_date


def test_profile_exposes_only_approved_fields():
    actor = {"actor_id": "mi_abc", "role": "INVERSOR",
             "validation_state": "VERIFIED", "public_code": "OI-INV-000001",
             "email": "person@example.org", "email_verified": True,
             "password_hash": "secret", "reviewed_by": "private"}
    profile = safe_profile(actor)
    assert profile["public_code"] == "OI-INV-000001"
    assert "password_hash" not in profile
    assert "reviewed_by" not in profile


def test_document_projection_never_exposes_storage_secrets():
    row = {"file_id": "a", "display_name": "file.pdf", "mime": "application/pdf",
           "size": 123, "status": "AVAILABLE",
           "storage_key": "personal/private/secret", "scan_details": "x",
           "actor_id": "private"}
    result = safe_document(row)
    assert result["file_id"] == "a"
    assert "storage_key" not in result
    assert "actor_id" not in result
    assert "scan_details" not in result


@pytest.mark.asyncio
async def test_private_documents_requires_login():
    with pytest.raises(HTTPException) as exc:
        await private_documents(None, None)
    assert exc.value.status_code == 401


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
    def sort(self, *args):
        return self
    def limit(self, n):
        self.rows = self.rows[:n]
        return self
    def __aiter__(self):
        self.iterator = iter(self.rows)
        return self
    async def __anext__(self):
        try:
            return next(self.iterator)
        except StopIteration:
            raise StopAsyncIteration


class FakeFiles:
    def find(self, query, projection):
        assert query["actor_id"] == "mi_actor_owner"
        assert projection["storage_key"] == 0
        return FakeCursor([{"file_id": "own", "status": "AVAILABLE",
                            "storage_key": "private"}])


@pytest.mark.asyncio
async def test_document_lookup_is_actor_scoped():
    db = type("DB", (), {"mi_user_files": FakeFiles()})()
    result = await private_documents(db, {"actor_id": "mi_actor_owner"})
    assert result[0]["file_id"] == "own"
    assert "storage_key" not in result[0]


@pytest.mark.asyncio
async def test_invalid_profile_update_never_reaches_db():
    with pytest.raises(HTTPException) as exc:
        await profile_update(None, {"actor_id": "mi_actor_owner"}, preferred_name="  ")
    assert exc.value.status_code == 422


class OptionalQueue:
    def __init__(self):
        self.calls=[]
    async def update_many(self,query,update):
        self.calls.append((query,update))
        return type("Result",(),{"modified_count":0})()


class PreferenceActors:
    async def update_one(self, query, update):
        assert query["actor_id"] == "mi_owner"
        assert update["$set"]["document_reminders"] is True
        return type("Result", (), {"matched_count": 1})()


@pytest.mark.asyncio
async def test_optional_reminder_consent_changes_only_current_actor():
    db = type("DB", (), {"mi_actors": PreferenceActors(),
                           "mi_notification_outbox": OptionalQueue()})()
    result = await set_document_reminder_consent(
        db, {"actor_id": "mi_owner"}, enabled=True)
    assert result == {"document_reminders": True}


@pytest.mark.asyncio
async def test_reminder_consent_cannot_be_set_anonymously():
    with pytest.raises(HTTPException) as exc:
        await set_document_reminder_consent(None, None, enabled=True)
    assert exc.value.status_code == 401



class FakeReviewFiles:
    def __init__(self, found=True):
        self.found = found
        self.query = None
        self.update = None
    async def update_one(self, query, update):
        self.query, self.update = query, update
        return type("Result", (), {"matched_count": int(self.found)})()


@pytest.mark.asyncio
async def test_review_date_can_only_modify_owners_clean_verified_file():
    files=FakeReviewFiles()
    db=type("DB", (), {"mi_user_files": files,
                           "mi_notification_outbox": OptionalQueue()})()
    date=datetime.now(timezone.utc)+timedelta(days=30)
    result=await set_document_review_date(
        db, {"actor_id":"mi_owner"}, file_id="a"*32,
        next_review_at=date,
    )
    assert files.query == {"actor_id":"mi_owner","file_id":"a"*32,
                           "status":"AVAILABLE","scan_verdict":"CLEAN"}
    assert files.update["$set"]["review_reminders"] is True
    assert result["next_review_at"] == date


@pytest.mark.asyncio
async def test_review_date_clearing_disables_document_reminders():
    files=FakeReviewFiles()
    db=type("DB", (), {"mi_user_files": files,
                        "mi_notification_outbox": OptionalQueue()})()
    result=await set_document_review_date(
        db, {"actor_id":"mi_owner"}, file_id="a"*32,
        next_review_at=None,
    )
    assert result["review_reminders"] is False
    assert "next_review_at" in files.update["$unset"]


@pytest.mark.asyncio
async def test_review_date_rejects_past_unowned_and_invalid_file_ids():
    future=datetime.now(timezone.utc)+timedelta(days=8)
    files=FakeReviewFiles(found=False)
    db=type("DB", (), {"mi_user_files": files,
                        "mi_notification_outbox": OptionalQueue()})()
    with pytest.raises(HTTPException) as exc:
        await set_document_review_date(
            db, {"actor_id":"mi_owner"}, file_id="a"*32,
            next_review_at=future,
        )
    assert exc.value.status_code == 404
    with pytest.raises(HTTPException) as exc:
        await set_document_review_date(
            db, {"actor_id":"mi_owner"}, file_id="a"*32,
            next_review_at=datetime.now(timezone.utc)-timedelta(days=1),
        )
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        await set_document_review_date(
            db, {"actor_id":"mi_owner"}, file_id="../other",
            next_review_at=future,
        )
    assert exc.value.status_code == 404


def test_review_field_whitelist_never_includes_storage_secrets():
    doc=safe_document({"file_id":"a"*32,"status":"AVAILABLE",
                       "next_review_at":datetime.now(timezone.utc),
                       "review_reminders":True,"storage_key":"private"})
    assert doc["review_reminders"] is True
    assert "next_review_at" in doc
    assert "storage_key" not in doc
