"""Short-lived download grants for private WEB-owned files.

Look up by authenticated actor and ID before touching R2. Refuse pending,
quarantined, unreadable and mismatched keys. URL must never enter analytics.
"""
import asyncio
import re
from fastapi import HTTPException
from personal_document_storage import PersonalFileScope, _r2, _scope
from mi_private_upload import _enabled


async def signed_private_download(db, actor, file_id):
    _enabled()
    if not actor or not actor.get("email_verified"):
        raise HTTPException(401, "Sesión verificada necesaria")
    if not isinstance(file_id, str) or not re.fullmatch(r"[0-9a-f]{32}", file_id):
        raise HTTPException(404, "Documento no encontrado")
    row = await db.mi_user_files.find_one({
        "actor_id": actor["actor_id"], "file_id": file_id,
        "status": "AVAILABLE", "scan_verdict": "CLEAN",
    })
    if not row:
        raise HTTPException(404, "Documento no disponible")
    namespace = _scope(PersonalFileScope(actor["actor_id"], True))
    prefix = "personal/v1/" + namespace + "/"
    key = row.get("storage_key", "")
    original = prefix + file_id + "/original"
    parent = row.get("original_file_id", "")
    derivative = prefix + parent + "/derivatives/" + file_id
    if key != original and not (
        re.fullmatch(r"[0-9a-f]{32}", parent) and key == derivative
    ):
        raise HTTPException(403, "Ubicación documental no autorizada")
    client, bucket = _r2()
    url = await asyncio.to_thread(
        client.generate_presigned_url, "get_object",
        Params={"Bucket": bucket, "Key": key,
                "ResponseContentType": row.get("mime") or "application/octet-stream",
                "ResponseCacheControl": "no-store"},
        ExpiresIn=60, HttpMethod="GET",
    )
    return {"download_url": url, "expires_seconds": 60}
