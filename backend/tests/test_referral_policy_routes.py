from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
from test_web_identity import system, login
from web_referrals import register_routes

def test_policy_requires_session_and_wallet_is_personal(system):
    client, db, mail = system
    router=APIRouter(prefix='/api');register_routes(router,db);client.app.include_router(router)
    assert client.get('/api/account/referrals/policy').status_code==401
    assert client.get('/api/account/referrals/bonuses').status_code==401
    login(client,mail)
    policy=client.get('/api/account/referrals/policy').json()
    assert policy['version']=='2026-11-16'
    assert policy['network_operation_percent']==5
    assert policy['premium']['redemption_is_user_choice']
    assert policy['premium']['additional_to_cash']
    wallet=client.get('/api/account/referrals/bonuses').json()
    assert wallet['available_bonuses']==0
    assert wallet['redemption_status']=='BILLING_NOT_CONNECTED'
    assert client.get('/api/account/referrals/dossiers/not-a-figure').status_code==404

def test_dossier_download_is_authenticated_and_pdf(system):
    client,db,mail=system
    router=APIRouter(prefix='/api');register_routes(router,db);client.app.include_router(router)
    assert client.get('/api/account/referrals/dossiers/partner').status_code==401
    login(client,mail)
    for figure in ['partner','suscriptor','equipo','colaborador','inversor']:
        response=client.get('/api/account/referrals/dossiers/'+figure)
        assert response.status_code==200
        assert response.content.startswith(b'%PDF-')
        assert response.headers['cache-control']=='private, no-store'
