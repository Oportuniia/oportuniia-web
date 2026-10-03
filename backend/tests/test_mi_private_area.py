import pytest
from fastapi import HTTPException
from mi_private_area import safe_profile, safe_document, private_documents, profile_update, set_document_reminder_consent


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


class PreferenceActors:
    async def update_one(self, query, update):
        assert query["actor_id"] == "mi_owner"
        assert update["$set"]["document_reminders"] is True
        return type("Result", (), {"matched_count": 1})()


@pytest.mark.asyncio
async def test_optional_reminder_consent_changes_only_current_actor():
    db = type("DB", (), {"mi_actors": PreferenceActors()})()
    result = await set_document_reminder_consent(
        db, {"actor_id": "mi_owner"}, enabled=True)
    assert result == {"document_reminders": True}


@pytest.mark.asyncio
async def test_reminder_consent_cannot_be_set_anonymously():
    with pytest.raises(HTTPException) as exc:
        await set_document_reminder_consent(None, None, enabled=True)
    assert exc.value.status_code == 401
