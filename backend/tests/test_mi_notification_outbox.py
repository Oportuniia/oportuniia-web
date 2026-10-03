from datetime import datetime,timedelta,timezone
import pytest
from pymongo.errors import DuplicateKeyError
from mi_notification_outbox import enqueue,claim_one,mark_sent,mark_uncertain,cancel_pending

NOW=datetime(2026,10,3,12,tzinfo=timezone.utc)
NOTICE={"key":"offer:offer_test:deadline-48h","kind":"OFFER_DOCUMENT_DEADLINE",
        "actor_id":"mi_testowner","offer_id":"offer_test","threshold_hours":48,
        "deadline":NOW+timedelta(days=2),"redact_attachment_details":True}


class FakeCollection:
    def __init__(self):self.rows={}
    async def insert_one(self,row):
        if row["key"] in self.rows:raise DuplicateKeyError("duplicate")
        self.rows[row["key"]]=row.copy()
    async def find_one_and_update(self,query,update,sort=None,return_document=None):
        for row in self.rows.values():
            if row["state"]!=query["state"]:continue
            row.update(update.get("$set",{}))
            row["attempts"]+=update.get("$inc",{}).get("attempts",0)
            return row.copy()
        return None
    async def update_one(self,query,update):
        row=self.rows.get(query["key"])
        valid=bool(row and all(row.get(k)==v for k,v in query.items()
                               if k not in ("key","lease_expires_at")))
        if valid and "lease_expires_at" in query:
            valid=row["lease_expires_at"]>=query["lease_expires_at"]["$gte"]
        if valid:
            row.update(update.get("$set",{}))
            for key in update.get("$unset",{}):row.pop(key,None)
        return type("Update",(),{"modified_count":int(valid)})()


def db():return type("DB",(),{"mi_notification_outbox":FakeCollection()})()


@pytest.mark.asyncio
async def test_queue_idempotence_and_redaction():
    database=db()
    assert await enqueue(database,NOTICE,now=NOW) is True
    assert await enqueue(database,NOTICE,now=NOW) is False
    stored=database.mi_notification_outbox.rows[NOTICE["key"]]
    assert stored["state"]=="PENDING"
    assert "email" not in stored and "filename" not in stored
    assert "attachment" not in stored


@pytest.mark.asyncio
async def test_atomic_claim_and_verified_delivery_receipt():
    database=db()
    await enqueue(database,NOTICE,now=NOW)
    claim=await claim_one(database,worker_id="test-worker",now=NOW)
    assert claim["state"]=="CLAIMED"
    assert await claim_one(database,worker_id="other",now=NOW) is None
    assert not await mark_sent(database,key=NOTICE["key"],worker_id="wrong",
                              receipt="receipt123",now=NOW)
    assert await mark_sent(database,key=NOTICE["key"],worker_id="test-worker",
                           receipt="receipt123",now=NOW)
    assert database.mi_notification_outbox.rows[NOTICE["key"]]["state"]=="SENT"


@pytest.mark.asyncio
async def test_uncertain_delivery_is_not_blindly_retried():
    database=db()
    await enqueue(database,NOTICE,now=NOW)
    await claim_one(database,worker_id="test-worker",now=NOW)
    assert await mark_uncertain(database,key=NOTICE["key"],worker_id="test-worker",now=NOW)
    assert await claim_one(database,worker_id="another",now=NOW) is None


@pytest.mark.asyncio
async def test_cancel_optional_reminder_before_delivery():
    database=db()
    await enqueue(database,NOTICE,now=NOW)
    assert await cancel_pending(database,key=NOTICE["key"],reason="DOCUMENTS_RECEIVED",now=NOW)
    assert await claim_one(database,worker_id="test-worker",now=NOW) is None


@pytest.mark.asyncio
async def test_outbox_disallows_insecure_or_invalid_notifications():
    database=db()
    with pytest.raises(ValueError):
        await enqueue(database,{**NOTICE,"redact_attachment_details":False},now=NOW)
    with pytest.raises(ValueError):
        await enqueue(database,{**NOTICE,"threshold_hours":100},now=NOW)
    with pytest.raises(ValueError):
        await mark_sent(database,key="x",worker_id="w",receipt="",now=NOW)
