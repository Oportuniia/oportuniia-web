"""Private identity-collision gate for human-reviewed investor acquisition.

No live endpoints: the verified WEB registry and an eventually approved APP
identity index must be searched BEFORE any proposed referral is associated.
Never disclose which exact email or telephone collided in public invitations.
"""
from __future__ import annotations
import re
from fastapi import HTTPException
from personal_user_registry import normalize_email

PHONE=re.compile(r"^\+[1-9][0-9]{7,14}$")


def normalized_identity(*,email=None,phone=None):
    """Only explicitly supplied international phone numbers; never guess country."""
    clean_email=normalize_email(email) if email else None
    if phone is not None:
        if not isinstance(phone,str):
            raise ValueError("invalid phone")
        clean_phone=re.sub(r"[ \-().]","",phone)
        if not PHONE.fullmatch(clean_phone):
            raise ValueError("phone must include verified international country code")
    else:
        clean_phone=None
    if not clean_email and not clean_phone:
        raise ValueError("verified contact identity required")
    return {"email":clean_email,"phone_e164":clean_phone}


def collision_result(*,verified_web_matches,verified_app_matches,
                     same_investor_ref=None):
    """Existing people always block new assignment, including APP contacts.

    A central human review may reconcile legitimate duplicates; this function
    NEVER transfers ownership or assigns the person to a referrer.
    """
    if verified_web_matches is None or verified_app_matches is None:
        return {"state":"BLOCKED_IDENTITY_INDEX_UNAVAILABLE",
                "assignable":False}
    matches=list(verified_web_matches)+list(verified_app_matches)
    if matches:
        return {"state":"ALREADY_REGISTERED",
                "assignable":False,"requires_private_owner_review":True}
    return {"state":"ELIGIBLE_FOR_EMAIL_CONFIRMATION",
            "assignable":False,"requires_private_owner_review":True}


def referrer_registration_decision(*,identity,web_search_complete,
                                   app_search_complete,web_matches,
                                   app_matches):
    if not isinstance(identity,dict) or not (identity.get("email") or identity.get("phone_e164")):
        raise ValueError("missing normalized identity")
    if not (web_search_complete and app_search_complete):
        return collision_result(verified_web_matches=None,verified_app_matches=None)
    return collision_result(verified_web_matches=web_matches,
                            verified_app_matches=app_matches)
