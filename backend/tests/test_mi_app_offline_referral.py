import pytest
from mi_app_offline_referral import new_offline_draft,offline_transition,correlation_id


def draft(consent=True):
    return new_offline_draft(local_event_id="event_123",app_report_id="report_456",
                             app_actor_id="app_owner",has_contact_consent=consent)


def test_no_coverage_never_assigns_web_code():
    offline=offline_transition(draft(),event="OFFLINE")
    assert offline["state"]=="WAITING_CONNECTIVITY"
    assert offline["web_code"] is None
    assert not offline["attribution_confirmed"]
    submitted=offline_transition(offline,event="APP_ACCEPTED")
    checking=offline_transition(submitted,event="WEB_INTAKE")
    blocked=offline_transition(checking,event="WEB_RESULT",web_decision="EXISTING")
    assert blocked["state"]=="WEB_DUPLICATE_BLOCKED"
    assert not blocked["attribution_confirmed"]


def test_unavailable_web_requires_reconciliation_not_claim():
    x=offline_transition(offline_transition(draft(),event="APP_ACCEPTED"),
                         event="WEB_INTAKE")
    x=offline_transition(x,event="WEB_RESULT",web_decision="UNAVAILABLE")
    assert x["state"]=="MANUAL_RECONCILE"
    assert x["web_code"] is None


def test_new_only_human_approved_after_email():
    x=offline_transition(draft(),event="APP_ACCEPTED")
    x=offline_transition(x,event="WEB_INTAKE")
    x=offline_transition(x,event="WEB_RESULT",web_decision="NEW")
    with pytest.raises(ValueError):
        offline_transition(x,event="HUMAN_APPROVED")
    x=offline_transition(x,event="INVESTOR_VERIFIED")
    x=offline_transition(x,event="HUMAN_APPROVED")
    assert x["attribution_confirmed"] is True
    assert x["web_code"] is None  # actual WEB assigns code after approval


def test_legal_gate_and_replay_protection():
    with pytest.raises(PermissionError):
        offline_transition(draft(consent=False),event="APP_ACCEPTED")
    accepted=offline_transition(draft(),event="APP_ACCEPTED")
    with pytest.raises(ValueError):
        offline_transition(accepted,event="APP_ACCEPTED")
    assert correlation_id(app_actor_id="app_owner",app_report_id="report_456",
                          local_event_id="event_123")==("app_owner","report_456","event_123")
