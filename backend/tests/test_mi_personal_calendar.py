from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest
from fastapi import HTTPException
from mi_personal_calendar import next_payroll_occurrence, set_payroll_calendar, list_payroll_calendar

UTC=timezone.utc
NOW=datetime(2026,10,3,12,tzinfo=UTC)
SIGNAL="a"*32


def test_month_boundary_and_local_timezone_stable():
    value=next_payroll_occurrence(now=datetime(2026,10,28,12,tzinfo=UTC),day=5,lead_days=1)
    local=value["event_at"].astimezone(ZoneInfo("Europe/Madrid"))
    assert (local.year,local.month,local.day,local.hour)==(2026,11,5,10)
    assert value["notify_at"]<value["event_at"]


def test_no_guessed_month_end_or_invalid_timezone():
    with pytest.raises(ValueError):
        next_payroll_occurrence(now=NOW,day=31)
    with pytest.raises(ValueError):
        next_payroll_occurrence(now=NOW.replace(tzinfo=None),day=15)
    with pytest.raises(ValueError):
        next_payroll_occurrence(now=NOW,day=15,lead_days=9)


class OptionalQueue:
    async def update_many(self,query,update):
        assert query["actor_id"]=="mi_owner"
        assert query["kind"]=="PREMIUM_PAYROLL_REMINDER"
        return type("Result",(),{"modified_count":0})()


class Signals:
    def __init__(self, *,found=True):
        self.row={"actor_id":"mi_owner","signal_id":SIGNAL,
                  "kind":"PAYROLL_PAYMENT_DAY","active":True,
                  "source":"OWNER_CONFIRMED_DOCUMENT_PROPOSAL",
                  "confirmed_value":12}
        self.found=found
        self.changes=[]
    async def find_one(self,query):
        assert query["actor_id"]=="mi_owner"
        return self.row if self.found else None
    async def update_one(self,query,update):
        assert query["actor_id"]=="mi_owner"
        assert query["calendar_version"]=={"$exists":False}
        self.changes.append(update["$set"])
        return type("Result",(),{"modified_count":1})()


@pytest.mark.asyncio
async def test_activation_is_explicit_and_revocable_on_owner_signal():
    files=Signals()
    db=type("DB",(),{"mi_secretary_signals":files,
                       "mi_notification_outbox":OptionalQueue()})()
    result=await set_payroll_calendar(db,{"actor_id":"mi_owner"},
                                     signal_id=SIGNAL,enabled=True,lead_days=2)
    assert result["calendar_enabled"] is True
    assert files.changes[0]["calendar_timezone"]=="Europe/Madrid"
    assert files.changes[0]["calendar_version"]==1
    result=await set_payroll_calendar(db,{"actor_id":"mi_owner"},
                                     signal_id=SIGNAL,enabled=False,lead_days=0)
    assert result["calendar_enabled"] is False
    assert files.changes[1]["calendar_enabled"] is False


@pytest.mark.asyncio
async def test_no_calendar_for_unconfirmed_or_wrong_owner_signal():
    db=type("DB",(),{"mi_secretary_signals":Signals(found=False)})()
    with pytest.raises(HTTPException) as exc:
        await set_payroll_calendar(db,{"actor_id":"mi_owner"},
                                   signal_id=SIGNAL,enabled=True,lead_days=1)
    assert exc.value.status_code==404


@pytest.mark.asyncio
async def test_rejects_invalid_calendar_preferences_without_db_read():
    with pytest.raises(HTTPException):
        await set_payroll_calendar(None,{"actor_id":"mi_owner"},
                                   signal_id=SIGNAL,enabled=1,lead_days=0)
    with pytest.raises(HTTPException):
        await set_payroll_calendar(None,{"actor_id":"mi_owner"},
                                   signal_id=SIGNAL,enabled=True,lead_days=99)
