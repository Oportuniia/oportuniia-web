"""Stripe adapter. Off until legal/commercial approval and server credentials.
Only signed webhooks + fresh provider state confirm payment. No browser success
URL activates Premium, verifies an identity or grants operation documents.
"""
import asyncio
import hashlib
import os
import uuid
import httpx
from datetime import datetime, timezone

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument

from investor_access import fail, future
from web_identity import public_origin, resolve_session


def plain(value):
    return value if isinstance(value, dict) else value.to_dict()


def provider():
    key = os.getenv("WEB_STRIPE_SECRET_KEY", "")
    if os.getenv("WEB_PAYMENTS_ENABLED") != "true" or os.getenv("WEB_CONTRACTING_APPROVED") != "true" or not os.getenv("WEB_STRIPE_WEBHOOK_SECRET"):
        fail("payment_gateway_not_activated", 503)
    if not key.startswith("sk_test_") and not (key.startswith("sk_live_") and os.getenv("WEB_PAYMENTS_LIVE_ENABLED") == "true"):
        fail("payment_gateway_not_activated", 503)
    import stripe
    return stripe.StripeClient(key)


async def create_checkout(db, subject, kind, *, plan="monthly", op_ref="", modality=""):
    client = provider()
    user = await db.web_users.find_one({"subject_id": subject, "active": True, "email_verified": True}, {"_id": 0})
    if not user: fail("account_not_found", 403)
    if kind == "PREMIUM":
        if plan not in {"monthly", "annual"}: fail("invalid_premium_plan", 422)
        price = os.getenv("WEB_STRIPE_PREMIUM_"+plan.upper()+"_PRICE", "")
        mode, revision = "subscription", os.getenv("WEB_PREMIUM_TERMS_VERSION", "")
    else:
        quote = await db.web_reservation_quotes.find_one({"subject_id": subject, "op_ref": op_ref, "modality": modality, "approved": True}, {"_id": 0})
        if not quote or not future(quote.get("valid_until")): fail("approved_reservation_quote_required", 409)
        price, revision, mode = quote.get("stripe_price_id", ""), quote.get("terms_version", ""), "payment"
    if not price.startswith("price_") or not revision: fail("approved_payment_price_and_terms_required", 503)
    try:
        approved_price = await asyncio.to_thread(client.v1.prices.retrieve, price)
    except Exception: fail("payment_provider_unavailable", 503)
    approved_price = plain(approved_price)
    if approved_price.get("currency") != "eur" or (approved_price.get("unit_amount") or 0) <= 0: fail("invalid_approved_payment_price", 503)
    if kind == "PREMIUM":
        recurring = approved_price.get("recurring") or {}
        if recurring.get("interval") != ("year" if plan == "annual" else "month") or recurring.get("interval_count") != 1: fail("invalid_approved_payment_interval", 503)
    elif approved_price.get("recurring"): fail("reservation_must_be_one_time", 503)
    ident = hashlib.sha256(f"{subject}|{kind}|{plan}|{op_ref}|{modality}|{revision}".encode()).hexdigest()
    intent = await db.web_checkout_intents.find_one_and_update({"_id": ident}, {"$setOnInsert": {"request_id": str(uuid.uuid4()), "subject_id": subject, "kind": kind, "plan": plan,
        "op_ref": op_ref, "modality": modality, "terms_version": revision, "price_id": price, "created_at": datetime.now(timezone.utc).isoformat()}}, upsert=True, return_document=ReturnDocument.AFTER)
    if intent.get("state") == "PAID": fail("payment_already_confirmed", 409)
    if intent.get("url"):
        if not future(intent.get("valid_until")): fail("checkout_expired_contact_team", 409)
        return {"url": intent["url"]}
    origin = public_origin()
    # A persisted request id makes concurrent clicks/retries use the same session.
    params = {"mode": mode, "client_reference_id": intent["request_id"], "customer_email": user["email"], "line_items": [{"price": price, "quantity": 1}],
        "success_url": origin+"/mi-oportuniia#notificaciones", "cancel_url": origin+"/mi-oportuniia#resumen", "consent_collection": {"terms_of_service": "required"}}
    if mode == "subscription": params["subscription_data"] = {"metadata": {"web_request_id": intent["request_id"]}}
    try:
        checkout = await asyncio.to_thread(client.v1.checkout.sessions.create, params, {"idempotency_key": intent["request_id"]})
    except Exception: fail("payment_provider_unavailable", 503)
    url = checkout.url
    if not isinstance(url, str) or not url.startswith("https://checkout.stripe.com/"): fail("invalid_checkout_url", 502)
    valid_until = datetime.fromtimestamp(checkout.expires_at, timezone.utc).isoformat()
    await db.web_checkout_intents.update_one({"_id": ident}, {"$set": {"session_id": checkout.id, "url": url, "state": "PENDING_PAYMENT", "valid_until": valid_until}})
    return {"url": url}


