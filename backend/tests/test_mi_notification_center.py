from datetime import datetime,timezone
import pytest
from fastapi import HTTPException
from mi_notification_center import list_my_notices,cancel_pending_optional

T=datetime(2026,10,3,12,tzinfo=timezone.utc)

class Cursor:
    def __init__(self,rows):self.rows=rows
    def sort(self,*a):return self
    def limit(self,n):self.rows=self.rows[:n];return self
    def __aiter__(self):self.i=iter(self.rows);return self
    async def __anext__(self):
        try:return next(self.i)
        except StopIteration:raise StopAsyncIteration

class Outbox:
    def __init__(self):self.queries=[]
    def find(self,query,projection):
        assert query["actor_id"]=="mi_owner"
        assert set(projection)=={"_id","kind","state","created_at"}
        return Cursor([
            {"kind":"PREMIUM_PAYROLL_REMINDER","state":"PENDING","created_at":T,
             "provider_receipt":"PRIVATE","file_id":"PRIVATE"},
            {"kind":"OFFER_DOCUMENT_DEADLINE","state":"CLAIMED","created_at":T},
        ])
    async def update_many(self,query,update):
        self.queries.append((query,update))
        assert query["actor_id"]=="mi_owner"
        assert query["state"]=="PENDING"
        assert "OFFER_DOCUMENT_DEADLINE" not in str(query)
        return type("Result",(),{"modified_count":2})()

@pytest.mark.asyncio
async def test_owner_only_redacted_inbox():
    db=type("DB",(),{"mi_notification_outbox":Outbox()})()
    rows=await list_my_notices(db,{"actor_id":"mi_owner"})
    assert len(rows)==2
    assert rows[0]=={"title":"Aviso de agenda Premium","status":"PENDIENTE",
                     "created_at":T,"is_optional":True}
    assert rows[1]["is_optional"] is False
    assert "PRIVATE" not in str(rows)
    with pytest.raises(HTTPException):
        await list_my_notices(db,None)

@pytest.mark.asyncio
async def test_opt_out_cancels_only_pending_optional_and_not_offer():
    outbox=Outbox()
    db=type("DB",(),{"mi_notification_outbox":outbox})()
    assert await cancel_pending_optional(db,actor_id="mi_owner",now=T)==2
    query,update=outbox.queries[0]
    assert set(query["kind"]["$in"])=={"PREMIUM_PAYROLL_REMINDER","PREMIUM_DOCUMENT_REVIEW"}
    assert update["$set"]["state"]=="CANCELLED"
    await cancel_pending_optional(db,actor_id="mi_owner",now=T,signal_id="a"*32)
    assert outbox.queries[1][0]["signal_id"]=="a"*32
    await cancel_pending_optional(db,actor_id="mi_owner",now=T,file_id="b"*32)
    assert outbox.queries[2][0]["file_id"]=="b"*32
    with pytest.raises(ValueError):
        await cancel_pending_optional(db,actor_id="mi_owner",now=T,
                                     signal_id="a"*32,file_id="b"*32)
