from datetime import datetime,timedelta,timezone
import pytest
from fastapi import HTTPException
from mi_collaborator_policy import (
    attributed_investor,protection_state,model_a_eligibility,
    model_b_internal_recognition,
)
NOW=datetime(2026,10,3,12,tzinfo=timezone.utc)
COL={"actor_id":"mi_collab","role":"COLABORADOR",
     "validation_state":"VERIFIED","email_verified":True}
INV={"actor_id":"mi_investor","role":"INVERSOR","email_verified":True}


def test_referral_must_be_approved_and_investor_consented():
    case=attributed_investor(collaborator=COL,investor=INV,
            invitation_proof="verified-token-hash",
            investor_acceptance="consent-receipt",associated_at=NOW)
    assert case["attribution_state"]=="PENDING_OPERATIONS_VALIDATION"
    assert case["source_verified"] is False
    with pytest.raises(HTTPException):
        attributed_investor(collaborator={**COL,"validation_state":"PENDING"},
                            investor=INV,invitation_proof="yes",
                            investor_acceptance="yes",associated_at=NOW)
    with pytest.raises(ValueError):
        attributed_investor(collaborator=COL,investor=INV,
                            invitation_proof="yes",investor_acceptance="yes",
                            associated_at=NOW,previous_relation=True)
    with pytest.raises(ValueError):
        attributed_investor(collaborator=COL,investor=INV,
                            invitation_proof="yes",investor_acceptance=None,
                            associated_at=NOW)


def test_two_year_rights_not_deleted_by_commercial_unlink():
    association={"attribution_state":"VERIFIED","source_verified":True,
                 "relationship_state":"UNLINKED"}
    end=NOW.replace(year=2028)
    assert protection_state(association=association,at=NOW+timedelta(days=100),
            contract_start=NOW,contract_end=end)=="WITHIN_CONTRACT_WINDOW"
    assert protection_state(association=association,at=end,
            contract_start=NOW,contract_end=end)=="OUTSIDE_CONTRACT_WINDOW"
    assert protection_state(association={**association,"conflict_state":"HOLD_FOR_LEGAL"},
            at=NOW,contract_start=NOW,contract_end=end)=="LEGAL_REVIEW"
    assert protection_state(association={**association,"source_verified":False},
            at=NOW,contract_start=NOW,contract_end=end)=="UNVERIFIED"


def test_model_a_requires_contract_accepted_before_notary():
    assert model_a_eligibility(agreement_kind="A",
           notarial_signed_at=NOW,recognition=None,
           verified_by_legal=True)=="NO_DOCUMENTED_ELIGIBILITY"
    assert model_a_eligibility(agreement_kind="A",
           notarial_signed_at=NOW,
           recognition={"recognition_ref":"contract123","accepted_at":NOW},
           verified_by_legal=True)=="NO_DOCUMENTED_ELIGIBILITY"
    assert model_a_eligibility(agreement_kind="A",
           notarial_signed_at=NOW,
           recognition={"recognition_ref":"contract123",
                        "accepted_at":NOW-timedelta(days=1)},
           verified_by_legal=True)=="DOCUMENT_PRECONDITION_MET_REQUIRES_ACCOUNTING"
    assert model_a_eligibility(agreement_kind="B",
           notarial_signed_at=NOW,recognition=None,
           verified_by_legal=False)=="NOT_MODEL_A"


def test_model_b_alert_internal_discretionary_and_only_unique_closed_operations():
    ops=[{"operation_id":f"OP{i}","closed_verified":True,
          "attribution_verified":True,"year":2026} for i in range(10)]
    assert model_b_internal_recognition(agreement_kind="B",
           unique_verified_operations=ops[:9],reporting_year=2026) is None
    result=model_b_internal_recognition(agreement_kind="B",
           unique_verified_operations=ops+[ops[0]],reporting_year=2026)
    assert result["visibility"]=="ADMIN_ONLY"
    assert result["amount"] is None and result["contractual_right"] is False
    assert result["award_decided"] is False
    assert model_b_internal_recognition(agreement_kind="A",
           unique_verified_operations=ops,reporting_year=2026) is None
