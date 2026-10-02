"""Local OCR for scanned personal documents, isolated from LEGAL LAB.

Uses Tesseract installed on the isolated worker. No PDF/image bytes are
sent to an external AI provider. Only available behind Premium and antivirus
checks enforced in the calling service.
"""
from __future__ import annotations

from io import BytesIO
import os
import fitz

MAX_OCR_PAGES = 20
MAX_IMAGE_BYTES = 15 * 1024 * 1024


def _ocr_enabled():
    if os.getenv("MI_OCR_ENABLED", "0") != "1":
        raise RuntimeError("OCR Premium no configurado")


def _language():
    # Fixed allowlist; never accept Tesseract arguments from a user.
    language = os.getenv("MI_OCR_LANGUAGE", "spa+eng")
    if language not in ("spa", "eng", "spa+eng"):
        raise RuntimeError("Idioma OCR no autorizado")
    return language


def ocr_scanned_page(page) -> str:
    """OCR just one page if text extraction was insufficient."""
    _ocr_enabled()
    import pytesseract
    from PIL import Image
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), colorspace=fitz.csGRAY, alpha=False)
    if pixmap.width * pixmap.height > 8_000_000:
        raise ValueError("Imagen excede la memoria permitida para OCR")
    image = Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples)
    return pytesseract.image_to_string(image, lang=_language(), timeout=25)[:40000]


def text_for_page(page, *, budget: dict) -> tuple[str, bool]:
    text = page.get_text()
    if len(text.strip()) >= 24:
        return text, False
    if not os.getenv("MI_OCR_ENABLED") == "1":
        # Do not present an empty scanned page as a confidently classified page.
        return "", False
    if budget["remaining"] <= 0:
        return "", False
    budget["remaining"] -= 1
    try:
        return ocr_scanned_page(page), True
    except Exception:
        # A failed page remains unclassified and still requires manual review.
        return "", False


def image_to_searchable_pdf(data: bytes, mime: str) -> bytes:
    """Turn a verified photo into a single-page searchable PDF locally."""
    _ocr_enabled()
    if mime not in ("image/jpeg", "image/png", "image/webp"):
        raise ValueError("Tipo de imagen no válido")
    if not 1 <= len(data) <= MAX_IMAGE_BYTES:
        raise ValueError("Imagen fuera de los límites OCR")
    from PIL import Image, ImageOps
    from PIL import UnidentifiedImageError
    try:
        image = Image.open(BytesIO(data))
        image = ImageOps.exif_transpose(image)
        if image.width * image.height > 16_000_000:
            raise ValueError("Imagen demasiado grande")
        image = image.convert("RGB")
        out = BytesIO()
        image.save(out, format="PNG")
        pix = fitz.Pixmap(out.getvalue())
        try:
            return pix.pdfocr_tobytes(language=_language(), tessdata=os.getenv("TESSDATA_PREFIX"))
        finally:
            pix = None
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("No se pudo procesar la imagen") from exc
