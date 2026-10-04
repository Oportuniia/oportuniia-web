"""SANDBOX-only APP ↔ WEB HTTP bridge. Never enable with real third-party PII before LEGAL."""
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ConfigDict

router=APIRouter(prefix="/api/integrations/oportuniiapp/v1",include_in_schema=False)
STATES={"WEB_CHECK_PENDING","INDEX_UNAVAILABLE","DUPLICATE_BLOCKED","INVESTOR_VERIFICATION_PENDING","HUMAN_REVIEW_PENDING","APPROVED_WITH_WEB_CODE","REJECTED"}

class Intake(BaseModel):
    model_config=ConfigDict(extra="forbid")
    schema_version:str="1"
    app_event_id:str=Field(min_length=8,max_length=128)
    app_report_id:str=Field(min_length=1,max_length=128)
    app_subject:str=Field(min_length=1,max_length=128)
    # No third-party identity fields accepted while legal gate is closed.
    investor_email:str|None=None
    investor_phone:str|None=None
    consent_evidence_ref:str|None=None

def _authorize(request,subject=None):
    secret=os.getenv("WEB_APP_N8N_ORCHESTRATOR_KEY","")
    supplied=request.headers.get("x-oportuniia-web-app-m2m-key","")
    if not secret or not hmac.compare_digest(supplied,secret):
        raise HTTPException(401,"Service authentication required")
    bound=request.headers.get("x-app-subject","")
    if not bound or (subject is not None and not hmac.compare_digest(bound,subject)):
        raise HTTPException(403,"Subscriber scope mismatch")
    return bound

def _payload_hash(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def register_routes(db):
    r=APIRouter()
    @r.post("/api/integrations/oportuniiapp/v1/referral-intakes",status_code=202)
    async def intake(request:Request,body:Intake):
        subject=_authorize(request,body.app_subject)
        if os.getenv("WEB_APP_LEGAL_THIRD_PARTY_CONTACTS_ENABLED")!="1":
            if body.investor_email or body.investor_phone or body.consent_evidence_ref:
                raise HTTPException(423,"Third-party contact capture not legally authorized")
        key=request.headers.get("idempotency-key","")
        if not (8<=len(key)<=128):
            raise HTTPException(422,"Stable idempotency key required")
        doc=body.model_dump()
        digest=_payload_hash(doc)
        ident=hashlib.sha256((subject+"\0"+key).encode()).hexdigest()
        # No live identity indexes have been authorized: hold all intakes fail-closed.
        status="INDEX_UNAVAILABLE"
        try:
            await db.app_web_intakes.insert_one({"_id":ident,"app_subject":subject,"digest":digest,
                "app_event_id":body.app_event_id,"app_report_id":body.app_report_id,
                "status":status,"created_at":datetime.now(timezone.utc)})
        except Exception as exc:
            from pymongo.errors import DuplicateKeyError
            if not isinstance(exc,DuplicateKeyError):
                raise HTTPException(503,"Sandbox storage unavailable")
            existing=await db.app_web_intakes.find_one({"_id":ident})
            if not existing or existing["app_subject"]!=subject or existing["digest"]!=digest:
                raise HTTPException(409,"Idempotency key reused with different payload")
            status=existing["status"]
        return {"schema_version":"1","intake_id":ident,"status":status,"retryable":status=="INDEX_UNAVAILABLE"}
    @r.get("/api/integrations/oportuniiapp/v1/referral-intakes/{intake_id}")
    async def follow_up(intake_id:str,request:Request):
        subject=_authorize(request)
        item=await db.app_web_intakes.find_one({"_id":intake_id,"app_subject":subject})
        if not item:
            raise HTTPException(404,"Not found")
        return {"schema_version":"1","intake_id":intake_id,"status":item["status"],
                "retryable":item["status"]=="INDEX_UNAVAILABLE"}
    @r.get("/api/integrations/oportuniiapp/v1/subscriber-portfolio")
    async def portfolio(request:Request):
        subject=_authorize(request)
        # Fail closed unless an independently approved APP↔WEB link is recorded.
        link=await db.app_web_subscriber_links.find_one({"app_subject":subject,"approved":True,
                                                          "membership_active":True})
        if not link:
            raise HTTPException(403,"Approved subscriber link required")
        # Financial projection intentionally empty until verified source adapters exist.
        return {"schema_version":"1","web_referrer_code":link["web_referrer_code"],
                "investors":[],"earnings":[],"sync_status":"SOURCE_ADAPTER_PENDING"}
    return r
