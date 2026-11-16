from datetime import datetime, timezone
import pytest
from referral_policy import calculate, premium_balance, anniversary

START = datetime(2026, 11, 16, 12, tzinfo=timezone.utc)
CLOSE = datetime(2026, 12, 1, 12, tzinfo=timezone.utc)


def operation(kind='INVESTOR_OPERATION', **kw):
    args = dict(kind=kind, collected_minor=1000000, registered_at=START,
                closed_at=CLOSE, consent_signed=True, modality_a_signed=True,
                partner_agreement_signed=True)
    args.update(kw)
    return calculate(**args)


def test_first_is_fifty_not_fifty_five_and_later_five():
    assert operation(first_operation=True)['amount_minor'] == 500000
    assert operation()['amount_minor'] == 50000


@pytest.mark.parametrize('kind', ['AGENCY_OPERATION', 'COLLABORATOR_OPERATION'])
def test_network_operations_are_five_for_all_operations(kind):
    assert operation(kind, first_operation=True)['rate_percent'] == 5
    assert operation(kind)['rate_percent'] == 5


def test_original_registration_cutoff_not_corrected_attribution_date():
    assert operation(closed_at=anniversary(START))['status'] == 'RENEWAL_REVIEW_REQUIRED'
    assert operation(closed_at=START)['rate_percent'] == 5
    assert operation(closed_at=START.replace(year=2025))['amount_minor'] == 0


def test_leap_year_anniversary():
    assert anniversary(START.replace(year=2024, month=2, day=29)).day == 28


@pytest.mark.parametrize('field', ['consent_signed', 'modality_a_signed'])
def test_unsigned_attribution_never_commissions(field):
    assert operation(**{field: False})['amount_minor'] == 0


def test_existing_investor_excluded():
    assert operation(preexisting_investor=True)['amount_minor'] == 0


def test_fee_only_collected_active_and_agreed():
    args = dict(kind='SUBSCRIPTION_FEE', collected_minor=240000,
                active_paying=True, partner_agreement_signed=True)
    assert calculate(**args)['amount_minor'] == 36000
    assert calculate(**{**args, 'active_paying': False})['amount_minor'] == 0
    assert calculate(**args, refunded_minor=40000)['amount_minor'] == 30000


@pytest.mark.parametrize('n,free,half', [(0,0,0),(1,0,1),(2,0,2),(3,1,3),(4,1,4),(10,3,10)])
def test_premium_group_replaces_not_adds(n, free, half):
    balance = premium_balance([str(i) for i in range(n)])
    assert (balance['possible_free_months'], balance['possible_half_price_months']) == (free, half)
    assert balance['choices_are_alternatives']


def test_duplicate_event_not_extra_investor():
    assert premium_balance(['a','a','b'])['qualifying_investors'] == 2


def test_consumed_credit_not_reused():
    assert premium_balance(['a','b','c'], consumed_investor_ids=['a'])['possible_free_months'] == 0


def test_invalid_money_and_naive_time_rejected():
    with pytest.raises(ValueError): operation(collected_minor=-1)
    with pytest.raises(ValueError): operation(collected_minor=True)
    with pytest.raises(ValueError): operation(refunded_minor=1000001)
    with pytest.raises(ValueError): operation(closed_at=CLOSE.replace(tzinfo=None))
