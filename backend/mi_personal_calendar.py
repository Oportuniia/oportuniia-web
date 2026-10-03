"""Private personalized Premium calendar; explicitly consented, revocable.

A historical payroll signal is NOT a forward payroll date. User supplies
their currently confirmed recurring day, optional lead days, and timezone.
All entries default inactive until explicit enable; no fiscal schedules are
generated from old declarations.
"""
from __future__ import annotations

import calendar
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import HTTPException

ZONE="Europe/Madrid"
KINDS={"PAYROLL_PAYMENT_DAY"}
MAX_LEAD=7


def next_payroll_occurrence(*, now: datetime, day: int, lead_days: int=0):
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    if type(day) is not int or not 1<=day<=28:
        raise ValueError("explicit payroll day from 1 to 28 required")
    if type(lead_days) is not int or not 0<=lead_days<=MAX_LEAD:
        raise ValueError("invalid notification lead")
    local=now.astimezone(ZoneInfo(ZONE))
    year,month=local.year,local.month
    for _ in range(3):
        # Fixed 10:00 local time avoids overnight/dst ambiguous send times.
        event=datetime(year,month,day,10,tzinfo=ZoneInfo(ZONE))
        notify=event-timedelta(days=lead_days)
        if notify.astimezone(timezone.utc)>now.astimezone(timezone.utc):
            return {"event_at":event.astimezone(timezone.utc),
                    "notify_at":notify.astimezone(timezone.utc)}
        month+=1
        if month>12:year,month=year+1,1
    raise ValueError("no valid future occurrence")


async def set_payroll_calendar(db, actor, *, signal_id: str,
                               enabled: bool, lead_days: int=1):
    """Manage only caller's confirmed payroll signal, not inferred proposals."""
    if not actor or not actor.get("actor_id"):
        raise HTTPException(401,"Sesión necesaria")
    if not isinstance(signal_id,str) or not re.fullmatch(r"[0-9a-f]{32}",signal_id):
        raise HTTPException(404,"Dato confirmado no encontrado")
    if type(enabled) is not bool or type(lead_days) is not int or not 0<=lead_days<=MAX_LEAD:
        raise HTTPException(422,"Preferencia de calendario no válida")
    result=await db.mi_secretary_signals.find_one({
        "actor_id":actor["actor_id"],"signal_id":signal_id,
        "kind":"PAYROLL_PAYMENT_DAY","active":True,
        "source":"OWNER_CONFIRMED_DOCUMENT_PROPOSAL",
    })
    if not result:
        raise HTTPException(404,"Día de cobro confirmado no encontrado")
    day=result.get("confirmed_value")
    if type(day) is not int or not 1<=day<=28:
        raise HTTPException(422,"Confirma un día de cobro del 1 al 28")
    now=datetime.now(timezone.utc)
    changes={"calendar_enabled":enabled,"calendar_updated_at":now,
             "calendar_version":result.get("calendar_version",0)+1}
    if enabled:
        changes.update({"calendar_lead_days":lead_days,"calendar_timezone":ZONE})
    update=await db.mi_secretary_signals.update_one(
        {"actor_id":actor["actor_id"],"signal_id":signal_id,
         "active":True,"calendar_version":result.get("calendar_version",0)},
        {"$set":changes},
    )
    if update.modified_count!=1:
        raise HTTPException(409,"Preferencias modificadas: actualiza tu calendario")
    return {"signal_id":signal_id,"calendar_enabled":enabled,
            "lead_days":lead_days if enabled else None}


async def list_payroll_calendar(db,actor,*,now:datetime):
    if not actor or not actor.get("actor_id"):
        raise HTTPException(401,"Sesión necesaria")
    cursor=db.mi_secretary_signals.find(
        {"actor_id":actor["actor_id"],"active":True,"calendar_enabled":True,
         "kind":"PAYROLL_PAYMENT_DAY"},
        {"_id":0,"signal_id":1,"confirmed_value":1,"calendar_lead_days":1},
    ).limit(30)
    items=[]
    async for row in cursor:
        try:
            next_event=next_payroll_occurrence(
                now=now,day=row["confirmed_value"],
                lead_days=row.get("calendar_lead_days",1),
            )
        except (ValueError,KeyError):
            continue
        items.append({"signal_id":row["signal_id"],"kind":"PAYROLL_REMINDER",
                      "local_timezone":ZONE,**next_event})
    return items
