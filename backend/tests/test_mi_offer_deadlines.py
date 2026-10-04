from datetime import datetime, timedelta, timezone
import pytest
from mi_offer_deadlines import approval_decision, mark_notice_delivered, receipt, expire, next_offer_candidate

NOW=datetime(2026,10,3,8,0,tzinfo=timezone.utc)
BASE={"offer_id":"off_1","opportunity_id":"OP0001","actor_id":"mi_actor",
      "state":"UNDER_REVIEW","version":1,"submitted_at":NOW-timedelta(days=1)}

def activated():
    approved=approval_decision(BASE, approver_id="staff_a", at=NOW)
    assert approved["state"]=="APPROVED_PENDING_NOTICE"
    return mark_notice_delivered(approved, delivery_ref="delivery-verified-1",at=NOW+timedelta(minutes=10))

def test_three_days_start_when_notice_is_delivered_not_when_submitted():
    result=activated()
    assert result["document_deadline"]==NOW+timedelta(minutes=10,hours=72)
    with pytest.raises(ValueError):
        expire(result,at=result["document_deadline"])

def test_deadline_enforced_without_exceptions_and_is_versioned():
    result=activated()
    assert receipt(result,verified_at=result["document_deadline"],evidence_id="verified_packet")["state"]=="DOCUMENTS_RECEIVED"
    with pytest.raises(ValueError):
        receipt(result,verified_at=result["document_deadline"]+timedelta(seconds=1),evidence_id="late")
    expired=expire(result,at=result["document_deadline"]+timedelta(seconds=1))
    assert expired["state"]=="EXPIRED"
    with pytest.raises(ValueError):
        expire(expired,at=NOW+timedelta(days=10))

def test_no_deadline_without_approval_and_notice_receipt():
    with pytest.raises(ValueError):
        mark_notice_delivered(BASE,delivery_ref="fake",at=NOW)
    with pytest.raises(ValueError):
        approval_decision({**BASE,"state":"SUBMITTED"},approver_id="staff_a",at=NOW)

def test_runner_up_is_never_automatically_approved():
    expired=expire(activated(),at=NOW+timedelta(days=4))
    runner={"offer_id":"off_2","opportunity_id":"OP0001",
            "state":"UNDER_REVIEW","submitted_at":NOW,"version":1}
    unrelated={"offer_id":"off_3","opportunity_id":"OP0002",
               "state":"UNDER_REVIEW","submitted_at":NOW-timedelta(days=2)}
    selected=next_offer_candidate([unrelated,runner],expired_offer=expired)
    assert selected==runner and selected["state"]=="UNDER_REVIEW"
    with pytest.raises(ValueError):
        next_offer_candidate([runner],expired_offer=BASE)

def test_naive_timestamp_rejected():
    with pytest.raises(ValueError):
        approval_decision(BASE,approver_id="staff_a",at=datetime(2026,10,3))
