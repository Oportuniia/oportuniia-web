"""Pure collaborator attribution policy guards. SANDBOX: no writes or payment.

Actual A/B signed contracts determine legal entitlement and the exact
24-month commencement. These functions reject missing source evidence;
they cannot grant commissions, punish users or infer judicial findings.
"""
from datetime import datetime,timezone
from calendar import monthrange
from fastapi import HTTPException


def _date(v):
    if not isinstance(v,datetime) or v.tzinfo is None:
        raise ValueError("authenticated aware timestamp required")
    return v.astimezone(timezone.utc)


def _anniversary(start,years=2):
    # Explicit calendar-year anniversary for *technical demonstration only*.
    # Signed agreement overrides exact end-date semantics.
    try:
        return start.replace(year=start.year+years)
    except ValueError:
        return start.replace(year=start.year+years,day=monthrange(start.year+years,start.month)[1])


def attributed_investor(*,collaborator,investor,invitation_proof,investor_acceptance,
                         associated_at,previous_relation=False):
    """Create only a proposed association, never overwrite previous links."""
    at=_date(associated_at)
    if not (collaborator and collaborator.get("role")=="COLABORADOR"
            and collaborator.get("validation_state")=="VERIFIED"
            and collaborator.get("email_verified") is True):
        raise HTTPException(403,"Colaborador sin aprobación vigente")
    if investor.get("role")!="INVERSOR" or investor.get("email_verified") is not True:
        raise ValueError("independent investor verification required")
    if previous_relation or not invitation_proof or not investor_acceptance:
        raise ValueError("prior claim conflict or missing explicit association proof")
    if collaborator.get("actor_id")==investor.get("actor_id"):
        raise ValueError("no self-attribution")
    return {"collaborator_id":collaborator["actor_id"],
            "investor_id":investor["actor_id"],"associated_at":at,
            "attribution_state":"PENDING_OPERATIONS_VALIDATION",
            "investor_consented":True,"source_verified":False}


def protection_state(*,association,at,contract_start,contract_end):
    """Dates MUST come from operative signed agreement; do not calculate them."""
    moment=_date(at)
    start,end=_date(contract_start),_date(contract_end)
    if end<=start:
        raise ValueError("invalid approved contract coverage")
    if association.get("attribution_state")!="VERIFIED" or not association.get("source_verified"):
        return "UNVERIFIED"
    if association.get("conflict_state")=="HOLD_FOR_LEGAL":
        return "LEGAL_REVIEW"
    return "WITHIN_CONTRACT_WINDOW" if start<=moment<end else "OUTSIDE_CONTRACT_WINDOW"


def model_a_eligibility(*,agreement_kind,notarial_signed_at,recognition,
                        verified_by_legal):
    """Honorarium recognition must precede notarial signing."""
    if agreement_kind!="A":
        return "NOT_MODEL_A"
    signing=_date(notarial_signed_at)
    if not recognition or verified_by_legal is not True:
        return "NO_DOCUMENTED_ELIGIBILITY"
    recognized=_date(recognition.get("accepted_at"))
    if not recognition.get("recognition_ref") or recognized>=signing:
        return "NO_DOCUMENTED_ELIGIBILITY"
    # Not a payable commission: later sale/profit, exact base and signed
    # contract still require an independent accounting determination.
    return "DOCUMENT_PRECONDITION_MET_REQUIRES_ACCOUNTING"


def model_b_internal_recognition(*,agreement_kind,unique_verified_operations,
                                 reporting_year):
    """Non-contractual admin-only flag; never produces award or payable."""
    if agreement_kind!="B" or type(reporting_year) is not int:
        return None
    if not 2000<=reporting_year<=2200:
        raise ValueError("invalid reporting year")
    valid=set()
    for op in unique_verified_operations:
        if (op.get("closed_verified") is True
            and op.get("attribution_verified") is True
            and op.get("year")==reporting_year
            and isinstance(op.get("operation_id"),str)
            and op.get("operation_id")):
            valid.add(op["operation_id"])
    if len(valid)<10:
        return None
    return {"event":"MODEL_B_TEN_VERIFIED_OPERATIONS",
            "year":reporting_year,"visibility":"ADMIN_ONLY",
            "award_decided":False,"amount":None,"contractual_right":False}