async def confirm_intent(db, client, intent, *, payment_received_at=None):
    try:
        checkout = await asyncio.to_thread(client.v1.checkout.sessions.retrieve, intent["session_id"])
    except Exception: fail("payment_provider_unavailable", 503)
    if checkout.client_reference_id != intent["request_id"] or checkout.payment_status != "paid": return False
    if intent["kind"] == "PREMIUM":
        try: subscription = await asyncio.to_thread(client.v1.subscriptions.retrieve, checkout.subscription)
        except Exception: fail("payment_provider_unavailable", 503)
        subscription = plain(subscription)
        if intent.get("plan") == "annual" and not subscription.get("cancel_at_period_end"):
            # Approved annual term has no obligatory renewal.
            try: subscription = await asyncio.to_thread(client.v1.subscriptions.update, checkout.subscription, {"cancel_at_period_end": True})
            except Exception: fail("payment_provider_unavailable", 503)
        subscription = plain(subscription)
        items = list(subscription["items"]["data"])
        if subscription["status"] != "active" or len(items) != 1 or items[0]["price"]["id"] != intent["price_id"]: return False
        end = items[0].get("current_period_end") or subscription.get("current_period_end", 0)
        expiry = datetime.fromtimestamp(end, timezone.utc).isoformat()
        if not future(expiry): return False
        await db.web_entitlements.update_one({"subject_id": intent["subject_id"], "product": "PREMIUM"}, {"$set": {"subject_id": intent["subject_id"], "product": "PREMIUM", "active": True,
            "valid_until": expiry, "provider": "STRIPE", "subscription_id": checkout.subscription, "customer_id": checkout.customer}}, upsert=True)
    else:
        payment_intent = checkout.payment_intent
        payment_reference = payment_intent.get("id") if isinstance(payment_intent, dict) else payment_intent
        amount_total = checkout.amount_total
        currency = str(checkout.currency or "").lower()
        if not isinstance(amount_total, int) or amount_total <= 0 or currency != "eur" or not payment_reference:
            fail("invalid_settled_reservation_payment", 409)
        if isinstance(payment_received_at, (int, float)):
            received_at = datetime.fromtimestamp(payment_received_at, timezone.utc)
        elif isinstance(payment_received_at, str):
            received_at = datetime.fromisoformat(payment_received_at.replace("Z", "+00:00"))
        else:
            received_at = datetime.fromtimestamp(checkout.created, timezone.utc)
        if received_at.tzinfo is None:
            fail("invalid_payment_received_at", 409)
        await db.web_reservations.update_one({"checkout_request_id": intent["request_id"]}, {
            "$setOnInsert": {"subject_id": intent["subject_id"], "op_ref": intent["op_ref"], "modality": intent["modality"],
                "checkout_request_id": intent["request_id"], "state": "PAID_PENDING_OPERATION_REVIEW", "terms_version": intent["terms_version"]},
            "$set": {"payment_reference": str(payment_reference), "amount_received_minor": amount_total, "currency": "EUR",
                "payment_received_at": received_at.astimezone(timezone.utc).isoformat(), "payment_provider": "STRIPE"}}, upsert=True)
    await db.web_checkout_intents.update_one({"_id": intent["_id"]}, {"$set": {"state": "PAID", "customer_id": checkout.customer, "subscription_id": checkout.subscription}})
    return True



class FinanceCloseConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checkout_request_id: str = Field(min_length=1, max_length=120)
    report_id: str = Field(min_length=1, max_length=120)
    signed_at: str = Field(min_length=1, max_length=80)
    closed_at: str = Field(min_length=1, max_length=80)


async def _finance_closer(request, db):
    user, session = await resolve_session(request, db)
    allowed = {v.strip() for v in os.getenv("WEB_FINANCE_CLOSER_SUBJECT_IDS", "").split(",") if v.strip()}
    if not allowed or user.get("subject_id") not in allowed or not user.get("mfa_enabled") or not session.get("mfa_verified"):
        fail("finance_closer_authorization_required", 403)
    return user["subject_id"]



