"""Atomic bonus wallet. One immutable credit per referred investor's first sale.

Only internal verified settlement handlers may call award(). No public endpoint
can award credit. Reserving is not redeeming: a billing receipt must complete it.
"""
import hashlib
from pymongo.errors import DuplicateKeyError
from web_identity import now, denied

CHOICES = {'HALF_PRICE_MONTH': (1, 50), 'FREE_MONTH': (3, 100)}


async def award(db, owner, investor, operation, *, consent_reference, settlement_reference):
    if not all(isinstance(x, str) and x.strip() for x in
               [owner, investor, operation, consent_reference, settlement_reference]) or owner == investor:
        raise ValueError('verified_first_operation_evidence_required')
    # Investor identity must be the verified canonical identity, not an email.
    credit_id = hashlib.sha256(investor.encode()).hexdigest()
    record = {'_id': credit_id, 'owner': owner, 'investor': investor, 'operation': operation,
              'consent_reference': consent_reference, 'settlement_reference': settlement_reference}
    try:
        await db.web_referral_bonus_awards.update_one({'_id': credit_id},
            {'$setOnInsert': {**record, 'created_at': now()}}, upsert=True)
    except DuplicateKeyError:
        pass
    saved = await db.web_referral_bonus_awards.find_one({'_id': credit_id})
    if any(saved.get(k) != v for k, v in record.items()):
        denied('first_operation_credit_already_assigned', 409)
    # Retry repairs an interrupted wallet update, without granting a second credit.
    await db.web_referral_bonus_wallets.update_one({'_id': owner},
        {'$setOnInsert': {'revision': 0, 'redemptions': {}}, '$addToSet': {'credits': credit_id}}, upsert=True)
    return {'credit_id': credit_id, 'granted': True}


def available(wallet):
    used = {credit for r in wallet.get('redemptions', {}).values()
            if r['state'] in {'RESERVED', 'APPLIED'} for credit in r['credits']}
    return sorted(set(wallet.get('credits', [])) - used)


def snapshot(wallet):
    remaining = len(available(wallet))
    return {'available_bonuses': remaining, 'half_price_month_cost': 1, 'free_month_cost': 3,
            'possible_half_price_months': remaining, 'possible_free_months': remaining // 3,
            'choices_are_alternatives': True,
            'redemptions': [{'id': key, 'choice': v['choice'], 'state': v['state']}
                            for key, v in wallet.get('redemptions', {}).items()]}


async def reserve(db, owner, request_id, choice):
    if choice not in CHOICES or not isinstance(request_id, str) or not 8 <= len(request_id) <= 100:
        denied('invalid_bonus_redemption', 422)
    key = hashlib.sha256(request_id.encode()).hexdigest()
    cost, percent = CHOICES[choice]
    for _ in range(8):
        wallet = await db.web_referral_bonus_wallets.find_one({'_id': owner})
        if not wallet: denied('insufficient_bonuses', 409)
        previous = wallet.get('redemptions', {}).get(key)
        if previous:
            if previous['choice'] != choice: denied('redemption_id_conflict', 409)
            return {'id': key, **previous}
        remaining = available(wallet)
        if len(remaining) < cost: denied('insufficient_bonuses', 409)
        redemption = {'choice': choice, 'percent_off': percent, 'state': 'RESERVED',
                      'credits': remaining[:cost], 'created_at': now()}
        changed = await db.web_referral_bonus_wallets.update_one(
            {'_id': owner, 'revision': wallet['revision'], 'credits': wallet['credits']},
            {'$set': {'redemptions.'+key: redemption}, '$inc': {'revision': 1}})
        if changed.matched_count: return {'id': key, **redemption}
    denied('wallet_busy_retry_same_request', 409)


async def applied(db, owner, redemption_id, provider_receipt):
    if not isinstance(provider_receipt, str) or not provider_receipt.strip():
        raise ValueError('billing_confirmation_required')
    path = 'redemptions.' + redemption_id
    wallet = await db.web_referral_bonus_wallets.find_one({'_id': owner}) or {}
    previous = wallet.get('redemptions', {}).get(redemption_id)
    if not previous: denied('redemption_not_found', 404)
    if previous['state'] == 'APPLIED':
        if previous.get('provider_receipt') != provider_receipt: denied('billing_receipt_conflict', 409)
        return {'applied': True, 'replayed': True}
    result = await db.web_referral_bonus_wallets.update_one({'_id': owner, path+'.state': 'RESERVED'},
        {'$set': {path+'.state': 'APPLIED', path+'.provider_receipt': provider_receipt,
                  path+'.applied_at': now()}, '$inc': {'revision': 1}})
    if not result.matched_count: denied('redemption_state_changed_retry', 409)
    return {'applied': True, 'replayed': False}
