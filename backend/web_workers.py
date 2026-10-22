"""Existing orchestrator can invoke these once-only tasks; no new scheduler.
No task ever approves identity/PBC or operation permissions.
"""
import asyncio
import hashlib
import ipaddress
import os
import socket
import struct
from datetime import datetime, timedelta, timezone

from pymongo import ReturnDocument

from web_identity import send_transactional, mail_ready, public_origin
from web_workspace import s3_client, MAX_BYTES, storage_ready


async def dispatch_email_once(db):
    if not mail_ready(): return {"processed": False, "reason": "MAIL_NOT_CONFIGURED"}
    stamp = datetime.now(timezone.utc)
    row = await db.web_email_outbox.find_one_and_update({"state": {"$in": ["PENDING_EMAIL_PROVIDER", "PENDING_RETRY"]}, "$or": [{"next_attempt": {"$exists": False}}, {"next_attempt": {"$lte": stamp}}]},
        {"$set": {"state": "SENDING", "claimed_at": stamp}, "$inc": {"attempts": 1}}, return_document=ReturnDocument.AFTER)
    if not row: return {"processed": False}
    user = await db.web_users.find_one({"subject_id": row["subject_id"], "active": True, "email_verified": True}, {"_id": 0})
    prefs = await db.web_workspace_settings.find_one({"subject_id": row["subject_id"]}, {"_id": 0}) or {}
    if not user or prefs.get("email_copies") is False:
        await db.web_email_outbox.update_one({"_id": row["_id"]}, {"$set": {"state": "SKIPPED_ACCOUNT_OR_PREFERENCE"}})
        return {"processed": True, "submitted": False}
    try:
        # Never copy judicial/personal documents into SMTP. Link to the protected inbox.
        await send_transactional(user["email"], "Tienes una respuesta · OPORTUNIIA", "Tienes una nueva respuesta del equipo en MI OPORTUNIIA.\n\n"+public_origin()+"/mi-oportuniia#notificaciones\n\nEste aviso es operativo y corresponde a tu relación con OPORTUNIIA.")
    except Exception:
        await db.web_email_outbox.update_one({"_id": row["_id"]}, {"$set": {"state": "PENDING_RETRY" if row["attempts"] < 5 else "NEEDS_MANUAL_REVIEW", "next_attempt": stamp+timedelta(minutes=20)}})
        return {"processed": True, "submitted": False}
    await db.web_email_outbox.update_one({"_id": row["_id"]}, {"$set": {"state": "SUBMITTED_TO_SMTP", "submitted_at": stamp, "email_sent": True}})
    # SMTP acceptance is not a delivery receipt. A crashed SENDING claim is reviewed,
    # never blindly resent; this prevents an automatic duplicate after ambiguous send.
    return {"processed": True, "submitted": True}


def scan_bytes(data):
    host = os.getenv("WEB_CLAMAV_PRIVATE_HOST", "")
    if not host: raise RuntimeError("scanner_not_configured")
    addresses = socket.getaddrinfo(host, int(os.getenv("WEB_CLAMAV_PORT", "3310")), type=socket.SOCK_STREAM)
    address = next((a[4][0] for a in addresses if ipaddress.ip_address(a[4][0]).is_private), None)
    if not address: raise RuntimeError("scanner_must_use_private_network")
    with socket.create_connection((address, int(os.getenv("WEB_CLAMAV_PORT", "3310"))), timeout=30) as connection:
        connection.sendall(b"zINSTREAM\0")
        for i in range(0, len(data), 65536):
            part = data[i:i+65536]
            connection.sendall(struct.pack("!I", len(part))+part)
        connection.sendall(struct.pack("!I", 0))
        response = b""
        while b"\0" not in response and len(response) < 4096:
            part = connection.recv(4096)
            if not part: break
            response += part
    if response.rstrip(b"\0") == b"stream: OK": return "CLEAN"
    if response.rstrip(b"\0").endswith(b" FOUND"): return "INFECTED"
    raise RuntimeError("scanner_did_not_confirm_result")


async def scan_document_once(db):
    if not storage_ready() or not os.getenv("WEB_CLAMAV_PRIVATE_HOST"): return {"processed": False, "reason": "SCANNER_OR_STORAGE_NOT_CONFIGURED"}
    row = await db.web_personal_documents.find_one_and_update({"scan_state": "QUARANTINED"}, {"$set": {"scan_state": "SCANNING"}}, return_document=ReturnDocument.AFTER)
    if not row: return {"processed": False}
    try:
        from web_personal_storage import read
        data = await asyncio.to_thread(read, row)
        state = await asyncio.to_thread(scan_bytes, data)
    except Exception: state = "SCAN_FAILED"
    await db.web_personal_documents.update_one({"_id": row["_id"], "scan_state": "SCANNING"}, {"$set": {"scan_state": state, "scanned_at": datetime.now(timezone.utc)}})
    return {"processed": True, "scan_state": state}


def register_worker_routes(router, db):
    from fastapi import Request
    import hmac
    @router.post("/m2m/maintenance/run")
    async def run(request: Request):
        expected = os.getenv("WEB_WORKER_M2M_KEY", "")
        supplied = request.headers.get("X-OPP-Worker-Key", "")
        from investor_access import fail
        if len(expected) < 40: fail("maintenance_not_configured", 503)
        if not supplied or not hmac.compare_digest(supplied, expected): fail("invalid_maintenance_authority", 401)
        return {"mail": await dispatch_email_once(db), "scan": await scan_document_once(db)}
