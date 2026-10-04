"""Isolated payment architecture contracts; SANDBOX ONLY, no bank/API calls.

NOTARIAL_ESCROW and RESERVATION_BANK are different payment rails.
No reservation event can authorize escrow funding or release. Notarial
signature alone never releases funds without independent contract checks.
All money stays with the actual provider/bank; never modeled as WEB balance.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

RAIL_NOTARY = "NOTARIAL_ESCROW"
RAIL_RESERVATION = "RESERVATION_BANK"
STATES = {
    RAIL_NOTARY: frozenset({"DRAFT", "TERMS_ACCEPTED", "PROVIDER_REFERENCED",
                            "CONDITIONS_UNDER_REVIEW", "READY_FOR_MANUAL_INSTRUCTION",
                            "CLOSED", "DISPUTED"}),
    RAIL_RESERVATION: frozenset({"DRAFT", "TERMS_ACCEPTED", "TRANSFER_REFERENCED",
                                "BANK_RECEIPT_RECONCILED", "CLOSED", "DISPUTED"}),
}


def _at(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("timezone-aware event time required")
    return value.astimezone(timezone.utc)


def _money(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("invalid fixed amount") from None
    if not amount.is_finite() or not Decimal("0") < amount <= Decimal("100000000") or amount.as_tuple().exponent < -2:
        raise ValueError("invalid EUR amount")
    return str(amount.quantize(Decimal("0.01")))


def new_payment_case(*, rail, case_id, operation_id, amount_eur, terms_version, at):
    if rail not in STATES:
        raise ValueError("unsupported payment rail")
    for value in (case_id, operation_id, terms_version):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", value):
            raise ValueError("invalid case identity or legal terms version")
    return {"rail": rail, "case_id": case_id, "operation_id": operation_id,
            "amount_eur": _money(amount_eur), "terms_version": terms_version,
            "state": "DRAFT", "version": 1, "created_at": _at(at),
            "sandbox_only": True}


def accept_approved_terms(case, *, verified_acceptance_ref, at):
    if case.get("rail") not in STATES or case.get("state") != "DRAFT":
        raise ValueError("invalid acceptance state")
    if not isinstance(verified_acceptance_ref, str) or not verified_acceptance_ref.strip():
        raise ValueError("server-verified legal acceptance required")
    return {**case, "state": "TERMS_ACCEPTED",
            "terms_accepted_at": _at(at),
            "terms_acceptance_ref": verified_acceptance_ref, "version": case["version"] + 1}


def reserve_bank_reference(case, *, bank_reference, at):
    """A reservation transfer reference, NOT proof of funds or bank custody."""
    if case.get("rail") != RAIL_RESERVATION or case.get("state") != "TERMS_ACCEPTED":
        raise ValueError("reservation bank reference cannot enter notarial rail")
    if not isinstance(bank_reference, str) or not 8 <= len(bank_reference) <= 120:
        raise ValueError("bank reference required")
    return {**case, "state": "TRANSFER_REFERENCED",
            "bank_reference": bank_reference, "reference_created_at": _at(at),
            "version": case["version"] + 1}


def reconcile_bank_receipt(case, *, verified_bank_receipt, at):
    """Requires externally verified statement; no credit from user screenshot."""
    if case.get("rail") != RAIL_RESERVATION or case.get("state") != "TRANSFER_REFERENCED":
        raise ValueError("no eligible reservation receipt")
    if not isinstance(verified_bank_receipt, str) or not verified_bank_receipt.strip():
        raise ValueError("verified bank receipt required")
    return {**case, "state": "BANK_RECEIPT_RECONCILED",
            "bank_receipt_ref": verified_bank_receipt, "bank_reconciled_at": _at(at),
            "version": case["version"] + 1}


def assign_notarial_provider(case, *, provider_ref, eligible_b2b, legal_approved, at):
    """Backend approval only; not a call to escrow provider."""
    if case.get("rail") != RAIL_NOTARY or case.get("state") != "TERMS_ACCEPTED":
        raise ValueError("reservation cannot open notarial provider case")
    if eligible_b2b is not True or legal_approved is not True:
        raise ValueError("B2B eligibility and current LEGAL approval required")
    if not isinstance(provider_ref, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,120}", provider_ref):
        raise ValueError("trusted provider reference required")
    return {**case, "state": "PROVIDER_REFERENCED",
            "provider_ref": provider_ref, "provider_linked_at": _at(at),
            "version": case["version"] + 1}


def review_notarial_conditions(case, *, verified_signature_ref, legal_check_ref,
                                operations_check_ref, at):
    """No release without two separate independently evidenced checks."""
    if case.get("rail") != RAIL_NOTARY or case.get("state") != "PROVIDER_REFERENCED":
        raise ValueError("notarial provider case required")
    evidence = (verified_signature_ref, legal_check_ref, operations_check_ref)
    if any(not isinstance(x, str) or len(x.strip()) < 6 for x in evidence):
        raise ValueError("notarial, LEGAL and operations proof required")
    if len(set(evidence)) != len(evidence):
        raise ValueError("independent evidence references required")
    return {**case, "state": "READY_FOR_MANUAL_INSTRUCTION",
            "notarial_evidence_ref": verified_signature_ref,
            "legal_evidence_ref": legal_check_ref,
            "operations_evidence_ref": operations_check_ref,
            "reviewed_at": _at(at), "version": case["version"] + 1,
            "automated_release_allowed": False}


def propose_notarial_action(case, *, action, staff_approval_ref, at):
    """Generates a human review candidate; NEVER authorizes actual transfer."""
    if case.get("rail") != RAIL_NOTARY or case.get("state") != "READY_FOR_MANUAL_INSTRUCTION":
        raise ValueError("notarial evidence and review not completed")
    if action not in ("RELEASE", "RETURN") or not isinstance(staff_approval_ref, str) or len(staff_approval_ref.strip()) < 6:
        raise ValueError("approved action and staff reference required")
    return {"case_id": case["case_id"], "rail": RAIL_NOTARY,
            "provider_ref": case["provider_ref"], "action": action,
            "staff_approval_ref": staff_approval_ref,
            "requested_at": _at(at), "status": "DRAFT_FOR_PROVIDER_REVIEW",
            "executes_transfer": False}
