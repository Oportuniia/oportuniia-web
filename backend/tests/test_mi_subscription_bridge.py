import hashlib
import hmac
import json
import pytest
from datetime import datetime, timezone
from fastapi import HTTPException
from mi_subscription_bridge import verify_signed_event, apply_signed_event


def event():
    return {"schema":"mi-billing-v1", "event_id":"evt-12345678",
            "customer_id":"customer-987654", "plan":"PREMIUM",
            "status":"ACTIVE", "effective_at":"2026-10-01T00:00:00Z",
            "expires_at":"2026-11-01T00:00:00Z"}


def test_signed_event_rejects_unconfigured_bridge(monkeypatch):
    monkeypatch.delenv("MI_BILLING_BRIDGE_ENABLED", raising=False)
    with pytest.raises(HTTPException) as exc:
        verify_signed_event(b"{}",timestamp="1",signature="0"*64)
    assert exc.value.status_code == 503


def test_bridge_rejects_modified_payload_and_expired_signature(monkeypatch):
    monkeypatch.setenv("MI_BILLING_BRIDGE_ENABLED","1")
    monkeypatch.setenv("MI_BILLING_BRIDGE_SECRET","s"*64)
    raw=json.dumps(event()).encode()
    now=datetime(2026,10,2,12,0,tzinfo=timezone.utc)
    ts=str(int(now.timestamp()))
    sig=hmac.new(b"s"*64,ts.encode()+b"."+raw,hashlib.sha256).hexdigest()
    assert verify_signed_event(raw,timestamp=ts,signature=sig,now=now)["plan"]=="PREMIUM"
    with pytest.raises(HTTPException) as exc:
        verify_signed_event(raw+b" ",timestamp=ts,signature=sig,now=now)
    assert exc.value.status_code == 401
    with pytest.raises(HTTPException) as exc:
        verify_signed_event(raw,timestamp=str(int(now.timestamp())-999),signature=sig,now=now)
    assert exc.value.status_code == 401


class UnknownLinks:
    async def find_one(self, query):
        assert query["verified"] is True
        return None


@pytest.mark.asyncio
async def test_webhook_never_self_registers_customer_as_premium():
    db=type("DB",(),{"mi_subscription_links":UnknownLinks()})()
    with pytest.raises(HTTPException) as exc:
        await apply_signed_event(db,event())
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_unrecognized_plan_rejected_before_db():
    invalid={**event(),"plan":"FREE"}
    with pytest.raises(HTTPException) as exc:
        await apply_signed_event(None,invalid)
    assert exc.value.status_code == 422
