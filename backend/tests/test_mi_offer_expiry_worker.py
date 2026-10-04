from datetime import datetime,timedelta,timezone
import pytest
from mi_offer_expiry_worker import expire_due_once

NOW=datetime(2026,10,3,12,tzinfo=timezone.utc)

class Cursor:
    def __init__(self,rows):self.rows=rows
    def sort(self,*args):return self
    def limit(self,n):self.rows=self.rows[:n];return self
    def __aiter__(self):self.iter=iter(self.rows);return self
    async def __anext__(self):
        try:return next(self.iter)
        except StopIteration:raise StopAsyncIteration

class FakeOffers:
    def __init__(self,record):self.record=record
    def find(self,query,projection):
        assert query["documents_verified_at"]=={"$exists":False}
        return Cursor([{"offer_id":self.record["offer_id"],"version":self.record["version"]}]
                      if self.record["state"]=="AWAITING_DOCUMENTS"
                      and "documents_verified_at" not in self.record
                      and self.record["document_deadline"]<NOW else [])
    async def find_one_and_update(self,query,update):
        r=self.record
        if (r["offer_id"]!=query["offer_id"] or r["version"]!=query["version"]
            or r["state"]!="AWAITING_DOCUMENTS" or "documents_verified_at" in r
            or not r["document_deadline"]<NOW):return None
        r.update(update["$set"]);r["version"]+=1
        r.setdefault("events",[]).append(update["$push"]["events"])
        return r

@pytest.mark.asyncio
async def test_expiry_once_is_atomic_and_idempotent():
    record={"offer_id":"offer-1","version":1,"state":"AWAITING_DOCUMENTS",
            "document_deadline":NOW-timedelta(seconds=1)}
    db=type("DB",(),{"mi_offers":FakeOffers(record)})()
    assert await expire_due_once(db,now=NOW)==["offer-1"]
    assert await expire_due_once(db,now=NOW)==[]
    assert record["operations_review_pending"] is True
    assert record["events"][0]["kind"]=="DOCS_DEADLINE_EXPIRED"
    assert record["version"]==2

@pytest.mark.asyncio
async def test_received_documents_block_expiry():
    record={"offer_id":"offer-2","version":1,"state":"AWAITING_DOCUMENTS",
            "document_deadline":NOW-timedelta(minutes=1),
            "documents_verified_at":NOW-timedelta(minutes=2)}
    db=type("DB",(),{"mi_offers":FakeOffers(record)})()
    assert await expire_due_once(db,now=NOW)==[]
    assert record["state"]=="AWAITING_DOCUMENTS"

@pytest.mark.asyncio
async def test_deadline_boundary_respected():
    record={"offer_id":"offer-3","version":1,"state":"AWAITING_DOCUMENTS",
            "document_deadline":NOW}
    db=type("DB",(),{"mi_offers":FakeOffers(record)})()
    assert await expire_due_once(db,now=NOW)==[]

@pytest.mark.asyncio
async def test_worker_requires_timestamp():
    with pytest.raises(ValueError):
        await expire_due_once(None,now=datetime(2026,10,3))
