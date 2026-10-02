import io
import fitz
import pytest
from mi_ocr import MAX_OCR_PAGES, image_to_searchable_pdf, text_for_page
from mi_pdf_organizer import inspect_pdf


def make_pdf(text=""):
    doc=fitz.open()
    page=doc.new_page()
    if text:
        page.insert_text((60, 60), text)
    raw=doc.tobytes()
    doc.close()
    return raw


def test_blank_page_unclassified_if_local_ocr_disabled(monkeypatch):
    monkeypatch.delenv("MI_OCR_ENABLED", raising=False)
    result=inspect_pdf(make_pdf())
    assert result["pages"][0]["suggested_kind"] == "SIN_CLASIFICAR"
    assert result["pages"][0]["ocr_attempted"] is False
    assert result["pages"][0]["requires_review"] is True


def test_embedded_text_needs_no_ocr(monkeypatch):
    monkeypatch.setenv("MI_OCR_ENABLED", "1")
    doc=fitz.open(stream=make_pdf("Esta es una nomina y recibo de salarios"), filetype="pdf")
    budget={"remaining": MAX_OCR_PAGES}
    text, used=text_for_page(doc[0], budget=budget)
    assert "nomina" in text
    assert not used
    assert budget["remaining"] == MAX_OCR_PAGES
    doc.close()


def test_ocr_bounded_and_review_required(monkeypatch):
    monkeypatch.setenv("MI_OCR_ENABLED", "1")
    monkeypatch.setattr("mi_ocr.ocr_scanned_page", lambda page: "nomina recibo de salarios")
    result=inspect_pdf(make_pdf())
    assert result["pages"][0]["ocr_attempted"] is True
    assert result["pages"][0]["suggested_kind"] == "NOMINA"
    assert result["pages"][0]["requires_review"]


def test_photo_ocr_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MI_OCR_ENABLED", raising=False)
    with pytest.raises(RuntimeError):
        image_to_searchable_pdf(b"fake", "image/jpeg")


def test_ocr_requires_supported_image_type(monkeypatch):
    monkeypatch.setenv("MI_OCR_ENABLED", "1")
    with pytest.raises(ValueError):
        image_to_searchable_pdf(b"fake", "application/pdf")
