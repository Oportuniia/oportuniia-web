"""Runtime E2E verifier for PRESENTACIÓN -> WEB.

Disabled by default. When WEB_PRESENTATION_E2E=1, the verifier:
1) pulls a READY_FOR_WEB output from PRESENTACIÓN using the real M2M contract,
2) verifies one real PDF artifact hash over HTTP,
3) stores it as DRAFT in Mongo,
4) publishes it,
5) verifies catalogue materialization,
6) withdraws it,
7) removes the synthetic test records from Mongo.

No real opportunity is modified.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os

import requests

import catalog_data as cat
from presentation_ingress import (
    PRODUCER_HEADER,
    _producer_config,
    pull_from_presentation,
    store_draft,
)
from presentation_publish import publish_active_draft, withdraw_publication

logger = logging.getLogger(__name__)

DEFAULT_INTERNAL_ID = "OP-2026-E2E-WEB-001"


def _verify_pdf_artifact(detail: dict) -> tuple[str, int]:
    docs = detail.get("documents") or {}
    candidate = next(
        ((name, info) for name, info in docs.items()
         if isinstance(info, dict) and info.get("status") == "READY"),
        None,
    )
    if not candidate:
        raise RuntimeError("no_ready_document")

    product, info = candidate
    base, key = _producer_config()
    url = (
        f"{base}/api/m2m/outputs/web/{detail['output_id']}"
        f"/artifacts/{product}"
    )
    response = requests.get(
        url,
        headers={PRODUCER_HEADER: key, "Accept": "application/pdf"},
        timeout=30,
    )
    response.raise_for_status()
    body = response.content
    if not body.startswith(b"%PDF"):
        raise RuntimeError("artifact_not_pdf")
    expected = info.get("content_hash")
    actual = hashlib.sha256(body).hexdigest()
    if expected and actual != expected:
        raise RuntimeError("artifact_hash_mismatch")
    return product, len(body)


async def run_presentation_e2e_if_enabled(db) -> None:
    if (os.environ.get("WEB_PRESENTATION_E2E") or "").strip() != "1":
        return

    internal_id = (
        os.environ.get("WEB_PRESENTATION_E2E_INTERNAL_ID") or DEFAULT_INTERNAL_ID
    ).strip()
    attempts = max(1, int(os.environ.get("WEB_PRESENTATION_E2E_ATTEMPTS", "40")))
    delay = max(2, int(os.environ.get("WEB_PRESENTATION_E2E_DELAY_SECONDS", "15")))

    for attempt in range(1, attempts + 1):
        try:
            detail = await pull_from_presentation(internal_id)
            if detail.get("state") != "READY_FOR_WEB":
                raise RuntimeError(f"source_state_{detail.get('state')}")

            product, artifact_size = await asyncio.to_thread(
                _verify_pdf_artifact, detail
            )

            # Synthetic test id only: remove leftovers from a previous interrupted run.
            await db.presentation_web_published.delete_many(
                {"internal_id": internal_id}
            )
            await db.presentation_web_drafts.delete_many(
                {"internal_id": internal_id}
            )
            await db.presentation_web_active.delete_many(
                {"internal_id": internal_id}
            )

            stored = await store_draft(db, detail)
            active = await db.presentation_web_active.find_one(
                {"internal_id": internal_id}, {"_id": 0}
            )
            if not active or active.get("publication_state") != "DRAFT":
                raise RuntimeError("draft_not_materialized")

            published = await publish_active_draft(db, internal_id)
            slug = published.get("slug")
            if not slug:
                raise RuntimeError("published_slug_missing")

            extra = await db.presentation_web_published.find(
                {"publication_state": "PUBLISHED"},
                {"_id": 0, "item": 1},
            ).to_list(1000)
            items = [x["item"] for x in extra if isinstance(x.get("item"), dict)]
            catalog_item = cat.get_by_slug(slug, extra=items)
            if not catalog_item or catalog_item.get("internal_id") != internal_id:
                raise RuntimeError("catalog_item_missing")

            await withdraw_publication(db, internal_id)
            after = await db.presentation_web_published.find_one(
                {"internal_id": internal_id}, {"_id": 0}
            )
            if not after or after.get("publication_state") != "WITHDRAWN":
                raise RuntimeError("withdrawal_not_persisted")

            # Leave Mongo clean after proof.
            output_id = detail.get("output_id")
            await db.presentation_web_published.delete_many(
                {"internal_id": internal_id}
            )
            await db.presentation_web_active.delete_many(
                {"internal_id": internal_id}
            )
            if output_id:
                await db.presentation_web_drafts.delete_many(
                    {"output_id": output_id}
                )

            logger.info(
                "PRESENTATION_WEB_E2E_PASS internal_id=%s output_id=%s "
                "artifact=%s artifact_bytes=%s draft=%s published_slug=%s "
                "withdrawn=true cleaned=true",
                internal_id,
                detail.get("output_id"),
                product,
                artifact_size,
                stored.get("publication_state"),
                slug,
            )
            return
        except Exception as exc:
            logger.warning(
                "PRESENTATION_WEB_E2E_WAIT attempt=%s/%s type=%s detail=%s",
                attempt,
                attempts,
                type(exc).__name__,
                str(exc)[:160],
            )
            if attempt < attempts:
                await asyncio.sleep(delay)

    logger.error(
        "PRESENTATION_WEB_E2E_FAIL internal_id=%s attempts=%s",
        internal_id,
        attempts,
    )
