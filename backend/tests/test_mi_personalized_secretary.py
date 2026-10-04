from datetime import datetime, timezone
import pytest

from mi_personalized_secretary import (
    confirm_secretary_signal, suggest_document_signals,
)

FILE = "a"*32
AT = datetime(2026,10,3,12,tzinfo=timezone.utc)


def test_payroll_historical_payment_is_only_a_suggestion():
    candidates = suggest_document_signals(
        "Nómina. Fecha de pago: 28/09/2026. Periodo de liquidación: mensual.",
        document_kind="NOMINA", file_id=FILE,
    )
    by_kind = {item["kind"]:item for item in candidates}
    assert by_kind["PAYROLL_PAYMENT_DAY"]["candidate_value"] == 28
    assert by_kind["PAYROLL_PAYMENT_DAY"]["source_date"] == "2026-09-28"
    assert by_kind["PAYROLL_PAYMENT_DAY"]["needs_owner_confirmation"] is True
    assert by_kind["PAYROLL_PERIOD"]["candidate_value"] == "mensual"
    assert all(item["source_file_id"] == FILE for item in candidates)
    assert all("Nómina" not in str(item) for item in candidates)


def test_tax_return_does_not_guess_tax_filing_date():
    candidates = suggest_document_signals(
        "Declaración de la renta. Residencia fiscal declarada: España.",
        document_kind="RENTA", file_id=FILE,
    )
    assert [item["kind"] for item in candidates] == ["TAX_RESIDENCY_DECLARED"]
    assert candidates[0]["candidate_value"] == "ES"
    assert all("deadline" not in item for item in candidates)


@pytest.mark.parametrize("text",[
    "Fecha de pago 31/02/2026",
    "Aparece 24/09/2026 sin etiqueta de pago",
    "Nómina mensual pero sin fecha explícita",
])
def test_unknown_or_invalid_payday_is_not_fabricated(text):
    assert all(item["kind"] != "PAYROLL_PAYMENT_DAY"
               for item in suggest_document_signals(
                   text, document_kind="NOMINA", file_id=FILE,
               ))


def test_confirmed_signal_is_separate_from_candidate():
    candidate = suggest_document_signals(
        "Fecha de pago: 12/09/2026",document_kind="NOMINA",file_id=FILE,
    )[0]
    result = confirm_secretary_signal(actor_id="mi_verified", candidate=candidate,
                                      value=12, confirmed_at=AT)
    assert result["confirmed_value"] == 12
    assert result["source"] == "OWNER_CONFIRMED_DOCUMENT_PROPOSAL"
    assert result["tax_advice"] is False
    assert "source_date" not in result


def test_refuse_day_29_and_unconfirmed_or_naive_confirmation():
    candidate = suggest_document_signals(
        "Fecha de pago: 28/09/2026",document_kind="NOMINA",file_id=FILE,
    )[0]
    with pytest.raises(ValueError):
        confirm_secretary_signal(actor_id="mi_verified",candidate=candidate,
                                 value=29,confirmed_at=AT)
    with pytest.raises(ValueError):
        confirm_secretary_signal(actor_id="mi_verified",
                                 candidate={**candidate,"needs_owner_confirmation":False},
                                 value=20,confirmed_at=AT)
    with pytest.raises(ValueError):
        confirm_secretary_signal(actor_id="mi_verified",candidate=candidate,
                                 value=20,confirmed_at=AT.replace(tzinfo=None))
