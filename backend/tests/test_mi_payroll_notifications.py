from datetime import datetime,timedelta,timezone
import pytest
from mi_payroll_notifications import plan_payroll_reminder
from mi_mail_templates import render_notice

T=datetime(2026,10,3,8,tzinfo=timezone.utc)
OWNER="mi_owner"
SIGNAL={"actor_id":OWNER,"signal_id":"a"*32,"kind":"PAYROLL_PAYMENT_DAY",
        "source":"OWNER_CONFIRMED_DOCUMENT_PROPOSAL","active":True,
        "calendar_enabled":True,"calendar_timezone":"Europe/Madrid",
        "calendar_lead_days":1,"calendar_version":1,"confirmed_value":4}
ACTOR={"actor_id":OWNER,"document_reminders":True}
SUB={"actor_id":OWNER,"status":"ACTIVE","source_verified":True,
     "valid_from":T-timedelta(days=7),"expires_at":T+timedelta(days=40)}

def test_due_once_and_no_private_details():
    notice=plan_payroll_reminder(SIGNAL,actor=ACTOR,entitlement=SUB,now=T)
    assert notice is not None
    assert notice["kind"]=="PREMIUM_PAYROLL_REMINDER"
    assert notice["key"].endswith("v1:2026-10")
    assert "salary" not in str(notice) and "email" not in str(notice)
    assert not plan_payroll_reminder(SIGNAL,actor=ACTOR,entitlement=SUB,now=T+timedelta(hours=1))

def test_revoke_optout_and_version_change_stops_old_plan():
    assert plan_payroll_reminder({**SIGNAL,"calendar_enabled":False},
                                actor=ACTOR,entitlement=SUB,now=T) is None
    assert plan_payroll_reminder(SIGNAL,actor={**ACTOR,"document_reminders":False},
                                entitlement=SUB,now=T) is None
    assert plan_payroll_reminder(SIGNAL,actor=ACTOR,entitlement={**SUB,"source_verified":False},
                                now=T) is None
    updated=plan_payroll_reminder({**SIGNAL,"calendar_version":2},
                                 actor=ACTOR,entitlement=SUB,now=T)
    assert updated["key"]!=plan_payroll_reminder(SIGNAL,actor=ACTOR,
                                                  entitlement=SUB,now=T)["key"]

def test_lead_days_cross_month_and_december_to_january():
    from zoneinfo import ZoneInfo
    local=datetime(2026,12,27,10,tzinfo=ZoneInfo("Europe/Madrid"))
    signal={**SIGNAL,"confirmed_value":2,"calendar_lead_days":6}
    notice=plan_payroll_reminder(signal,actor=ACTOR,
      entitlement={**SUB,"expires_at":datetime(2027,2,1,tzinfo=timezone.utc)},
      now=local.astimezone(timezone.utc))
    # Input subscription started October 2026; Jan 2 2027 due Dec 27 2026
    assert notice["key"].endswith("2027-01")

def test_neutral_email_body():
    subject,body=render_notice({"kind":"PREMIUM_PAYROLL_REMINDER",
        "employer":"CONFIDENTIAL COMPANY","salary":"90000","day":4})
    assert "agenda personal" in body
    assert "CONFIDENTIAL" not in subject+body and "90000" not in body
