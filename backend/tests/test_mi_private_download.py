import pytest
from fastapi import HTTPException
from mi_private_download import signed_private_download


class Files:
    def __init__(self, row):
        self.row = row
    async def find_one(self, query):
        assert query["actor_id"] == "mi_owner"
        assert query["status"] == "AVAILABLE"
        assert query["scan_verdict"] == "CLEAN"
        return self.row


@pytest.mark.asyncio
async def test_denies_missing_or_quarantined_documents(monkeypatch):
    monkeypatch.setenv("MI_PRIVATE_FILES_ENABLED", "1")
    db = type("DB", (), {"mi_user_files": Files(None)})()
    with pytest.raises(HTTPException) as exc:
        await signed_private_download(db, {"actor_id": "mi_owner", "email_verified": True}, "a" * 32)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_denies_cross_namespace_without_touching_r2(monkeypatch):
    monkeypatch.setenv("MI_PRIVATE_FILES_ENABLED", "1")
    row = {"storage_key": "personal/v1/another-actor/a/original",
           "mime": "application/pdf"}
    db = type("DB", (), {"mi_user_files": Files(row)})()
    with pytest.raises(HTTPException) as exc:
        await signed_private_download(db, {"actor_id": "mi_owner", "email_verified": True}, "a" * 32)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_denies_unverified_actor_before_db(monkeypatch):
    monkeypatch.setenv("MI_PRIVATE_FILES_ENABLED", "1")
    with pytest.raises(HTTPException) as exc:
        await signed_private_download(None, {"actor_id": "mi_owner", "email_verified": False}, "a" * 32)
    assert exc.value.status_code == 401
