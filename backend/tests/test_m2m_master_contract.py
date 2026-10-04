try:
    from backend.m2m_master_contract import (
        M2MContractError,
        build_ack,
        build_event,
        payload_hash,
        retry_offset_seconds,
        validate_ack,
        validate_event,
    )
except ModuleNotFoundError:
    from m2m_master_contract import (
        M2MContractError,
        build_ack,
        build_event,
        payload_hash,
        retry_offset_seconds,
        validate_ack,
        validate_event,
    )


def test_hash_is_deterministic_for_key_order():
    assert payload_hash({"b": 2, "a": 1}) == payload_hash({"a": 1, "b": 2})


def test_event_and_ack_match():
    event = build_event(
        event_type="TEST",
        producer="CORE",
        consumer="IA",
        contract_name="TEST_CONTRACT_v1",
        contract_version="1",
        payload={"ok": True},
        event_id="evt-test-0001",
        correlation_id="corr-test-0001",
    )
    validate_event(event)
    ack = build_ack(event=event, receiver="IA", ack_status="ACCEPTED")
    validate_ack(ack, event=event)


def test_modified_payload_fails_closed():
    event = build_event(
        event_type="TEST",
        producer="CORE",
        consumer="IA",
        contract_name="TEST_CONTRACT_v1",
        contract_version="1",
        payload={"value": 1},
        event_id="evt-test-0002",
        correlation_id="corr-test-0002",
    )
    event["payload"] = {"value": 2}
    try:
        validate_event(event)
    except M2MContractError:
        pass
    else:
        raise AssertionError("modified payload must fail closed")


def test_retry_policy_is_exact_master_sequence():
    assert [retry_offset_seconds(i) for i in range(1, 7)] == [0, 300, 900, 1800, 3600, 5400]
