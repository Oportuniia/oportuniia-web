"""Direct-to-S3 quarantine. Only a server-verified, version-bound scan can promote bytes.

No document bytes reach WEB or R2 until GuardDuty reports NO_THREATS_FOUND.
The application credential must not have PutObjectTagging permissions.
"""
import asyncio
import base64
import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from investor_access import authenticated_subject, fail
import web_personal_storage as storage

MAX_BYTES = 20 * 1024 * 1024
MIMES = {"application/pdf": "pdf", "image/png": "png", "image/jpeg": "jpg"}
CATEGORIES = {"identity", "representative_identity", "company_representation", "company_tax_document"}


def configured():
    return os.getenv("WEB_SCAN_MODE") == "guardduty-s3" and storage.ready() and all(
        os.getenv(k) for k in ("WEB_QUARANTINE_BUCKET", "WEB_QUARANTINE_REGION",
                              "WEB_QUARANTINE_ACCESS_KEY_ID", "WEB_QUARANTINE_SECRET_ACCESS_KEY"))


def client():
    import boto3
    from botocore.config import Config
    return boto3.client("s3", region_name=os.environ["WEB_QUARANTINE_REGION"],
                        aws_access_key_id=os.environ["WEB_QUARANTINE_ACCESS_KEY_ID"],
                        aws_secret_access_key=os.environ["WEB_QUARANTINE_SECRET_ACCESS_KEY"],
                        config=Config(signature_version="s3v4", connect_timeout=10, read_timeout=30,
                                      retries={"max_attempts": 2}))


class UploadIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: str
    mime: str
    size: int = Field(gt=0, le=MAX_BYTES)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    filename: str = Field(default="", max_length=240)


def signed_upload(row):
    checksum = base64.b64encode(bytes.fromhex(row["sha256"])).decode()
    fields = {"Content-Type": row["mime"], "x-amz-checksum-algorithm": "SHA256",
              "x-amz-checksum-sha256": checksum, "success_action_status": "204"}
    conditions = [{key: value} for key, value in fields.items()]
    conditions.append(["content-length-range", row["size"], row["size"]])
    return client().generate_presigned_post(row["quarantine_bucket"], row["quarantine_key"],
                                            Fields=fields, Conditions=conditions, ExpiresIn=300)


def inspect_scan(row):
    s3 = client()
    location = {"Bucket": row["quarantine_bucket"], "Key": row["quarantine_key"]}
    if row.get("quarantine_version"):
        location["VersionId"] = row["quarantine_version"]
    result = s3.get_object_tagging(**location)
    version = result.get("VersionId")
    if not version or version == "null":
        raise ValueError("quarantine_versioning_required")
    tags = result["TagSet"]
    verdict = next((tag["Value"] for tag in tags if tag["Key"] == "GuardDutyMalwareScanStatus"), None)
    state = {"NO_THREATS_FOUND": "CLEAN", "THREATS_FOUND": "INFECTED",
                     "UNSUPPORTED": "REJECTED", "ACCESS_DENIED": "SCAN_FAILED",
                     "FAILED": "SCAN_FAILED"}.get(verdict, "QUARANTINED")
    if state == "CLEAN":
        head = s3.head_object(**{**location, "VersionId": version})
        if head["ContentLength"] != row["size"] or head.get("ContentType") != row["mime"]:
            return version, "REJECTED"
    return version, state


