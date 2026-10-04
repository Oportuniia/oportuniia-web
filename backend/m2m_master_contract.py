"""OPORTUNIIA M2M MASTER v1 transport contract helpers.

Sandbox/common contract layer. Business contracts remain sovereign.
No network, database, or production side effects are performed here.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

EVENT_SCHEMA_VERSION = "OPORTUNIIA_M2M_EVENT_v1"
ACK_SCHEMA_VERSION = "OPORTUNIIA_M2M_ACK_v1"
HASH_ALGORITHM = "SHA-256"
ACK_STATUSES = {"ACCEPTED", "REPLAYED", "CONFLICT", "REJECTED"}
RETRY_OFFSETS_SECONDS = (0, 300, 900, 1800, 3600, 5400)


class M2MContractError(ValueError):
    """Fail-closed validation error for the common transport contract."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def universal_json_bytes(value: Any) -> bytes:
    """Return the universal deterministic JSON representation used for hashing."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def payload_hash(payload: Any) -> str:
    return hashlib.sha256(universal_json_bytes(payload)).hexdigest()


def build_event(
    *,
    event_type: str,
    producer: str,
    consumer: str,
    contract_name: str,
    contract_version: str,
    payload: Any,
    event_id: str | None = None,
    correlation_id: str | None = None,
    occurred_at: str | None = None,
    timestamp: str | None = None,
    nonce: str | None = None,
    attempt: int = 1,
) -> dict[str, Any]:
    if not 1 <= attempt <= 6:
        raise M2MContractError("attempt must be between 1 and 6")

    eid = event_id or str(uuid4())
    cid = correlation_id or str(uuid4())
    event = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": eid,
        "event_type": event_type,
        "producer": producer,
        "consumer": consumer,
        "contract_name": contract_name,
        "contract_version": contract_version,
        "correlation_id": cid,
        "occurred_at": occurred_at or utc_now_iso(),
        "payload_hash": payload_hash(payload),
        "hash_algorithm": HASH_ALGORITHM,
        "payload": payload,
        "transport": {
            "timestamp": timestamp or utc_now_iso(),
            "nonce": nonce or str(uuid4()),
            "attempt": attempt,
        },
    }
    validate_event(event)
    return event


def validate_event(event: Mapping[str, Any]) -> None:
    required = {
        "schema_version", "event_id", "event_type", "producer", "consumer",
        "contract_name", "contract_version", "correlation_id", "occurred_at",
        "payload_hash", "hash_algorithm", "payload",
    }
    missing = sorted(required - set(event))
    if missing:
        raise M2MContractError(f"missing required fields: {', '.join(missing)}")
    if event["schema_version"] != EVENT_SCHEMA_VERSION:
        raise M2MContractError("unsupported event schema_version")
    if event["hash_algorithm"] != HASH_ALGORITHM:
        raise M2MContractError("unsupported hash algorithm")
    expected = payload_hash(event["payload"])
    if event["payload_hash"] != expected:
        raise M2MContractError("payload_hash mismatch")

    transport = event.get("transport")
    if transport is not None:
        attempt = transport.get("attempt", 1)
        if not isinstance(attempt, int) or not 1 <= attempt <= 6:
            raise M2MContractError("transport.attempt must be between 1 and 6")


def build_ack(
    *,
    event: Mapping[str, Any],
    receiver: str,
    ack_status: str,
    business_state: str | None = None,
    error_code: str | None = None,
    received_at: str | None = None,
) -> dict[str, Any]:
    validate_event(event)
    if ack_status not in ACK_STATUSES:
        raise M2MContractError("invalid ack_status")
    ack = {
        "schema_version": ACK_SCHEMA_VERSION,
        "event_id": event["event_id"],
        "correlation_id": event["correlation_id"],
        "payload_hash": event["payload_hash"],
        "receiver": receiver,
        "ack_status": ack_status,
        "received_at": received_at or utc_now_iso(),
        "business_state": business_state,
        "error_code": error_code,
    }
    validate_ack(ack, event=event)
    return ack


def validate_ack(ack: Mapping[str, Any], *, event: Mapping[str, Any] | None = None) -> None:
    required = {
        "schema_version", "event_id", "correlation_id", "payload_hash",
        "receiver", "ack_status", "received_at",
    }
    missing = sorted(required - set(ack))
    if missing:
        raise M2MContractError(f"missing ACK fields: {', '.join(missing)}")
    if ack["schema_version"] != ACK_SCHEMA_VERSION:
        raise M2MContractError("unsupported ACK schema_version")
    if ack["ack_status"] not in ACK_STATUSES:
        raise M2MContractError("invalid ack_status")

    if event is not None:
        validate_event(event)
        for field in ("event_id", "correlation_id", "payload_hash"):
            if ack[field] != event[field]:
                raise M2MContractError(f"ACK {field} mismatch")
        if ack["receiver"] != event["consumer"]:
            raise M2MContractError("ACK receiver mismatch")


def retry_offset_seconds(attempt: int) -> int:
    if not 1 <= attempt <= len(RETRY_OFFSETS_SECONDS):
        raise M2MContractError("attempt must be between 1 and 6")
    return RETRY_OFFSETS_SECONDS[attempt - 1]
