import asyncio
from datetime import datetime, timedelta, timezone
import pytest
from types import SimpleNamespace
from test_web_identity import DB
import web_workers as workers
import web_personal_storage as storage


@pytest.fixture
def scan(monkeypatch):
    db = DB()
    monkeypatch.setattr(workers, 'storage_ready', lambda: True)
    monkeypatch.setenv('WEB_CLAMAV_PRIVATE_HOST', 'test-private')
    monkeypatch.setattr(storage, 'read', lambda row: b'FICTICIO')
    monkeypatch.setattr(workers, 'scan_bytes', lambda data: 'CLEAN')
    return db


def test_failure_remains_closed_and_retries_after_delay(scan, monkeypatch):
    scan.raw.web_personal_documents.insert_one({'document_id': 'd', 'scan_state': 'QUARANTINED'})
    def unavailable(data): raise TimeoutError()
    monkeypatch.setattr(workers, 'scan_bytes', unavailable)
    assert asyncio.run(workers.scan_document_once(scan))['scan_state'] == 'SCAN_FAILED'
    assert asyncio.run(workers.scan_document_once(scan))['processed'] is False
    scan.raw.web_personal_documents.update_one({}, {'$set': {'scan_retry_at': datetime.now(timezone.utc)-timedelta(seconds=1)}})
    monkeypatch.setattr(workers, 'scan_bytes', lambda data: 'CLEAN')
    assert asyncio.run(workers.scan_document_once(scan))['scan_state'] == 'CLEAN'
    assert scan.raw.web_personal_documents.find_one({})['scan_attempts'] == 2
    assert scan.raw.web_access_reviews.count_documents({}) == 0


def test_expired_scan_reclaimed_but_active_scan_not_duplicated(scan):
    scan.raw.web_personal_documents.insert_one({'document_id': 'd', 'scan_state': 'SCANNING', 'scan_lease_until': datetime.now(timezone.utc)+timedelta(minutes=1)})
    assert asyncio.run(workers.scan_document_once(scan))['processed'] is False
    scan.raw.web_personal_documents.update_one({}, {'$set': {'scan_lease_until': datetime.now(timezone.utc)-timedelta(seconds=1)}})
    assert asyncio.run(workers.scan_document_once(scan))['scan_state'] == 'CLEAN'


@pytest.mark.parametrize('state', ['INFECTED', 'CLEAN'])
def test_terminal_states_never_rescanned(scan, state):
    scan.raw.web_personal_documents.insert_one({'scan_state': state})
    assert asyncio.run(workers.scan_document_once(scan))['processed'] is False


def test_exhausted_failure_requires_intervention(scan):
    scan.raw.web_personal_documents.insert_one({'scan_state': 'SCAN_FAILED', 'scan_attempts': 5, 'scan_retry_at': datetime.now(timezone.utc)-timedelta(days=1)})
    assert asyncio.run(workers.scan_document_once(scan))['processed'] is False


@pytest.mark.parametrize('code,expected', [(0, 'CLEAN'), (1, 'INFECTED'), (2, None)])
def test_local_scanner_exit_codes_fail_closed(monkeypatch, code, expected):
    monkeypatch.setenv('WEB_SCAN_MODE', 'local-clamscan')
    def run(args, **kwargs):
        from pathlib import Path
        assert Path(args[-1]).read_bytes() == b'FICTICIO'
        assert kwargs['timeout'] == 120
        return SimpleNamespace(returncode=code)
    monkeypatch.setattr(workers.subprocess, 'run', run)
    if expected:
        assert workers.scan_bytes(b'FICTICIO') == expected
    else:
        with pytest.raises(RuntimeError): workers.scan_bytes(b'FICTICIO')
