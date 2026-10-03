"""Check live authorizations again AFTER outbox claim and BEFORE delivery.

The send adapter must call these immediately before transport. Provider
timeouts remain RECONCILE, not auto-retried. The adapter must also store proof
of provider acceptance; inbox delivery is a distinct fact.
"""
from __future__ import annotations
from datetime import datetime, timezone
from mi_document_notifications import premium_document_review_reminder
from mi_payroll_notifications import plan_payroll_reminder


def _now(now):
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return now.astimezone(timezone.utc)


async def revalidate_claimed_notice(db, notice, *, now):
    """Strict owner-scoped checks; return False unless fully eligible."""
    at=_now(now)
    if notice.get("state")!="CLAIMED" or not notice.get("actor_id"):
        return False
    if notice.get("kind")=="OFFER_DOCUMENT_DEADLINE":
        offer=await db.mi_offers.find_one({
            "offer_id":notice.get("offer_id"),
            "actor_id":notice["actor_id"],
            "state":"AWAITING_DOCUMENTS",
            "documents_verified_at":{"$exists":False},
        })
        if not offer or not offer.get("notice_delivery_ref"):
            return False
        deadline=offer.get("document_deadline")
        if not isinstance(deadline,datetime) or deadline.tzinfo is None:
            return False
        from mi_document_notifications import offer_deadline_notifications
        try:
            plans=offer_deadline_notifications(offer,now=at)
        except (ValueError,KeyError,TypeError):
            return False
        return any(item["key"]==notice.get("key") for item in plans)
    if notice.get("kind")=="PREMIUM_PAYROLL_REMINDER":
        actor_id=notice["actor_id"]
        actor=await db.mi_actors.find_one({
            "actor_id":actor_id,"email_verified":True,
            "validation_state":"VERIFIED","document_reminders":True,
        })
        if not actor:
            return False
        entitlement=await db.mi_premium_entitlements.find_one({
            "actor_id":actor_id,"status":"ACTIVE","source_verified":True,
            "valid_from":{"$lte":at},"expires_at":{"$gt":at},
        })
        if not entitlement:
            return False
        signal=await db.mi_secretary_signals.find_one({
            "actor_id":actor_id,"signal_id":notice.get("signal_id"),
            "kind":"PAYROLL_PAYMENT_DAY","active":True,
            "calendar_enabled":True,
            "calendar_version":notice.get("calendar_version"),
        })
        if not signal:
            return False
        try:
            plan=plan_payroll_reminder(signal,actor=actor,
                                      entitlement=entitlement,now=at)
        except (ValueError,KeyError,TypeError):
            return False
        return bool(plan and plan["key"]==notice.get("key"))
    if notice.get("kind")=="PREMIUM_DOCUMENT_REVIEW":
        actor_id=notice["actor_id"]
        actor=await db.mi_actors.find_one({
            "actor_id":actor_id,"email_verified":True,
            "validation_state":"VERIFIED",
        })
        if not actor or actor.get("document_reminders") is not True:
            return False
        subscription=await db.mi_premium_entitlements.find_one({
            "actor_id":actor_id,"status":"ACTIVE","source_verified":True,
            "valid_from":{"$lte":at},"expires_at":{"$gt":at},
        })
        if not subscription:
            return False
        document=await db.mi_user_files.find_one({
            "actor_id":actor_id,"file_id":notice.get("file_id"),
            "status":"AVAILABLE","review_reminders":True,
        })
        if not document:
            return False
        try:
            plan=premium_document_review_reminder(
                document,subscription,{"document_reminders":True},now=at)
        except (ValueError,KeyError,TypeError):
            return False
        return bool(plan and plan["key"]==notice.get("key"))
    return False
