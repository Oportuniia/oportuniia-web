"""Fail-closed sovereign document authorization policy.

This module deliberately NEVER verifies login credentials or trusts browser
headers. Identity must be supplied by a future independently verified,
server-side adapter with operation-specific grants. OPORTUNIIAPP's local
subscriber session is not a WEB investor/Premium identity.
"""
from dataclasses import dataclass, field

VALID_PRODUCTS = frozenset({"PC", "RE", "IC", "RF"})


@dataclass(frozen=True)
class VerifiedDocumentPrincipal:
    """Construct only from a trusted, server-side identity integration."""
    actor_id: str
    active: bool
    permitted_documents: dict[str, frozenset[str]] = field(default_factory=dict)


def can_read_presentation_pdf(
    principal: VerifiedDocumentPrincipal | None,
    published_item: dict | None,
    product: str,
) -> bool:
    """Explicit per-OP, per-document grants; no VIP/role inference."""
    if principal is None or not principal.active or not principal.actor_id:
        return False
    if product not in VALID_PRODUCTS or not published_item:
        return False
    internal_id = published_item.get("internal_id")
    if not isinstance(internal_id, str) or not internal_id:
        return False
    if not published_item.get("source_output_id"):
        return False
    info = (published_item.get("documents") or {}).get(product)
    if not isinstance(info, dict) or info.get("status") != "READY":
        return False
    grants = principal.permitted_documents.get(internal_id, frozenset())
    return product in grants
