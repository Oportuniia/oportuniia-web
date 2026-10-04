"""No secrets and no network: corporate sender and transport preflight tests."""
import pytest
from mi_corporate_mail import CORPORATE_WEB_SENDER, mailbox_config, send_corporate_message


def test_corporate_sender_is_fail_closed(monkeypatch):
    for key in ("MI_SMTP_ENABLED","MI_SMTP_HOST","MI_SMTP_USER",
                "MI_SMTP_PASSWORD","MI_SMTP_FROM"):
        monkeypatch.delenv(key,raising=False)
    with pytest.raises(RuntimeError):
        mailbox_config()


def test_non_web_sender_is_never_accepted(monkeypatch):
    monkeypatch.setenv("MI_SMTP_ENABLED","1")
    monkeypatch.setenv("MI_SMTP_FROM","info.personal@oportuniia.com")
    with pytest.raises(RuntimeError):
        mailbox_config()


def test_expected_sender_tls_only(monkeypatch):
    monkeypatch.setenv("MI_SMTP_ENABLED","1")
    monkeypatch.setenv("MI_SMTP_FROM",CORPORATE_WEB_SENDER)
    monkeypatch.setenv("MI_SMTP_HOST","smtp.example.test")
    monkeypatch.setenv("MI_SMTP_USER","smtp-alias")
    monkeypatch.setenv("MI_SMTP_PASSWORD","mock-secret")
    monkeypatch.setenv("MI_SMTP_PORT","587")
    assert mailbox_config()["sender"]==CORPORATE_WEB_SENDER
    monkeypatch.setenv("MI_SMTP_PORT","25")
    with pytest.raises(RuntimeError):
        mailbox_config()


def test_invalid_destination_rejected_before_smtp(monkeypatch):
    with pytest.raises(ValueError):
        send_corporate_message(to="bad@example.test\r\nBcc:someone@example.test",
                               subject="test",body="body")
