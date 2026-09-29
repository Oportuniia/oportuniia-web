"""PRESENTACIÓN → WEB consumer.

Consumes PRESENTATION_WEB_PUBLICATION_v1 and stores validated outputs as DRAFT.
Reception never publishes an opportunity and never recalculates economic/legal data.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

CONTRACT_VERSION = "PRESENTATION_WEB_PUBLICATION_v1"
CONSUMER = "WEB"
PRODUCER_HEADER = "X-Presentation-Web-Key"
INGEST_HEADER = "X-Web-Presentation-Ingest-Key"


def _canonical(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")


def payload_hash(payload: dict[str, Any]) -> str:
    base = dict(payload)
    base.pop("output_hash", None)
    return hashlib.sha256(_canonical(base)).hexdigest()


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise HTTPException(status_code=422, detail={"code": "contract_version_invalid"})
    if payload.get("consumer") != CONSUMER:
        raise HTTPException(status_code=422, detail={"code": "consumer_invalid"})
    if payload.get("publication_state") != "DRAFT_ONLY":
        raise HTTPException(status_code=422, detail={"code": "publication_state_invalid"})
    required = ("output_id", "output_version", "internal_id", "output_hash")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"code": "required_fields_missing", "fields": missing},
        )
    expected = payload_hash(payload)
    if not hmac.compare_digest(str(payload.get("output_hash")), expected):
        raise HTTPException(status_code=422, detail={"code": "output_hash_invalid"})


def _ingest_key() -> str:
    return (os.environ.get("WEB_PRESENTATION_INGEST_KEY") or "").strip()


def _producer_config() -> tuple[str, str]:
    base = (os.environ.get("PRESENTATION_WEB_BASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("WEB_PRESENTATION_M2M_KEY") or "").strip()
    if not base or not key:
        raise HTTPException(
            status_code=503, detail={"code": "presentation_source_not_configured"}
        )
    return base, key


def _require_ingest_auth(request: Request) -> None:
    expected = _ingest_key()
    if not expected:
        raise HTTPException(
            status_code=503, detail={"code": "web_presentation_ingest_not_configured"}
        )
    supplied = (request.headers.get(INGEST_HEADER) or "").strip()
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=401, detail={"code": "invalid_web_presentation_ingest_key"}
        )


class PresentationPublicationIn(BaseModel):
    model_config = ConfigDict(extra="allow")


async def store_draft(db, payload: dict[str, Any]) -> dict[str, Any]:
    validate_payload(payload)
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.presentation_web_drafts.find_one(
        {"output_id": payload["output_id"]},
        {"_id": 0, "output_hash": 1, "publication_state": 1, "received_at": 1},
    )
    if existing and existing.get("output_hash") != payload["output_hash"]:
        raise HTTPException(status_code=409, detail={"code": "output_id_hash_conflict"})
    if existing and existing.get("publication_state") == "PUBLISHED":
        raise HTTPException(
            status_code=409, detail={"code": "published_output_immutable"}
        )

    record = {
        "output_id": payload["output_id"],
        "output_version": payload["output_version"],
        "internal_id": payload["internal_id"],
        "output_hash": payload["output_hash"],
        "contract_version": payload["contract_version"],
        "consumer": payload["consumer"],
        "source_state": payload.get("state"),
        "publication_state": "DRAFT",
        "payload": payload,
        "received_at": (existing or {}).get("received_at") or now,
        "updated_at": now,
    }
    await db.presentation_web_drafts.update_one(
        {"output_id": payload["output_id"]}, {"$set": record}, upsert=True
    )
    await db.presentation_web_active.update_one(
        {"internal_id": payload["internal_id"]},
        {
            "$set": {
                "internal_id": payload["internal_id"],
                "output_id": payload["output_id"],
                "output_version": payload["output_version"],
                "output_hash": payload["output_hash"],
                "publication_state": "DRAFT",
                "updated_at": now,
            }
        },
        upsert=True,
    )
    return {
        "stored": True,
        "idempotent": bool(existing),
        "internal_id": payload["internal_id"],
        "output_id": payload["output_id"],
        "output_version": payload["output_version"],
        "output_hash": payload["output_hash"],
        "publication_state": "DRAFT",
    }


def _get_json(
    url: str, key: str, params: dict[str, str] | None = None
) -> dict[str, Any]:
    try:
        response = requests.get(
            url,
            params=params,
            headers={PRODUCER_HEADER: key, "Accept": "application/json"},
            timeout=20,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502, detail={"code": "presentation_source_unreachable"}
        ) from exc
    try:
        body = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502, detail={"code": "presentation_source_invalid_json"}
        ) from exc
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "presentation_source_error",
                "upstream_status": response.status_code,
            },
        )
    return body


async def pull_from_presentation(internal_id: str) -> dict[str, Any]:
    base, key = _producer_config()
    discovery = await asyncio.to_thread(
        _get_json,
        f"{base}/api/m2m/outputs/web",
        key,
        {"internal_id": internal_id},
    )
    if (
        discovery.get("contract_version") != CONTRACT_VERSION
        or discovery.get("consumer") != CONSUMER
    ):
        raise HTTPException(
            status_code=422, detail={"code": "discovery_contract_invalid"}
        )
    items = discovery.get("items") or []
    if not items:
        raise HTTPException(
            status_code=404, detail={"code": "presentation_output_not_found"}
        )
    item = items[0]
    if item.get("internal_id") != internal_id:
        raise HTTPException(status_code=409, detail={"code": "internal_id_mismatch"})
    output_id = item.get("output_id")
    if not output_id:
        raise HTTPException(status_code=422, detail={"code": "output_id_missing"})

    detail = await asyncio.to_thread(
        _get_json,
        f"{base}/api/m2m/outputs/web/{output_id}",
        key,
        None,
    )
    validate_payload(detail)
    if detail.get("internal_id") != internal_id:
        raise HTTPException(
            status_code=409, detail={"code": "detail_internal_id_mismatch"}
        )
    if detail.get("output_hash") != item.get("output_hash"):
        raise HTTPException(
            status_code=409, detail={"code": "discovery_detail_hash_mismatch"}
        )
    if detail.get("output_version") != item.get("output_version"):
        raise HTTPException(
            status_code=409, detail={"code": "discovery_detail_version_mismatch"}
        )
    return detail


def register_routes(api_router: APIRouter, db) -> None:
    @api_router.post("/m2m/presentation/ingest")
    async def ingest(payload: PresentationPublicationIn, request: Request):
        _require_ingest_auth(request)
        return await store_draft(db, payload.model_dump(mode="python"))

    @api_router.post("/m2m/presentation/sync/{internal_id}")
    async def sync(internal_id: str, request: Request):
        _require_ingest_auth(request)
        detail = await pull_from_presentation(internal_id)
        return await store_draft(db, detail)

    @api_router.get("/m2m/presentation/drafts/{internal_id}")
    async def draft_status(internal_id: str, request: Request):
        _require_ingest_auth(request)
        active = await db.presentation_web_active.find_one(
            {"internal_id": internal_id}, {"_id": 0}
        )
        if not active:
            raise HTTPException(
                status_code=404, detail={"code": "presentation_draft_not_found"}
            )
        draft = await db.presentation_web_drafts.find_one(
            {"output_id": active["output_id"]}, {"_id": 0, "payload": 0}
        )
        return {"active": active, "draft": draft}
