from datetime import datetime, timedelta, timezone
import pytest
from mi_notification_validation import revalidate_claimed_notice

T=datetime(2026,10,3,12,tzinfo=timezone.utc)
CLAIM={"key":"offer:o1:deadline-48h","actor_id":"mi_owner",
       "kind":"OFFER_DOCUMENT_DEADLINE","offer_id":"o1","state":"CLAIMED"}
OFFER={"offer_id":"o1","actor_id":"mi_owner","state":"AWAITING_DOCUMENTS",
       "notice_delivery_ref":"provider-accepted",
       "notice_delivered_at":T-timedelta(hours=24),
       "document_deadline":T+timedelta(hours=48)}

class Find:
    def __init__(self, row): self.row=row
    async def find_one(self,query):
        if query.get("actor_id")!=self.row.get("actor_id"):return None
        if query.get("state") and query["state"]!=self.row.get("state"):return None
        if query.get("documents_verified_at")=={"$exists":False} and "documents_verified_at" in self.row:
            return None
        return self.row

@pytest.mark.asyncio
async def test_offer_reminder_requires_still_open_complete_unreceived_offer():
    db=type("DB",(),{"mi_offers":Find(OFFER)})()
    assert await revalidate_claimed_notice(db,CLAIM,now=T)
    received=type("DB",(),{"mi_offers":Find({**OFFER,"documents_verified_at":T})})()
    assert not await revalidate_claimed_notice(received,CLAIM,now=T)
    wrong=type("DB",(),{"mi_offers":Find({**OFFER,"actor_id":"mi_other"})})()
    assert not await revalidate_claimed_notice(wrong,CLAIM,now=T)
    assert not await revalidate_claimed_notice(db,CLAIM,now=T+timedelta(days=3))

@pytest.mark.asyncio
async def test_never_send_notice_not_exclusively_claimed():
    assert not await revalidate_claimed_notice(None,{**CLAIM,"state":"PENDING"},now=T)

class PremiumFind:
    def __init__(self, row):self.row=row
    async def find_one(self, query):
        if self.row is None:return None
        if query.get("actor_id")!=self.row.get("actor_id"):return None
        if "document_reminders" in query and query["document_reminders"]!=self.row.get("document_reminders"):return None
        return self.row

@pytest.mark.asyncio
async def test_premium_notice_cancelled_after_opt_out():
    actor={"actor_id":"mi_owner","email_verified":True,
           "validation_state":"VERIFIED","document_reminders":False}
    db=type("DB",(),{"mi_actors":PremiumFind(actor)})()
    notice={"kind":"PREMIUM_DOCUMENT_REVIEW","state":"CLAIMED",
            "actor_id":"mi_owner","file_id":"a"*32,
            "key":"premium:mi_owner:"+("a"*32)+":2026-10-07T12:00:00+00:00:7d"}
    assert not await revalidate_claimed_notice(db,notice,now=T)
