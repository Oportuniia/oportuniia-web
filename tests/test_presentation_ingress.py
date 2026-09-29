import copy
import hashlib
import json

import pytest
from fastapi import HTTPException

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import presentation_ingress as ingress


def _canonical(obj):
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")


def _payload():
    p = {
        "contract_version": "PRESENTATION_WEB_PUBLICATION_v1",
        "consumer": "WEB",
        "output_id": "web_test_001",
        "output_version": "v1",
        "internal_id": "OP-TEST-001",
        "state": "READY_FOR_WEB",
        "publication_state": "DRAFT_ONLY",
        "catalog": {
            "title": "Operación sintética",
            "product": "NPL",
            "economic": {
                "capital_requerido_eur": 155000,
                "roi_pct": 53,
                "horizonte_meses": 8,
            },
        },
        "documents": {
            "IC": {
                "status": "READY",
                "artifact_key": "synthetic/IC.pdf",
                "content_hash": "a" * 64,
            }
        },
        "history": [],
    }
    p["output_hash"] = hashlib.sha256(_canonical(p)).hexdigest()
    return p


class FakeCollection:
    def __init__(self):
        self.docs = {}

    async def find_one(self, query, projection=None):
        key = query.get("output_id") or query.get("internal_id")
        doc = self.docs.get(key)
        if not doc:
            return None
        out = copy.deepcopy(doc)
        if projection:
            for k, include in projection.items():
                if include == 0:
                    out.pop(k, None)
        return out

    async def update_one(self, query, update, upsert=False):
        key = query.get("output_id") or query.get("internal_id")
        current = self.docs.get(key, {})
        current.update(copy.deepcopy(update.get("$set", {})))
        self.docs[key] = current
        return object()


class FakeDB:
    def __init__(self):
        self.presentation_web_drafts = FakeCollection()
        self.presentation_web_active = FakeCollection()


def test_validate_accepts_canonical_payload():
    p = _payload()
    ingress.validate_payload(p)
    assert ingress.payload_hash(p) == p["output_hash"]


def test_validate_rejects_hash_mutation():
    p = _payload()
    p["catalog"]["economic"]["roi_pct"] = 999
    with pytest.raises(HTTPException) as exc:
        ingress.validate_payload(p)
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "output_hash_invalid"


def test_validate_rejects_non_draft_source():
    p = _payload()
    p["publication_state"] = "PUBLISHED"
    p["output_hash"] = ingress.payload_hash(p)
    with pytest.raises(HTTPException) as exc:
        ingress.validate_payload(p)
    assert exc.value.detail["code"] == "publication_state_invalid"


@pytest.mark.asyncio
async def test_store_draft_is_idempotent_and_preserves_values():
    db = FakeDB()
    p = _payload()
    first = await ingress.store_draft(db, p)
    second = await ingress.store_draft(db, p)
    assert first["publication_state"] == "DRAFT"
    assert first["idempotent"] is False
    assert second["idempotent"] is True
    stored = db.presentation_web_drafts.docs[p["output_id"]]
    assert stored["payload"]["catalog"]["economic"]["capital_requerido_eur"] == 155000
    assert stored["payload"]["catalog"]["economic"]["roi_pct"] == 53


@pytest.mark.asyncio
async def test_store_draft_rejects_same_id_with_different_hash():
    db = FakeDB()
    p = _payload()
    await ingress.store_draft(db, p)
    changed = copy.deepcopy(p)
    changed["catalog"]["title"] = "Mutada"
    changed["output_hash"] = ingress.payload_hash(changed)
    with pytest.raises(HTTPException) as exc:
        await ingress.store_draft(db, changed)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "output_id_hash_conflict"


@pytest.mark.asyncio
async def test_pull_validates_discovery_detail_binding(monkeypatch):
    p = _payload()
    calls = []

    def fake_get(url, key, params=None):
        calls.append((url, key, params))
        if url.endswith("/api/m2m/outputs/web"):
            return {
                "contract_version": ingress.CONTRACT_VERSION,
                "consumer": ingress.CONSUMER,
                "items": [{
                    "output_id": p["output_id"],
                    "output_version": p["output_version"],
                    "internal_id": p["internal_id"],
                    "output_hash": p["output_hash"],
                }],
            }
        return p

    monkeypatch.setenv("PRESENTATION_WEB_BASE_URL", "https://presentation.example")
    monkeypatch.setenv("WEB_PRESENTATION_M2M_KEY", "synthetic-key")
    monkeypatch.setattr(ingress, "_get_json", fake_get)

    detail = await ingress.pull_from_presentation("OP-TEST-001")
    assert detail["output_hash"] == p["output_hash"]
    assert len(calls) == 2
    assert calls[0][2] == {"internal_id": "OP-TEST-001"}
