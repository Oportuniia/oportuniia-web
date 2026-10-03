"""Sandbox authenticated, consent-driven extraction/confirmation of secretary signals.

Requires Premium gate and owner-scoped antivirus-CLEAN PDF. No raw document
text is persisted: proposals contain only approved scalar suggestions,
source SHA and 20-minute expiry. No calendars or messages are activated here.
"""
from __future__ import annotations
import asyncio
import secrets
from datetime import datetime, timedelta, timezone

import fitz
from fastapi import HTTPException
from pymongo import ReturnDocument

from mi_ocr import MAX_OCR_PAGES, text_for_page
from mi_personalized_secretary import suggest_document_signals, confirm_secretary_signal
from mi_premium_service import require_premium, _scanned_pdf

PROPOSAL_TTL=timedelta(minutes=20)


def extract_proposals(pdf: bytes, *, kind: str, file_id: str):
    """Local bounded text/OCR; never send source material to external AI."""
    if kind not in {"NOMINA","RENTA"}:
        return []
    document=fitz.open(stream=pdf,filetype="pdf")
    try:
        if document.needs_pass or document.page_count > 20:
            raise ValueError("Documento no elegible para análisis contextual")
        proposals=[]
        budget={"remaining":MAX_OCR_PAGES}
        for page in document:
            text,_=text_for_page(page,budget=budget)
            if text:
                proposals.extend(suggest_document_signals(
                    text[:40000],document_kind=kind,file_id=file_id))
        # Avoid multiple suggestions of the same kind from multi-page PDFs:
        # show first candidate; user must confirm any periodic recurrence.
        return list({p["kind"]:p for p in reversed(proposals)}.values())
    finally:
        document.close()


async def preview_signals(db,actor,*,file_id:str,analysis_consent:bool):
    if analysis_consent is not True:
        raise HTTPException(422,"Debes autorizar expresamente este análisis")
    await require_premium(db,actor)
    raw,row,_,_,_=await _scanned_pdf(db,actor,file_id)
    kind=row.get("document_kind")
    if kind not in {"NOMINA","RENTA"}:
        raise HTTPException(422,"Solo se admiten nóminas y declaraciones clasificadas")
    try:
        candidates=await asyncio.to_thread(
            extract_proposals,raw,kind=kind,file_id=file_id)
    except ValueError as exc:
        raise HTTPException(422,"No ha sido posible analizar el documento") from exc
    now=datetime.now(timezone.utc)
    token=secrets.token_hex(20)
    expiry=now+PROPOSAL_TTL
    await db.mi_secretary_proposals.insert_one({
        "proposal_id":token,"actor_id":actor["actor_id"],
        "file_id":file_id,"source_sha256":row["sha256"],
        "state":"PENDING","candidates":candidates,
        "expires_at":expiry,"created_at":now,
        "consent_at":now,
    })
    return {"proposal_id":token,"expires_at":expiry,
            "candidates":candidates,"requires_confirmation":True}


async def confirm_proposal(db,actor,*,proposal_id:str,kind:str,value):
    await require_premium(db,actor)
    now=datetime.now(timezone.utc)
    if not isinstance(proposal_id,str) or len(proposal_id)!=40:
        raise HTTPException(404,"Propuesta no encontrada")
    proposal=await db.mi_secretary_proposals.find_one({
        "proposal_id":proposal_id,"actor_id":actor["actor_id"],
        "state":"PENDING","expires_at":{"$gt":now},
    })
    if not proposal:
        raise HTTPException(404,"Propuesta caducada o no encontrada")
    source=await db.mi_user_files.find_one({
        "actor_id":actor["actor_id"],"file_id":proposal["file_id"],
        "status":"AVAILABLE","scan_verdict":"CLEAN",
        "sha256":proposal["source_sha256"],
    })
    if not source:
        raise HTTPException(409,"El documento ha cambiado o ya no está disponible")
    candidate=next((c for c in proposal["candidates"] if c["kind"]==kind),None)
    if not candidate:
        raise HTTPException(422,"Selecciona una propuesta válida")
    try:
        confirmed=confirm_secretary_signal(
            actor_id=actor["actor_id"],candidate=candidate,
            value=value,confirmed_at=now,
        )
    except (ValueError,TypeError):
        raise HTTPException(422,"Confirma un valor válido") from None
    # Atomic claim prevents duplicate confirmation by concurrent sessions.
    claimed=await db.mi_secretary_proposals.find_one_and_update(
        {"proposal_id":proposal_id,"actor_id":actor["actor_id"],
         "state":"PENDING","expires_at":{"$gt":now},
         "source_sha256":proposal["source_sha256"]},
        {"$set":{"state":"CONFIRMED","confirmed_at":now}},
        return_document=ReturnDocument.AFTER,
    )
    if not claimed:
        raise HTTPException(409,"La propuesta ya se ha utilizado")
    confirmed["signal_id"]=secrets.token_hex(16)
    confirmed["proposal_id"]=proposal_id
    # Still no recurring event until an independent scheduling consent.
    confirmed["calendar_enabled"]=False
    await db.mi_secretary_signals.insert_one(confirmed)
    return {"signal_id":confirmed["signal_id"],"kind":kind,
            "confirmed_value":confirmed["confirmed_value"],
            "calendar_enabled":False}


async def list_confirmed_signals(db,actor):
    await require_premium(db,actor)
    cursor=db.mi_secretary_signals.find(
        {"actor_id":actor["actor_id"],"active":True},
        {"_id":0,"signal_id":1,"kind":1,"confirmed_value":1,
         "calendar_enabled":1,"owner_confirmed_at":1},
    ).limit(50)
    return [row async for row in cursor]
