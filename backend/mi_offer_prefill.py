"""Server-authoritative, minimally disclosed offer prefill.

The public reference is NEVER enough to grant access to a restricted
opportunity. Only explicitly published, commercially visible records may
appear. Applicant details are read from the actor's verified WEB profile
rather than request query parameters. Do not include supplier references,
private economics, debt amounts or internal PRESENTACIÓN/R2 identifiers.
"""
import re
from fastapi import HTTPException

REFERENCE = re.compile(r"^OP[0-9]{4,10}$")


def applicant_snapshot(actor):
    if not actor or actor.get("role") != "INVERSOR" or actor.get("validation_state") != "VERIFIED":
        raise HTTPException(403, "Cuenta inversora pendiente de validación")
    profile=actor.get("offer_profile") or {}
    # Do not silently claim these values are confirmed: separate provenance.
    allowed=("legal_name","tax_identifier","telephone","street_address",
             "city","postal_code","country","representative_name")
    validated=set(actor.get("validated_offer_fields") or [])
    result={key: profile.get(key, "") if key in validated else ""
            for key in allowed}
    return {"fields": result, "email": actor.get("email", ""),
            "verified_fields": sorted(set(result)&validated),
            "missing_fields": [key for key in allowed if not result[key]],
            "public_code": actor.get("public_code")}


async def published_offer_property(db, reference):
    if not isinstance(reference,str) or not REFERENCE.fullmatch(reference):
        raise HTTPException(404, "Referencia no disponible")
    published=await db.presentation_web_published.find_one({
        "publication_state":"PUBLISHED",
        "item.public_reference":reference,
    },{"_id":0,"item":1})
    if not published:
        raise HTTPException(404, "Operación no publicada")
    item=published.get("item") or {}
    # Acuerdos require their own explicit entitlement and cannot be
    # unlocked using a public offer URL.
    if item.get("universe")=="acuerdos" or item.get("offer_enabled") is not True:
        raise HTTPException(403, "Ofertas no habilitadas para esta operación")
    return {key: item.get(key) for key in
            ("public_reference","title","city","province","product","universe",
             "public_price","public_address")}


async def prefilling(db,actor,reference):
    applicant=applicant_snapshot(actor)
    property_data=await published_offer_property(db,reference)
    return {"applicant":applicant,"property":property_data,
            "approval_required":True,"reservation":False,
            "commitment":"DRAFT_ONLY"}
