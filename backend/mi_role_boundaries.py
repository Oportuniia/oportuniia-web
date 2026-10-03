"""WEB vs OPORTUNIIAPP access boundaries, independent of visual navigation.

INVERSOR owns MI OPORTUNIIA. COLABORADOR may register in WEB but
requires independent OPORTUNIIA administrative validation; cannot enter the
investor's private area. SUSCRIPTOR is authenticated by OPORTUNIIAPP,
whose own profile and history remain authoritative; no MI identity is minted.
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


def subscriber_access_contract():
    """Integration contract; do not assert SSO has been implemented."""
    return {"identity_source":"OPORTUNIIAPP",
            "credentials":"EXISTING_CODE_AND_PASSWORD",
            "profile_source":"OPORTUNIIAPP",
            "history_source":"OPORTUNIIAPP",
            "mi_oportuniia_allowed":False,
            "integration_status":"PENDING"}
