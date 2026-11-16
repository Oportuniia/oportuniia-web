import asyncio
import pytest
from fastapi import HTTPException
from test_web_identity import DB
from referral_bonus_bank import award, reserve, applied, snapshot

def run(c): return asyncio.run(c)

def credit(db, investor):
    return run(award(db, 'owner', investor, 'op-'+investor,
                    consent_reference='signed-'+investor, settlement_reference='settled-'+investor))

def balance(db):
    return snapshot(run(db.web_referral_bonus_wallets.find_one({'_id':'owner'})))

def test_choose_one_discount_or_save_three_for_free():
    db=DB()
    for i in ['a','b','c']: credit(db,i)
    assert balance(db)['available_bonuses']==3
    free=run(reserve(db,'owner','request-001','FREE_MONTH'))
    assert balance(db)['available_bonuses']==0
    assert run(reserve(db,'owner','request-001','FREE_MONTH'))['id']==free['id']
    run(applied(db,'owner',free['id'],'receipt-001'))
    assert run(applied(db,'owner',free['id'],'receipt-001'))['replayed']
    with pytest.raises(HTTPException):run(reserve(db,'owner','request-002','HALF_PRICE_MONTH'))

def test_spent_credit_does_not_count_toward_three():
    db=DB(); credit(db,'a')
    half=run(reserve(db,'owner','request-001','HALF_PRICE_MONTH'))
    run(applied(db,'owner',half['id'],'receipt-001'))
    credit(db,'b');credit(db,'c')
    assert balance(db)['available_bonuses']==2
    with pytest.raises(HTTPException):run(reserve(db,'owner','request-002','FREE_MONTH'))
    credit(db,'d')
    assert run(reserve(db,'owner','request-002','FREE_MONTH'))['percent_off']==100

def test_same_investor_awarded_once_and_cannot_move_owner():
    db=DB();credit(db,'a');credit(db,'a')
    assert balance(db)['available_bonuses']==1
    with pytest.raises(HTTPException):
        run(award(db,'other','a','op-a',consent_reference='signed-a',settlement_reference='settled-a'))

def test_concurrent_reservation_does_not_double_spend():
    db=DB();credit(db,'a')
    async def race():
        return await asyncio.gather(reserve(db,'owner','request-001','HALF_PRICE_MONTH'),
                                    reserve(db,'owner','request-002','HALF_PRICE_MONTH'),return_exceptions=True)
    results=run(race())
    assert sum(isinstance(r,HTTPException) for r in results)==1
    assert balance(db)['available_bonuses']==0

def test_id_cannot_change_choice_and_receipt_cannot_change():
    db=DB();credit(db,'a')
    r=run(reserve(db,'owner','request-001','HALF_PRICE_MONTH'))
    with pytest.raises(HTTPException):run(reserve(db,'owner','request-001','FREE_MONTH'))
    run(applied(db,'owner',r['id'],'receipt-001'))
    with pytest.raises(HTTPException):run(applied(db,'owner',r['id'],'different-receipt'))
