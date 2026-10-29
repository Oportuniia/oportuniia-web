import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
import httpx
import pytest
from fastapi import APIRouter, FastAPI
import web_course_onboarding as course


@pytest.fixture
def api(monkeypatch):
    user = {'subject_id': 'web-person', 'username': 'existing-person', 'active': True, 'role': 'user', 'session_version': 2}
    database = SimpleNamespace(web_users=SimpleNamespace(find_one=AsyncMock(return_value=user), insert_one=AsyncMock()),
        oportuniiapp_web_identity_map=SimpleNamespace(find_one=AsyncMock(return_value=None), update_one=AsyncMock()),
        web_identity_tokens=SimpleNamespace(insert_one=AsyncMock()))
    monkeypatch.setenv('COURSE_WEB_BRIDGE_KEY', 'k' * 40)
    monkeypatch.setattr(course, 'blocked', AsyncMock(return_value=False))
    monkeypatch.setattr(course, 'public_origin', lambda: 'https://oportuniia.com')
    router = APIRouter(prefix='/api'); course.register_course_onboarding_routes(router, database)
    app = FastAPI(); app.include_router(router)
    def post(key='k' * 40):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                return await client.post('/api/course-onboarding/provision', json={
                    'app_subject': 'app-person', 'code': 'SUS-001', 'name': 'Prueba Curso', 'email': 'course@example.com'},
                    headers={'X-OPORTUNIIA-Course-Key': key})
        return asyncio.run(run())
    return post, database, user


def test_bridge_denies_wrong_key(api):
    post, database, _ = api
    assert post('wrong').status_code == 403
    database.web_users.find_one.assert_not_called()


def test_existing_account_keeps_username_and_password(api):
    post, database, _ = api
    result = post()
    assert result.status_code == 200
    assert result.json()['username'] == 'existing-person'
    database.web_users.insert_one.assert_not_called()
    record = database.web_identity_tokens.insert_one.call_args.args[0]
    assert record['version'] == 2
    assert record['course_email_verification'] is False
    assert 'token' not in record


@pytest.mark.parametrize('changes', [{'active': False}, {'role': 'superadmin'}, {'app_subject': 'someone-else'}])
def test_never_reactivates_or_overwrites_privileged_accounts(api, changes):
    post, database, user = api
    user.update(changes)
    assert post().status_code == 409
    database.web_identity_tokens.insert_one.assert_not_called()
    database.oportuniiapp_web_identity_map.update_one.assert_not_called()
