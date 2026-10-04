import pytest
from fastapi import HTTPException
from mi_offer_prefill import applicant_snapshot,published_offer_property,prefilling


ACTOR={"role":"INVERSOR","validation_state":"VERIFIED","email":"persona@example.test",
"public_code":"OI-INV-000001","offer_profile":{
"legal_name":"Persona De Prueba","tax_identifier":"TEST-ID",
"street_address":"should not expose unverified address","city":"Madrid"},
"validated_offer_fields":["legal_name","tax_identifier"]}


def test_only_validated_actor_fields_are_auto_filled():
    data=applicant_snapshot(ACTOR)
    assert data["fields"]["legal_name"]=="Persona De Prueba"
    assert data["fields"]["tax_identifier"]=="TEST-ID"
    assert data["fields"]["street_address"]==""
    assert "street_address" in data["missing_fields"]
    assert data["email"]=="persona@example.test"


@pytest.mark.parametrize("role,state",[("COLABORADOR","VERIFIED"),("INVERSOR","PENDING")])
def test_only_verified_investors_can_prefill(role,state):
    with pytest.raises(HTTPException) as exc:
        applicant_snapshot({**ACTOR,"role":role,"validation_state":state})
    assert exc.value.status_code==403


class Published:
    def __init__(self,item):self.item=item
    async def find_one(self,query,projection):
        assert query["publication_state"]=="PUBLISHED"
        assert query["item.public_reference"]=="OP0001"
        return {"item":self.item} if self.item else None


@pytest.mark.asyncio
async def test_only_explicit_published_offer_enabled_property_is_eligible():
    item={"public_reference":"OP0001","offer_enabled":True,"universe":"judicial",
          "title":"Activo de prueba","city":"Madrid","public_price":200000,
          "internal_id":"private","source_output_id":"secret","private_margin":45000}
    db=type("DB",(),{"presentation_web_published":Published(item)})()
    result=await prefilling(db,ACTOR,"OP0001")
    assert result["property"]["title"]=="Activo de prueba"
    assert "internal_id" not in result["property"]
    assert "private_margin" not in result["property"]
    assert result["reservation"] is False
    assert result["commitment"]=="DRAFT_ONLY"


@pytest.mark.asyncio
async def test_no_fabricated_op0001_mapping():
    db=type("DB",(),{"presentation_web_published":Published(None)})()
    with pytest.raises(HTTPException) as exc:
        await prefilling(db,ACTOR,"OP0001")
    assert exc.value.status_code==404


@pytest.mark.asyncio
async def test_restricted_agreement_not_unlocked_by_offer_url():
    db=type("DB",(),{"presentation_web_published":Published({
        "public_reference":"OP0001","universe":"acuerdos","offer_enabled":True})})()
    with pytest.raises(HTTPException) as exc:
        await published_offer_property(db,"OP0001")
    assert exc.value.status_code==403
