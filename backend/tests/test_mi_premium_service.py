import pytest
from fastapi import HTTPException
from mi_premium_service import require_premium, _scanned_pdf


class FakeEntitlements:
    async def find_one(self, query):
        assert query["actor_id"] == "mi_owner"
        assert query["status"] == "ACTIVE"
        assert query["source_verified"] is True
        return None


class FakeFiles:
    async def find_one(self, query):
        assert query["actor_id"] == "mi_owner"
        assert query["scan_verdict"] == "CLEAN"
        return None


class DB:
    mi_premium_entitlements = FakeEntitlements()
    mi_user_files = FakeFiles()


ACTOR = {"actor_id": "mi_owner", "email_verified": True,
         "validation_state": "VERIFIED"}


@pytest.mark.asyncio
async def test_premium_gate_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MI_ORGANIZER_ENABLED", raising=False)
    with pytest.raises(HTTPException) as exc:
        await require_premium(DB(), ACTOR)
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_non_premium_cannot_use_organizer(monkeypatch):
    monkeypatch.setenv("MI_ORGANIZER_ENABLED", "1")
    with pytest.raises(HTTPException) as exc:
        await require_premium(DB(), ACTOR)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_unverified_profile_cannot_use_organizer(monkeypatch):
    monkeypatch.setenv("MI_ORGANIZER_ENABLED", "1")
    with pytest.raises(HTTPException) as exc:
        await require_premium(DB(), {**ACTOR, "validation_state": "PENDING"})
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_only_owners_clean_scanned_pdf_can_enter_processor():
    with pytest.raises(HTTPException) as exc:
        await _scanned_pdf(DB(), ACTOR, "a" * 32)
    assert exc.value.status_code == 404
