"""Premium PDF organizer engine for MI OPORTUNIIA.

Backend-only deterministic page classification. This is NOT OCR and never
automatically modifies originals. All suggested groups require user review.
Run only on already virus-scanned, private PDF bytes in isolated workers;
access to this module alone never grants Premium privileges.
"""
from __future__ import annotations
import re

import fitz  # PyMuPDF
from mi_ocr import MAX_OCR_PAGES, text_for_page

MAX_PDF_BYTES = 15 * 1024 * 1024
MAX_PAGES = 100
PATTERNS = {
    "IDENTIDAD": (r"documento nacional de identidad", r"\bdni\b", r"\bnie\b", r"pasaporte"),
    "NOMINA": (r"\bn[oó]mina\b", r"recibo de salarios", r"devengos", r"base de cotizaci[oó]n"),
    "RENTA": (r"declaraci[oó]n de la renta", r"\birpf\b", r"modelo 100"),
    "SOCIEDAD": (r"registro mercantil", r"escritura de constituci[oó]n", r"\bcif\b"),
    "BANCO": (r"certificado de titularidad", r"\biban\b", r"extracto bancario"),
}
 
def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())[:40000]


def classify_page(text: str) -> tuple[str, bool]:
    """Conservative suggestions; unknowns stay unclassified."""
    normalized = _normalize(text)
    hits = {kind: sum(bool(re.search(pattern, normalized)) for pattern in patterns)
            for kind, patterns in PATTERNS.items()}
    positive = [(kind, points) for kind, points in hits.items() if points]
    if not positive:
        return "SIN_CLASIFICAR", False
    positive.sort(key=lambda kv: kv[1], reverse=True)
    if len(positive) > 1 and positive[0][1] == positive[1][1]:
        return "SIN_CLASIFICAR", False
    return positive[0][0], positive[0][1] >= 2


def inspect_pdf(data: bytes) -> dict:
    if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_PDF_BYTES:
        raise ValueError("PDF vacío o supera el límite de 15 MB")
    if not data.startswith(b"%PDF-"):
        raise ValueError("Archivo PDF inválido")
    try:
        document = fitz.open(stream=data, filetype="pdf")
        if document.needs_pass:
            document.close()
            raise ValueError("PDF protegido: desbloquéalo antes de subirlo")
        if not 1 <= document.page_count <= MAX_PAGES:
            document.close()
            raise ValueError("Máximo 100 páginas por trabajo")
        pages = []
        budget = {"remaining": MAX_OCR_PAGES}
        for number, page in enumerate(document):
            text, used_ocr = text_for_page(page, budget=budget)
            kind, high_confidence = classify_page(text)
            pages.append({"page": number + 1, "suggested_kind": kind,
                          "high_confidence": high_confidence,
                          "ocr_attempted": used_ocr,
                          "requires_review": True})
        document.close()
        return {"page_count": len(pages), "pages": pages,
                "requires_review": True, "original_preserved": True}
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise ValueError("No se puede abrir este PDF") from exc


def split_reviewed_pdf(data: bytes, groups: list[dict]) -> list[dict]:
    """Export only after explicit review; no missing, duplicated or unsafe pages."""
    if not groups or len(groups) > MAX_PAGES:
        raise ValueError("Selecciona al menos un documento")
    source = fitz.open(stream=data, filetype="pdf")
    try:
        if source.needs_pass or not 1 <= source.page_count <= MAX_PAGES:
            raise ValueError("PDF no admitido")
        seen = []
        outputs = []
        allowed = set(PATTERNS) | {"OTROS"}
        for group in groups:
            kind = group.get("kind")
            pages = group.get("pages")
            if kind not in allowed or not isinstance(pages, list) or not pages:
                raise ValueError("Clasificación o páginas inválidas")
            if any(type(n) is not int or not 1 <= n <= source.page_count for n in pages):
                raise ValueError("Página fuera de rango")
            seen.extend(pages)
            output = fitz.open()
            for n in pages:
                output.insert_pdf(source, from_page=n - 1, to_page=n - 1)
            pdf = output.tobytes(garbage=4, deflate=True)
            output.close()
            outputs.append({"kind": kind, "pages": pages, "bytes": pdf})
        if sorted(seen) != list(range(1, source.page_count + 1)):
            raise ValueError("Todas las páginas deben asignarse una sola vez")
        return outputs
    finally:
        source.close()
