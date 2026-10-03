import pytest
from fastapi import HTTPException
from mi_role_boundaries import (
    require_mi_investor, collaborator_is_approved,
    subscriber_access_contract,
)


def test_mi_is_for_investor_only():
    owner={"role":"INVERSOR","actor_id":"mi_owner"}
    assert require_mi_investor(owner) is owner
    for role in ("COLABORADOR","SUSCRIPTOR",None):
        with pytest.raises(HTTPException) as exc:
            require_mi_investor({"role":role})
        assert exc.value.status_code==403


def test_collaborator_has_independent_approval():
    base={"role":"COLABORADOR","public_code":"OI-COL-000123",
          "email_verified":True,"validation_state":"VERIFIED"}
    assert collaborator_is_approved(base)
    assert not collaborator_is_approved({**base,"validation_state":"PENDING"})
    assert not collaborator_is_approved({**base,"email_verified":False})
    assert not collaborator_is_approved({**base,"role":"INVERSOR"})


def test_subscriber_uses_existing_app_identity_without_mi():
    contract=subscriber_access_contract()
    assert contract["credentials"]=="EXISTING_CODE_AND_PASSWORD"
    assert contract["profile_source"]==contract["history_source"]=="OPORTUNIIAPP"
    assert contract["mi_oportuniia_allowed"] is False
    assert contract["integration_status"]=="PENDING"


def test_all_web_private_routes_are_guarded():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/"mi_auth.py").read_text()
    private_section=source.split('    @router.post("/private/offers/',1)[1].split(
        '    @router.post("/auth/logout-all")',1)[0]
    assert "require_mi_investor" in private_section
    assert "actor = await _session(request)" not in private_section


def test_unapproved_collaborator_cannot_get_web_session():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/"mi_auth.py").read_text()
    login=source.split('    @router.post("/auth/login")',1)[1].split(
        '    async def _session(request',1)[0]
    session=source.split('    async def _session(request',1)[1].split(
        '    @router.get("/auth/me")',1)[0]
    assert 'actor.get("role")=="COLABORADOR"' in login
    assert 'actor.get("role")=="COLABORADOR"' in session
    assert 'actor["validation_state"]!="VERIFIED"' in session
