import pytest
from mi_referral_identity_guard import normalized_identity, collision_result, referrer_registration_decision


def test_verified_phone_or_email_blocks_takeover_even_from_another_system():
    identity=normalized_identity(email="Investor@Example.COM",phone="+34 600 100 200")
    assert identity=={"email":"investor@example.com","phone_e164":"+34600100200"}
    for web,app in (([{"id":"w"}],[]),([],[{"id":"a"}])):
        result=referrer_registration_decision(identity=identity,
            web_search_complete=True,app_search_complete=True,
            web_matches=web,app_matches=app)
        assert result["state"]=="ALREADY_REGISTERED"
        assert result["assignable"] is False
        assert "email" not in str(result) and "phone" not in str(result)


def test_fail_closed_if_either_identity_index_unavailable():
    identity=normalized_identity(phone="+34600100200")
    result=referrer_registration_decision(identity=identity,
        web_search_complete=True,app_search_complete=False,
        web_matches=[],app_matches=[])
    assert result["state"]=="BLOCKED_IDENTITY_INDEX_UNAVAILABLE"
    assert result["assignable"] is False


def test_new_identity_is_not_assigned_until_email_and_human_verification():
    identity=normalized_identity(email="investor@example.com")
    result=referrer_registration_decision(identity=identity,
        web_search_complete=True,app_search_complete=True,
        web_matches=[],app_matches=[])
    assert result["state"]=="ELIGIBLE_FOR_EMAIL_CONFIRMATION"
    assert result["assignable"] is False


def test_phone_without_country_code_is_rejected():
    with pytest.raises(ValueError):
        normalized_identity(phone="600100200")
