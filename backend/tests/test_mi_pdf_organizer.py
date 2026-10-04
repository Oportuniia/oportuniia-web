import pytest
import fitz
from mi_pdf_organizer import classify_page, inspect_pdf, split_reviewed_pdf


def make_pdf(texts):
    doc = fitz.open()
    for text in texts:
        page = doc.new_page()
        page.insert_text((40, 40), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_classification_is_conservative():
    assert classify_page("Recibo de salarios; nómina de septiembre")[0] == "NOMINA"
    assert classify_page("Documento sin encabezado") == ("SIN_CLASIFICAR", False)
    assert classify_page("IBAN y DNI")[0] == "SIN_CLASIFICAR"


def test_inspection_never_auto_accepts():
    data = make_pdf(["Recibo de salarios nomina", "Extracto bancario IBAN"])
    result = inspect_pdf(data)
    assert result["page_count"] == 2
    assert result["original_preserved"] is True
    assert all(page["requires_review"] for page in result["pages"])


def test_reviewed_split_is_complete_and_preserves_original():
    data = make_pdf(["NOMINA", "IBAN"])
    original = bytes(data)
    outputs = split_reviewed_pdf(data, [
        {"kind": "NOMINA", "pages": [1]},
        {"kind": "BANCO", "pages": [2]},
    ])
    assert len(outputs) == 2
    assert data == original
    for output in outputs:
        doc = fitz.open(stream=output["bytes"], filetype="pdf")
        assert doc.page_count == 1
        doc.close()


@pytest.mark.parametrize("groups", [
    [{"kind": "NOMINA", "pages": [1]}],
    [{"kind": "NOMINA", "pages": [1, 1]}, {"kind": "OTROS", "pages": [2]}],
    [{"kind": "NOMINA", "pages": [0, 2]}],
    [{"kind": "NO_VALIDO", "pages": [1, 2]}],
])
def test_rejects_unreviewed_missing_duplicate_or_out_of_range_pages(groups):
    with pytest.raises(ValueError):
        split_reviewed_pdf(make_pdf(["one", "two"]), groups)


def test_rejects_non_pdf():
    with pytest.raises(ValueError):
        inspect_pdf(b"not a pdf")
