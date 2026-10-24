"""User declarations organize documents; only staff review establishes evidence."""
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field
from investor_access import authenticated_subject, fail

LABELS = {"identity": "DNI", "representative_identity": "DNI DEL REPRESENTANTE",
          "company_tax_document": "CIF / NIF DE EMPRESA", "constitution": "ESCRITURA DE CONSTITUCIÓN",
          "beneficial_ownership": "ACTA DE TITULARIDAD REAL", "representation": "PODER DE REPRESENTACIÓN",
          "other": "DOCUMENTO PENDIENTE DE CLASIFICAR"}

def normalized(value):
    return re.sub(r"\s+", " ", "".join(c for c in unicodedata.normalize("NFKD", value).casefold()
                    if not unicodedata.combining(c))).strip()

def name_mismatch(expected, detected):
    a, b = set(normalized(expected).split()), set(normalized(detected).split())
    return bool(a and b and a != b)

class Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kinds: list[str] = Field(min_length=1, max_length=6)
    detected_name: str = Field(default="", max_length=180)
    identity_answer: str = Field(default="", max_length=30)
    explanation: str = Field(default="", max_length=1000)
    confirmed: bool

def register_dossier_routes(router, db):
    @router.post("/investor/personal-documents/{document_id}/confirm")
    async def confirm(document_id: str, payload: Confirmation, subject: str = Depends(authenticated_subject)):
        row = await db.web_personal_documents.find_one({"document_id": document_id, "subject_id": subject, "deleted": {"$ne": True}})
        if not row: fail("document_not_found", 404)
        if row.get("dossier_state") == "EXPIRED": fail("document_not_found", 404)
        if row.get("review_state") == "APPROVED": fail("reviewed_document_cannot_be_reclassified", 409)
        if row.get("scan_state") != "CLEAN": fail("document_not_ready", 409)
        if not payload.confirmed or any(k not in LABELS for k in payload.kinds): fail("document_confirmation_required", 422)
        kinds = list(dict.fromkeys(payload.kinds))
        draft = await db.web_profile_drafts.find_one({"subject_id": subject}) or {}
        profile = draft.get("profile", {})
        identity = bool(set(kinds) & {"identity", "representative_identity"})
        expected = profile.get("representative" if "representative_identity" in kinds else "full_name", "")
        mismatch = identity and name_mismatch(expected, payload.detected_name)
        if identity and payload.identity_answer not in {"matches", "different", "unreadable"}:
            fail("document_identity_answer_required", 422)
        discrepancy = identity and (mismatch or payload.identity_answer != "matches" or not payload.detected_name or not expected)
        if discrepancy and not payload.explanation.strip(): fail("document_discrepancy_explanation_required", 422)
        temporary = "other" in kinds
        state = "TEMPORARY" if temporary else "DISCREPANCY" if discrepancy else "FILED"
        stamp = datetime.now(timezone.utc)
        values = {"dossier_state": state, "document_kinds": kinds, "name": " · ".join(LABELS[k] for k in kinds),
                  "declared_identity": payload.detected_name, "identity_discrepancy": bool(discrepancy),
                  "discrepancy_explanation": payload.explanation, "user_confirmed_at": stamp,
                  "review_state": "PENDING", "operational_evidence": False,
                  "temporary_until": stamp + timedelta(days=7) if temporary else None}
        # Preserve the actual category for staff contracts; never derive approval from browser text.
        values["category"] = next((k for k in kinds if k in {"identity", "representative_identity", "company_tax_document"}), "company_representation")
        saved = await db.web_personal_documents.update_one({"_id": row["_id"], "dossier_state": {"$ne": "EXPIRED"}, "deleted": {"$ne": True}}, {"$set": values})
        if not saved.matched_count: fail("document_not_found", 404)
        return {"document_id": document_id, "dossier_state": state, "name": values["name"]}

async def expire_temporary(db):
    import asyncio
    import web_personal_storage as storage
    stamp = datetime.now(timezone.utc)
    rows = await db.web_personal_documents.find({"deleted": {"$ne": True}, "dossier_state": {"$in": ["TEMPORARY", "EXPIRED"]}, "temporary_until": {"$lt": stamp}}).to_list(20)
    for row in rows:
        claimed = await db.web_personal_documents.update_one({"_id": row["_id"], "dossier_state": {"$in": ["TEMPORARY", "EXPIRED"]}, "temporary_until": {"$lt": stamp}}, {"$set": {"dossier_state": "EXPIRED"}})
        if not claimed.matched_count: continue
        try:
            await asyncio.to_thread(storage.client(row.get("storage_backend")).delete_object,
                                    Bucket=row["storage_bucket"], Key=row["storage_key"])
        except Exception:
            continue  # inaccessible immediately; retry physical deletion next worker pass
        await db.web_personal_documents.update_one({"_id": row["_id"], "dossier_state": "EXPIRED"},
            {"$set": {"deleted": True, "deleted_at": stamp}, "$unset": {"declared_identity": "", "discrepancy_explanation": ""}})
