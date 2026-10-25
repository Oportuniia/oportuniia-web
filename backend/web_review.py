"""Human review authority: configured reviewer IDs or stored superadmin role.
Requires MFA, forbids self-approval, snapshots reviewed data and records evidence.
No upload, email confirmation, OCR result or payment can invoke this approval.
"""
import os
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field

from investor_access import missing_profile_fields, fail
from web_identity import resolve_session


async def reviewer(request, db):
    user, session = await resolve_session(request, db)
    allowed = {v.strip() for v in os.getenv("WEB_REVIEWER_SUBJECT_IDS", "").split(",") if v.strip()}
    if (user["subject_id"] not in allowed and user.get("role") != "superadmin") or not user.get("mfa_enabled") or not session.get("mfa_verified"):
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
    discrepancy_resolution: str = Field(default="", max_length=2000)

class DocumentReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    legible: bool
    reason: str = Field(min_length=10, max_length=1000)

class DocumentRemoval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    removed: bool
    reason: str = Field(min_length=10, max_length=1000)


def register_review_routes(router, db, prefix="/staff/reviews"):
    @router.post(prefix + "/{subject}/documents/{document_id}/removal")
    async def remove_document(subject: str, document_id: str, payload: DocumentRemoval, request: Request):
        actor = await reviewer(request, db)
        if actor['subject_id'] == subject: fail('self_review_forbidden')
        row = await db.web_personal_documents.find_one({'subject_id': subject, 'document_id': document_id})
        if not row: fail('document_not_found', 404)
        if not payload.removed and not row.get('removed_by_reviewer'): fail('document_not_in_review_trash', 409)
        stamp = datetime.now(timezone.utc)
        await db.web_document_review_events.insert_one({'subject_id': subject, 'document_id': document_id,
            'reviewer_subject_id': actor['subject_id'], 'at': stamp, 'action': 'REMOVE' if payload.removed else 'RESTORE', 'reason': payload.reason})
        await db.web_personal_documents.update_one({'_id': row['_id']}, {'$set': {'deleted': payload.removed, 'removed_by_reviewer': payload.removed, 'removed_at': stamp if payload.removed else None}})
        if payload.removed and row.get('review_state') == 'APPROVED':
            await db.web_access_reviews.update_one({'subject_id': subject}, {'$set': {'revoked': True, 'dossier_status': 'PENDING', 'documents_complete': False}})
        return {'saved': True, 'removed': payload.removed, 'restored_approval': False}

    @router.post(prefix + "/{subject}/documents/{document_id}/classify")
    async def classify_document(subject: str, document_id: str, payload: DocumentReview, request: Request):
        from web_dossier import LABELS, expired
        actor = await reviewer(request, db)
        if actor["subject_id"] == subject: fail("self_review_forbidden")
        row = await db.web_personal_documents.find_one({"subject_id": subject, "document_id": document_id, "deleted": {"$ne": True}})
        if not row or expired(row): fail("document_not_found", 404)
        if row.get("scan_state") != "CLEAN": fail("document_not_ready", 409)
        if payload.kind not in LABELS or payload.kind == "other": fail("invalid_document_kind", 422)
        if row.get("review_state") == "APPROVED": fail("reviewed_document_cannot_be_reclassified", 409)
        stamp = datetime.now(timezone.utc)
        state = "QUALITY_REJECTED" if not payload.legible else "DISCREPANCY" if row.get("identity_discrepancy") else "FILED"
        await db.web_document_review_events.insert_one({"subject_id": subject, "document_id": document_id,
            "reviewer_subject_id": actor["subject_id"], "at": stamp, **payload.model_dump()})
        saved = await db.web_personal_documents.update_one({"_id": row["_id"], "review_state": {"$ne": "APPROVED"}, "deleted": {"$ne": True}, "dossier_state": {"$ne": "EXPIRED"}}, {"$set": {
            "document_kinds": [payload.kind], "name": LABELS[payload.kind], "category": payload.kind,
            "dossier_state": state, "quality": "READABLE" if payload.legible else "UNREADABLE", "analysis_version": 2,
            "review_state": "PENDING", "operational_evidence": False,
            "temporary_until": stamp + timedelta(days=7) if not payload.legible else None}})
        if not saved.matched_count: fail("document_changed_reload", 409)
        return {"saved": True, "identity_approved": False}

    @router.get(prefix)
    async def queue(request: Request, query: str = ""):
        await reviewer(request, db)
        if query.strip():
            pattern = re.escape(query.strip()[:100])
            users = await db.web_users.find({'$or': [{key: {'$regex': pattern, '$options': 'i'}} for key in ('name', 'email', 'username')], 'active': True}, {'_id': 0, 'subject_id': 1, 'name': 1, 'username': 1}).to_list(100)
            return {'items': [{'subject_id': u['subject_id'], 'profile': {'full_name': u.get('name') or u.get('username') or 'Perfil'}} for u in users]}
        rows = await db.web_profile_drafts.find({"state": "PENDING_REVIEW"}, {"_id": 0, "subject_id": 1, "profile.full_name": 1, "updated_at": 1}).to_list(100)
        pending = await db.web_review_requests.find({"state": "PENDING"}, {"_id": 0, "subject_id": 1, "updated_at": 1}).to_list(100)
        known = {r["subject_id"] for r in rows}
        rows.extend(r for r in pending if r["subject_id"] not in known)
        return {"items": rows}

    @router.get(prefix + "/{subject}")
    async def dossier(subject: str, request: Request):
        actor = await reviewer(request, db)
        if actor["subject_id"] == subject: fail("self_review_forbidden")
        draft = await db.web_profile_drafts.find_one({"subject_id": subject}, {"_id": 0})
        if not draft: draft = {"profile": {}, "revision": ""}
        docs = await db.web_personal_documents.find({"subject_id": subject, "$or": [{"deleted": {"$ne": True}}, {"removed_by_reviewer": True}]}, {"_id": 0, "document_id": 1, "category": 1, "name": 1, "scan_state": 1, "dossier_state": 1, "document_kinds": 1, "declared_identity": 1, "identity_discrepancy": 1, "discrepancy_explanation": 1, "quality": 1, "identity_read_status": 1, "review_state": 1, "deleted": 1}).to_list(100)
        return {"revision": draft.get("revision"), "profile": draft["profile"], "documents": docs, "missing_fields": missing_profile_fields(draft["profile"])}

    @router.get(prefix + "/{subject}/documents/{document_id}")
    async def review_document(subject: str, document_id: str, request: Request, preview: bool = False):
        from web_workspace import stream_personal_document
        actor = await reviewer(request, db)
        if actor["subject_id"] == subject: fail("self_review_forbidden")
        return await stream_personal_document(db, subject, document_id, actor["subject_id"], preview=preview)

    @router.post(prefix + "/{subject}")
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
        categories = {k for d in docs if d.get("scan_state") == "CLEAN" for k in d.get("document_kinds", [d["category"]])}
        required = {"representative_identity", "company_tax_document"} if profile.get("subject_type") == "PJ" else {"identity"}
        approved = payload.decision == "APPROVE"
        from web_dossier import expired
        if approved and any(d.get("scan_state") != "CLEAN" or d.get("deleted") or expired(d) for d in docs):
            fail("complete_clean_and_contrasted_dossier_required", 409)
        if approved and any(d.get("dossier_state") not in {None, "FILED", "DISCREPANCY"} for d in docs):
            fail("documents_require_confirmation_or_discrepancy_resolution", 409)
        if approved and any(d.get("dossier_state") == "DISCREPANCY" for d in docs) and len(payload.discrepancy_resolution.strip()) < 20:
            fail("document_discrepancy_resolution_required", 409)
        if approved and (missing_profile_fields(profile) or not required.issubset(categories) or not payload.identity_contrasted or not payload.dossier_contrasted):
            fail("complete_clean_and_contrasted_dossier_required", 409)
        stamp = datetime.now(timezone.utc)
        version = str(uuid.uuid4())
        # Immutable evidence first. No endpoint updates an old decision/snapshot.
        await db.web_review_decisions.insert_one({"decision_id": version, "subject_id": subject, "reviewer_subject_id": actor["subject_id"], **payload.model_dump(), "at": stamp})
        if approved:
            await db.web_verified_profiles.insert_one({"subject_id": subject, "version": version, "profile": profile, "reviewer_subject_id": actor["subject_id"], "created_at": stamp})
            await db.web_personal_documents.update_many({"subject_id": subject, "document_id": {"$in": payload.reviewed_document_ids}},
                {"$set": {"review_state": "APPROVED", "dossier_state": "FILED", "operational_evidence": True, "review_decision_id": version}})
        await db.web_access_reviews.update_one({"subject_id": subject}, {"$set": {"subject_id": subject, "profile_version": version if approved else None, "profile_revision": payload.expected_revision,
            "profile_complete": approved, "documents_complete": approved, "identity_status": "VERIFIED" if approved else "REJECTED", "dossier_status": "APPROVED" if approved else "REJECTED",
            "pbc_status": "CLEARED" if approved and payload.pbc_cleared else "PENDING", "revoked": not approved, "reviewer_subject_id": actor["subject_id"],
            "valid_until": (stamp+timedelta(days=90)).isoformat()}}, upsert=True)
        await db.web_profile_drafts.update_one({"subject_id": subject, "revision": payload.expected_revision}, {"$set": {"state": "REVIEWED" if approved else "CHANGES_REQUIRED"}})
        await db.web_notifications.insert_one({"id": version, "subject_id": subject, "title": "Perfil verificado" if approved else "Tu perfil necesita una revisión",
            "body": "Hemos revisado tu expediente. Los permisos de cada operación se autorizan por separado." if approved else "Consulta con el equipo los cambios necesarios para continuar.", "read": False, "created_at": stamp})
        await db.web_review_requests.update_one({"_id": subject}, {"$set": {"state": "REVIEWED", "decision_id": version}})
        return {"saved": True, "decision_id": version, "approved": approved, "operation_access_granted": False}
