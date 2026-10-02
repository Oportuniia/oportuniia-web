"""Premium-only organizer orchestration; no public file bytes, no cross-user read.

Enable only after private R2, malware scanning and entitlement subscription
source have been separately configured and verified in the WEB environment.
"""
from __future__ import annotations
import asyncio
import hashlib
import os
import secrets
from datetime import datetime, timezone
from fastapi import HTTPException
from personal_document_storage import PersonalFileScope, _scope, _r2
from mi_pdf_organizer import MAX_PDF_BYTES, inspect_pdf, split_reviewed_pdf
from mi_private_upload import _virus_scan


def _gate():
    if os.getenv("MI_ORGANIZER_ENABLED", "0") != "1":
        raise HTTPException(503, "Organizador Premium pendiente de activación")


async def require_premium(db, actor):
    _gate()
    if not actor or not actor.get("actor_id") or not actor.get("email_verified"):
        raise HTTPException(401, "Identidad WEB verificada necesaria")
    if actor.get("validation_state") != "VERIFIED":
        raise HTTPException(403, "Perfil pendiente de validación")
    now = datetime.now(timezone.utc)
    entitlement = await db.mi_premium_entitlements.find_one({
        "actor_id": actor["actor_id"], "status": "ACTIVE",
        "valid_from": {"$lte": now}, "expires_at": {"$gt": now},
        "source_verified": True,
    })
    if not entitlement:
        raise HTTPException(403, "Suscripción Premium vigente necesaria")


async def _scanned_pdf(db, actor, file_id):
    if not isinstance(file_id, str) or len(file_id) != 32 or any(c not in "0123456789abcdef" for c in file_id):
        raise HTTPException(404, "Documento no encontrado")
    row = await db.mi_user_files.find_one({
        "actor_id": actor["actor_id"], "file_id": file_id,
        "status": "AVAILABLE", "scan_verdict": "CLEAN",
        "mime": "application/pdf",
    })
    if not row:
        raise HTTPException(404, "Documento no disponible")
    key = row.get("storage_key", "")
    prefix = "personal/v1/" + _scope(PersonalFileScope(actor["actor_id"], True)) + "/" + file_id + "/"
    if key != prefix + "original":
        raise HTTPException(403, "Ubicación documental no autorizada")
    if not 1 <= row.get("size", 0) <= MAX_PDF_BYTES:
        raise HTTPException(413, "PDF fuera de límites")
    client, bucket = _r2()
    # Run blocking cloud I/O off the ASGI event loop.
    obj = await asyncio.to_thread(client.get_object, Bucket=bucket, Key=key)
    stream = obj["Body"]
    try:
        raw = await asyncio.to_thread(stream.read, MAX_PDF_BYTES + 1)
    finally:
        stream.close()
    if len(raw) > MAX_PDF_BYTES or len(raw) != row["size"]:
        raise HTTPException(413, "Tamaño del documento no coincide")
    if hashlib.sha256(raw).hexdigest() != row.get("sha256"):
        raise HTTPException(409, "Integridad documental no verificada")
    return raw, row, client, bucket, prefix


async def premium_inspect(db, actor, file_id):
    await require_premium(db, actor)
    raw, row, _, _, _ = await _scanned_pdf(db, actor, file_id)
    return await asyncio.to_thread(inspect_pdf, raw)


async def premium_confirm(db, actor, file_id, groups):
    await require_premium(db, actor)
    raw, row, client, bucket, prefix = await _scanned_pdf(db, actor, file_id)
    # Enforce current entitlement on every operation, not only when inspecting.
    outputs = await asyncio.to_thread(split_reviewed_pdf, raw, groups)
    # Every resulting PDF is independently antivirus-scanned before upload.
    # Scanner unavailability fails closed: no derivative becomes AVAILABLE.
    for output in outputs:
        try:
            clean = await asyncio.to_thread(_virus_scan, output["bytes"])
        except Exception as exc:
            raise HTTPException(503, "Antivirus de salida no disponible") from exc
        if not clean:
            raise HTTPException(422, "Un documento generado no ha superado el antivirus")
    job_id = secrets.token_hex(16)
    now = datetime.now(timezone.utc)
    saved = []
    for i, output in enumerate(outputs):
        derivative_id = secrets.token_hex(16)
        key = prefix + "derivatives/" + derivative_id
        data = output["bytes"]
        await asyncio.to_thread(
            client.put_object, Bucket=bucket, Key=key, Body=data,
            ContentType="application/pdf", ServerSideEncryption="AES256"
        )
        doc = {"actor_id": actor["actor_id"], "file_id": derivative_id,
               "original_file_id": file_id, "organizer_job_id": job_id,
               "storage_key": key, "display_name": output["kind"] + ".pdf",
               "document_kind": output["kind"], "mime": "application/pdf",
               "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
               "status": "AVAILABLE", "scan_verdict": "CLEAN",
               "pages": output["pages"], "created_at": now, "updated_at": now}
        await db.mi_user_files.insert_one(doc)
        saved.append({"file_id": derivative_id, "kind": output["kind"],
                      "pages": output["pages"], "status": "AVAILABLE"})
    return {"job_id": job_id, "files": saved, "original_preserved": True,
            "status": "available_after_security_scan"}
