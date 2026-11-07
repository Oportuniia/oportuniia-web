"""Authenticated blank legal matrices, never evidence of a signed agreement."""
from pathlib import Path
from fastapi import Depends
from fastapi.responses import FileResponse
from investor_access import authenticated_subject, fail, PRIVATE_HEADERS

VERSION = "2026-11-07"
ROOT = Path(__file__).resolve().parent / "legal_templates"
DOCUMENTS = {
    "recognition": ("MATRIZ_RECONOCIMIENTO_INVERSOR_COLABORADOR_20261107.pdf", "Reconocimiento inversor–colaborador"),
    "contract": ("CONTRATO_COLABORADOR_ACTUALIZADO_20261107.pdf", "Contrato de colaboración externa"),
}


def register_collaborator_document_routes(router, db):
    async def collaborator(subject=Depends(authenticated_subject)):
        user = await db.web_users.find_one({"subject_id": subject, "active": True}) or {}
        # Self-declared account kind grants access only to a blank matrix, not money or files of others.
        if user.get("account_kind") != "colaborador" and user.get("role") != "superadmin":
            fail("collaborator_documents_only", 403)
        return subject

    @router.get("/collaborator/legal-templates")
    async def catalog(subject=Depends(collaborator)):
        return {"version": VERSION, "items": [
            {"id": key, "title": title, "url": "/api/collaborator/legal-templates/" + key}
            for key, (_, title) in DOCUMENTS.items()
        ]}

    @router.get("/collaborator/legal-templates/{document_id}")
    async def download(document_id: str, subject=Depends(collaborator)):
        if document_id not in DOCUMENTS:
            fail("document_not_found", 404)
        name, _ = DOCUMENTS[document_id]
        return FileResponse(ROOT / name, media_type="application/pdf", filename=name, headers=PRIVATE_HEADERS)
