"""Owner-only notification summary and proactive pending Premium cancellation.

No private document metadata, receipt details, email addresses or legal-case
references are returned. PENDING opt-out cancellation never affects essential
offer notices. Claimed notices still require final live revalidation.
"""
from __future__ import annotations
from datetime import datetime,timezone
from fastapi import HTTPException

OPTIONAL=("PREMIUM_DOCUMENT_REVIEW","PREMIUM_PAYROLL_REMINDER")
VIEW_STATES=("PENDING","CLAIMED","CANCELLED","SENT","RECONCILE")
PUBLIC_STATES={"PENDING":"PENDIENTE","CLAIMED":"EN_PROCESO",
               "CANCELLED":"CANCELADO","SENT":"PROCESADO",
               "RECONCILE":"EN_REVISION"}
PUBLIC_LABELS={"OFFER_DOCUMENT_DEADLINE":"Plazo documental de oferta",
               "PREMIUM_DOCUMENT_REVIEW":"Revisión documental Premium",
               "PREMIUM_PAYROLL_REMINDER":"Aviso de agenda Premium"}


async def list_my_notices(db,actor,*,limit=30):
    if not actor or not actor.get("actor_id"):
        raise HTTPException(401,"Sesión necesaria")
    if type(limit) is not int or not 1<=limit<=50:
        raise HTTPException(422,"Límite inválido")
    cursor=db.mi_notification_outbox.find({
        "actor_id":actor["actor_id"],"state":{"$in":list(VIEW_STATES)},
        "kind":{"$in":list(PUBLIC_LABELS)},
    },{"_id":0,"kind":1,"state":1,"created_at":1}).sort("created_at",-1).limit(limit)
    rows=[]
    async for item in cursor:
        if item.get("kind") in PUBLIC_LABELS and item.get("state") in PUBLIC_STATES:
            rows.append({"title":PUBLIC_LABELS[item["kind"]],
                         "status":PUBLIC_STATES[item["state"]],
                         "created_at":item.get("created_at"),
                         "is_optional":item["kind"] in OPTIONAL})
    return rows


async def cancel_pending_optional(db,*,actor_id,now,signal_id=None,file_id=None):
    """Only queued optional notices; claimed ones remain guarded by revalidation."""
    if not isinstance(actor_id,str) or not actor_id.startswith("mi_"):
        raise ValueError("owner required")
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise ValueError("aware cancellation time required")
    if signal_id is not None and file_id is not None:
        raise ValueError("mutually exclusive scope")
    query={"actor_id":actor_id,"state":"PENDING","kind":{"$in":list(OPTIONAL)}}
    if signal_id is not None:
        query["kind"]="PREMIUM_PAYROLL_REMINDER"
        query["signal_id"]=signal_id
    if file_id is not None:
        query["kind"]="PREMIUM_DOCUMENT_REVIEW"
        query["file_id"]=file_id
    result=await db.mi_notification_outbox.update_many(query,{"$set":{
        "state":"CANCELLED","cancel_reason":"OPT_OUT",
        "cancelled_at":now.astimezone(timezone.utc),
    }})
    return result.modified_count
