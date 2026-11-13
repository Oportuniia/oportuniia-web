"""Durable, minimal review notices. No identity images or extracted text in email."""
from datetime import datetime, timedelta, timezone
from pymongo import ReturnDocument
from web_identity import send_transactional, public_origin

async def enqueue(db, subject, document_id):
    stamp = datetime.now(timezone.utc)
    doc = await db.web_personal_documents.find_one({"subject_id": subject, "document_id": document_id}) or {}
    event = "document:" + subject + ":" + doc.get("sha256", document_id)
    await db.web_review_requests.update_one({"_id": subject}, {"$set": {"subject_id": subject, "state": "PENDING", "updated_at": stamp}}, upsert=True)
    await db.web_review_mail.update_one({"_id": event}, {"$setOnInsert": {
        "subject_id": subject, "state": "PENDING", "created_at": stamp, "attempts": 0}}, upsert=True)

async def sync_received(db):
    rows = await db.web_personal_documents.find({"scan_state": "CLEAN", "deleted": {"$ne": True},
        "review_state": {"$ne": "APPROVED"}, "review_notice_queued": {"$ne": True},
        "dossier_state": {"$nin": ["QUALITY_REJECTED", "TEMPORARY", "EXPIRED"]}}).to_list(20)
    for row in rows:
        await enqueue(db, row["subject_id"], row["document_id"])
        await db.web_personal_documents.update_one({"_id": row["_id"]}, {"$set": {"review_notice_queued": True}})

async def dispatch(db):
    stamp = datetime.now(timezone.utc)
    row = await db.web_review_mail.find_one_and_update({"state": {"$in": ["PENDING", "RETRY"]},
        "$or": [{"next_attempt": {"$exists": False}}, {"next_attempt": {"$lte": stamp}}]},
        {"$set": {"state": "SENDING", "claimed_at": stamp}, "$inc": {"attempts": 1}}, return_document=ReturnDocument.AFTER)
    if not row: return False
    try:
        await send_transactional("info@oportuniia.com", "Documentación recibida · Revisión OPORTUNIIA",
            "Hay documentación nueva pendiente de revisión en Mi OPORTUNIIA.\n\n"
            "Accede con tu cuenta de revisor y verificación en dos pasos:\n" + public_origin() +
            "/revision-cuentas.html#" + row["subject_id"] +
            "\n\nEl correo no contiene documentos ni datos de identidad. La revisión se realiza dentro del área protegida.")
    except Exception:
        await db.web_review_mail.update_one({"_id": row["_id"]}, {"$set": {
            "state": "RETRY" if row["attempts"] < 5 else "NEEDS_ATTENTION", "next_attempt": stamp + timedelta(minutes=5)}})
        return False
    await db.web_review_mail.update_one({"_id": row["_id"]}, {"$set": {"state": "SUBMITTED", "submitted_at": stamp}})
    return True
