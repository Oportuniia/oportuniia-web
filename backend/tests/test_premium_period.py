from datetime import datetime
import pytest
from investor_access import premium_period_active


@pytest.mark.parametrize('instant,expected', [
    ('2026-10-31T22:59:59+00:00', False),
    ('2026-10-31T23:00:00+00:00', True),
    ('2026-11-30T22:59:59+00:00', True),
    ('2026-11-30T23:00:00+00:00', False),
])
def test_november_madrid_boundaries(instant, expected):
    paid = {'active': True, 'valid_from': '2026-11-01T00:00:00+01:00',
            'valid_until': '2026-12-01T00:00:00+01:00'}
    assert premium_period_active(paid, datetime.fromisoformat(instant)) is expected


@pytest.mark.parametrize('changes', [
    {'active': False}, {'valid_until': None}, {'valid_until': 'invalid'},
    {'valid_from': 'invalid'}, {'valid_from': '2026-11-01T00:00:00'},
    {'valid_until': '2026-12-01T00:00:00'},
])
def test_invalid_or_disabled_period_does_not_grant_access(changes):
    paid = {'active': True, 'valid_until': '2026-12-01T00:00:00+01:00', **changes}
    assert not premium_period_active(paid, datetime.fromisoformat('2026-11-15T12:00:00+01:00'))


def test_existing_immediate_subscription():
    assert premium_period_active({'active': True, 'valid_until': '2026-12-01T00:00:00+01:00'},
                                 datetime.fromisoformat('2026-11-15T12:00:00+01:00'))
