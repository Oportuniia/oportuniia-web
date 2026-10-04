import pytest
from fastapi import HTTPException
from mi_rate_limit import _key, throttle


def test_requires_nondefault_secret(monkeypatch):
    monkeypatch.delenv("MI_RATE_SECRET", raising=False)
    with pytest.raises(HTTPException) as exc:
        _key("login", "user@example.com")
    assert exc.value.status_code == 503


def test_hashed_rate_key_never_includes_pii(monkeypatch):
    monkeypatch.setenv("MI_RATE_SECRET", "s" * 64)
    key = _key("register", "person@example.com")
    assert "person@" not in key
    assert len(key) == 64
    assert key != _key("login", "person@example.com")


class FakeRate:
    def __init__(self):
        self.calls = 0
    async def find_one_and_update(self, query, update, **kwargs):
        assert "@" not in query["_id"]
        self.calls += 1
        return {"count": self.calls}


@pytest.mark.asyncio
async def test_rate_limiter_rejects_excess(monkeypatch):
    monkeypatch.setenv("MI_RATE_SECRET", "s" * 64)
    db = type("DB", (), {"mi_rate_limits": FakeRate()})()
    await throttle(db, action="register", subject="person@example.com", limit=2, seconds=900)
    await throttle(db, action="register", subject="person@example.com", limit=2, seconds=900)
    with pytest.raises(HTTPException) as exc:
        await throttle(db, action="register", subject="person@example.com", limit=2, seconds=900)
    assert exc.value.status_code == 429
