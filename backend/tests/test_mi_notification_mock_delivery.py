from datetime import datetime,timedelta,timezone
import pytest
from mi_notification_mock_delivery import dry_run_once
from mi_notification_outbox import enqueue

T=datetime(2026,10,3,8,tzinfo=timezone.utc)
NOTICE={"key":"payroll:mi_owner:"+("a"*32)+":v1:2026-10",
        "kind":"PREMIUM_PAYROLL_REMINDER","actor_id":"mi_owner",
        "signal_id":"a"*32,"calendar_version":1,
        "event_at":T+timedelta(days=1),"notify_at":T,
        "redact_attachment_details":True}


class Collection:
    def __init__(self):self.rows={}
    async def insert_one(self,row):self.rows[row["key"]]=row.copy()
    async def find_one_and_update(self,query,update,sort=None,return_document=None):
        row=next((r for r in self.rows.values() if r["state"]==query["state"]),None)
        if row is None:return None
        row.update(update.get("$set",{}))
        row["attempts"]+=update.get("$inc",{}).get("attempts",0)
        return row.copy()
    async def update_one(self,query,update):
        row=self.rows.get(query["key"])
        ok=bool(row and all(row.get(k)==v for k,v in query.items()
              if k not in ("lease_expires_at","key")))
        if ok and "lease_expires_at" in query:
            ok=row["lease_expires_at"]>=query["lease_expires_at"]["$gte"]
        if ok:
            row.update(update.get("$set",{}))
            for key in update.get("$unset",{}):row.pop(key,None)
        return type("Result",(),{"modified_count":int(ok)})()


def db():
    return type("DB",(),{"mi_notification_outbox":Collection()})()


@pytest.mark.asyncio
async def test_opt_out_after_queue_before_claim_cancels_without_transport(monkeypatch):
    database=db()
    await enqueue(database,NOTICE,now=T)
    async def no_permission(_db,_notice,*,now):return False
    monkeypatch.setattr("mi_notification_mock_delivery.revalidate_claimed_notice",no_permission)
    assert await dry_run_once(database,now=T)=={"result":"CANCELLED"}
    row=database.mi_notification_outbox.rows[NOTICE["key"]]
    assert row["state"]=="CANCELLED" and "provider_receipt" not in row
    assert await dry_run_once(database,now=T)=={"result":"EMPTY"}


@pytest.mark.asyncio
async def test_accepted_mock_marks_receipt_but_never_sends_email(monkeypatch):
    database=db()
    await enqueue(database,NOTICE,now=T)
    async def yes(_db,_notice,*,now):return True
    monkeypatch.setattr("mi_notification_mock_delivery.revalidate_claimed_notice",yes)
    assert await dry_run_once(database,now=T)=={"result":"MOCK_SENT"}
    row=database.mi_notification_outbox.rows[NOTICE["key"]]
    assert row["state"]=="SENT"
    assert row["provider_receipt"].startswith("MOCK-ACCEPTED:")
    assert "email" not in row and "salary" not in row


@pytest.mark.asyncio
async def test_ambiguous_mock_never_retries_automatically(monkeypatch):
    database=db()
    await enqueue(database,NOTICE,now=T)
    async def yes(_db,_notice,*,now):return True
    monkeypatch.setattr("mi_notification_mock_delivery.revalidate_claimed_notice",yes)
    assert await dry_run_once(database,now=T,simulate="ambiguous")=={"result":"RECONCILE"}
    assert await dry_run_once(database,now=T)=={"result":"EMPTY"}
    assert database.mi_notification_outbox.rows[NOTICE["key"]]["state"]=="RECONCILE"


@pytest.mark.asyncio
async def test_disallow_production_like_worker_id():
    with pytest.raises(ValueError):
        await dry_run_once(db(),now=T,worker_id="live-worker")
