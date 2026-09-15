# OPORTUNIIA Control Write Bridge — Artifact Manifest

- Component: OPORTUNIIA Control Write Bridge (SEPARATE from Read Bridge v1.0.1)
- Version: 0.1.0-rc1 (PRE-RELEASE — not final until MASTER approval)
- Artifact ZIP: oportuniia-control-write-bridge-0.1.0-rc1.zip
- ZIP SHA256: ce6378afb3380a32c24a9af174cef836fb5aa4e300813d447bb50c4ab4fa67e4
- PHP SHA256: c1fafdc4428b450795f32b9994d2fcfdfebe77a8c0e9836d3568afbddb7bdb02

## Files in ZIP
- oportuniia-control-write-bridge/
- oportuniia-control-write-bridge/oportuniia-control-write-bridge.php

## Supporting files (NOT in ZIP)
- tests/wp-stubs.php               (WP stubs, test-only)
- tests/test_write_bridge.php      (40 PHP security/behaviour tests)
- control_layer/write_orchestrator.py  (snapshot/audit/rollback primitives)
- control_layer/test_orchestrator.py   (15 Python tests)
- MANIFEST.md / TEST_REPORT.md / SECURITY_REVIEW.md

## Fixed targets (hardcoded, no client IDs)
- HOME: id 1630, type page, status draft, field _elementor_data
- HEADER: id 1641, type elementor_library, status draft, field _elementor_data
- Authorized user: emergent_build

## Routes
- GET  /wp-json/oportuniia-control-write/v1/home/prepare
- POST /wp-json/oportuniia-control-write/v1/home
- GET  /wp-json/oportuniia-control-write/v1/header/prepare
- POST /wp-json/oportuniia-control-write/v1/header

## Removal / rollback of component
- WP Admin → Plugins → deactivate "OPORTUNIIA Control Write Bridge" → delete.
- Independent of Read Bridge v1.0.1 (which stays ACTIVE/UNCHANGED).
- No tables/options/cron created (nonces use auto-expiring transients).