def register_payment_routes(router, db):
    @router.post("/staff/operations/{op_ref}/finance-close")
    async def confirm_signed_operation_finance(op_ref: str, payload: FinanceCloseConfirmation, request: Request):
        actor = await _finance_closer(request, db)
        if not op_ref or len(op_ref) > 160:
            fail("invalid_operation_reference", 422)
        try:
            signed_at = datetime.fromisoformat(payload.signed_at.replace("Z", "+00:00"))
            closed_at = datetime.fromisoformat(payload.closed_at.replace("Z", "+00:00"))
            if signed_at.tzinfo is None or closed_at.tzinfo is None or closed_at < signed_at:
                raise ValueError()
        except ValueError:
            fail("invalid_signature_or_close_timestamp", 422)

        reservation = await db.web_reservations.find_one({
            "checkout_request_id": payload.checkout_request_id,
            "op_ref": op_ref,
            "state": "PAID_PENDING_OPERATION_REVIEW",
        }, {"_id": 0})
        if not reservation:
            fail("paid_operation_reservation_not_found", 404)
        if not reservation.get("payment_reference") or not reservation.get("payment_received_at") or reservation.get("currency") != "EUR":
            fail("settled_payment_details_missing", 409)
        amount_minor = reservation.get("amount_received_minor")
        if not isinstance(amount_minor, int) or amount_minor <= 0:
            fail("invalid_settled_payment_amount", 409)

        sync_url = os.getenv("OPORTUNIIAPP_FINANCE_SYNC_URL", "").strip()
        sync_key = os.getenv("OPORTUNIIAPP_WEB_FINANCE_M2M_KEY", "").strip()
        if not sync_url.startswith("https://") or not sync_key:
            fail("finance_sync_not_configured", 503)

        payment_reference = str(reservation["payment_reference"])
        event_id = "stripe:" + payment_reference + ":signed-operation"
        record = await db.web_operation_finance_closures.find_one({"checkout_request_id": payload.checkout_request_id}, {"_id": 0})
        if record and (record.get("op_ref") != op_ref or record.get("report_id") != payload.report_id):
            fail("finance_close_already_linked_differently", 409)

        confirmation = {
            "event_id": event_id,
            "report_id": payload.report_id,
            "op_ref": op_ref,
            "generated_income": round(amount_minor / 100.0, 2),
            "payment_reference": payment_reference,
            "payment_received_at": reservation["payment_received_at"],
            "signed_at": signed_at.astimezone(timezone.utc).isoformat(),
            "currency": "EUR",
            "closed_at": closed_at.astimezone(timezone.utc).isoformat(),
        }
        await db.web_operation_finance_closures.update_one(
            {"checkout_request_id": payload.checkout_request_id},
            {"$setOnInsert": {
                "checkout_request_id": payload.checkout_request_id,
                "event_id": event_id,
                "op_ref": op_ref,
                "report_id": payload.report_id,
                "confirmed_by": actor,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }, "$set": {"sync_state": "PENDING", "confirmation": confirmation}},
            upsert=True,
        )
        try:
            async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
                response = await client.post(
                    sync_url,
                    json=confirmation,
                    headers={"X-Oportuniia-Web-Finance-M2M-Key": sync_key},
                )
        except httpx.HTTPError:
            await db.web_operation_finance_closures.update_one(
                {"checkout_request_id": payload.checkout_request_id},
                {"$set": {"sync_state": "RETRY_REQUIRED", "last_attempt_at": datetime.now(timezone.utc).isoformat()}},
            )
            fail("finance_sync_unavailable_retry", 502)
        if response.status_code < 200 or response.status_code >= 300:
            await db.web_operation_finance_closures.update_one(
                {"checkout_request_id": payload.checkout_request_id},
                {"$set": {"sync_state": "RETRY_REQUIRED", "last_http_status": response.status_code, "last_attempt_at": datetime.now(timezone.utc).isoformat()}},
            )
            fail("finance_sync_rejected_retry", 502)
        await db.web_operation_finance_closures.update_one(
            {"checkout_request_id": payload.checkout_request_id},
            {"$set": {"sync_state": "SYNCED", "synced_at": datetime.now(timezone.utc).isoformat(), "last_http_status": response.status_code}},
        )
        return {"confirmed": True, "finance_sync": "SYNCED", "event_id": event_id}

    @router.post("/payments/stripe/webhook")
    async def webhook(request: Request):
        import stripe
        client = provider()
        raw = await request.body()
        if len(raw) > 1024*1024: fail("webhook_too_large", 413)
        try: event = stripe.Webhook.construct_event(raw, request.headers.get("stripe-signature", ""), os.environ["WEB_STRIPE_WEBHOOK_SECRET"], tolerance=300)
        except Exception: fail("invalid_webhook_signature", 400)
        event = plain(event)
        expected_live = os.environ["WEB_STRIPE_SECRET_KEY"].startswith("sk_live_")
        if bool(event.get("livemode")) != expected_live: fail("payment_environment_mismatch", 400)
        # Set-on-insert ledger, but retry pending/failed processing after interruptions.
        await db.web_payment_events.update_one({"_id": event["id"]}, {"$setOnInsert": {"event_type": event["type"], "processed": False}}, upsert=True)
        ledger = await db.web_payment_events.find_one({"_id": event["id"]})
        if ledger.get("processed"): return {"received": True}
        obj = event["data"]["object"]
        if event["type"] in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
            intent = await db.web_checkout_intents.find_one({"session_id": obj["id"]})
            if intent: await confirm_intent(db, client, intent, payment_received_at=event.get("created"))
        elif event["type"] in {"customer.subscription.deleted", "customer.subscription.updated", "invoice.payment_failed", "charge.refunded", "charge.dispute.created"}:
            # Fail closed on cancellation/non-active state, payment failure or dispute.
            if event["type"] != "customer.subscription.updated" or obj.get("status") != "active":
                await db.web_entitlements.update_many({"provider": "STRIPE", "customer_id": obj.get("customer")}, {"$set": {"active": False}})
        elif event["type"] == "invoice.paid":
            intents = await db.web_checkout_intents.find({"customer_id": obj.get("customer"), "kind": "PREMIUM"}).to_list(100)
            for intent in intents: await confirm_intent(db, client, intent)
        await db.web_payment_events.update_one({"_id": event["id"]}, {"$set": {"processed": True}})
        return {"received": True}
