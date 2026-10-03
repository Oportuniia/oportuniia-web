from datetime import datetime, timezone
import pytest
from mi_mail_templates import render_notice


def test_offer_message_discloses_only_deadline_in_local_time():
    notice={"kind":"OFFER_DOCUMENT_DEADLINE","threshold_hours":24,
            "deadline":datetime(2026,10,6,12,tzinfo=timezone.utc),
            "actor_id":"mi_private","offer_id":"private-id"}
    subject,body=render_notice(notice)
    assert "OPORTUNIIA" in subject
    assert "06/10/2026 a las 14:00" in body
    assert "tres días" in body
    assert "mi_private" not in body
    assert "private-id" not in body
    assert "https://oportuniia.com/mi-oportuniia" in body


def test_premium_message_never_reveals_document_name():
    subject,body=render_notice({
        "kind":"PREMIUM_DOCUMENT_REVIEW","display_name":"DNI PRIVADO.pdf",
        "actor_id":"mi_private",
    })
    assert "DNI PRIVADO.pdf" not in subject+body
    assert "desactivar" in body


def test_no_unapproved_redirect_or_missing_timezone():
    with pytest.raises(ValueError):
        render_notice({"kind":"PREMIUM_DOCUMENT_REVIEW"},
                      web_area_url="https://attacker.example.test")
    with pytest.raises(ValueError):
        render_notice({"kind":"OFFER_DOCUMENT_DEADLINE",
                       "threshold_hours":24,
                       "deadline":datetime(2026,10,6)})
