from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
from mi_secretary_proposals import (
    extract_proposals, preview_signals, confirm_proposal,
)

NOW=datetime.now(timezone.utc)
ACTOR={"actor_id":"mi_owner"}
FILE="a"*32
SHA="b"*64


def test_no_pdf_extraction_for_other_document_categories():
    assert extract_proposals(b"",kind="IDENTIDAD",file_id=FILE)==[]


@pytest.mark.asyncio
async def test_preview_requires_explicit_opt_in_before_any_file_read(monkeypatch):
    with pytest.raises(HTTPException) as exc:
        await preview_signals(None,ACTOR,file_id=FILE,analysis_consent=False)
    assert exc.value.status_code==422


class DBRecords:
    async def find_one(self,query):
        assert query["actor_id"]=="mi_owner"
        assert query["file_id"]==FILE
        assert query["sha256"]==SHA
        assert query["scan_verdict"]=="CLEAN"
        return {"file_id":FILE,"sha256":SHA}


class Proposals:
    def __init__(self):
        self.row={
            "proposal_id":"f"*40,"actor_id":"mi_owner","file_id":FILE,
            "source_sha256":SHA,"state":"PENDING",
            "candidates":[{
                "kind":"PAYROLL_PAYMENT_DAY","candidate_value":12,
                "source_file_id":FILE,"needs_owner_confirmation":True,
            }],
        }
        self.claims=0
    async def find_one(self,query):
        if query["actor_id"]!="mi_owner":
            return None
        return self.row if self.row["state"]=="PENDING" else None
    async def find_one_and_update(self,query,update,return_document=None):
        if self.row["state"]!="PENDING":return None
        self.claims+=1
        self.row.update(update["$set"])
        return self.row


class Signals:
    def __init__(self):self.rows=[]
    async def insert_one(self,row):self.rows.append(row)


@pytest.mark.asyncio
async def test_confirm_needs_premium_owner_scanned_source_and_is_one_use(monkeypatch):
    async def premium(_db,_actor):return None
    monkeypatch.setattr("mi_secretary_proposals.require_premium",premium)
    proposals=Proposals()
    db=type("DB",(),{
        "mi_secretary_proposals":proposals,
        "mi_user_files":DBRecords(),
        "mi_secretary_signals":Signals(),
    })()
    result=await confirm_proposal(db,ACTOR,proposal_id="f"*40,
                                   kind="PAYROLL_PAYMENT_DAY",value=12)
    assert result["calendar_enabled"] is False
    assert result["confirmed_value"]==12
    assert len(db.mi_secretary_signals.rows)==1
    assert db.mi_secretary_signals.rows[0]["source_file_id"]==FILE
    with pytest.raises(HTTPException):
        await confirm_proposal(db,ACTOR,proposal_id="f"*40,
                               kind="PAYROLL_PAYMENT_DAY",value=12)


@pytest.mark.asyncio
async def test_unlisted_or_unsupported_values_cannot_be_saved(monkeypatch):
    async def premium(_db,_actor):return None
    monkeypatch.setattr("mi_secretary_proposals.require_premium",premium)
    db=type("DB",(),{
        "mi_secretary_proposals":Proposals(),
        "mi_user_files":DBRecords(),
        "mi_secretary_signals":Signals(),
    })()
    with pytest.raises(HTTPException) as exc:
        await confirm_proposal(db,ACTOR,proposal_id="f"*40,
                               kind="FILING_PERIOD_DECLARED",value="invented")
    assert exc.value.status_code==422
    with pytest.raises(HTTPException) as exc:
        await confirm_proposal(db,ACTOR,proposal_id="f"*40,
                               kind="PAYROLL_PAYMENT_DAY",value=31)
    assert exc.value.status_code==422
    assert db.mi_secretary_signals.rows==[]
