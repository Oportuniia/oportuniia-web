"""WEB vs OPORTUNIIAPP access boundaries, independent of visual navigation.

Only INVERSOR accesses personal/documentary MI. COLABORADOR has a separately
approved WEB referral workspace. SUSCRIPTOR keeps APP identity and historical
operations but may access the separate WEB referral section (always model A)
after trusted APP membership attestation, never a duplicate WEB password.
"""
from fastapi import HTTPException


def require_mi_investor(actor):
    if not actor or actor.get("role")!="INVERSOR":
        raise HTTPException(403,"MI OPORTUNIIA está reservado al usuario inversor")
    return actor


def collaborator_is_approved(actor):
    """Eligibility flag only; never an OPORTUNIIAPP authentication token."""
    return bool(actor and actor.get("role")=="COLABORADOR"
                and actor.get("email_verified") is True
                and actor.get("validation_state")=="VERIFIED"
                and actor.get("public_code")
                and str(actor["public_code"]).startswith("OI-COL-"))


def subscriber_referral_eligible(attestation):
    """Trusted backend-only APP assertion; never client-supplied or bearer login."""
    return bool(attestation and attestation.get("issuer")=="OPORTUNIIAPP"
                and attestation.get("verified_by_backend") is True
                and attestation.get("membership_active") is True
                and isinstance(attestation.get("app_subject"),str)
                and attestation.get("app_subject"))


def subscriber_access_contract():
    """Integration contract; do not assert SSO has been implemented."""
    return {"identity_source":"OPORTUNIIAPP",
            "credentials":"EXISTING_CODE_AND_PASSWORD",
            "profile_source":"OPORTUNIIAPP",
            "history_source":"OPORTUNIIAPP",
            "personal_investor_mi_allowed":False,
            "web_referral_section_allowed_after_app_verification":True,
            "referral_contract_model":"A",
            "integration_status":"PENDING"}
