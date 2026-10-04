import pytest
from fastapi import HTTPException
from mi_private_upload import _enabled, _magic_valid, upload_intent, confirm_upload


def test_magic_signatures_never_trust_filename():
    assert _magic_valid(b"%PDF-1.7 contents", "application/pdf")
    assert _magic_valid(bytes.fromhex("ffd8ff") + b"data", "image/jpeg")
    assert _magic_valid(bytes.fromhex("89504e470d0a1a0a"), "image/png")
    assert not _magic_valid(b"untrusted file", "application/pdf")
    assert not _magic_valid(b"%PDF-1.7", "image/png")


def test_private_file_upload_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MI_PRIVATE_FILES_ENABLED", raising=False)
    with pytest.raises(HTTPException) as exc:
        _enabled()
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_unverified_actor_cannot_request_upload(monkeypatch):
    monkeypatch.setenv("MI_PRIVATE_FILES_ENABLED", "1")
    with pytest.raises(HTTPException) as exc:
        await upload_intent(None, {"actor_id": "mi_unverified", "email_verified": False},
                            name="identity.pdf", mime="application/pdf", size=1024)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_invalid_file_id_fails_before_db(monkeypatch):
    monkeypatch.setenv("MI_PRIVATE_FILES_ENABLED", "1")
    with pytest.raises(HTTPException) as exc:
        await confirm_upload(None, {"actor_id": "mi_own"}, "../other-document")
    assert exc.value.status_code == 404
