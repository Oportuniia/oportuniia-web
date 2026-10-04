"""Offline sold-by-me reconciliation contract. Pure SANDBOX state transitions.

OPORTUNIIAPP owns encrypted local draft while offline. WEB owns investor
identity and code assignment. Network replay cannot imply confirmed sale or
referral; duplicates, uncertain delivery and collisions require server review.
"""
from __future__ import annotations

VALID={"LOCAL_PENDING","WAITING_CONNECTIVITY","APP_SUBMITTED","WEB_CHECK_PENDING",
       "WEB_DUPLICATE_BLOCKED","WEB_EMAIL_CONFIRMATION_PENDING",
       "WEB_HUMAN_REVIEW","WEB_APPROVED","MANUAL_RECONCILE"}
FINALS={"WEB_DUPLICATE_BLOCKED","WEB_APPROVED"}


def new_offline_draft(*,local_event_id,app_report_id,app_actor_id,has_contact_consent):
    if not all(isinstance(x,str) and x for x in (local_event_id,app_report_id,app_actor_id)):
        raise ValueError("stable local, report and app actor references required")
    return {"event_id":local_event_id,"report_id":app_report_id,
            "app_actor_id":app_actor_id,"state":"LOCAL_PENDING",
            "attribution_confirmed":False,"web_code":None,
            "contact_collection_gate_required":True,
            "has_contact_consent":has_contact_consent is True}


def offline_transition(draft,*,event,web_decision=None):
    if draft.get("state") not in VALID:
        raise ValueError("unknown draft state")
    current=draft["state"]
    if event=="OFFLINE":
        if current not in ("LOCAL_PENDING","WAITING_CONNECTIVITY"):
            raise ValueError("cannot move submitted draft back offline")
        target="WAITING_CONNECTIVITY"
    elif event=="APP_ACCEPTED":
        if current not in ("LOCAL_PENDING","WAITING_CONNECTIVITY"):
            raise ValueError("APP replay already processed")
        if not draft.get("has_contact_consent"):
            raise PermissionError("APP legal contact gate / user consent not satisfied")
        target="APP_SUBMITTED"
    elif event=="WEB_INTAKE":
        if current!="APP_SUBMITTED":raise ValueError("APP acceptance required")
        target="WEB_CHECK_PENDING"
    elif event=="WEB_RESULT":
        if current!="WEB_CHECK_PENDING":raise ValueError("WEB lookup required")
        outcome={"EXISTING":"WEB_DUPLICATE_BLOCKED",
                 "NEW":"WEB_EMAIL_CONFIRMATION_PENDING",
                 "UNAVAILABLE":"MANUAL_RECONCILE"}.get(web_decision)
        if not outcome:raise ValueError("unknown WEB result")
        target=outcome
    elif event=="INVESTOR_VERIFIED":
        if current!="WEB_EMAIL_CONFIRMATION_PENDING":
            raise ValueError("investor must verify own email")
        target="WEB_HUMAN_REVIEW"
    elif event=="HUMAN_APPROVED":
        if current!="WEB_HUMAN_REVIEW":
            raise ValueError("WEB review and investor verification required")
        target="WEB_APPROVED"
    else:raise ValueError("unknown transition")
    # A human WEB approval is the only place where an immutable user code can
    # be attached by the real persistence layer, never by a client event.
    return {**draft,"state":target,"attribution_confirmed":target=="WEB_APPROVED"}


def correlation_id(*,app_report_id,app_actor_id,local_event_id):
    """Stable idempotent lookup identity for authenticated APP events."""
    if not all(isinstance(x,str) and x for x in (app_report_id,app_actor_id,local_event_id)):
        raise ValueError("nonempty authoritative IDs required")
    return (app_actor_id,app_report_id,local_event_id)
