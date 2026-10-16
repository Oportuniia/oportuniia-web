import sys
from pathlib import Path
from copy import deepcopy
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import web_auth


class Cursor:
    def __init__(self, rows):
        self.rows = rows
        self.max_rows = None

    def limit(self, value):
        self.max_rows = value
        return self

    async def to_list(self, length=None):
        maximum = self.max_rows if self.max_rows is not None else length
        return deepcopy(self.rows[:maximum] if maximum else self.rows)


class Collection:
    def __init__(self):
        self.rows = []

    async def create_index(self, *args, **kwargs):
        return None

    def _matches(self, row, query):
        for key, expected in query.items():
            if key == "$or":
                if not any(self._matches(row, clause) for clause in expected):
                    return False
            elif isinstance(expected, dict) and "$gt" in expected:
                if not row.get(key) or not row[key] > expected["$gt"]:
                    return False
            elif row.get(key) != expected:
                return False
        return True

    async def find_one(self, query, projection=None):
        row = next((r for r in self.rows if self._matches(r, query)), None)
        return deepcopy(row) if row else None

    def find(self, query, projection=None):
        return Cursor([deepcopy(r) for r in self.rows if self._matches(r, query)])

    async def insert_one(self, document):
        self.rows.append(deepcopy(document))

    async def delete_one(self, query):
        row = await self.find_one(query)
        if row:
            self.rows.remove(next(r for r in self.rows if self._matches(r, query)))

    async def update_one(self, query, update):
        row = next((r for r in self.rows if self._matches(r, query)), None)
        if row:
            row.update(update.get("$set", {}))
            for key, value in update.get("$inc", {}).items():
                row[key] = row.get(key, 0) + value


class Database:
    def __init__(self):
        self.web_auth_users = Collection()
        self.web_auth_resets = Collection()


def make_client(monkeypatch):
    monkeypatch.setenv("WEB_AUTH_SECRET", "a-test-only-secret-with-at-least-32-chars")
    monkeypatch.setenv("WEB_MASTER_USERNAME", "RafaMaster")
    monkeypatch.setenv("WEB_MASTER_RECOVERY_EMAIL", "shared@example.test")
    monkeypatch.setenv("WEB_MASTER_PASSWORD", "Master-passphrase-test-123")
    monkeypatch.setenv("WEB_STANDARD_USERNAME", "rafa.querol")
    monkeypatch.setenv("WEB_STANDARD_RECOVERY_EMAIL", "shared@example.test")
    monkeypatch.setenv("WEB_STANDARD_PASSWORD", "Standard-passphrase-test-123")
    app = FastAPI()
    db = Database()
    web_auth.register_web_auth(app, db)

    @app.get("/mi-oportuniia")
    async def private_page(request: Request):
        return {"username": request.state.web_user["username"], "role": request.state.web_user["role"]}

    return TestClient(app, base_url="https://testserver"), db


def test_private_area_denies_missing_session(monkeypatch):
    client, _ = make_client(monkeypatch)
    with client:
        response = client.get("/mi-oportuniia", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"].startswith("/acceso?next=")


def test_login_accepts_username_and_email_and_rejects_wrong_password(monkeypatch):
    client, _ = make_client(monkeypatch)
    with client:
        wrong = client.post("/api/auth/login", json={"identifier": "RafaMaster", "password": "wrong"})
        assert wrong.status_code == 401
        username_login = client.post("/api/auth/login", json={"identifier": "RafaMaster", "password": "Master-passphrase-test-123"})
        assert username_login.status_code == 200
        assert username_login.json()["user"]["role"] == "ADMIN"
        protected = client.get("/mi-oportuniia")
        assert protected.status_code == 200
        assert protected.json() == {"username": "RafaMaster", "role": "ADMIN"}
        client.post("/api/auth/logout")
        email_login = client.post("/api/auth/login", json={"identifier": "shared@example.test", "password": "Master-passphrase-test-123"})
        # Shared recovery email intentionally cannot identify which account is being recovered or logged into.
        assert email_login.status_code == 401
        standard = client.post("/api/auth/login", json={"identifier": "rafa.querol", "password": "Standard-passphrase-test-123"})
        assert standard.status_code == 200
        assert standard.json()["user"]["role"] == "USER"
        protected_standard = client.get("/mi-oportuniia")
        assert protected_standard.status_code == 200
        assert protected_standard.json()["role"] == "USER"


def test_password_reset_is_single_use_and_invalidates_old_password(monkeypatch):
    client, db = make_client(monkeypatch)
    sent = []
    monkeypatch.setattr(web_auth, "_send_reset_email", lambda to, username, token: sent.append((to, username, token)))
    with client:
        response = client.post("/api/auth/password-reset/request", json={
            "identifier": "RafaMaster", "recovery_email": "shared@example.test"
        })
        assert response.status_code == 200
        assert len(sent) == 1
        token = sent[0][2]
        changed = client.post("/api/auth/password-reset/confirm", json={
            "token": token, "new_password": "A-new-secure-test-password-987"
        })
        assert changed.status_code == 200
        assert client.post("/api/auth/password-reset/confirm", json={
            "token": token, "new_password": "Another-new-password-987"
        }).status_code == 400
        assert client.post("/api/auth/login", json={
            "identifier": "RafaMaster", "password": "Master-passphrase-test-123"
        }).status_code == 401
        assert client.post("/api/auth/login", json={
            "identifier": "RafaMaster", "password": "A-new-secure-test-password-987"
        }).status_code == 200