def promote(row):
    # Recheck the exact version immediately before reading, never read the latest key.
    version, verdict = inspect_scan(row)
    if verdict != "CLEAN" or version != row["quarantine_version"]:
        raise ValueError("scan_not_clean")
    response = client().get_object(Bucket=row["quarantine_bucket"], Key=row["quarantine_key"], VersionId=version)
    stream = response["Body"]
    try:
        data = stream.read(MAX_BYTES + 1)
    finally:
        stream.close()
    if len(data) != row["size"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise ValueError("quarantine_integrity_failure")
    from web_workspace import file_type
    if file_type(data)[0] != row["mime"]:
        raise ValueError("document_type_mismatch")
    storage.write(data, row)
    try:
        from web_document_preview import prepare
        row['private_preview'] = prepare(data, row)
    except Exception:
        # A missing preview never blocks the intact original or grants access.
        pass
    return row


def register_quarantine_routes(router, db):
    @router.post("/investor/personal-documents/upload-intent")
    async def create_intent(payload: UploadIntent, request: Request, subject: str = Depends(authenticated_subject)):
        if not configured(): fail("external_quarantine_not_configured", 503)
        if payload.category not in CATEGORIES or payload.mime not in MIMES: fail("unsupported_document", 415)
        from web_identity import rate_limit
        await rate_limit(db, request, "personal-upload", subject)
        from web_dossier import normalized
        stamp = datetime.now(timezone.utc)
        # A per-account atomic lease serializes duplicate and quota reservations.
        try:
            lease = await db.web_document_leases.find_one_and_update(
                {"_id": subject, "$or": [{"until": {"$lt": stamp}}, {"until": {"$exists": False}}]},
                {"$set": {"until": stamp + timedelta(minutes=5)}}, upsert=True, return_document=ReturnDocument.AFTER)
        except DuplicateKeyError:
            fail("upload_already_in_progress", 409)
        if not lease: fail("upload_already_in_progress", 409)
        existing = await db.web_personal_documents.find({"subject_id": subject, "deleted": {"$ne": True}}).to_list(101)
        filename = normalized(payload.filename)
        if any(d.get("sha256") == payload.sha256 or (filename and d.get("normalized_filename") == filename and d.get("dossier_state") != "QUALITY_REJECTED") for d in existing):
            await db.web_document_leases.update_one({"_id": subject}, {"$set": {"until": stamp}})
            fail("document_already_received", 409)
        if len(existing) >= 100 or sum(d.get("size", 0) for d in existing) + payload.size > 200 * 1024 * 1024:
            fail("document_storage_limit", 429)
        pending = await db.web_personal_documents.find({"subject_id": subject, "scan_state": {"$in": ["QUARANTINED", "PROMOTING"]},
            "upload_expires_at": {"$gt": datetime.now(timezone.utc)}}).to_list(10)
        if len(pending) >= 10: fail("too_many_pending_uploads", 429)
        ident, stamp = str(uuid.uuid4()), datetime.now(timezone.utc)
        row = {**payload.model_dump(), "document_id": ident, "subject_id": subject,
               "name": "Documento " + payload.category + "." + MIMES[payload.mime],
               "storage_key": "web-personal/approved/" + subject + "/" + ident,
               "quarantine_bucket": os.environ["WEB_QUARANTINE_BUCKET"], "quarantine_key": "incoming/" + ident,
               "scan_state": "QUARANTINED", "review_state": "PENDING", "created_at": stamp,
               "normalized_filename": filename, "dossier_state": "AWAITING_CONFIRMATION", "operational_evidence": False,
               "upload_expires_at": stamp + timedelta(minutes=5), "scan_provider": "AWS_GUARDDUTY"}
        upload = await asyncio.to_thread(signed_upload, row)
        await db.web_personal_documents.insert_one(row)
        await db.web_document_leases.update_one({"_id": subject}, {"$set": {"until": stamp}})
        return {"document_id": ident, "upload": upload, "scan_state": "QUARANTINED"}

    @router.post("/investor/personal-documents/{document_id}/scan-status")
    async def scan_status(document_id: str, subject: str = Depends(authenticated_subject)):
        if not configured(): fail("external_quarantine_not_configured", 503)
        row = await db.web_personal_documents.find_one({"document_id": document_id, "subject_id": subject, "deleted": {"$ne": True}})
        if not row or row.get("scan_provider") != "AWS_GUARDDUTY": fail("document_not_found", 404)
        return await reconcile_document(db, row)


async def reconcile_document(db, row):
    document_id = row["document_id"]
    await db.web_personal_documents.update_one({"_id": row["_id"]}, {"$set": {"scan_checked_at": datetime.now(timezone.utc)}})
    if row["scan_state"] in {"CLEAN", "INFECTED", "REJECTED", "SCAN_FAILED"}:
        return {"document_id": document_id, "scan_state": row["scan_state"], "review_state": "PENDING"}
    try:
        version, state = await asyncio.to_thread(inspect_scan, row)
    except Exception:
        # Missing upload and transient AWS failures never grant access.
        return {"document_id": document_id, "scan_state": "QUARANTINED", "review_state": "PENDING"}
    if not row.get("quarantine_version"):
        await db.web_personal_documents.update_one({"_id": row["_id"], "quarantine_version": {"$exists": False}}, {"$set": {"quarantine_version": version}})
        row = await db.web_personal_documents.find_one({"_id": row["_id"]})
        if row["quarantine_version"] != version:
            return {"document_id": document_id, "scan_state": "QUARANTINED", "review_state": "PENDING"}
    if state == "CLEAN":
        stamp, claim = datetime.now(timezone.utc), str(uuid.uuid4())
        claimed = await db.web_personal_documents.find_one_and_update({"_id": row["_id"], "$or": [
            {"scan_state": "QUARANTINED"}, {"scan_state": "PROMOTING", "promotion_until": {"$lt": stamp}}]},
            {"$set": {"scan_state": "PROMOTING", "promotion_claim": claim, "promotion_until": stamp + timedelta(minutes=5)}},
            return_document=ReturnDocument.AFTER)
        if not claimed: return {"document_id": document_id, "scan_state": "QUARANTINED", "review_state": "PENDING"}
        try:
            promoted = await asyncio.to_thread(promote, claimed)
        except Exception:
            await db.web_personal_documents.update_one({"_id": row["_id"], "promotion_claim": claim}, {"$set": {"scan_state": "QUARANTINED"}})
            return {"document_id": document_id, "scan_state": "QUARANTINED", "review_state": "PENDING"}
        values = {k: promoted[k] for k in ("storage_backend", "storage_bucket", "encryption_key_id", "private_preview") if k in promoted}
        values.update(scan_state="CLEAN", scanned_at=stamp)
        saved = await db.web_personal_documents.update_one({"_id": row["_id"], "promotion_claim": claim}, {"$set": values})
        if not saved.matched_count:
            return {"document_id": document_id, "scan_state": "QUARANTINED", "review_state": "PENDING"}
    elif state != "QUARANTINED":
        await db.web_personal_documents.update_one({"_id": row["_id"], "scan_state": "QUARANTINED"}, {"$set": {"scan_state": state}})
    return {"document_id": document_id, "scan_state": state, "review_state": "PENDING"}


async def reconcile_pending(db):
    rows = await db.web_personal_documents.find({
        "scan_provider": "AWS_GUARDDUTY", "deleted": {"$ne": True},
        "scan_state": {"$in": ["QUARANTINED", "PROMOTING"]},
    }).sort("scan_checked_at", 1).to_list(50)
    for row in rows:
        try:
            await reconcile_document(db, row)
        except Exception:
            # Failure remains pending; a later pass resumes from persisted state.
            continue
    return len(rows)


async def quarantine_worker(db):
    while True:
        try:
            await reconcile_pending(db)
            from web_dossier import expire_temporary
            await expire_temporary(db)
            from web_review_mail import sync_received
            await sync_received(db)
            from web_digest import tick
            await tick(db)
        except Exception:
            pass
        await asyncio.sleep(30)
