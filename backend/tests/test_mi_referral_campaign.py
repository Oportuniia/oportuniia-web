from mi_referral_campaign import campaign_spec, investor_referral_candidate

COL={'kind':'COLABORADOR','referrer_code':'OI-COL-000021','web_actor':{'role':'COLABORADOR','actor_id':'mi_col','email_verified':True,'validation_state':'VERIFIED','public_code':'OI-COL-000021'}}
SUB={'kind':'SUSCRIPTOR','referrer_code':'OI-SUB-000008','app_subject':'app_08','contract_model':'A'}
VERIFIED={'issuer':'OPORTUNIIAPP','verified_by_backend':True,'membership_active':True,'app_subject':'app_08','approved_web_referrer_code':'OI-SUB-000008'}
INV={'role':'INVERSOR','actor_id':'mi_inv','email_verified':True}

def test_subscriber_has_a_separate_model_a_campaign():
    c=campaign_spec(referrer=SUB,subscriber_attestation=VERIFIED)
    assert c['contract_model']=='A'
    assert c['creates_attribution_automatically'] is False

def test_all_channels_require_human_review():
    c=campaign_spec(referrer=COL)
    for channel in ('MANUAL','LINK','QR'):
        row=investor_referral_candidate(campaign=c,investor=INV,consent_proof='consent1234',invitation_channel=channel)
        assert row['state']=='PENDING_HUMAN_REVIEW'
        assert row['commercial_rights_activated'] is False

def test_prior_attribution_requires_conflict_review():
    c=campaign_spec(referrer=COL)
    row=investor_referral_candidate(campaign=c,investor=INV,consent_proof='consent1234',invitation_channel='LINK',prior_attribution=True)
    assert row['state']=='MANUAL_CONFLICT_REVIEW'

def test_code_must_match_verified_source():
    from fastapi import HTTPException
    import pytest
    with pytest.raises(HTTPException):
        campaign_spec(referrer={**COL,'referrer_code':'OI-COL-000099'})
    with pytest.raises(HTTPException):
        campaign_spec(referrer={**SUB,'referrer_code':'OI-SUB-000099'},subscriber_attestation=VERIFIED)
