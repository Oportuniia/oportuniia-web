"""Build a PUBLIC, non-downloadable document status view for a published operation.

No artifact keys, hashes, output ids or R2 paths leave this view. Access to PDF
bytes requires a separate sovereign identity/entitlement gate (not implemented).
"""
PRODUCTS = (
    ("PC", "Portada comercial"),
    ("RE", "Resumen ejecutivo"),
    ("IC", "Informe completo"),
    ("RF", "Reportaje fotográfico"),
)

def public_document_status(published_item):
    """Return None for DEMO/fixtures; sanitized display rows for real publications."""
    if not published_item or not published_item.get("source_output_id"):
        return None
    source_docs = published_item.get("documents") or {}
    rows = []
    for code, label in PRODUCTS:
        info = source_docs.get(code)
        status = (info or {}).get("status") if isinstance(info, dict) else None
        rows.append({
            "code": code,
            "name": label,
            "status": "Preparado · acceso pendiente" if status == "READY" else "No disponible",
            "ready": status == "READY",
            "access": "protected",
        })
    return rows
