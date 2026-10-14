"""Stripe adapter. Off until legal/commercial approval and server credentials.
Only signed webhooks + fresh provider state confirm payment. No browser success
URL activates Premium, verifies an identity or grants operation documents.
"""
import asyncio
import hashlib
import os
import uuid
from datetime import datetime, timezone

from fastapi import Request
from pymongo import ReturnDocument

from investor_access import fail, future
from web_identity import public_origin


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


async def confirm_intent(db, client, intent):
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
        await db.web_reservations.update_one({"checkout_request_id": intent["request_id"]}, {"$setOnInsert": {"subject_id": intent["subject_id"], "op_ref": intent["op_ref"], "modality": intent["modality"],
            "checkout_request_id": intent["request_id"], "state": "PAID_PENDING_OPERATION_REVIEW", "terms_version": intent["terms_version"]}}, upsert=True)
    await db.web_checkout_intents.update_one({"_id": intent["_id"]}, {"$set": {"state": "PAID", "customer_id": checkout.customer, "subscription_id": checkout.subscription}})
    return True


def register_payment_routes(router, db):
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
            if intent: await confirm_intent(db, client, intent)
        elif event["type"] in {"customer.subscription.deleted", "customer.subscription.updated", "invoice.payment_failed", "charge.refunded", "charge.dispute.created"}:
            # Fail closed on cancellation/non-active state, payment failure or dispute.
            if event["type"] != "customer.subscription.updated" or obj.get("status") != "active":
                await db.web_entitlements.update_many({"provider": "STRIPE", "customer_id": obj.get("customer")}, {"$set": {"active": False}})
        elif event["type"] == "invoice.paid":
            intents = await db.web_checkout_intents.find({"customer_id": obj.get("customer"), "kind": "PREMIUM"}).to_list(100)
            for intent in intents: await confirm_intent(db, client, intent)
        await db.web_payment_events.update_one({"_id": event["id"]}, {"$set": {"processed": True}})
        return {"received": True}
