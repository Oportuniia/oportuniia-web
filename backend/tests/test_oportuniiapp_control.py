import os
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# server requires runtime env at import.
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test")

import server

client = TestClient(server.app)
PATH = "/api/integrations/oportuniiapp/v1/subscriber-portfolio"
HEAD = {
    "x-oportuniia-web-app-m2m-key": "test-key",
    "x-app-subject": "app-user-1",
    "X-OPORTUNIIA-Correlation-ID": "corr-test-0001",
}

def test_missing_config_503(monkeypatch):
    monkeypatch.delenv(server.WEB_APP_KEY_ENV, raising=False)
    assert client.get(PATH, headers=HEAD).status_code == 503

def test_bad_key_401(monkeypatch):
    monkeypatch.setenv(server.WEB_APP_KEY_ENV, "test-key")
    h = dict(HEAD); h["x-oportuniia-web-app-m2m-key"] = "wrong"
    assert client.get(PATH, headers=h).status_code == 401

def test_invalid_subject_400(monkeypatch):
    monkeypatch.setenv(server.WEB_APP_KEY_ENV, "test-key")
    h = dict(HEAD); h["x-app-subject"] = ""
    assert client.get(PATH, headers=h).status_code == 400

def test_not_registered_200(monkeypatch):
    monkeypatch.setenv(server.WEB_APP_KEY_ENV, "test-key")
    with patch.object(server, "_resolve_web_subject", AsyncMock(return_value=(False, None))):
        r = client.get(PATH, headers=HEAD)
    assert r.status_code == 200
    data = r.json()
    assert data["schema_version"] == "WEB_OPORTUNIIAPP_SUBSCRIBER_PORTFOLIO_v1"
    assert data["registration"] == {"registered": False, "status": "NOT_REGISTERED"}
    assert data["investors"] == []
    assert data["correlation_id"] == "corr-test-0001"

def test_registered_200(monkeypatch):
    monkeypatch.setenv(server.WEB_APP_KEY_ENV, "test-key")
    with patch.object(server, "_resolve_web_subject", AsyncMock(return_value=(True, "web-1"))):
        r = client.get(PATH, headers=HEAD)
    assert r.status_code == 200
    assert r.json()["registration"] == {"registered": True, "status": "REGISTERED"}

def test_repeat_has_no_business_side_effect(monkeypatch):
    monkeypatch.setenv(server.WEB_APP_KEY_ENV, "test-key")
    resolver = AsyncMock(return_value=(False, None))
    with patch.object(server, "_resolve_web_subject", resolver):
        a = client.get(PATH, headers=HEAD).json()
        b = client.get(PATH, headers=HEAD).json()
    assert a["registration"] == b["registration"]
    assert a["investors"] == b["investors"] == []
    assert resolver.await_count == 2
