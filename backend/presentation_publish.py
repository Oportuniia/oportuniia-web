"""Publicación controlada de borradores PRESENTACIÓN en el catálogo WEB.

La recepción M2M guarda DRAFT. Este módulo exige una acción explícita para
publicar o retirar. No calcula negocio: solo representa campos ya recibidos.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from presentation_ingress import _require_ingest_auth, validate_payload
import catalog_data as cat


def _slugify(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text or "op"


def _number(value: Any) -> float | int | None:
    if value is None or value == "":
        return None
    try:
        n = float(str(value).replace("%", "").replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
    return int(n) if n.is_integer() else n


def _first(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _geo_codes(ccaa_name: str, province_name: str, municipality_name: str) -> tuple[str, str, str]:
    ccaa_code = None
    province_code = None
    municipality_code = None
    target_ccaa = _slugify(ccaa_name)
    target_province = _slugify(province_name)
    target_municipality = _slugify(municipality_name)

    for code, data in cat.GEO.items():
        if _slugify(data.get("name")) == target_ccaa:
            ccaa_code = code
            for pcode, pdata in (data.get("provincias") or {}).items():
                if _slugify(pdata.get("name")) == target_province:
                    province_code = pcode
                    for mcode, mname in (pdata.get("municipios") or {}).items():
                        if _slugify(mname) == target_municipality:
                            municipality_code = mcode
                            break
                    break
            break

    return (
        ccaa_code or target_ccaa,
        province_code or target_province,
        municipality_code or target_municipality,
    )


def materialize_catalog_item(payload: dict[str, Any]) -> dict[str, Any]:
    validate_payload(payload)
    if payload.get("state") != "READY_FOR_WEB":
        raise HTTPException(
            status_code=409, detail={"code": "presentation_output_not_ready_for_web"}
        )

    catalog = payload.get("catalog") or {}
    asset = catalog.get("asset") or {}
    geo = catalog.get("geography") or {}
    economic = catalog.get("economic") or {}
    legal = catalog.get("legal_process") or {}

    universe = catalog.get("universe")
    product = catalog.get("product")
    title = catalog.get("title")
    asset_type = asset.get("type")
    ccaa_name = geo.get("ccaa")
    province_name = geo.get("province")
    municipality_name = geo.get("municipality")
    investment = _number(economic.get("inversion_total_eur"))
    roi_num = _number(_first(economic, "roi_pct", "roi"))
    timeframe = _number(economic.get("horizonte_meses"))

    missing = []
    for key, value in (
        ("catalog.universe", universe),
        ("catalog.product", product),
        ("catalog.title", title),
        ("catalog.asset.type", asset_type),
        ("catalog.geography.ccaa", ccaa_name),
        ("catalog.geography.province", province_name),
        ("catalog.geography.municipality", municipality_name),
        ("catalog.economic.inversion_total_eur", investment),
        ("catalog.economic.roi_pct", roi_num),
        ("catalog.economic.horizonte_meses", timeframe),
    ):
        if value in (None, ""):
            missing.append(key)
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"code": "publication_fields_missing", "fields": missing},
        )
    if universe not in {"judicial", "acuerdos"}:
        raise HTTPException(status_code=422, detail={"code": "universe_invalid"})
    if product not in {"NPL", "CDR", "REO"}:
        raise HTTPException(status_code=422, detail={"code": "product_invalid"})

    internal_id = str(payload["internal_id"])
    suffix = hashlib.sha256(internal_id.encode("utf-8")).hexdigest()[:8]
    slug = _slugify(f"{municipality_name}-{product}-{title}-{suffix}")
    ccaa_code, province_code, municipality_code = _geo_codes(
        str(ccaa_name), str(province_name), str(municipality_name)
    )

    family = asset.get("family")
    category = " · ".join(str(x) for x in (family, asset_type) if x) or str(asset_type)
    situation = _first(
        legal,
        "situacion",
        "fase_procesal",
        "estado_procesal",
        "fase",
        "estado",
    ) or "—"
    roi_display = f"{roi_num:g}%".replace(".", ",")
    image = _first(catalog, "primary_image_url", "image_url") or _first(
        asset, "primary_image_url", "image_url"
    )

    return {
        "slug": slug,
        "order": 0,
        "universe": universe,
        "product": product,
        "title": title,
        "asset_type": str(asset_type),
        "category": category,
        "ccaa": ccaa_code,
        "provincia": province_code,
        "municipio": municipality_code,
        "ccaa_name": ccaa_name,
        "provincia_name": province_name,
        "municipio_name": municipality_name,
        "price": investment,
        "timeframe": int(timeframe) if float(timeframe).is_integer() else timeframe,
        "situation": str(situation),
        "occupancy": catalog.get("occupancy") or "—",
        "strategy": catalog.get("strategy") or "—",
        "roi": roi_display,
        "roi_num": float(roi_num),
        "surface": asset.get("surface_m2"),
        "bedrooms": asset.get("bedrooms"),
        "bathrooms": asset.get("bathrooms"),
        "image": image or "",
        "summary": catalog.get("summary") or "",
        "procedure": catalog.get("procedure_code"),
        "phase": catalog.get("phase_code"),
        "possession": catalog.get("possession_code"),
        "internal_id": internal_id,
        "source_output_id": payload["output_id"],
        "source_output_version": payload["output_version"],
        "source_output_hash": payload["output_hash"],
        "documents": payload.get("documents") or {},
    }


async def publish_active_draft(db, internal_id: str) -> dict[str, Any]:
    active = await db.presentation_web_active.find_one(
        {"internal_id": internal_id}, {"_id": 0}
    )
    if not active:
        raise HTTPException(status_code=404, detail={"code": "presentation_draft_not_found"})
    draft = await db.presentation_web_drafts.find_one(
        {"output_id": active.get("output_id")}, {"_id": 0}
    )
    if not draft or not isinstance(draft.get("payload"), dict):
        raise HTTPException(status_code=404, detail={"code": "presentation_payload_not_found"})

    payload = draft["payload"]
    item = materialize_catalog_item(payload)
    existing = await db.presentation_web_published.find_one(
        {"internal_id": internal_id},
        {"_id": 0, "source_output_hash": 1, "published_at": 1},
    )
    now = datetime.now(timezone.utc)
    published_at = (existing or {}).get("published_at") or now.isoformat()
    item["order"] = int(now.timestamp())

    record = {
        "internal_id": internal_id,
        "slug": item["slug"],
        "source_output_id": payload["output_id"],
        "source_output_version": payload["output_version"],
        "source_output_hash": payload["output_hash"],
        "publication_state": "PUBLISHED",
        "published_at": published_at,
        "updated_at": now.isoformat(),
        "item": item,
    }
    await db.presentation_web_published.update_one(
        {"internal_id": internal_id}, {"$set": record}, upsert=True
    )
    await db.presentation_web_drafts.update_one(
        {"output_id": payload["output_id"]},
        {"$set": {"publication_state": "PUBLISHED", "published_at": published_at}},
        upsert=False,
    )
    await db.presentation_web_active.update_one(
        {"internal_id": internal_id},
        {"$set": {"publication_state": "PUBLISHED", "slug": item["slug"]}},
        upsert=False,
    )
    return {
        "published": True,
        "idempotent": bool(
            existing and existing.get("source_output_hash") == payload["output_hash"]
        ),
        "internal_id": internal_id,
        "slug": item["slug"],
        "output_id": payload["output_id"],
        "output_version": payload["output_version"],
        "output_hash": payload["output_hash"],
    }


async def withdraw_publication(db, internal_id: str) -> dict[str, Any]:
    existing = await db.presentation_web_published.find_one(
        {"internal_id": internal_id}, {"_id": 0, "source_output_id": 1}
    )
    if not existing:
        raise HTTPException(status_code=404, detail={"code": "published_item_not_found"})
    now = datetime.now(timezone.utc).isoformat()
    await db.presentation_web_published.update_one(
        {"internal_id": internal_id},
        {"$set": {"publication_state": "WITHDRAWN", "withdrawn_at": now, "updated_at": now}},
        upsert=False,
    )
    await db.presentation_web_active.update_one(
        {"internal_id": internal_id},
        {"$set": {"publication_state": "DRAFT", "withdrawn_at": now}},
        upsert=False,
    )
    output_id = existing.get("source_output_id")
    if output_id:
        await db.presentation_web_drafts.update_one(
            {"output_id": output_id},
            {"$set": {"publication_state": "DRAFT", "withdrawn_at": now}},
            upsert=False,
        )
    return {"published": False, "internal_id": internal_id, "state": "WITHDRAWN"}


def register_publish_routes(api_router: APIRouter, db) -> None:
    @api_router.post("/m2m/presentation/publish/{internal_id}")
    async def publish(internal_id: str, request: Request):
        _require_ingest_auth(request)
        return await publish_active_draft(db, internal_id)

    @api_router.delete("/m2m/presentation/publish/{internal_id}")
    async def unpublish(internal_id: str, request: Request):
        _require_ingest_auth(request)
        return await withdraw_publication(db, internal_id)
