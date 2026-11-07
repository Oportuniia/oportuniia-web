import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).parents[1] / 'backend'))
from web_collaborator_documents import register_collaborator_document_routes
from investor_access import authenticated_subject

class Users:
    def __init__(self, kind): self.kind = kind
    async def find_one(self, query):
        return {'account_kind': self.kind, 'active': True}
class DB:
    def __init__(self, kind): self.web_users = Users(kind)
def client(kind='colaborador', authenticated=True):
    app = FastAPI()
    register_collaborator_document_routes(app, DB(kind))
    if authenticated:
        app.dependency_overrides[authenticated_subject] = lambda: 'test-subject'
    return TestClient(app)

def test_blank_matrix_download_and_headers():
    c = client()
    catalog = c.get('/collaborator/legal-templates')
    assert catalog.status_code == 200
    assert len(catalog.json()['items']) == 2
    response = c.get('/collaborator/legal-templates/recognition')
    assert response.status_code == 200
    assert response.content.startswith(b'%PDF-')
    assert response.headers['cache-control'] == 'private, no-store'
    assert 'attachment' in response.headers['content-disposition']

def test_investor_cannot_download_collaborator_documents():
    assert client('inversor').get('/collaborator/legal-templates/recognition').status_code == 403

def test_no_arbitrary_filename_download():
    assert client().get('/collaborator/legal-templates/not-a-template').status_code == 404

def test_without_session_fails_closed(monkeypatch):
    monkeypatch.setenv('WEB_IDENTITY_MODE', 'web_sessions')
    assert client(authenticated=False).get('/collaborator/legal-templates').status_code != 200
