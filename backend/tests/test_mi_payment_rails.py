from datetime import datetime, timezone
import pytest
from mi_payment_rails import (
    RAIL_NOTARY, RAIL_RESERVATION, new_payment_case, accept_approved_terms,
    reserve_bank_reference, reconcile_bank_receipt, assign_notarial_provider,
    review_notarial_conditions, propose_notarial_action,
)

T=datetime(2026,10,3,12,tzinfo=timezone.utc)


def case(rail):
    return new_payment_case(
        rail=rail, case_id="case001", operation_id="OP0001",
        amount_eur="5000.00", terms_version="legal-v1", at=T)


def accepted(rail):
    return accept_approved_terms(case(rail),verified_acceptance_ref="verifiedterms001",at=T)


def test_reservation_never_enters_escrow():
    reservation=accepted(RAIL_RESERVATION)
    with pytest.raises(ValueError):
        assign_notarial_provider(reservation,provider_ref="provider001",
                                 eligible_b2b=True,legal_approved=True,at=T)
    reservation=reserve_bank_reference(reservation,bank_reference="bank-ref001",at=T)
    with pytest.raises(ValueError):
        review_notarial_conditions(reservation,verified_signature_ref="notary123",
                                   legal_check_ref="legal123",operations_check_ref="ops1234",at=T)
    reconciled=reconcile_bank_receipt(reservation,verified_bank_receipt="bankstmt001",at=T)
    assert reconciled["state"]=="BANK_RECEIPT_RECONCILED"
    assert "provider_ref" not in reconciled


def test_notarial_case_cannot_use_reservation_bank():
    notary=accepted(RAIL_NOTARY)
    with pytest.raises(ValueError):
        reserve_bank_reference(notary,bank_reference="bank-ref001",at=T)
    with pytest.raises(ValueError):
        assign_notarial_provider(notary,provider_ref="provider001",
                                 eligible_b2b=False,legal_approved=True,at=T)
    linked=assign_notarial_provider(notary,provider_ref="provider001",
                                   eligible_b2b=True,legal_approved=True,at=T)
    with pytest.raises(ValueError):
        propose_notarial_action(linked,action="RELEASE",
                                staff_approval_ref="staff001",at=T)
    with pytest.raises(ValueError):
        review_notarial_conditions(linked,verified_signature_ref="notary123",
                                   legal_check_ref="notary123",operations_check_ref="ops1234",at=T)
    reviewed=review_notarial_conditions(linked,verified_signature_ref="notary123",
                                        legal_check_ref="legal123",operations_check_ref="ops1234",at=T)
    proposed=propose_notarial_action(reviewed,action="RELEASE",
                                     staff_approval_ref="staff001",at=T)
    assert reviewed["automated_release_allowed"] is False
    assert proposed["executes_transfer"] is False
    assert proposed["status"]=="DRAFT_FOR_PROVIDER_REVIEW"


@pytest.mark.parametrize("invalid", ["NaN","Infinity", "-1","0","1.001","100000001"])
def test_untrusted_amount_is_rejected(invalid):
    with pytest.raises(ValueError):
        new_payment_case(rail=RAIL_NOTARY,case_id="case001",operation_id="OP0001",
                         amount_eur=invalid,terms_version="legal-v1",at=T)


def test_no_money_moves_or_providers_auto_configured():
    for rail in (RAIL_RESERVATION,RAIL_NOTARY):
        fresh=case(rail)
        assert fresh["sandbox_only"] is True
        assert "iban" not in fresh and "provider_ref" not in fresh
        assert fresh["state"]=="DRAFT"
    with pytest.raises(ValueError):
        accept_approved_terms(case(RAIL_RESERVATION),
                              verified_acceptance_ref="",at=T)
