"""Plan private payroll reminders ONLY from explicitly enabled confirmed signals.

Hourly scheduling window; single stable key per signal/config-version/month.
No dates derived from OCR alone and no fiscal deadline inference.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo

ZONE=ZoneInfo("Europe/Madrid")

def plan_payroll_reminder(signal, *, actor, entitlement, now):
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    at=now.astimezone(timezone.utc)
    if not actor or actor.get("document_reminders") is not True:
        return None
    if not entitlement or entitlement.get("actor_id")!=signal.get("actor_id"):
        return None
    try:
        if not (entitlement.get("status")=="ACTIVE" and entitlement.get("source_verified") is True
                and entitlement["valid_from"]<=at<entitlement["expires_at"]):
            return None
    except (KeyError,TypeError):
        return None
    if not (signal.get("kind")=="PAYROLL_PAYMENT_DAY"
            and signal.get("source")=="OWNER_CONFIRMED_DOCUMENT_PROPOSAL"
            and signal.get("active") is True and signal.get("calendar_enabled") is True
            and signal.get("calendar_timezone")=="Europe/Madrid"):
        return None
    day=signal.get("confirmed_value")
    lead=signal.get("calendar_lead_days")
    version=signal.get("calendar_version")
    signal_id=signal.get("signal_id")
    owner=signal.get("actor_id")
    if (type(day) is not int or not 1<=day<=28
        or type(lead) is not int or not 0<=lead<=7
        or type(version) is not int or version<1
        or not isinstance(signal_id,str) or len(signal_id)!=32
        or not isinstance(owner,str) or not owner.startswith("mi_")):
        return None
    # Scan current and next LOCAL months so day-1 events with lead 7 can
    # become due at the end of the preceding month.
    local=at.astimezone(ZONE)
    for offset in (0,1):
        index=(local.year*12+local.month-1)+offset
        year,month=divmod(index,12)
        month+=1
        event=datetime(year,month,day,10,tzinfo=ZONE).astimezone(timezone.utc)
        notify=(datetime(year,month,day,10,tzinfo=ZONE)-timedelta(days=lead)).astimezone(timezone.utc)
        if notify<=at<notify+timedelta(hours=1):
            return {
                "kind":"PREMIUM_PAYROLL_REMINDER",
                "key":f"payroll:{owner}:{signal_id}:v{version}:{year:04d}-{month:02d}",
                "actor_id":owner,"signal_id":signal_id,"calendar_version":version,
                "event_at":event,"notify_at":notify,
                "redact_attachment_details":True,
            }
    return None
