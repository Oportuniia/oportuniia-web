from io import BytesIO
import pytest
from pypdf import PdfReader
from mi_offer_pdf import make_offer_preview_pdf

VALID=dict(reference="OP0001",property_title="Vivienda urbana",
           property_city="Madrid",applicant_name="Persona de prueba",
           tax_identifier="TEST-NIF",email="persona@example.test",
           amount_eur="195000.00",notes="Oferta sujeta a estudio")


def test_premium_offer_pdf_is_watermarked_nonbinding_draft():
    raw=make_offer_preview_pdf(**VALID)
    assert raw.startswith(b"%PDF-")
    text=" ".join(page.extract_text() or "" for page in PdfReader(BytesIO(raw)).pages)
    assert "BORRADOR" in text
    assert "NO" in text.upper() or "no vinculante" in text
    assert "195,000.00 EUR" in text
    assert "Persona de prueba" in text
    assert "OP0001" in text


@pytest.mark.parametrize("changes",[
    {"reference":"../OP0001"},{"amount_eur":"-100"},
    {"amount_eur":"NaN"},{"amount_eur":"0"},{"applicant_name":""},
    {"notes":"very long "*200},
])
def test_offer_pdf_rejects_invalid_or_dangerous_fields(changes):
    with pytest.raises((ValueError,ArithmeticError)):
        make_offer_preview_pdf(**{**VALID,**changes})
