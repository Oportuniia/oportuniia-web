# PRESENTACIÓN → WEB · UI validation gate (2026-10-01)

Status: REVIEW BRANCH ONLY. No production deployment or data writes authorized.

## Existing evidence — don't repeat transport E2E without a new reason
Render application logs on 2026-09-29:
- PRESENTATION_WEB_E2E_SEED_READY for synthetic OP-2026-E2E-WEB-001; PC/RE/IC/RF READY.
- PRESENTATION_WEB_E2E_PASS for same OP; verified IC PDF/hash, Mongo DRAFT, publish, catalogue lookup, withdrawal and synthetic WEB cleanup.
- The seed used PRESENTACIÓN's production R2 configuration, so it is NOT a demonstration of fully isolated infrastructure. Avoid re-running it on shared production resources.

## Verified current code split
- backend/server.py: production-style FastAPI queries presentation_web_published (and includes demo fixtures) for opportunity API/catalogue.
- backend/preview_server.py: Render review uses fixture catalogue only, not production DB or PRESENTACIÓN.
- backend/templates/detalle.html: documentary section currently built from cat.documentation_for(o) (demo taxonomy), not gated PDF routes backed by PRESENTACIÓN.
- _vip_active() currently returns False; no real human identity/entitlement integrated.
- README/integration: PRESENTATION_WEB_PUBLICATION_v1 ships document metadata (artifact_key, hash, status) and serves guarded PDF endpoints on PRESENTACIÓN. R2 remains server-side and owned by PRESENTACIÓN.

## Remaining acceptance gates
1. Build an isolated WEB UI review path/fixture using the synthetic contract, without production Mongo or R2 writes.
2. Render actual published item documents from payload.documents (PC/RE/IC/RF) with correct READY/unavailable statuses, not placeholder links.
3. Authorize documents server-side via existing sovereign identity integration BEFORE implementing real downloads; do not rely on blurred UI or JavaScript hiding.
4. When explicit real access rules are supplied, add a backend PDF proxy to PRESENTACIÓN protected M2M route, never expose Cloudflare credentials or private artifact keys in the browser.
5. Test access matrix (anonymous, validated user, Premium where authorized) + direct URL denial; do not infer entitlements.
6. Keep main/production WordPress/Render unchanged until owner approval and backups.
