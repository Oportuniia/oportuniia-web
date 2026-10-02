"""Private R2 document upload and verification workflow.

Each action is scoped to the independently authenticated WEB actor. Raw uploads
stay PENDING until server-side size, magic signature, SHA-256 and ClamAV checks
have completed. This module is disabled unless explicitly configured.
"""
from __future__ import annotations
import asyncio
import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from personal_document_storage import PersonalFileScope, new_upload, _r2, _scope

MAX_FILE_BYTES = 25 * 1024 * 1024
MIMES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


def _enabled():
    if os.getenv("MI_PRIVATE_FILES_ENABLED") != "1":
        raise HTTPException(503, "Archivo privado pendiente de activación")


def _magic_valid(data, mime):
    checks = {
        "application/pdf": data.startswith(b"%PDF-"),
        "image/jpeg": data.startswith(b"\\xff\\xd8\\xff"),
        "image/png": data.startswith(b"\\x89PNG\\r\\n\\x1a\\n"),
        "image/webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
    }
    return checks.get(mime, False)


def _virus_scan(raw):
    """Requires independently provisioned ClamAV; failure denies availability."""
    import clamd
    host = os.getenv("MI_CLAMD_HOST", "").strip()
    if not host:
        raise RuntimeError("Antivirus no configurado")
    port = int(os.getenv("MI_CLAMD_PORT", "3310"))
    scanner = clamd.ClamdNetworkSocket(host=host, port=port, timeout=30)
    if not scanner.ping():
        raise RuntimeError("Antivirus no disponible")
    result = scanner.instream(raw)
    if not result:
        return True
    return all(value[0] == "OK" for value in result.values())


async def upload_intent(db, actor, *, name, mime, size):
    _enabled()
    if not actor or not actor.get("email_verified"):
        raise HTTPException(401, "Cuenta verificada necesaria")
    if mime not in MIMES or type(size) is not int or not 1 <= size <= MAX_FILE_BYTES:
        raise HTTPException(422, "Tipo o tamaño de documento no admitido")
    name = name.strip()
    if not 1 <= len(name) <= 120 or any(ord(c) < 32 or c in "/\\\\"
                                          for c in name):
        raise HTTPException(422, "Nombre de documento inválido")
    count = await db.mi_user_files.count_documents({"actor_id": actor["actor_id"]})
    if count >= 100:
        raise HTTPException(429, "Cuota documental alcanzada")
    reservation = await asyncio.to_thread(
        new_upload, PersonalFileScope(actor["actor_id"], True),
        mime=mime, size=size
    )
    now = datetime.now(timezone.utc)
    row = {
        "actor_id": actor["actor_id"], "file_id": reservation["file_id"],
        "storage_key": reservation["storage_key"], "mime": mime, "size": size,
        "display_name": name, "status": "PENDING", "scan_verdict": "PENDING",
        "created_at": now, "updated_at": now,
        "upload_expires": now + timedelta(seconds=reservation["expires_seconds"]),
    }
    await db.mi_user_files.insert_one(row)
    return {"file_id": reservation["file_id"],
            "upload_url": reservation["upload_url"],
            "expires_seconds": reservation["expires_seconds"]}


async def confirm_upload(db, actor, file_id):
    _enabled()
    if not re.fullmatch(r"[0-9a-f]{32}", file_id):
        raise HTTPException(404, "Documento no encontrado")
    now = datetime.now(timezone.utc)
    row = await db.mi_user_files.find_one_and_update(
        {"actor_id": actor["actor_id"], "file_id": file_id, "status": "PENDING",
         "upload_expires": {"$gt": now}},
        {"$set": {"status": "SCANNING", "updated_at": now}},
    )
    if not row:
        raise HTTPException(404, "Documento no encontrado o plazo agotado")
    try:
        expected_prefix = "personal/v1/" + _scope(
            PersonalFileScope(actor["actor_id"], True)) + "/" + file_id + "/"
        if row["storage_key"] != expected_prefix + "original":
            raise ValueError("Invalid namespace")
        client, bucket = _r2()
        obj = await asyncio.to_thread(client.get_object,
                                      Bucket=bucket, Key=row["storage_key"])
        try:
            raw = await asyncio.to_thread(obj["Body"].read, MAX_FILE_BYTES + 1)
        finally:
            obj["Body"].close()
        if len(raw) != row["size"] or not _magic_valid(raw[:16], row["mime"]):
            raise ValueError("Contenido no coincide con el documento declarado")
        clean = await asyncio.to_thread(_virus_scan, raw)
        if not clean:
            raise ValueError("El control antivirus ha rechazado el documento")
        sha = hashlib.sha256(raw).hexdigest()
        await db.mi_user_files.update_one(
            {"actor_id": actor["actor_id"], "file_id": file_id, "status": "SCANNING"},
            {"$set": {"status": "AVAILABLE", "scan_verdict": "CLEAN",
                      "sha256": sha, "updated_at": datetime.now(timezone.utc)}}
        )
        return {"file_id": file_id, "status": "AVAILABLE"}
    except Exception:
        # Fail closed even if the scanner or R2 is unavailable.
        await db.mi_user_files.update_one(
            {"actor_id": actor["actor_id"], "file_id": file_id, "status": "SCANNING"},
            {"$set": {"status": "QUARANTINED", "scan_verdict": "UNKNOWN",
                      "updated_at": datetime.now(timezone.utc)}}
        )
        raise HTTPException(422, "Documento pendiente de revisión de seguridad")
