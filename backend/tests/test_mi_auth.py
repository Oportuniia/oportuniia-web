import pytest
from fastapi import HTTPException
from starlette.requests import Request
from mi_auth import _check_password, _password, _digest, _enabled, _same_origin


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
