"""Investor gateway. Uploads, OCR, payment and browser roles NEVER grant access.
Real mode requires verified OIDC identity, independent reviews and per-operation grants.
Public OP references are resolved server-side; provider references never leave this module.
"""
from __future__ import annotations
import asyncio
import hashlib
import hmac
import io
import os
import re
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

PRODUCTS = {"PC": ("Portada comercial", "PRESENTACION", 1), "RE": ("Resumen ejecutivo", "PRESENTACION", 2),
            "IC": ("Informe completo", "PRESENTACION", 2), "RF": ("Álbum de fotos", "PRESENTACION", 2),
            "LEGAL": ("Documentación judicial", "LEGAL", 3)}
OP_RE = re.compile(r"^OP-[A-Za-z0-9-]{1,70}$")
PRIVATE_HEADERS = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff", "X-Robots-Tag": "noindex, nofollow"}


def fail(code: str, status=403):
    raise HTTPException(status_code=status, detail={"code": code})


def future(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.tzinfo is not None and dt > datetime.now(timezone.utc)
    except ValueError:
        return False


@lru_cache(maxsize=4)
def _jwks(url):
    from jwt import PyJWKClient
    return PyJWKClient(url, cache_keys=True, lifespan=300)


async def authenticated_subject(request: Request) -> str:
    if os.getenv("WEB_IDENTITY_MODE") == "web_sessions":
        from web_identity import resolve_session
        db = getattr(request.app.state, "web_db", None)
        if db is None: fail("identity_database_not_configured", 503)
        user, session = await resolve_session(request, db)
        if user.get("role") == "superadmin" and (not user.get("mfa_enabled") or not session.get("mfa_verified")):
            fail("second_factor_setup_required", 403)
        return user["subject_id"]
    issuer, audience, jwks = (os.getenv(k, "").strip() for k in ("WEB_AUTH_ISSUER", "WEB_AUTH_AUDIENCE", "WEB_AUTH_JWKS_URL"))
    if not issuer or not audience or urlparse(jwks).scheme != "https":
        fail("identity_provider_not_configured", 503)
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer ") or len(authorization) > 12000:
        fail("authentication_required", 401)
    token = authorization[7:]
    def verify():
        import jwt
        key = _jwks(jwks).get_signing_key_from_jwt(token).key
        return jwt.decode(token, key, algorithms=["RS256"], audience=audience, issuer=issuer,
                          options={"require": ["exp", "iat", "sub", "iss", "aud"]})
    try:
        claims = await asyncio.to_thread(verify)
    except Exception:
        fail("invalid_or_expired_session", 401)
    subject = claims.get("sub")
    if not isinstance(subject, str) or not 1 <= len(subject) <= 200:
        fail("invalid_subject", 401)
    db = getattr(request.app.state, "web_db", None)
    if db is not None:
        from web_access_restrictions import blocked
        if await blocked(db, {"subject_id": subject}): fail("account_access_restricted", 403)
    return subject


def access_stage(review: dict) -> int:
    # Ordered, independently reviewed stages. A stale review revokes all stages.
    if not future(review.get("valid_until")) or review.get("revoked"):
        return 0
    if review.get("identity_status") != "VERIFIED":
        return 0
    if review.get("dossier_status") != "APPROVED":
        return 1
    return 2


async def context(db, subject: str, op_ref: str | None = None):
    owner = await db.web_users.find_one({"subject_id": subject, "active": True}, {"role": 1, "username": 1, "email": 1}) or {}
    founder = owner.get("role") == "superadmin" and owner.get("username") == "rafamaster" and owner.get("email") == "info@oportuniia.com"
    review = await db.web_access_reviews.find_one({"subject_id": subject}, {"_id": 0}) or {}
    if review.get("profile_revision"):
        current = await db.web_profile_drafts.find_one({"subject_id": subject}, {"_id": 0, "revision": 1}) or {}
        if current.get("revision") != review["profile_revision"]: review["revoked"] = True
    entitlement = await db.web_entitlements.find_one({"subject_id": subject, "product": "PREMIUM", "active": True}, {"_id": 0}) or {}
    result = {"subject": subject, "review": review, "stage": access_stage(review),
              "premium": future(entitlement.get("valid_until")), "grant": {}}
    result["founder_access"] = founder
    if founder:
        result.update(stage=2, premium=True)
        result["review"] = {"identity_status": "ADMINISTRATOR", "dossier_status": "NOT_REQUIRED"}
    if op_ref:
        if not OP_RE.fullmatch(op_ref): fail("invalid_public_reference", 400)
        grant = await db.web_operation_grants.find_one({"subject_id": subject, "op_ref": op_ref}, {"_id": 0}) or {}
        if future(grant.get("valid_until")) and not grant.get("revoked"):
            result["grant"] = grant
    result["premium"] = result["premium"] and (await contracting_eligibility(db, result))["can_contract"]
    return result


def authorize_document(ctx: dict, doc: dict) -> None:
    code = doc.get("product")
    if code not in PRODUCTS or doc.get("approved") is not True or doc.get("public_reference_safe") is not True or doc.get("owner") != PRODUCTS[code][1]:
        fail("document_not_authorized")
    configured_stage = doc.get("minimum_stage", 3)
    if type(configured_stage) is not int or configured_stage not in (1, 2, 3): fail("invalid_document_policy")
    if doc.get("valid_until") and not future(doc["valid_until"]): fail("document_expired")
    required = max(PRODUCTS[code][2], configured_stage)
    # Judicial documents need an additional explicit dossier authorization and PBC review.
    stage = ctx["stage"]
    if stage >= 2 and ctx["grant"].get("dossier_authorized") and ctx["grant"].get("pbc_status") == "CLEARED" and ctx["review"].get("pbc_status") == "CLEARED":
        stage = 3
    if stage < required: fail("verified_dossier_required")
    if code not in ctx["grant"].get("permissions", []): fail("operation_permission_required")
    if code == "RF" and not ctx["premium"]: fail("premium_required")


async def operation_documents(db, op_ref: str) -> list[dict]:
    rows = await db.web_operation_documents.find({"op_ref": op_ref, "approved": True}, {"_id": 0}).to_list(100)
    binding = await db.web_operation_bindings.find_one({"public_ref": op_ref, "publication_approved": True}, {"_id": 0})
    if not binding or not binding.get("internal_id") or binding.get("documents_reference_safe") is not True:
        return rows
    published = await db.presentation_web_published.find_one({"internal_id": binding["internal_id"], "publication_state": "PUBLISHED"}, {"_id": 0})
    if not published: return rows
    item = published.get("item") or {}
    output_id = item.get("source_output_id", "")
    if not re.fullmatch(r"web_[a-f0-9]{24}", output_id): return rows
    for product, meta in (item.get("documents") or {}).items():
        if product not in {"PC", "RE", "IC", "RF"} or not isinstance(meta, dict) or meta.get("status") != "READY": continue
        checksum = str(meta.get("checksum") or meta.get("content_hash") or "").removeprefix("sha256:")
        if not re.fullmatch(r"[a-f0-9]{64}", checksum): continue
        ident = hashlib.sha256(f"{op_ref}|{product}|{checksum}".encode()).hexdigest()[:24]
        rows.append({"op_ref": op_ref, "document_id": ident, "product": product, "owner": "PRESENTACION", "approved": True,
                     "minimum_stage": PRODUCTS[product][2], "public_reference_safe": True, "sha256": checksum, "mime": "application/pdf", "presentation_output_id": output_id})
    return rows


class ProfileDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_kind: str
    subject_type: str
    full_name: str = Field(min_length=1, max_length=150)
    investment_profile: str = Field(default="", max_length=100)
    country: str = Field(default="", max_length=80)
    company_name: str = Field(default="", max_length=180)
    legal_form: str = Field(default="", max_length=80)
    representative: str = Field(default="", max_length=150)
    collaborator_model: str = ""

    email: str = Field(default="", max_length=180)
    phone: str = Field(default="", max_length=80)
    birth_date: str = Field(default="", max_length=20)
    address: str = Field(default="", max_length=180)
    nationality: str = Field(default="", max_length=100)
    tax_id: str = Field(default="", max_length=80)
    company_tax_id: str = Field(default="", max_length=80)
    registered_address: str = Field(default="", max_length=180)
    representative_id: str = Field(default="", max_length=80)
    representative_position: str = Field(default="", max_length=100)
    fiscal_address: str = Field(default="", max_length=180)
    municipality: str = Field(default="", max_length=100)
    region: str = Field(default="", max_length=100)
    province: str = Field(default="", max_length=180)
    fiscal_address_number: str = Field(default="", max_length=80)
    fiscal_address_unit: str = Field(default="", max_length=80)
    fiscal_address_postal_code: str = Field(default="", max_length=80)
    address_number: str = Field(default="", max_length=80)
    address_unit: str = Field(default="", max_length=80)
    address_postal_code: str = Field(default="", max_length=80)
    registered_address_number: str = Field(default="", max_length=80)
    registered_address_unit: str = Field(default="", max_length=80)
    registered_address_postal_code: str = Field(default="", max_length=80)
    professional_activity: str = Field(default="", max_length=180)
    consents: dict[str, bool] = Field(default_factory=dict)


def missing_profile_fields(profile):
    required = ["account_kind", "subject_type", "full_name", "email", "tax_id", "fiscal_address", "fiscal_address_number", "municipality", "province", "region", "country"]
    required += (["company_name", "company_tax_id", "registered_address", "representative", "representative_id", "representative_position", "registered_address_number"] if profile.get("subject_type") == "PJ" else ["birth_date"])
    if profile.get("account_kind") == "inversor": required += ["address", "address_number", "nationality", "professional_activity"]
    else: required += ["collaborator_model"]
    missing = [k for k in required if not str(profile.get(k, "")).strip()]
    consents = ["privacy", "confidentiality", "ethics"] if profile.get("account_kind") == "colaborador" else ["privacy", "truthfulness", "no_commitment", "terms"]
    missing += ["consent_"+k for k in consents if profile.get("consents", {}).get(k) is not True]
    if profile.get("account_kind") not in {"inversor", "colaborador"}: missing.append("valid_account_kind")
    if profile.get("subject_type") not in {"PF", "PJ"}: missing.append("valid_subject_type")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", str(profile.get("email", ""))): missing.append("valid_email")
    if profile.get("account_kind") == "colaborador" and profile.get("collaborator_model") not in {"A", "B"}: missing.append("valid_collaborator_model")
    return sorted(set(missing))


async def contracting_eligibility(db, ctx):
    if ctx.get("founder_access"):
        return {"can_contract": True, "profile_complete": True, "documents_verified": False,
                "verified": True, "reason": "FOUNDER_ADMINISTRATOR_ACCESS", "verification_basis": "SERVER_ROLE"}
    review = ctx["review"]
    version = review.get("profile_version")
    snapshot = await db.web_verified_profiles.find_one({"subject_id": ctx["subject"], "version": version}, {"_id": 0}) if version else None
    missing = missing_profile_fields((snapshot or {}).get("profile", {}))
    approved = ctx["stage"] >= 2 and review.get("profile_complete") is True and review.get("documents_complete") is True and snapshot is not None and not missing
    return {"can_contract": approved, "profile_complete": not missing, "documents_verified": review.get("documents_complete") is True and ctx["stage"] >= 2,
            "verified": approved, "reason": "VERIFIED_PROFILE" if approved else "COMPLETE_AND_VERIFIED_PROFILE_REQUIRED"}


class MessageDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op_ref: str = ""
    body: str = Field(min_length=1, max_length=4000)


class TeamReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thread_id: str = Field(min_length=1, max_length=90)
    event_id: str = Field(min_length=1, max_length=90)
    body: str = Field(min_length=1, max_length=4000)


class PremiumCheckout(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan: str = "monthly"


class CheckoutDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    modality: str


def register_investor_routes(router: APIRouter, db):
    @router.get("/investor/access")
    async def access(subject: str = Depends(authenticated_subject)):
        ctx = await context(db, subject)
        from web_registration_feedback import CODES
        draft = await db.web_profile_drafts.find_one({'subject_id': subject}) or {}
        return {"founder_access": ctx.get("founder_access", False), "stage": ctx["stage"], "premium": ctx["premium"], "identity_status": ctx["review"].get("identity_status", "PENDING"),
                "automatic_issues": [c for c in draft.get('automatic_issues', []) if c in CODES] if ctx['stage'] < 2 else [],
                "dossier_status": ctx["review"].get("dossier_status", "PENDING"), "pbc_status": ctx["review"].get("pbc_status", "PENDING"),
                "contracting": await contracting_eligibility(db, ctx), "rule": "UPLOADING_AND_PAYMENT_DO_NOT_GRANT_ACCESS"}

    @router.get("/investor/opportunities")
    async def opportunities(universe: str = "judicial", subject: str = Depends(authenticated_subject)):
        if universe not in {"judicial", "acuerdos"}: fail("invalid_universe", 422)
        ctx = await context(db, subject)
        if ctx["stage"] < 2:
            # Only publication-approved safe catalog bindings. No protected bytes or
            # hidden fields are sent to the browser, even behind a visual blur.
            bindings = await db.web_operation_bindings.find(
                {"publication_approved": True, "catalog_reference_safe": True}, {"_id": 0}).to_list(500)
            previews = []
            for binding in bindings:
                op = binding.get("public_ref", "")
                if not OP_RE.fullmatch(op): continue
                published = await db.presentation_web_published.find_one(
                    {"internal_id": binding.get("internal_id"), "publication_state": "PUBLISHED"}, {"_id": 0})
                item = (published or {}).get("item") or {}
                if item.get("universe") != universe: continue
                import catalog_data
                phase = item.get("phase")
                previews.append({"op_ref": op, "municipio_name": item.get("municipio_name"),
                    "roi": item.get("roi"), "phase": catalog_data.phase_name(phase) if phase else None,
                    "locked": True})
            return {"items": previews, "total": len(previews), "universe": universe, "preview": True}
        if universe == "acuerdos" and not ctx["premium"]: fail("premium_required")
        grants = await db.web_operation_grants.find({"subject_id": subject}, {"_id": 0}).to_list(500)
        items = []
        for grant in grants:
            op = grant.get("op_ref", "")
            if not OP_RE.fullmatch(op) or not future(grant.get("valid_until")) or grant.get("revoked") or "CATALOG" not in grant.get("permissions", []): continue
            binding = await db.web_operation_bindings.find_one({"public_ref": op, "publication_approved": True, "catalog_reference_safe": True}, {"_id": 0})
            if not binding: continue
            published = await db.presentation_web_published.find_one({"internal_id": binding.get("internal_id"), "publication_state": "PUBLISHED"}, {"_id": 0})
            item = (published or {}).get("item") or {}
            if item.get("universe") != universe: continue
            allowed = ("product", "universe", "title", "asset_type", "category", "ccaa_name", "provincia_name", "municipio_name", "price", "roi", "timeframe", "phase")
            items.append({"op_ref": op, **{k: item.get(k) for k in allowed}})
        return {"items": items, "total": len(items), "universe": universe}

    @router.post("/investor/profile-draft")
    async def profile(payload: ProfileDraft, request: Request, subject: str = Depends(authenticated_subject)):
        if payload.account_kind not in {"inversor", "colaborador"} or payload.subject_type not in {"PF", "PJ"}:
            fail("invalid_profile_type", 422)
        if payload.account_kind == "inversor" and payload.collaborator_model:
            fail("investor_has_no_permanent_modality", 422)
        if payload.account_kind == "colaborador" and payload.collaborator_model not in {"A", "B"}:
            fail("collaborator_model_required", 422)
        if os.getenv("WEB_IDENTITY_MODE") == "web_sessions":
            owner = request.state.web_user
            if payload.email.lower() != owner["email"] or payload.account_kind != owner["account_kind"]: fail("account_identity_mismatch", 422)
        from web_access_restrictions import blocked
        if await blocked(db, {"subject_id": subject, "email": payload.email}, payload.model_dump()): fail("account_access_restricted", 403)
        # Editing the profile cannot retain an approval of an older identity snapshot.
        revision = str(uuid.uuid4())
        # Re-reading an edited profile is allowed only when its previous review
        # was not administratively revoked. A profile edit must not lift a hold.
        await db.web_access_reviews.update_one({"subject_id": subject, "$or": [
            {"revoked": {"$ne": True}}, {"automatic_recheck_revision": {"$exists": True}}]},
            {"$set": {"revoked": True, "identity_status": "PENDING", "dossier_status": "PENDING",
                      "automatic_recheck_revision": revision}})
        await db.web_profile_drafts.update_one({"subject_id": subject}, {"$set": {"subject_id": subject, "profile": payload.model_dump(),
            "state": "PENDING_REVIEW", "revision": revision, "automatic_issues": [], "automatic_state": "PENDING", "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
        return {"saved": True, "state": "PENDING_REVIEW", "access_granted": False}

    @router.get("/investor/operations/{op_ref}/documents")
    async def documents(op_ref: str, subject: str = Depends(authenticated_subject)):
        ctx = await context(db, subject, op_ref)
        rows = await operation_documents(db, op_ref)
        allowed = []
        for doc in rows:
            try: authorize_document(ctx, doc)
            except HTTPException: continue
            if not re.fullmatch(r"[A-Za-z0-9-]{1,90}", str(doc.get("document_id", ""))): continue
            allowed.append({"document_id": doc["document_id"], "product": doc["product"], "title": PRODUCTS[doc["product"]][0],
                            "owner": doc["owner"], "download": f"/api/investor/operations/{op_ref}/documents/{doc['document_id']}"})
        return {"op_ref": op_ref, "items": allowed, "stage": ctx["stage"]}

    @router.get("/investor/operations/{op_ref}/documents/{document_id}")
    async def document(op_ref: str, document_id: str, request: Request, subject: str = Depends(authenticated_subject)):
        ctx = await context(db, subject, op_ref)
        doc = next((d for d in await operation_documents(db, op_ref) if d.get("document_id") == document_id), None)
        if not doc: fail("document_unavailable", 404)
        authorize_document(ctx, doc)
        bucket = os.getenv("WEB_DOCUMENTS_PRIVATE_BUCKET", "").strip()
        prefix = os.getenv("WEB_DOCUMENTS_PRIVATE_PREFIX", "approved/").strip()
        key = doc.get("storage_key", "")
        from_presentation = bool(doc.get("presentation_output_id"))
        if not from_presentation and not bucket: fail("private_document_storage_not_configured", 503)
        if not from_presentation and (not prefix or not key.startswith(prefix) or ".." in key.split("/") or doc.get("mime") != "application/pdf"): fail("invalid_document_storage", 503)
        def read():
            if from_presentation:
                import requests
                from presentation_ingress import _producer_config
                base, m2m_key = _producer_config()
                if urlparse(base).scheme != "https": fail("invalid_presentation_origin", 503)
                url = f"{base}/api/m2m/outputs/web/{doc['presentation_output_id']}/artifacts/{doc['product']}"
                with requests.get(url, headers={"X-Presentation-Web-Key": m2m_key}, timeout=(5, 30), stream=True, allow_redirects=False) as response:
                    if response.status_code != 200: fail("presentation_artifact_unavailable", 503)
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 50 * 1024 * 1024: fail("invalid_document_size", 503)
                        chunks.append(chunk)
                    data = b"".join(chunks)
            else:
                import boto3
                response = boto3.client("s3").get_object(Bucket=bucket, Key=key)
                size = response.get("ContentLength", 0)
                if not 0 < size <= 50 * 1024 * 1024: fail("invalid_document_size", 503)
                try: data = response["Body"].read(50 * 1024 * 1024 + 1)
                finally: response["Body"].close()
                if len(data) != size: fail("invalid_document_size", 503)
            if not data.startswith(b"%PDF-"): fail("invalid_document_bytes", 503)
            expected = doc.get("sha256")
            if not isinstance(expected, str) or not hmac.compare_digest(hashlib.sha256(data).hexdigest(), expected): fail("document_integrity_error", 503)
            return data
        try: data = await asyncio.to_thread(read)
        except HTTPException: raise
        except Exception: fail("document_storage_unavailable", 503)
        await db.web_access_audit.insert_one({"subject_id": subject, "op_ref": op_ref, "document_id": document_id,
                                              "action": "DOCUMENT_READ", "at": datetime.now(timezone.utc).isoformat()})
        disposition = "inline" if request.query_params.get("view") == "1" else "attachment"
        return StreamingResponse(io.BytesIO(data), media_type="application/pdf", headers={**PRIVATE_HEADERS,
            "Content-Disposition": f'{disposition}; filename="{op_ref}_{doc["product"]}.pdf"'})

    @router.post("/investor/operations/{op_ref}/checkout")
    async def checkout(op_ref: str, payload: CheckoutDraft, subject: str = Depends(authenticated_subject)):
        if payload.modality not in {"A", "B", "C", "D"}: fail("invalid_modality", 422)
        ctx = await context(db, subject, op_ref)
        if not (await contracting_eligibility(db, ctx))["can_contract"]: fail("complete_and_verified_profile_required")
        if ctx["stage"] < 2 or ctx["review"].get("pbc_status") != "CLEARED" or not ctx["grant"].get("can_reserve"):
            fail("operation_readiness_required")
        readiness = await db.operation_readiness_snapshots.find_one({"operation_id": op_ref, "investor_id": subject, "modality": payload.modality}, {"_id": 0}, sort=[("received_at", -1)])
        if not readiness or not readiness.get("can_contract") or not future(readiness.get("valid_until")):
            fail("authoritative_readiness_required")
        from web_payments import create_checkout
        return await create_checkout(db, subject, "RESERVATION", op_ref=op_ref, modality=payload.modality)


    @router.post("/investor/premium/checkout")
    async def premium_checkout(payload: PremiumCheckout = PremiumCheckout(), subject: str = Depends(authenticated_subject)):
        ctx = await context(db, subject)
        if not (await contracting_eligibility(db, ctx))["can_contract"]: fail("complete_and_verified_profile_required")
        if ctx["premium"]: fail("premium_already_active", 409)
        from web_payments import create_checkout
        return await create_checkout(db, subject, "PREMIUM", plan=payload.plan)

    @router.get("/investor/messages")
    async def messages(subject: str = Depends(authenticated_subject)):
        rows = await db.web_message_threads.find({"subject_id": subject}, {"_id": 0}).to_list(100)
        return {"items": [{k: row.get(k) for k in ("thread_id", "op_ref", "messages", "state", "updated_at")} for row in rows]}

    @router.post("/investor/messages")
    async def message(payload: MessageDraft, subject: str = Depends(authenticated_subject)):
        if payload.op_ref and not OP_RE.fullmatch(payload.op_ref): fail("invalid_public_reference", 422)
        if not payload.body.strip(): fail("message_body_required", 422)
        now = datetime.now(timezone.utc).isoformat()
        ident = str(uuid.uuid4())
        await db.web_message_threads.insert_one({"thread_id": ident, "subject_id": subject, "op_ref": payload.op_ref,
            "messages": [{"sender": "INVESTOR", "body": payload.body.strip(), "at": now}], "state": "PENDING_TEAM_REPLY", "updated_at": now})
        return {"thread_id": ident, "saved": True, "email_sent": False, "state": "PENDING_TEAM_REPLY"}

    @router.post("/m2m/investor/replies")
    async def reply(payload: TeamReply, request: Request):
        expected = os.getenv("WEB_MESSAGES_M2M_KEY", "").strip()
        if not expected: fail("message_authority_not_configured", 503)
        supplied = request.headers.get("X-OPORTUNIIA-Messages-Key", "")
        if not supplied or not hmac.compare_digest(supplied, expected): fail("invalid_message_authority", 401)
        return await save_team_reply(db, payload)

    @router.get("/investor/operations/{op_ref}/offer-draft")
    async def offer(op_ref: str, subject: str = Depends(authenticated_subject)):
        ctx = await context(db, subject, op_ref)
        if ctx["stage"] < 2 or "PREPARE_OFFER" not in ctx["grant"].get("permissions", []): fail("verified_profile_and_operation_permission_required")
        version = ctx["review"].get("profile_version")
        if not version: fail("verified_profile_snapshot_required", 409)
        profile = await db.web_verified_profiles.find_one({"subject_id": subject, "version": version}, {"_id": 0})
        if not profile: fail("verified_profile_snapshot_required", 409)
        allowed = ("account_kind", "subject_type", "full_name", "email", "phone", "tax_id", "fiscal_address", "municipality", "province", "region", "country", "fiscal_address_number", "fiscal_address_unit", "fiscal_address_postal_code", "address_number", "address_unit", "address_postal_code", "registered_address_number", "registered_address_unit", "registered_address_postal_code", "address", "fiscal_address", "company_name", "company_tax_id", "registered_address", "representative", "representative_id", "representative_position")
        return {"op_ref": op_ref, "applicant": {k: profile.get("profile", {}).get(k, "") for k in allowed},
                "state": "DATA_DRAFT_ONLY", "template_approved": False, "signed": False, "submitted_to_provider": False}



async def save_team_reply(db, payload):
    thread = await db.web_message_threads.find_one({"thread_id": payload.thread_id}, {"_id": 0})
    if not thread: fail("thread_not_found", 404)
    if not payload.body.strip(): fail("message_body_required", 422)
    existing = await db.web_message_events.find_one({"event_id": payload.event_id}, {"_id": 0})
    fingerprint = hashlib.sha256((payload.thread_id+"|"+payload.body).encode()).hexdigest()
    if existing and existing.get("fingerprint") != fingerprint: fail("message_event_conflict", 409)
    if not existing:
        from pymongo.errors import DuplicateKeyError
        try:
            await db.web_message_events.insert_one({"_id": payload.event_id, "event_id": payload.event_id, "fingerprint": fingerprint, "thread_id": payload.thread_id})
        except DuplicateKeyError:
            raced = await db.web_message_events.find_one({"_id": payload.event_id}, {"_id": 0})
            if not raced or raced.get("fingerprint") != fingerprint: fail("message_event_conflict", 409)
    now = datetime.now(timezone.utc).isoformat()
    await db.web_message_threads.update_one({"thread_id": payload.thread_id, "messages.event_id": {"$ne": payload.event_id}}, {"$push": {"messages": {"event_id": payload.event_id, "sender": "OPORTUNIIA", "body": payload.body.strip(), "at": now}}, "$set": {"state": "TEAM_REPLIED", "updated_at": now}})
    await db.web_notifications.update_one({"id": payload.event_id, "subject_id": thread["subject_id"]}, {"$setOnInsert": {"id": payload.event_id, "subject_id": thread["subject_id"], "title": "Tienes una respuesta de OPORTUNIIA", "body": "Consulta la respuesta en tu área privada.", "read": False, "created_at": now}}, upsert=True)
    await db.web_email_outbox.update_one({"_id": payload.event_id}, {"$setOnInsert": {"event_id": payload.event_id, "subject_id": thread["subject_id"], "thread_id": payload.thread_id,
        "purpose": "OPERATIONAL_ONLY", "state": "PENDING_EMAIL_PROVIDER", "email_sent": False, "created_at": now}}, upsert=True)
    return {"saved": True, "idempotent": bool(existing), "email_sent": False, "delivery_state": "PENDING_EMAIL_PROVIDER"}
