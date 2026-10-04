import pytest
from fastapi import HTTPException
from mi_collaborator_portfolio import collaborator_portfolio,investor_operations

COL={"role":"COLABORADOR","actor_id":"mi_col",
     "email_verified":True,"validation_state":"VERIFIED",
     "public_code":"OI-COL-000001"}
LINK={"collaborator_id":"mi_col","investor_id":"mi_inv",
      "investor_code":"OI-INV-000011","attribution_state":"VERIFIED",
      "source_verified":True}
OP={"collaborator_id":"mi_col","investor_id":"mi_inv",
    "attribution_verified":True,"operations_reviewed":True,
    "public_reference":"OP0001","status":"COMPLETED","contract_model":"A",
    "honoraria_eur":"1500.00","honoraria_reviewed":True,
    "legal_recognition_verified":True,"accounting_approved":True}

def test_only_approved_collaborator_can_view_own_codes():
    with pytest.raises(HTTPException):
        collaborator_portfolio({**COL,"validation_state":"PENDING"},
                               associations=[LINK],operations=[OP])
    result=collaborator_portfolio(COL,associations=[LINK,{**LINK,"collaborator_id":"mi_other",
          "investor_id":"mi_other_inv","investor_code":"OI-INV-000099"}],
          operations=[OP,{**OP,"collaborator_id":"mi_other","investor_id":"mi_other_inv"}])
    assert len(result)==1
    assert result[0]["user_code"]=="OI-INV-000011"
    assert result[0]["completed"][0]["honoraria_eur"]=="1500.00"
    with pytest.raises(HTTPException) as error:
        investor_operations(result,"OI-INV-000099")
    assert error.value.status_code==404

def test_model_a_unapproved_money_hidden_and_work_in_progress_separated():
    running={**OP,"status":"IN_PROGRESS","honoraria_reviewed":False}
    result=collaborator_portfolio(COL,associations=[LINK],operations=[running])
    row=result[0]
    assert not row["completed"]
    assert row["in_progress"][0]["honoraria_status"]=="PENDING_REVIEW"
    assert "honoraria_eur" not in row["in_progress"][0]

def test_model_b_only_references_and_status_never_financials_or_gold_alert():
    b={**OP,"contract_model":"B"}
    result=collaborator_portfolio(COL,associations=[LINK],operations=[b])
    visible=result[0]["completed"][0]
    assert visible=={"reference":"OP0001","status":"COMPLETED","model":"B"}
    assert "gold" not in str(result).lower()
    assert "1500" not in str(result)

def test_must_verify_attribution_and_operations_internally():
    assert collaborator_portfolio(COL,associations=[{**LINK,"source_verified":False}],
                                  operations=[OP])==[]
    assert collaborator_portfolio(COL,associations=[LINK],
                     operations=[{**OP,"operations_reviewed":False}])[0]["completed"]==[]
