"""
OPORTUNIIA · Control-layer orchestration primitives for the Write Bridge.

Design/reference module (NOT wired to any auto-execution, no WordPress contact).
Snapshot + audit live in the control layer (MongoDB) per design; WordPress/Elementor
remains the source of truth. These pure functions are unit-tested locally.
"""

import hashlib
import time
import uuid

# Fixed targets. No dynamic/arbitrary object is ever accepted.
FIXED_TARGETS = {
    "home": {"id": 1630, "type": "page"},
    "header": {"id": 1641, "type": "elementor_library"},
}

# Keys that must NEVER appear in an audit record.
_FORBIDDEN_AUDIT_KEYS = {
    "authorization", "application_password", "app_password", "password",
    "cookie", "cookies", "secret", "wp_application_password",
    "_elementor_data", "elementor_data",
}


def sha256(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def build_snapshot(slug: str, current_elementor_data: str) -> dict:
    """Snapshot bound to a single fixed target. Stores previous data for rollback only."""
    if slug not in FIXED_TARGETS:
        raise ValueError("unknown target")
    cfg = FIXED_TARGETS[slug]
    raw = current_elementor_data or ""
    return {
        "operation_id": str(uuid.uuid4()),
        "target_id": cfg["id"],
        "post_type": cfg["type"],
        "status": "draft",
        "elementor_data_prev": raw,   # full previous data kept ONLY as rollback aid
        "before_hash": sha256(raw),
        "timestamp": int(time.time()),
        "size": len(raw.encode("utf-8")),
    }


def build_audit(operation: str, snapshot: dict, after_hash: str | None,
                payload_size: int, validation_result: str, result: str,
                http_status: int, failure_reason: str = "") -> dict:
    """Audit record with NO secrets and NO full _elementor_data."""
    return {
        "operation_id": snapshot["operation_id"],
        "timestamp": int(time.time()),
        "actor": "emergent_build",
        "target_id": snapshot["target_id"],
        "target_type": snapshot["post_type"],
        "operation": operation,
        "before_hash": snapshot["before_hash"],
        "after_hash": after_hash,
        "payload_size": payload_size,
        "validation_result": validation_result,
        "result": result,
        "failure_reason": failure_reason,
        "http_status": http_status,
    }


def audit_is_clean(record: dict) -> bool:
    """True if the audit record leaks no secret/sensitive keys or full data."""
    for k in record.keys():
        if k.lower() in _FORBIDDEN_AUDIT_KEYS:
            return False
    # Values must not contain a bearer/basic auth token or long elementor blob.
    for v in record.values():
        if isinstance(v, str) and (v.lower().startswith("basic ") or v.lower().startswith("bearer ")):
            return False
    return True


def can_rollback(snapshot: dict, requested_slug: str, requested_operation_id: str,
                 current_status: str) -> tuple[bool, str]:
    """Fail-closed rollback guard. No cross-object, no arbitrary id, draft-only."""
    if requested_slug not in FIXED_TARGETS:
        return False, "unknown_target"
    cfg = FIXED_TARGETS[requested_slug]
    if snapshot.get("operation_id") != requested_operation_id:
        return False, "operation_id_mismatch"
    if snapshot.get("target_id") != cfg["id"]:
        return False, "cross_object_denied"
    if snapshot.get("post_type") != cfg["type"]:
        return False, "type_mismatch"
    if current_status != "draft":
        return False, "target_not_draft"
    return True, "ok"


# Strict payload whitelist mirror (control-layer pre-validation before calling WP).
_ALLOWED_PAYLOAD_KEYS = {"operation_id", "base_hash", "_elementor_data"}


def payload_is_strict(body: dict) -> bool:
    if not isinstance(body, dict):
        return False
    return set(body.keys()) == _ALLOWED_PAYLOAD_KEYS
