import asyncio
from datetime import timedelta
import pytest
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.testclient import TestClient
from test_web_identity import DB, system, login, signup
import web_referrals as ref


def run(awaitable): return asyncio.run(awaitable)


def seed(db, subject):
    run(db.web_users.insert_one({'subject_id': subject, 'active': True, 'email_verified': True}))


def test_unique_link_and_integer_fee_policy():
    db=DB();run(ref.ensure_indexes(db))
    a=run(ref.own_link(db,'a'));b=run(ref.own_link(db,'a'));c=run(ref.own_link(db,'b'))
    assert a==b and a['code']!=c['code']
    assert ref.incentive_preview(kind='FEE',collected_minor=240000,partner=True,referred_kind='suscriptor')['amount_minor']==36000
    assert ref.incentive_preview(kind='FEE',collected_minor=240000,refunded_minor=40000,partner=True,referred_kind='colaborador_premium')['amount_minor']==30000
    assert ref.incentive_preview(kind='FEE',collected_minor=240000,referred_kind='suscriptor')['amount_minor']==0
    assert ref.incentive_preview(kind='AGENCY_OPERATION',collected_minor=100)['amount_minor'] is None
    assert ref.incentive_preview(kind='COLLABORATOR_FIRST_OPERATION',collected_minor=100)['amount_minor'] is None
    recognition=dict(kind='COLLABORATOR_FIRST_OPERATION',collected_minor=100000,referred_kind='colaborador',first_operation_verified=True)
    assert ref.incentive_preview(**recognition)['amount_minor']==15000
    assert ref.incentive_preview(**recognition,recognition_already_recorded=True)['amount_minor']==0
    with pytest.raises(ValueError):ref.incentive_preview(kind='FEE',collected_minor=-1)


def test_manual_correction_audit_conflicts_and_self_referral():
    db=DB();seed(db,'a');seed(db,'b');seed(db,'c')
    p=ref.Attribution(subject_id='a',referrer_id='b',source='MANUAL',expected_revision=0,event_id='manual-0001',reason='Aportado presencialmente')
    assert run(ref.attribute(db,'admin',p))['revision']==1
    assert run(ref.attribute(db,'admin',p))['replayed']
    with pytest.raises(HTTPException):run(ref.attribute(db,'admin',p.model_copy(update={'reason':'Motivo modificado'})))
    with pytest.raises(HTTPException):run(ref.attribute(db,'admin',p.model_copy(update={'referrer_id':'a','event_id':'self-0001'})))
    correction=p.model_copy(update={'referrer_id':'c','source':'CORRECTED','expected_revision':1,'event_id':'correct-0001'})
    assert run(ref.attribute(db,'admin',correction))['revision']==2
    row=run(db.web_users.find_one({'subject_id':'a'}))['acquisition']
    assert row['history'][1]['before']['referrer_id']=='b'
    assert row['history'][1]['actor_id']=='admin'
    with pytest.raises(HTTPException):run(ref.attribute(db,'admin',correction.model_copy(update={'event_id':'stale-0001'})))


def test_link_qr_signup_first_touch_and_duplicate_identity(system):
    client,db,mail=system
    router=APIRouter(prefix='/api');ref.register_routes(router,db);client.app.include_router(router)
    seed(db,'leader');seed(db,'other')
    a=run(ref.own_link(db,'leader'));b=run(ref.own_link(db,'other'))
    response=client.get('/api/referrals/visit/'+a['code']+'?channel=QR',follow_redirects=False)
    assert response.status_code==303 and 'HttpOnly' in response.headers['set-cookie']
    client.get('/api/referrals/visit/'+b['code'],follow_redirects=False)
    signup(client,mail)
    row=run(db.web_users.find_one({'email':'one@example.com'}))
    assert row['acquisition']['source']=='QR' and row['acquisition']['referrer_id']=='leader'
    signup(client,mail)
    assert db.raw.web_users.count_documents({'email':'one@example.com'})==1
    assert client.get('/api/account/referrals').status_code==401
    assert client.post('/api/account/admin/referrals/attribution',json={}).status_code in {401,422}


def test_organic_expired_and_unknown_are_distinct(system):
    client,db,mail=system
    signup(client,mail,'organic@example.com')
    assert run(db.web_users.find_one({'email':'organic@example.com'}))['acquisition']['source']=='ORGANIC'
    client.cookies.set(ref.COOKIE,'invalid',domain='portal.test',path='/')
    signup(client,mail,'unknown@example.com')
    assert run(db.web_users.find_one({'email':'unknown@example.com'}))['acquisition']['source']=='UNRESOLVED'


def test_own_portfolio_qr_and_bridge_fail_closed(system):
    client,db,mail=system
    router=APIRouter(prefix='/api');ref.register_routes(router,db);client.app.include_router(router)
    login(client,mail)
    data=client.get('/api/account/referrals').json()
    assert data['financial_status']=='NOT_CONNECTED'
    image=client.get('/api/account/referrals/qr')
    assert image.status_code==200 and '<svg' in image.text
    assert client.get('/api/integrations/oportuniiapp/v1/referral-portfolio').status_code==503
