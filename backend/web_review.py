"""Human review authority. Reviewer IDs are server configuration, never UI roles.
Requires MFA, forbids self-approval, snapshots reviewed data and records evidence.
No upload, email confirmation, OCR result or payment can invoke this approval.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field

from investor_access import missing_profile_fields, fail
from web_identity import resolve_session


async def reviewer(request, db):
    user, session = await resolve_session(request, db)
    allowed = {v.strip() for v in os.getenv("WEB_REVIEWER_SUBJECT_IDS", "").split(",") if v.strip()}
    if user["subject_id"] not in allowed or not user.get("mfa_enabled") or not session.get("mfa_verified"):
        fail("reviewer_authorization_required")
    return user


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: str = Field(min_length=1, max_length=100)
    decision: str
    reason: str = Field(min_length=20, max_length=2000)
    reviewed_document_ids: list[str] = Field(min_length=1, max_length=20)
    identity_contrasted: bool = False
    dossier_contrasted: bool = False
    pbc_cleared: bool = False


def register_review_routes(router, db):
    @router.get("/staff/reviews")
    async def queue(request: Request):
        await reviewer(request, db)
        rows = await db.web_profile_drafts.find({"state": "PENDING_REVIEW"}, {"_id": 0, "subject_id": 1, "profile.full_name": 1, "updated_at": 1}).to_list(100)
        return {"items": rows}

    @router.get("/staff/reviews/{subject}")
    async def dossier(subject: str, request: Request):
        actor = await reviewer(request, db)
        if actor["subject_id"] == subject: fail("self_review_forbidden")
        draft = await db.web_profile_drafts.find_one({"subject_id": subject}, {"_id": 0})
        if not draft: fail("profile_not_found", 404)
        docs = await db.web_personal_documents.find({"subject_id": subject}, {"_id": 0, "document_id": 1, "category": 1, "name": 1, "scan_state": 1}).to_list(100)
        return {"revision": draft.get("revision"), "profile": draft["profile"], "documents": docs, "missing_fields": missing_profile_fields(draft["profile"])}

    @router.get("/staff/reviews/{subject}/documents/{document_id}")
    async def review_document(subject: str, document_id: str, request: Request):
        from web_workspace import stream_personal_document
        actor = await reviewer(request, db)
        if actor["subject_id"] == subject: fail("self_review_forbidden")
        return await stream_personal_document(db, subject, document_id, actor["subject_id"])

    @router.post("/staff/reviews/{subject}")
    async def decide(subject: str, payload: Decision, request: Request):
        actor = await reviewer(request, db)
        if actor["subject_id"] == subject: fail("self_review_forbidden")
        if payload.decision not in {"APPROVE", "REJECT"}: fail("invalid_review_decision", 422)
        draft = await db.web_profile_drafts.find_one({"subject_id": subject}, {"_id": 0})
        if not draft: fail("profile_not_found", 404)
        if draft.get("revision") != payload.expected_revision: fail("profile_changed_reload_review", 409)
        docs = await db.web_personal_documents.find({"subject_id": subject, "document_id": {"$in": payload.reviewed_document_ids}}, {"_id": 0}).to_list(20)
        if {d["document_id"] for d in docs} != set(payload.reviewed_document_ids): fail("review_document_ownership_mismatch", 422)
        target = await db.web_users.find_one({"subject_id": subject, "active": True, "email_verified": True})
        if not target: fail("review_target_account_unavailable", 409)
        profile = draft["profile"]
        categories = {d["category"] for d in docs if d.get("scan_state") == "CLEAN"}
        required = {"representative_identity", "company_representation"} if profile.get("subject_type") == "PJ" else {"identity"}
        approved = payload.decision == "APPROVE"
        if approved and (missing_profile_fields(profile) or not required.issubset(categories) or not payload.identity_contrasted or not payload.dossier_contrasted):
            fail("complete_clean_and_contrasted_dossier_required", 409)
        stamp = datetime.now(timezone.utc)
        version = str(uuid.uuid4())
        # Immutable evidence first. No endpoint updates an old decision/snapshot.
        await db.web_review_decisions.insert_one({"decision_id": version, "subject_id": subject, "reviewer_subject_id": actor["subject_id"], **payload.model_dump(), "at": stamp})
        if approved:
            await db.web_verified_profiles.insert_one({"subject_id": subject, "version": version, "profile": profile, "reviewer_subject_id": actor["subject_id"], "created_at": stamp})
        await db.web_access_reviews.update_one({"subject_id": subject}, {"$set": {"subject_id": subject, "profile_version": version if approved else None, "profile_revision": payload.expected_revision,
            "profile_complete": approved, "documents_complete": approved, "identity_status": "VERIFIED" if approved else "REJECTED", "dossier_status": "APPROVED" if approved else "REJECTED",
            "pbc_status": "CLEARED" if approved and payload.pbc_cleared else "PENDING", "revoked": not approved, "reviewer_subject_id": actor["subject_id"],
            "valid_until": (stamp+timedelta(days=90)).isoformat()}}, upsert=True)
        await db.web_profile_drafts.update_one({"subject_id": subject, "revision": payload.expected_revision}, {"$set": {"state": "REVIEWED" if approved else "CHANGES_REQUIRED"}})
        await db.web_notifications.insert_one({"id": version, "subject_id": subject, "title": "Perfil verificado" if approved else "Tu perfil necesita una revisión",
            "body": "Hemos revisado tu expediente. Los permisos de cada operación se autorizan por separado." if approved else "Consulta con el equipo los cambios necesarios para continuar.", "read": False, "created_at": stamp})
        return {"saved": True, "decision_id": version, "approved": approved, "operation_access_granted": False}
