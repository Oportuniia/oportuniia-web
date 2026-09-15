"""Local tests for control-layer orchestration primitives. Run: python test_orchestrator.py"""
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from write_orchestrator import (
    build_snapshot, build_audit, audit_is_clean, can_rollback,
    payload_is_strict, sha256, FIXED_TARGETS,
)

P = F = 0
def check(name, cond):
    global P, F
    if cond:
        P += 1; print(f"PASS  {name}")
    else:
        F += 1; print(f"FAIL  {name}")

prev = '[{"id":"a","elType":"container","elements":[]}]'

# snapshot bound to fixed target, keeps prev data + hash
snap = build_snapshot("header", prev)
check("snapshot target id fixed 1641", snap["target_id"] == 1641 and snap["post_type"] == "elementor_library")
check("snapshot before_hash correct", snap["before_hash"] == sha256(prev))
check("snapshot size bytes", snap["size"] == len(prev.encode()))

# snapshot isolation: unknown target rejected
try:
    build_snapshot("evil", prev); ok = False
except ValueError:
    ok = True
check("snapshot rejects unknown target", ok)

# audit contains no secrets / no full data
audit = build_audit("write", snap, after_hash=sha256(prev), payload_size=123,
                    validation_result="ok", result="success", http_status=200)
check("audit clean (no secret keys)", audit_is_clean(audit))
check("audit has no _elementor_data key", "_elementor_data" not in audit)
# inject a forbidden key -> detected
dirty = dict(audit); dirty["authorization"] = "Basic abc"
check("audit leakage detected", not audit_is_clean(dirty))
dirty2 = dict(audit); dirty2["result"] = "Basic Zm9vOmJhcg=="
check("audit basic-token value detected", not audit_is_clean(dirty2))

# rollback guards
ok, reason = can_rollback(snap, "header", snap["operation_id"], "draft")
check("rollback allowed same object/op/draft", ok and reason == "ok")
ok, reason = can_rollback(snap, "home", snap["operation_id"], "draft")
check("rollback cross-object denied", (not ok) and reason == "cross_object_denied")
ok, reason = can_rollback(snap, "header", "other-op", "draft")
check("rollback wrong op denied", (not ok) and reason == "operation_id_mismatch")
ok, reason = can_rollback(snap, "header", snap["operation_id"], "publish")
check("rollback non-draft denied", (not ok) and reason == "target_not_draft")

# strict payload whitelist
check("payload strict ok", payload_is_strict({"operation_id": "x", "base_hash": "y", "_elementor_data": "[]"}))
check("payload extra field rejected", not payload_is_strict({"operation_id": "x", "base_hash": "y", "_elementor_data": "[]", "status": "publish"}))
check("payload missing field rejected", not payload_is_strict({"operation_id": "x", "base_hash": "y"}))

print("----")
print(f"TOTAL PASS={P} FAIL={F}")
sys.exit(0 if F == 0 else 1)
