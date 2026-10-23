"""Provider contract tests with fake credentials; not a live delivery test."""
import base64
from email import policy
from email.parser import BytesParser

import pytest
import web_gmail as gmail


@pytest.fixture
def config(monkeypatch):
    for key in gmail.ENV_KEYS:
        monkeypatch.setenv(key, "fictitious")
    monkeypatch.setenv("WEB_MAIL_FROM", "OPORTUNIIA <web@example.com>")


class Reply:
    def __init__(self, status, payload): self.status_code, self.payload = status, payload
    def json(self): return self.payload


def test_https_multipart_confirmation(config, monkeypatch):
    calls = []
    def post(url, **kw):
        calls.append((url, kw))
        return Reply(200, {"access_token": "fake", "scope": gmail.SCOPE}) if len(calls) == 1 else Reply(200, {"id": "fake-id"})
    monkeypatch.setattr(gmail.requests, "post", post)
    gmail.deliver("test@example.com", "Confirmación", "Confirmar mi correo: https://portal.test/cuenta#verify=fake")
    assert len(calls) == 2
    assert all(call[1]["allow_redirects"] is False for call in calls)
    message = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(calls[1][1]["json"]["raw"]))
    assert message["From"] == "OPORTUNIIA <web@example.com>"
    assert message["To"] == "test@example.com"
    assert message.get_body(preferencelist=("plain",))
    assert '>Confirmar mi correo</a>' in message.get_body(preferencelist=("html",)).get_content()


@pytest.mark.parametrize("status,payload", [(401, {"error": "secret-material"}), (200, {}), (200, {"access_token": "fake", "scope": "gmail.readonly"})])
def test_reject_bad_authorization_without_exposing_response(config, monkeypatch, status, payload):
    calls = []
    def post(*a, **kw): calls.append(a); return Reply(status, payload)
    monkeypatch.setattr(gmail.requests, "post", post)
    with pytest.raises(RuntimeError, match="^gmail_authorization_failed$"):
        gmail.deliver("test@example.com", "Test", "Test")
    assert len(calls) == 1


def test_missing_configuration_does_not_send(monkeypatch):
    for key in gmail.ENV_KEYS: monkeypatch.delenv(key, raising=False)
    assert not gmail.ready()
    with pytest.raises(RuntimeError, match="gmail_not_configured"):
        gmail.deliver("test@example.com", "Test", "Test")


@pytest.mark.parametrize("reply", [Reply(500, {"error": "private-provider-detail"}), Reply(200, {})])
def test_provider_failure_is_not_reported_as_sent(config, monkeypatch, reply):
    calls = []
    def post(*a, **kw):
        calls.append(a)
        return Reply(200, {"access_token": "fake", "scope": gmail.SCOPE}) if len(calls) == 1 else reply
    monkeypatch.setattr(gmail.requests, "post", post)
    with pytest.raises(RuntimeError, match="^gmail_delivery_failed$"):
        gmail.deliver("test@example.com", "Test", "Test")
    assert len(calls) == 2


def test_timeout_does_not_repeat_send(config, monkeypatch):
    calls = []
    def post(*a, **kw):
        calls.append(a)
        if len(calls) == 1: return Reply(200, {"access_token": "fake", "scope": gmail.SCOPE})
        raise gmail.requests.Timeout("fake timeout")
    monkeypatch.setattr(gmail.requests, "post", post)
    with pytest.raises(gmail.requests.Timeout):
        gmail.deliver("test@example.com", "Test", "Test")
    assert len(calls) == 2
