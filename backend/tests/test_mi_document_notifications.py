from datetime import datetime, timedelta, timezone
import pytest
from mi_document_notifications import (
    offer_deadline_notifications, premium_document_review_reminder,
)

T=datetime(2026,10,3,12,tzinfo=timezone.utc)
OFFER={"offer_id":"offer_test","actor_id":"mi_owner",
       "state":"AWAITING_DOCUMENTS","notice_delivered_at":T,
       "document_deadline":T+timedelta(hours=72)}


def test_deadline_reminders_48_and_24h_have_stable_keys():
    assert offer_deadline_notifications(OFFER, now=T+timedelta(hours=23))==[]
    first=offer_deadline_notifications(OFFER,now=T+timedelta(hours=24))
    assert [v["threshold_hours"] for v in first]==[48]
    both=offer_deadline_notifications(OFFER,now=T+timedelta(hours=48))
    assert [v["threshold_hours"] for v in both]==[48,24]
    assert both==offer_deadline_notifications(OFFER,now=T+timedelta(hours=48))
    assert all(v["redact_attachment_details"] for v in both)


def test_never_remind_expired_verified_or_unnotified_offer():
    assert offer_deadline_notifications(OFFER,now=T+timedelta(hours=72))==[]
    assert offer_deadline_notifications({**OFFER,"state":"DOCUMENTS_RECEIVED"},
                                        now=T+timedelta(hours=49))==[]
    assert offer_deadline_notifications({**OFFER,"documents_verified_at":T},
                                        now=T+timedelta(hours=49))==[]


def test_deadline_requires_same_72_hours_for_everyone():
    with pytest.raises(ValueError):
        offer_deadline_notifications({**OFFER,"document_deadline":T+timedelta(hours=96)},
                                      now=T+timedelta(hours=30))


SUB={"actor_id":"mi_owner","status":"ACTIVE","source_verified":True,
     "valid_from":T-timedelta(days=1),"expires_at":T+timedelta(days=40)}
DOC={"actor_id":"mi_owner","file_id":"a"*32,"status":"AVAILABLE",
     "review_reminders":True,"next_review_at":T+timedelta(days=4)}
OPTIN={"document_reminders":True}


def test_premium_review_is_opt_in_server_entitled_and_no_file_details():
    reminder=premium_document_review_reminder(DOC,SUB,OPTIN,now=T)
    assert reminder["kind"]=="PREMIUM_DOCUMENT_REVIEW"
    assert "display_name" not in reminder
    assert reminder["redact_attachment_details"]
    assert premium_document_review_reminder(DOC,SUB,{"document_reminders":False},now=T) is None
    assert premium_document_review_reminder(DOC,{**SUB,"source_verified":False},OPTIN,now=T) is None
    assert premium_document_review_reminder(DOC,{**SUB,"actor_id":"mi_other"},OPTIN,now=T) is None
    assert premium_document_review_reminder(DOC,{**SUB,"status":"EXPIRED"},OPTIN,now=T) is None
    assert premium_document_review_reminder(DOC,{**SUB,"expires_at":T-timedelta(seconds=1)},OPTIN,now=T) is None


def test_no_guessed_expiry_or_early_repeated_premium_reminders():
    assert premium_document_review_reminder({**DOC,"next_review_at":None},SUB,OPTIN,now=T) is None
    assert premium_document_review_reminder({**DOC,"next_review_at":T+timedelta(days=10)},SUB,OPTIN,now=T) is None
    assert premium_document_review_reminder({**DOC,"review_reminders":False},SUB,OPTIN,now=T) is None
