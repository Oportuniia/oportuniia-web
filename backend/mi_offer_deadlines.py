"""MI OPORTUNIIA · 72-hour documentation obligation after conditional offer approval.

Commercial policy configured by the owner: identical three-day periods for every
approved offer. Start at confirmed server-side approval notification delivery,
not at offer submission. No automatic payment/reservation/assignment to runner
up: independent approval is required for each subsequent offer.

This module implements a testable *sandbox* state-machine. A secured, idempotent
operations adapter must invoke these functions after authoritative human
approval, email delivery evidence and document verification. Untrusted users
must never call this module directly.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

PERIOD = timedelta(hours=72)
STATES = frozenset({"SUBMITTED", "UNDER_REVIEW", "APPROVED_PENDING_NOTICE",
                    "AWAITING_DOCUMENTS", "DOCUMENTS_RECEIVED", "EXPIRED",
                    "DECLINED", "WITHDRAWN"})


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return value.astimezone(timezone.utc)


def approval_decision(offer: dict, *, approver_id: str, at: datetime) -> dict:
    if offer.get("state") != "UNDER_REVIEW" or not approver_id:
        raise ValueError("only an under-review offer can be approved by staff")
    return {**offer, "state": "APPROVED_PENDING_NOTICE",
            "approved_at": _utc(at), "approved_by": approver_id,
            "version": offer["version"] + 1}


def mark_notice_delivered(offer: dict, *, delivery_ref: str, at: datetime) -> dict:
    if offer.get("state") != "APPROVED_PENDING_NOTICE" or not delivery_ref:
        raise ValueError("approved offer and verified delivery receipt required")
    when = _utc(at)
    if when < _utc(offer["approved_at"]):
        raise ValueError("delivery cannot precede approval")
    return {**offer, "state": "AWAITING_DOCUMENTS",
            "notice_delivered_at": when, "notice_delivery_ref": delivery_ref,
            "document_deadline": when + PERIOD,
            "version": offer["version"] + 1}


def receipt(offer: dict, *, verified_at: datetime, evidence_id: str) -> dict:
    if offer.get("state") != "AWAITING_DOCUMENTS" or not evidence_id:
        raise ValueError("verified complete document packet required")
    when = _utc(verified_at)
    # No late documentation after the deadline. Equality is accepted.
    if when > _utc(offer["document_deadline"]):
        raise ValueError("deadline passed")
    return {**offer, "state": "DOCUMENTS_RECEIVED",
            "documents_verified_at": when, "documents_evidence_id": evidence_id,
            "version": offer["version"] + 1}


def expire(offer: dict, *, at: datetime) -> dict:
    when = _utc(at)
    if offer.get("state") != "AWAITING_DOCUMENTS" or when <= _utc(offer["document_deadline"]):
        raise ValueError("no actionable expiry")
    return {**offer, "state": "EXPIRED", "expired_at": when,
            "version": offer["version"] + 1}


def next_offer_candidate(offers: list[dict], *, expired_offer: dict) -> dict | None:
    """Return next eligible candidate; NOT an award or approval."""
    if expired_offer.get("state") != "EXPIRED":
        raise ValueError("original offer has not expired")
    candidates = [o for o in offers
                  if o.get("opportunity_id") == expired_offer.get("opportunity_id")
                  and o.get("offer_id") != expired_offer.get("offer_id")
                  and o.get("state") == "UNDER_REVIEW"]
    candidates.sort(key=lambda o: (o["submitted_at"], o["offer_id"]))
    return candidates[0] if candidates else None
