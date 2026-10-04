"""Read-only collaborator portfolio projection for verified operation records.

No live endpoints, database writes or commission calculations. The caller must
fetch only independently verified associations and attributed operations for
the approved collaborator. Every financial number originates from authorized
accounting review, never from client input or a percent calculation.
"""
from __future__ import annotations
from decimal import Decimal
from fastapi import HTTPException
from mi_role_boundaries import collaborator_is_approved

ACTIVE={"IN_PROGRESS","UNDER_REVIEW"}
COMPLETE={"COMPLETED"}
STATES=ACTIVE|COMPLETE


def collaborator_portfolio(collaborator,*,associations,operations):
    if not collaborator_is_approved(collaborator):
        raise HTTPException(403,"Aprobación del colaborador requerida")
    owner=collaborator["actor_id"]
    # Only associations explicitly verified for the current collaborator.
    mine={}
    for relation in associations:
        if (relation.get("collaborator_id")==owner
            and relation.get("attribution_state")=="VERIFIED"
            and relation.get("source_verified") is True
            and isinstance(relation.get("investor_id"),str)
            and isinstance(relation.get("investor_code"),str)):
            mine[relation["investor_id"]]=relation["investor_code"]
    grouped={k:{"user_code":code,"in_progress":[],"completed":[]} for k,code in mine.items()}
    for op in operations:
        investor=op.get("investor_id")
        if op.get("collaborator_id")!=owner or investor not in grouped:
            continue
        if not (op.get("attribution_verified") is True
                and op.get("operations_reviewed") is True
                and op.get("status") in STATES
                and isinstance(op.get("public_reference"),str)
                and op["public_reference"]):
            continue
        model=op.get("contract_model")
        if model not in ("A","B"):
            continue
        visible={"reference":op["public_reference"],
                 "status":op["status"],"model":model}
        if model=="A":
            # Do not calculate or expose unapproved honoraria.
            financial_ok=(op.get("honoraria_reviewed") is True
                          and op.get("legal_recognition_verified") is True
                          and op.get("accounting_approved") is True)
            raw=op.get("honoraria_eur")
            if financial_ok and isinstance(raw,str):
                try:
                    amount=Decimal(raw)
                    if not amount.is_finite() or amount<0 or amount.as_tuple().exponent< -2:
                        raise ValueError
                    visible["honoraria_eur"]=str(amount.quantize(Decimal("0.01")))
                    visible["honoraria_status"]="REVIEWED"
                except (ValueError,ArithmeticError):
                    visible["honoraria_status"]="PENDING_REVIEW"
            else:
                visible["honoraria_status"]="PENDING_REVIEW"
        bucket="in_progress" if op["status"] in ACTIVE else "completed"
        grouped[investor][bucket].append(visible)
    return sorted(grouped.values(),key=lambda item:item["user_code"])


def investor_operations(portfolio,code):
    """Expands only an investor already present in the scoped projection."""
    for item in portfolio:
        if item["user_code"]==code:
            return item
    raise HTTPException(404,"Código de usuario no encontrado")
