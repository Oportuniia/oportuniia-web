# Write Bridge — Security Review (0.1.0-rc1)

Scope: design + code + local tests only. No installation, no WordPress writes.

| # | Threat | Mitigation | Residual |
|---|--------|-----------|----------|
| 1 | Privilege escalation | Only edit_post(fixed id); no manage_options/edit_theme_options; never elevates on failure | LOW |
| 2 | Arbitrary post modification | IDs hardcoded per route; no client ID accepted | LOW |
| 3 | IDOR | No id parameter in any route (structural) | LOW |
| 4 | Unexpected field injection | Exact 3-key whitelist; any extra → 422 | LOW |
| 5 | Arbitrary meta modification | Only _elementor_data (+edit_mode/version if missing) | LOW |
| 6 | Elementor JSON injection/malformed | Structural validation (list root, elType allow-list, depth 32), no auto-fix → 422 | LOW |
| 7 | Accidental publish | status never written; draft-only enforced; non-draft → 409 | LOW |
| 8 | Template takeover | Fixed object/type; no type/instance change | LOW |
| 9 | Active header modification | 1641 only; active header is another template, unreachable | LOW |
| 10 | Display conditions / instances | Never touched; readback confirms status/type | LOW |
| 11 | Replay | operation_id single-use, TTL 300s, target+base_hash bound, consumed on write | LOW |
| 12 | Stale-write / concurrent human edit | precondition hash re-read immediately before write → 409, nonce invalidated | LOW |
| 13 | Oversized payload / DoS | size cap (provisional 1.5 MiB) before write; depth limit | LOW |
| 14 | Credential leakage | Secrets server-side; never logged/returned; audit strips secrets | LOW |
| 15 | Audit-log leakage | Audit has no secret keys, no full _elementor_data (verified by test) | LOW |
| 16 | Rollback abuse | Same gate; operation_id + own snapshot; draft-only | LOW |
| 17 | Cross-object rollback | Snapshot bound to target_id; guard denies cross-object (tested) | LOW |
| 18 | Authentication bypass | Multi-check permission_callback; fail-closed | LOW |
| 19 | Route discovery w/o auth | Without valid creds → 401/403, no data | LOW |
| 20 | Future plugin scope creep | Separate versioned plugin; hardcoded ids/fields; mandatory code review | MEDIUM (organizational) |

## Notes
- CSS invalidation is object-scoped (\Elementor\Core\Files\CSS\Post($id)->delete()), guarded by class_exists; no global/site-wide purge.
- Elementor sovereignty preserved: only native _elementor_data node tree is transported; no HTML/iframe/opaque monolith. Rafa/Alba keep editing normally.
- Snapshot/audit live in the control layer (MongoDB); WordPress/Elementor is source of truth.

RESIDUAL RISK: LOW (one MEDIUM organizational item mitigated by process).
