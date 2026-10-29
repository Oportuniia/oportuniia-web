from datetime import datetime
import pytest
from web_payments import premium_expiry
from investor_access import premium_period_active


@pytest.mark.parametrize('provider_end,expected', [
    ('2026-12-09T16:35:00+01:00', '2026-12-08T23:00:00+00:00'),
    ('2026-04-09T16:35:00+02:00', '2026-04-08T22:00:00+00:00'),
    ('2027-02-28T12:00:00+01:00', '2027-02-27T23:00:00+00:00'),
    ('2028-02-29T12:00:00+01:00', '2028-02-28T23:00:00+00:00'),
])
def test_provider_anniversary_at_madrid_midnight(provider_end, expected):
    assert premium_expiry(datetime.fromisoformat(provider_end).timestamp()) == expected


def test_november_ninth_keeps_december_first_and_expires_december_ninth():
    paid = {'active': True, 'valid_from': '2026-11-09T16:35:00+01:00',
            'valid_until': premium_expiry(datetime.fromisoformat('2026-12-09T16:35:00+01:00').timestamp())}
    for instant, expected in [('2026-12-01T00:00:00+01:00', True),
                              ('2026-12-08T23:59:59+01:00', True),
                              ('2026-12-09T00:00:00+01:00', False)]:
        assert premium_period_active(paid, datetime.fromisoformat(instant)) is expected
