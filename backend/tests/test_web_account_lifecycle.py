import copy
import os
import re
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient
from local_accounts import utc
import web_auth

def matches(doc, query):
    for key, value in query.items():
        if key == "$or":
            if not any(matches(doc, part) for part in value):
                return False
            continue
        got = doc.get(key)
        if isinstance(value, dict):
            if "$gt" in value and not (got and utc(got) > utc(value["$gt"])):
                return False
            if "$regex" in value and not re.search(value["$regex"], str(got or ""), re.I):
                return False
        elif got != value:
            return False
    return True


class Cursor:
    def __init__(self, docs):
        self.docs = docs
    def limit(self, n):
        self.docs = self.docs[:n]
        return self
    async def to_list(self, *args, **kwargs):
        return copy.deepcopy(self.docs)


class Collection:
    def __init__(self, docs=()):
        self.docs = copy.deepcopy(list(docs))
    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if matches(doc, query):
                out = copy.deepcopy(doc)
                for key, include in (projection or {}).items():
                    if not include:
                        out.pop(key, None)
                return out
        return None
    def find(self, query, projection=None):
        return Cursor([d for d in self.docs if matches(d, query)])
    async def count_documents(self, query):
        return sum(matches(d, query) for d in self.docs)
    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.docs.append(copy.deepcopy(doc))
        return SimpleNamespace(inserted_id=doc["_id"])
    async def update_one(self, query, update, upsert=False, **kwargs):
        for doc in self.docs:
            if matches(doc, query):
                doc.update(copy.deepcopy(update.get("$set", {})))
                for k, v in update.get("$inc", {}).items():
                    doc[k] = doc.get(k, 0) + v
                for k in update.get("$unset", {}):
                    doc.pop(k, None)
                return SimpleNamespace(modified_count=1, matched_count=1)
        if upsert:
            self.docs.append(copy.deepcopy(query))
            return await self.update_one(query, update)
        return SimpleNamespace(modified_count=0, matched_count=0)
    async def find_one_and_update(self, query, update, **kwargs):
        await self.update_one(query, update, **kwargs)
        return await self.find_one(query)
    async def delete_one(self, query):
        self.docs = [d for d in self.docs if not matches(d, query)]
    async def delete_many(self, query):
        await self.delete_one(query)
    async def find_one_and_delete(self, query):
        doc = await self.find_one(query)
        if doc:
            await self.delete_one(query)
        return doc

class WebAccountsTests(TestCase):
    def setUp(self):
        self.password = "Initial-private-password-123"
        self.env = patch.dict(os.environ, {"WEB_AUTH_SECRET": "isolated-web-account-test-signing-secret-123456789"})
        self.env.start()
        web_auth._failed.clear()
        master = {"id": "master-id", "username": "master-test", "username_norm": "master-test", "email": "master@example.com", "email_norm": "master@example.com", "role": "ADMIN", "is_active": True, "token_version": 0, "password_hash": web_auth._hash_password(self.password)}
        self.db = SimpleNamespace(web_auth_users=Collection([master]), web_auth_resets=Collection(), account_reset_tokens=Collection(), account_reset_limits=Collection(), account_audit=Collection())
        self.app = FastAPI()
        web_auth.register_web_auth(self.app, self.db)
        @self.app.get("/mi-oportuniia")
        def private():
            return {"ok": True}
        self.admin = TestClient(self.app, base_url="https://testserver")
        self.member = TestClient(self.app, base_url="https://testserver")
        self.assertEqual(self.admin.post("/api/auth/login", json={"identifier": "master-test", "password": self.password}).status_code, 200)
    def tearDown(self):
        self.env.stop()
    def test_create_force_change_and_real_cookie_revocation(self):
        result = self.admin.post("/api/accounts/users", json={"username": "member-test", "email": "member@example.com", "name": "Member", "role": "USER", "password": self.password})
        self.assertEqual(result.status_code, 200, result.text)
        login = self.member.post("/api/auth/login", json={"identifier": "member-test", "password": self.password})
        self.assertEqual(login.status_code, 200, login.text)
        self.assertTrue(login.json()["user"]["must_change_password"])
        self.assertEqual(self.member.get("/mi-oportuniia", follow_redirects=False).status_code, 303)
        self.assertEqual(self.member.post("/api/accounts/password", json={"current_password": self.password, "new_password": "Private-new-password-123"}).status_code, 200)
        self.assertEqual(self.member.get("/api/accounts/me").status_code, 401)
        self.assertEqual(self.member.post("/api/auth/login", json={"identifier": "member-test", "password": "Private-new-password-123"}).status_code, 200)
        self.assertEqual(self.member.get("/mi-oportuniia").status_code, 200)
        self.assertEqual(self.member.get("/api/accounts/users").status_code, 403)
        self.assertEqual(self.admin.delete("/api/accounts/users/master-id").status_code, 400)
        self.assertEqual(self.admin.delete("/api/accounts/users/"+result.json()["id"]).status_code, 200)
    def test_cross_origin_account_mutation_is_rejected(self):
        response = self.admin.post("/api/accounts/users", headers={"Origin": "https://untrusted.example.com"}, json={"username": "member-test", "email": "member@example.com", "name": "Member", "role": "USER", "password": self.password})
        self.assertEqual(response.status_code, 403)

if __name__ == "__main__":
    main()
