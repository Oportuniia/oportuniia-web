import pytest
from fastapi import HTTPException
from starlette.requests import Request
from mi_auth import _check_password, _password, _digest, _enabled, _same_origin, register_routes
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MI_AUTH_ENABLED", raising=False)
    with pytest.raises(HTTPException) as exc:
        _enabled()
    assert exc.value.status_code == 503


def test_password_not_stored_in_clear():
    hashed = _password("VeryStrongPassword_ABC123!")
    assert b"VeryStrongPassword_ABC123!" not in hashed
    assert _check_password("VeryStrongPassword_ABC123!", hashed)
    assert not _check_password("different-password-12", hashed)


def test_password_minimum():
    with pytest.raises(ValueError):
        _password("short")


def test_token_digest():
    assert _digest("sensitive-token") != "sensitive-token"
    assert len(_digest("sensitive-token")) == 64


def test_cross_origin_mutations_blocked(monkeypatch):
    monkeypatch.setenv("MI_PUBLIC_ORIGIN", "https://oportuniia.com")
    req = Request({"type": "http", "headers": [(b"origin", b"https://attacker.invalid")]})
    with pytest.raises(HTTPException) as exc:
        _same_origin(req)
    assert exc.value.status_code == 403


def test_same_origin_allowed(monkeypatch):
    monkeypatch.setenv("MI_PUBLIC_ORIGIN", "https://oportuniia.com")
    req = Request({"type": "http", "headers": [(b"origin", b"https://oportuniia.com")]})
    _same_origin(req)


@pytest.mark.parametrize("terms,expected_status", [
    ("2026-10-approved", 503),  # Valid terms advance to the SMTP gate.
    ("old-version", 409),
])
def test_registration_terms_authority(monkeypatch, terms, expected_status):
    """Reject stale client terms before touching the DB or sending email."""
    monkeypatch.setenv("MI_AUTH_ENABLED", "1")
    monkeypatch.setenv("MI_PUBLIC_ORIGIN", "https://oportuniia.com")
    monkeypatch.setenv("MI_TERMS_VERSION", "2026-10-approved")
    for name in ("MI_SMTP_HOST", "MI_SMTP_USER", "MI_SMTP_PASSWORD", "MI_SMTP_FROM"):
        monkeypatch.delenv(name, raising=False)
    app = FastAPI()
    app.include_router(register_routes(object()))
    response = TestClient(app).post(
        "/api/mi/auth/register",
        headers={"origin": "https://oportuniia.com"},
        json={"email": "investor@example.com", "password": "Strong_Registered_Password_123",
              "role": "INVERSOR", "terms_version": terms, "privacy_accepted": True},
    )
    assert response.status_code == expected_status
    if terms == "old-version":
        assert "condiciones han cambiado" in response.json()["detail"]


def test_registration_fails_closed_without_configured_terms(monkeypatch):
    monkeypatch.setenv("MI_AUTH_ENABLED", "1")
    monkeypatch.setenv("MI_PUBLIC_ORIGIN", "https://oportuniia.com")
    monkeypatch.delenv("MI_TERMS_VERSION", raising=False)
    app = FastAPI()
    app.include_router(register_routes(object()))
    response = TestClient(app).post(
        "/api/mi/auth/register", headers={"origin": "https://oportuniia.com"},
        json={"email": "investor@example.com", "password": "Strong_Registered_Password_123",
              "role": "INVERSOR", "terms_version": "2026-10-approved", "privacy_accepted": True},
    )
    assert response.status_code == 503
