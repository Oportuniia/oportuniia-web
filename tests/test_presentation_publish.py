import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import presentation_publish as pub


def _canonical(obj):
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")


def _payload():
    p = {
        "contract_version": "PRESENTATION_WEB_PUBLICATION_v1",
        "consumer": "WEB",
        "output_id": "web_out_1",
        "output_version": "v1",
        "internal_id": "OP-REAL-MOCK-001",
        "state": "READY_FOR_WEB",
        "publication_state": "DRAFT_ONLY",
        "catalog": {
            "title": "Vivienda controlada",
            "summary": "Dato sintético.",
            "product": "NPL",
            "universe": "judicial",
            "asset": {
                "type": "piso",
                "family": "residencial",
                "surface_m2": 92,
                "bedrooms": 3,
                "bathrooms": 2,
            },
            "geography": {
                "ccaa": "Comunidad de Madrid",
                "province": "Madrid",
                "municipality": "Madrid",
            },
            "occupancy": "ocupado",
            "legal_process": {"fase_procesal": "Subasta señalada"},
            "economic": {
                "inversion_total_eur": 193000,
                "roi_pct": 53,
                "horizonte_meses": 8,
            },
        },
        "documents": {"IC": {"status": "READY", "content_hash": "a" * 64}},
        "history": [],
    }
    p["output_hash"] = hashlib.sha256(_canonical(p)).hexdigest()
    return p


class FakeCollection:
    def __init__(self):
        self.docs = {}

    async def find_one(self, query, projection=None):
        key = query.get("internal_id") or query.get("output_id")
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
        key = query.get("internal_id") or query.get("output_id")
        current = self.docs.get(key, {})
        current.update(copy.deepcopy(update.get("$set", {})))
        self.docs[key] = current
        return object()


class FakeDB:
    def __init__(self, payload):
        self.presentation_web_active = FakeCollection()
        self.presentation_web_drafts = FakeCollection()
        self.presentation_web_published = FakeCollection()
        self.presentation_web_active.docs[payload["internal_id"]] = {
            "internal_id": payload["internal_id"],
            "output_id": payload["output_id"],
            "publication_state": "DRAFT",
        }
        self.presentation_web_drafts.docs[payload["output_id"]] = {
            "output_id": payload["output_id"],
            "publication_state": "DRAFT",
            "payload": payload,
        }


def test_materialize_maps_only_explicit_public_fields():
    item = pub.materialize_catalog_item(_payload())
    assert item["universe"] == "judicial"
    assert item["product"] == "NPL"
    assert item["price"] == 193000
    assert item["roi_num"] == 53
    assert item["roi"] == "53%"
    assert item["timeframe"] == 8
    assert item["situation"] == "Subasta señalada"
    assert item["image"] == ""
    assert "OP-REAL-MOCK-001" not in item["slug"]


def test_materialize_requires_explicit_universe():
    p = _payload()
    p["catalog"].pop("universe")
    p["output_hash"] = hashlib.sha256(_canonical({k:v for k,v in p.items() if k != "output_hash"})).hexdigest()
    with pytest.raises(HTTPException) as exc:
        pub.materialize_catalog_item(p)
    assert exc.value.status_code == 422
    assert "catalog.universe" in exc.value.detail["fields"]


def test_materialize_refuses_not_ready_output():
    p = _payload()
    p["state"] = "NEEDS_ENRICHMENT"
    p["output_hash"] = hashlib.sha256(_canonical({k:v for k,v in p.items() if k != "output_hash"})).hexdigest()
    with pytest.raises(HTTPException) as exc:
        pub.materialize_catalog_item(p)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_publish_and_withdraw_are_explicit_state_changes():
    p = _payload()
    db = FakeDB(p)
    first = await pub.publish_active_draft(db, p["internal_id"])
    assert first["published"] is True
    assert first["idempotent"] is False
    stored = db.presentation_web_published.docs[p["internal_id"]]
    assert stored["publication_state"] == "PUBLISHED"
    assert stored["item"]["price"] == 193000
    second = await pub.publish_active_draft(db, p["internal_id"])
    assert second["idempotent"] is True
    withdrawn = await pub.withdraw_publication(db, p["internal_id"])
    assert withdrawn["state"] == "WITHDRAWN"
    assert db.presentation_web_published.docs[p["internal_id"]]["publication_state"] == "WITHDRAWN"


def test_materialized_item_participates_in_existing_catalog_filters():
    import catalog_data as cat
    item = pub.materialize_catalog_item(_payload())
    f = cat.normalize_filters(
        universe="judicial",
        products=["NPL"],
        price_min=190000,
        roi_min=50,
        term_max=10,
    )
    items = cat.filter_opportunities(f, order="recientes", extra=[item])
    assert any(x["slug"] == item["slug"] for x in items)
    counts = cat.facet_counts(f, extra=[item])
    assert counts["product"]["NPL"] >= 1
