"""Pure WEB investor-referral campaign guards. SANDBOX, no live emails/QR or writes.

One reusable public campaign URL/QR per approved referrer can be distributed
widely; it NEVER authenticates an investor or attributes an existing account.
Every signup requires the investor's verified email, separate consent and
human review for prior relationship conflicts.
"""
from __future__ import annotations
import re
from fastapi import HTTPException
from mi_role_boundaries import collaborator_is_approved, subscriber_referral_eligible

CODE=re.compile(r"^(OI-COL-[0-9]{6,}|OI-SUB-[0-9]{6,})$")


def eligible_referrer(*,referrer,subscriber_attestation=None):
    kind=referrer.get("kind") if isinstance(referrer,dict) else None
    if kind=="COLABORADOR":
        return collaborator_is_approved(referrer.get("web_actor"))
    if kind=="SUSCRIPTOR":
        return (subscriber_referral_eligible(subscriber_attestation)
                and referrer.get("app_subject")==subscriber_attestation.get("app_subject")
                and referrer.get("contract_model")=="A")
    return False


def campaign_spec(*,referrer,subscriber_attestation=None):
    """Build data for a share URL/QR only; never a login or user credential."""
    if not eligible_referrer(referrer=referrer,
                             subscriber_attestation=subscriber_attestation):
        raise HTTPException(403,"Aportador no autorizado")
    code=referrer.get("referrer_code")
    if not isinstance(code,str) or not CODE.fullmatch(code):
        raise ValueError("Código comercial no validado")
    if referrer["kind"]=="SUSCRIPTOR" and not code.startswith("OI-SUB-"):
        raise ValueError("El suscriptor precisa código WEB de aportación propio")
    if referrer["kind"]=="COLABORADOR" and not code.startswith("OI-COL-"):
        raise ValueError("Código de colaborador inválido")
    return {"referrer_code":code,"referrer_kind":referrer["kind"],
            "distribution":"REUSABLE_CAMPAIGN_URL_AND_QR",
            "requires_investor_email_verification":True,
            "creates_attribution_automatically":False,
            "contract_model":"A" if referrer["kind"]=="SUSCRIPTOR" else "FROM_SIGNED_CONTRACT",
            "activation_state":"SANDBOX_CONTRACT_ONLY"}


def investor_referral_candidate(*,campaign,investor,consent_proof,
                                 invitation_channel,prior_attribution=False):
    if campaign.get("activation_state")!="SANDBOX_CONTRACT_ONLY":
        raise ValueError("Unknown campaign")
    if invitation_channel not in ("MANUAL","LINK","QR"):
        raise ValueError("Unsupported onboarding channel")
    if investor.get("role")!="INVERSOR" or investor.get("email_verified") is not True:
        raise ValueError("Investor must independently verify email")
    if not isinstance(consent_proof,str) or len(consent_proof)<8:
        raise ValueError("Investor confirmation evidence required")
    if prior_attribution:
        return {"state":"MANUAL_CONFLICT_REVIEW","referrer_code":campaign["referrer_code"],
                "requires_human_approval":True}
    return {"state":"PENDING_HUMAN_REVIEW","referrer_code":campaign["referrer_code"],
            "referrer_kind":campaign["referrer_kind"],"investor_id":investor["actor_id"],
            "channel":invitation_channel,"requires_human_approval":True,
            "commercial_rights_activated":False}
