# Write Bridge — Local Test Report

Environment: PHP 8.2.33 CLI with stubbed WordPress; Python 3.11.
No WordPress contact. No writes to production. Tests are local only.

## PHP plugin tests (tests/test_write_bridge.php) — 40/40 PASS
Covers section 19 scenarios:
- correct user / wrong user / missing auth / missing capability
- non-draft target / wrong post_type
- unexpected payload field(s): status, title, publish, instances, meta, post_id, author, slug, featured_media, content
- malformed JSON / invalid root (object not list) / invalid elType / excessive depth / empty payload / oversized payload
- expired operation / reused operation (single-use) / unknown operation
- wrong base_hash / stale base (concurrent human edit) → 409 + nonce invalidated
- operation bound to target (home op cannot write header)
- no dynamic ID route params; exactly 4 fixed routes
- write touches ONLY _elementor_data / _elementor_edit_mode / _elementor_version, only object 1630
- rollback: restore previous data via same guarded write path (200 + data restored)

## Python control-layer tests (control_layer/test_orchestrator.py) — 15/15 PASS
- snapshot bound to fixed target; rejects unknown target (snapshot isolation)
- audit contains no secret keys and no full _elementor_data; leakage detection works
- rollback guard: same object/op/draft allowed; cross-object denied; wrong op denied; non-draft denied
- strict payload whitelist: exact 3 keys only

## Static analysis (plugin) — PASS
ABSENT (verified): wp_update_post, wp_insert_post, wp_delete_post, wp_publish_post,
manage_options, edit_theme_options, add/remove_role/cap, wp_insert/update_user,
activate/deactivate_plugins, flush_rewrite, wp_cache_flush, global purge, dynamic ID route params.
PRESENT (verified): hardcoded 1630/1641, current_user_can('edit_post', id), draft-only check,
hash_equals, update_post_meta(id,'_elementor_data'), wp_slash, delete_transient (single-use).
