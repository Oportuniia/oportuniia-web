"""Sandbox bridge tests with synthetic data and fake DB, no live third-party PII."""
import asyncio
import os
from unittest.mock import patch
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pymongo.errors import DuplicateKeyError
from mi_app_integration_api import register_routes

class Collection:
    def __init__(self): self.data={}
    async def insert_one(self,doc):
        if doc["_id"] in self.data: raise DuplicateKeyError("duplicate")
        self.data[doc["_id"]]=dict(doc)
    async def find_one(self,filter):
        for row in self.data.values():
            if all(row.get(k)==v for k,v in filter.items()): return row
        return None

class Links:
    def __init__(self): self.data={}
    async def find_one(self,filter):
        item=self.data.get(filter["app_subject"])
        return item if item and all(item.get(k)==v for k,v in filter.items()) else None

class DB:
    def __init__(self):
        self.app_web_intakes=Collection()
        self.app_web_subscriber_links=Links()

@pytest.fixture
def setup():
    db=DB()
    app=FastAPI()
    app.include_router(register_routes(db))
    return app,db

@pytest.mark.asyncio
async def test_auth_isolation_and_idempotence(setup):
    app,db=setup
    body={"app_event_id":"event-00001","app_report_id":"report-1","app_subject":"alice"}
    h={"x-oportuniia-web-app-m2m-key":"synthetic-secret","x-app-subject":"alice","idempotency-key":"retry-key-1"}
    with patch.dict(os.environ,{"WEB_APP_N8N_ORCHESTRATOR_KEY":"synthetic-secret"},clear=False):
        async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
            url="/api/integrations/oportuniiapp/v1/referral-intakes"
            assert (await c.post(url,json=body)).status_code==401
            first=await c.post(url,json=body,headers=h)
            assert first.status_code==202 and first.json()["status"]=="INDEX_UNAVAILABLE"
            assert (await c.post(url,json=body,headers=h)).json()==first.json()
            assert len(db.app_web_intakes.data)==1
            changed={**body,"app_report_id":"report-2"}
            assert (await c.post(url,json=changed,headers=h)).status_code==409
            assert (await c.post(url,json=body,headers={**h,"x-app-subject":"bob"})).status_code==403
            item=first.json()["intake_id"]
            assert (await c.get(url+"/"+item,headers=h)).status_code==200
            assert (await c.get(url+"/"+item,headers={**h,"x-app-subject":"bob"})).status_code==404

@pytest.mark.asyncio
async def test_legal_gate_and_empty_scoped_portfolio(setup):
    app,db=setup
    h={"x-oportuniia-web-app-m2m-key":"synthetic-secret","x-app-subject":"alice","idempotency-key":"retry-key-2"}
    root="/api/integrations/oportuniiapp/v1"
    with patch.dict(os.environ,{"WEB_APP_N8N_ORCHESTRATOR_KEY":"synthetic-secret",
                                "WEB_APP_LEGAL_THIRD_PARTY_CONTACTS_ENABLED":"0"},clear=False):
        async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
            payload={"app_event_id":"event-00002","app_report_id":"report-2",
                     "app_subject":"alice","investor_email":"synthetic@example.invalid"}
            assert (await c.post(root+"/referral-intakes",json=payload,headers=h)).status_code==423
            assert (await c.get(root+"/subscriber-portfolio",headers=h)).status_code==403
            db.app_web_subscriber_links.data["alice"]={"app_subject":"alice","approved":True,
                 "membership_active":True,"web_referrer_code":"OI-SUB-TEST"}
            result=await c.get(root+"/subscriber-portfolio",headers=h)
            assert result.status_code==200
            assert result.json()["investors"]==[] and result.json()["sync_status"]=="SOURCE_ADAPTER_PENDING"
            assert (await c.get(root+"/subscriber-portfolio",headers={**h,"x-app-subject":"bob"})).status_code==403

@pytest.mark.asyncio
async def test_unknown_third_party_fields_are_rejected(setup):
    app,_=setup
    h={"x-oportuniia-web-app-m2m-key":"synthetic-secret","x-app-subject":"alice","idempotency-key":"retry-key-3"}
    payload={"app_event_id":"event-00003","app_report_id":"report-3","app_subject":"alice","investor_name":"must-not-be-silently-accepted"}
    with patch.dict(os.environ,{"WEB_APP_N8N_ORCHESTRATOR_KEY":"synthetic-secret"},clear=False):
        async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as client:
            response=await client.post("/api/integrations/oportuniiapp/v1/referral-intakes",json=payload,headers=h)
            assert response.status_code==422
