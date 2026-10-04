"""Safety tests for isolated personal-documents storage contract."""
import pytest
from personal_document_storage import PersonalFileScope, _scope, new_upload, private_download


def test_no_verified_session():
    with pytest.raises(PermissionError):
        new_upload(PersonalFileScope("actor_12345678", False), mime="application/pdf", size=12)


def test_reject_invalid_actor():
    with pytest.raises(PermissionError):
        _scope(PersonalFileScope("../escape", True))


def test_unsupported_file_rejected_before_storage():
    with pytest.raises(ValueError):
        new_upload(PersonalFileScope("actor_12345678", True), mime="application/x-msdownload", size=12)


def test_reject_cross_user_key_before_storage():
    scope = PersonalFileScope("actor_12345678", True)
    with pytest.raises(PermissionError):
        private_download(scope, storage_key="personal/v1/another-user/0123456789abcdef0123456789abcdef/original")


def test_dedicated_bucket_required(monkeypatch):
    from personal_document_storage import _r2
    for name, val in {"MI_R2_ENDPOINT":"https://example.invalid", "MI_R2_ACCESS_KEY_ID":"placeholder",
                      "MI_R2_SECRET_ACCESS_KEY":"placeholder", "MI_R2_BUCKET":"oportuniia-presentacion-prod"}.items():
        monkeypatch.setenv(name, val)
    with pytest.raises(RuntimeError, match="separate"):
        _r2()
