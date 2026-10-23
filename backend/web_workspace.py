"""Private workspace persistence. Every record is scoped to the server session.
Uploaded files remain quarantined until an independent scanner marks them clean.
No public URL, browser role or filename is accepted as storage authority.
"""
import asyncio
import base64
import hashlib
import io
import os
import uuid
from datetime import datetime, timezone

from fastapi import Depends, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from investor_access import authenticated_subject, context, fail

MAX_BYTES = 20 * 1024 * 1024
CATEGORIES = {"identity", "representative_identity", "company_representation", "company_tax_document"}


from web_personal_storage import ready as storage_ready, client as s3_client
import web_personal_storage


def upload_ready():
    if os.getenv("WEB_SCAN_MODE") == "guardduty-s3":
        from web_quarantine import configured
        return bool(configured())
    return bool(storage_ready())


def file_type(data):
    if data.startswith(b"%PDF-"): return "application/pdf", "pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"): return "image/png", "png"
    if data.startswith(b"\xff\xd8\xff"): return "image/jpeg", "jpg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP": return "image/webp", "webp"
    fail("unsupported_document", 415)


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email_copies: bool = True
    operation_alerts: bool = True


class Photo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data_url: str = Field(max_length=500000)


def register_workspace_routes(router, db):
    @router.get("/investor/workspace")
    async def workspace(subject: str = Depends(authenticated_subject)):
        draft = await db.web_profile_drafts.find_one({"subject_id": subject}, {"_id": 0}) or {}
        settings = await db.web_workspace_settings.find_one({"subject_id": subject}, {"_id": 0}) or {}
        documents = await db.web_personal_documents.find({"subject_id": subject, "deleted": {"$ne": True}}, {"_id": 0, "document_id": 1, "category": 1, "name": 1, "scan_state": 1, "review_state": 1, "size": 1}).to_list(100)
        notifications = await db.web_notifications.find({"subject_id": subject}, {"_id": 0, "id": 1, "title": 1, "body": 1, "read": 1, "created_at": 1}).sort("created_at", -1).to_list(100)
        operations = await db.web_investor_operations.find({"subject_id": subject}, {"_id": 0, "op_ref": 1, "status": 1, "created_at": 1}).to_list(100)
        return {"profile": draft.get("profile", {}), "profile_state": draft.get("state", "DRAFT"), "documents": documents,
            "preferences": {"email_copies": settings.get("email_copies", True), "operation_alerts": settings.get("operation_alerts", True)},
            "photo": settings.get("photo", ""), "notifications": notifications, "operations": operations, "uploads_enabled": upload_ready(),
            "upload_mode": "external-quarantine" if os.getenv("WEB_SCAN_MODE") == "guardduty-s3" else "legacy"}

    @router.post("/investor/preferences")
    async def preferences(payload: Preferences, subject: str = Depends(authenticated_subject)):
        await db.web_workspace_settings.update_one({"subject_id": subject}, {"$set": payload.model_dump()}, upsert=True)
        return {"saved": True}

    @router.post("/investor/photo")
    async def photo(payload: Photo, subject: str = Depends(authenticated_subject)):
        value = payload.data_url
        if value:
            try:
                # Normalize raster pixels; reject SVG, malformed files and oversized images.
                from PIL import Image
                prefix, encoded = value.split(",", 1)
                if prefix not in {"data:image/jpeg;base64", "data:image/png;base64", "data:image/webp;base64"}: raise ValueError()
                raw = base64.b64decode(encoded, validate=True)
                img = Image.open(io.BytesIO(raw))
                if img.width * img.height > 1_000_000: raise ValueError()
                img.load()
                img = img.convert("RGB")
                img.thumbnail((320, 320))
                output = io.BytesIO()
                img.save(output, "JPEG", quality=85)
                value = "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode()
            except Exception:
                fail("invalid_profile_photo", 422)
        await db.web_workspace_settings.update_one({"subject_id": subject}, {"$set": {"photo": value}}, upsert=True)
        return {"saved": True, "photo": value}

    @router.post("/investor/notifications/{notification_id}/read")
    async def read_notification(notification_id: str, subject: str = Depends(authenticated_subject)):
        result = await db.web_notifications.update_one({"subject_id": subject, "id": notification_id}, {"$set": {"read": True}})
        if not result.matched_count: fail("notification_not_found", 404)
        return {"saved": True}

    @router.post("/investor/personal-documents")
    async def upload(request: Request, category: str = Form(...), file: UploadFile = File(...), subject: str = Depends(authenticated_subject)):
        if os.getenv("WEB_SCAN_MODE") == "guardduty-s3": fail("direct_quarantine_upload_required", 409)
        if not storage_ready(): fail("private_document_storage_not_activated", 503)
        from web_identity import rate_limit
        await rate_limit(db, request, "personal-upload")
        if category not in CATEGORIES: fail("invalid_document_category", 422)
        parts, size = [], 0
        while part := await file.read(1024 * 1024):
            size += len(part)
            if size > MAX_BYTES: fail("document_too_large", 413)
            parts.append(part)
        data = b"".join(parts)
        mime, suffix = file_type(data)
        if file.content_type != mime: fail("document_type_mismatch", 415)
        ident = str(uuid.uuid4())
        # Server-chosen key, no user-supplied storage paths or original filenames.
        key = "web-personal/quarantine/" + subject + "/" + ident + "." + suffix
        checksum = hashlib.sha256(data).hexdigest()
        row = {"document_id": ident, "subject_id": subject, "category": category, "name": "Documento " + category + "." + suffix,
            "size": size, "mime": mime, "storage_key": key, "sha256": checksum, "scan_state": "QUARANTINED", "review_state": "PENDING", "created_at": datetime.now(timezone.utc)}
        try:
            await asyncio.to_thread(web_personal_storage.write, data, row)
        except Exception:
            fail("private_document_storage_unavailable", 503)
        await db.web_personal_documents.insert_one(row)
        return {"document_id": ident, "category": category, "size": size, "scan_state": "QUARANTINED", "review_state": "PENDING", "access_granted": False}

    @router.get("/investor/personal-documents/{document_id}")
    async def own_document(document_id: str, subject: str = Depends(authenticated_subject)):
        return await stream_personal_document(db, subject, document_id, subject)


async def stream_personal_document(db, subject, document_id, actor):
    row = await db.web_personal_documents.find_one({"document_id": document_id, "subject_id": subject, "deleted": {"$ne": True}}, {"_id": 0})
    if not row: fail("document_not_found", 404)
    if row.get("scan_state") != "CLEAN": fail("document_awaiting_security_scan", 409)
    if not storage_ready(): fail("private_document_storage_not_activated", 503)
    try:
        data = await asyncio.to_thread(web_personal_storage.read, row)
    except Exception:
        fail("document_integrity_or_storage_error", 502)
    await db.web_security_audit.insert_one({"subject_id": subject, "actor_subject_id": actor, "event": "PERSONAL_DOCUMENT_READ", "document_id": document_id, "at": datetime.now(timezone.utc)})
    return StreamingResponse(io.BytesIO(data), media_type=row["mime"], headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff", "Content-Disposition": "attachment; filename=\"documento-personal\""})
