"""Dry-run delivery harness for WEB private notification outbox.

Never sends SMTP or opens n8n endpoints. This harness simulates the precise
worker contract, revalidates live authorization, and records only MOCK receipts.
Do not invoke against production collections: it is deliberately mock-only.
"""
from __future__ import annotations

from datetime import datetime,timezone

from mi_notification_outbox import claim_one, cancel_claimed, mark_sent, mark_uncertain
from mi_notification_validation import revalidate_claimed_notice
from mi_mail_templates import render_notice


async def dry_run_once(db, *, now: datetime, worker_id: str = "mock-notify-v1",
                       simulate: str = "accepted"):
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise ValueError("timezone-aware time required")
    if not worker_id.startswith("mock-"):
        raise ValueError("sandbox worker ID required")
    if simulate not in {"accepted","ambiguous"}:
        raise ValueError("unsupported mock transport")
    at=now.astimezone(timezone.utc)
    notice=await claim_one(db,worker_id=worker_id,now=at)
    if not notice:
        return {"result":"EMPTY"}
    eligible=await revalidate_claimed_notice(db,notice,now=at)
    if not eligible:
        cancelled=await cancel_claimed(
            db,key=notice["key"],worker_id=worker_id,reason="NOT_ELIGIBLE",now=at)
        if not cancelled:
            # A losing cancellation race must never trigger transport.
            return {"result":"RECONCILE_MANUALLY"}
        return {"result":"CANCELLED"}
    # Verify that only a reviewed minimal template will be handed off later.
    subject,body=render_notice(notice)
    if not subject or not body:
        raise ValueError("invalid mock notice template")
    if simulate=="ambiguous":
        await mark_uncertain(db,key=notice["key"],worker_id=worker_id,now=at)
        return {"result":"RECONCILE"}
    # An artificial receipt tests persistence only. It is NOT evidence of
    # third-party SMTP acceptance or legally effective notification.
    saved=await mark_sent(db,key=notice["key"],worker_id=worker_id,
                         receipt="MOCK-ACCEPTED:"+notice["key"][:85],now=at)
    return {"result":"MOCK_SENT" if saved else "RECONCILE_MANUALLY"}
