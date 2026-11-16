"""Versioned referral arithmetic. Does not authorize a payout or a signature.

Callers must supply verified provenance and actual OPORTUNIIA fee receipts.
Dates use Europe/Madrid calendar anniversaries, not 730-day approximations.
"""
from calendar import monthrange
from datetime import datetime
from zoneinfo import ZoneInfo

VERSION = '2026-11-16'
MADRID = ZoneInfo('Europe/Madrid')


def anniversary(start):
    if not isinstance(start, datetime) or start.tzinfo is None:
        raise ValueError('timezone_required')
    local = start.astimezone(MADRID)
    year = local.year + 2
    return local.replace(year=year, day=min(local.day, monthrange(year, local.month)[1]))


def money(collected, refunded):
    if type(collected) is not int or type(refunded) is not int or not 0 <= refunded <= collected:
        raise ValueError('invalid_amount_minor')
    return collected - refunded


def calculate(*, kind, collected_minor, refunded_minor=0, registered_at=None,
              closed_at=None, first_operation=False, consent_signed=False,
              modality_a_signed=False, partner_agreement_signed=False,
              active_paying=False, preexisting_investor=False):
    net = money(collected_minor, refunded_minor)
    result = {'policy_version': VERSION, 'amount_minor': 0, 'rate_percent': 0,
              'basis': 'OPORTUNIIA_FEES_ACTUALLY_COLLECTED', 'status': 'INELIGIBLE'}
    if kind == 'SUBSCRIPTION_FEE':
        if not partner_agreement_signed or not active_paying:
            return result
        rate = 15
    elif kind in {'AGENCY_OPERATION', 'COLLABORATOR_OPERATION', 'INVESTOR_OPERATION'}:
        if registered_at is None or closed_at is None:
            return {**result, 'status': 'DATES_REQUIRED'}
        end = anniversary(registered_at)
        if not isinstance(closed_at, datetime) or closed_at.tzinfo is None:
            raise ValueError('timezone_required')
        if closed_at < registered_at:
            return {**result, 'status': 'OPERATION_PRECEDES_REGISTRATION'}
        if closed_at >= end:
            return {**result, 'status': 'RENEWAL_REVIEW_REQUIRED'}
        if kind == 'INVESTOR_OPERATION':
            if preexisting_investor or not consent_signed or not modality_a_signed:
                return {**result, 'status': 'SIGNED_ATTRIBUTION_AND_MODALITY_A_REQUIRED'}
            rate = 50 if first_operation else 5
        else:
            if not partner_agreement_signed:
                return {**result, 'status': 'PARTNER_AGREEMENT_REQUIRED'}
            rate = 5
    else:
        raise ValueError('unsupported_reward_kind')
    return {**result, 'status': 'CALCULATED_NOT_PAID', 'rate_percent': rate,
            'amount_minor': (net * rate + 50) // 100}


def premium_balance(first_investor_ids, *, consumed_investor_ids=()):
    """One qualifying first operation per distinct verified investor.

    Alternatives for unconsumed credits. Never automatically convert credits.
    Three credits can buy a free month OR three half-price months, not both.
    """
    credits = set(first_investor_ids) - set(consumed_investor_ids)
    if any(not isinstance(v, str) or not v.strip() for v in credits):
        raise ValueError('verified_investor_id_required')
    return {'policy_version': VERSION, 'possible_free_months': len(credits)//3,
            'possible_half_price_months': len(credits), 'choices_are_alternatives': True,
            'qualifying_investors': len(credits), 'cash_commission_independent': True}
