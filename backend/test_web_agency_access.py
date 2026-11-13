import os
import uuid
import pytest
import httpx
from fastapi import APIRouter, FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from web_agency_access import register_agency_access_routes


@pytest.mark.asyncio
async def test_personal_access_revocation_and_recycled_code(monkeypatch):
    url = os.getenv('AGENCY_TEST_MONGO_URL')
    if not url:
        pytest.skip('isolated Mongo required')
    client = AsyncIOMotorClient(url)
    name = 'web_agency_test_' + uuid.uuid4().hex
    db = client[name]
    monkeypatch.setenv('COURSE_WEB_BRIDGE_KEY', 'x'*40)
    monkeypatch.setenv('WEB_PUBLIC_ORIGIN', 'https://oportuniia.com')
    try:
        await db.web_users.create_index('username', unique=True)
        await db.web_users.create_index('email', unique=True)
        await db.web_users.insert_one({'subject_id': 'parent-web', 'active': True, 'username': 'agency', 'email': 'agency@example.com'})
        await db.oportuniiapp_web_identity_map.insert_one({'app_subject': 'parent', 'web_subject_id': 'parent-web', 'active': True})
        router = APIRouter(prefix='/api'); register_agency_access_routes(router, db)
        app = FastAPI(); app.include_router(router)
        headers = {'X-OPORTUNIIA-Course-Key': 'x'*40}
        body = {'app_subject': 'one', 'agency_id': 'parent', 'code': 'SUS-010.01', 'name': 'Persona Uno', 'email': 'one@example.com'}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as http:
            assert (await http.post('/api/agency-access/provision', json=body)).status_code == 403
            first = await http.post('/api/agency-access/provision', json=body, headers=headers)
            assert first.status_code == 200, first.text
            assert first.json()['username'] == 'sus-010.01'
            assert (await http.post('/api/agency-access/provision', json=body, headers=headers)).json()['subject_id'] == first.json()['subject_id']
            revoke = {'app_subject': 'one', 'agency_id': 'parent'}
            assert (await http.post('/api/agency-access/revoke', json=revoke, headers=headers)).status_code == 200
            old = await db.web_users.find_one({'subject_id': first.json()['subject_id']})
            assert old['active'] is False and old['session_version'] == 1
            assert (await http.post('/api/agency-access/provision', json=body, headers=headers)).status_code == 409
            body.update(app_subject='two', name='Persona Dos', email='two@example.com')
            second = await http.post('/api/agency-access/provision', json=body, headers=headers)
            assert second.status_code == 200, second.text
            assert second.json()['username'] == 'sus-010.01'
            assert second.json()['subject_id'] != first.json()['subject_id']
    finally:
        await client.drop_database(name)
        client.close()
