import pytest
from personal_user_registry import (
    CODE_PATTERN, ROLES, normalize_email, public_actor, validate_legacy_code,
    register_pending, approve_and_assign,
)


def test_emails_are_normalized_and_validated():
    assert normalize_email("  Foo@EXAMPLE.COM ") == "foo@example.com"
    for bad in ("", "fake@", "test example.com"):
        with pytest.raises(ValueError):
            normalize_email(bad)


def test_roles_and_public_projection():
    assert ROLES == {"INVERSOR": "INV", "COLABORADOR": "COL"}
    actor = {"actor_id": "mi_123", "role": "INVERSOR", "validation_state": "PENDING",
             "public_code": None, "email": "private@example.com", "documents": ["sensitive"]}
    data = public_actor(actor)
    assert "email" not in data and "documents" not in data
    assert data["public_code"] is None


def test_never_assume_legacy_scheme():
    with pytest.raises(ValueError):
        validate_legacy_code("OLD-GHL-10", "INVERSOR")
    assert CODE_PATTERN.fullmatch("OI-INV-000001")


@pytest.mark.asyncio
async def test_pending_rejects_role_before_db():
    with pytest.raises(ValueError):
        await register_pending(None, email="a@b.es", role="SUSCRIPTOR")


@pytest.mark.asyncio
async def test_approval_rejects_untrusted_requests_before_db():
    with pytest.raises(ValueError):
        await approve_and_assign(None, actor_id="../invalid", reviewer_id="administrator")
    with pytest.raises(ValueError):
        await approve_and_assign(None, actor_id="mi_" + "a" * 32, reviewer_id="")
