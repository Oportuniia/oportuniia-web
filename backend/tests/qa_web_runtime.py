"""Loopback-only browser test fixture; never a deployment target.
Synthetic Mongo/mailer, no real external storage, SMTP or payment calls.
"""
import json
import os
import sys
from pathlib import Path

if os.getenv("WEB_QA_TEST_SERVER") != "1": raise RuntimeError("QA-only server must be explicitly enabled")
sys.path.insert(0, str(Path(__file__).parent))
from test_web_identity import DB
from cryptography.fernet import Fernet
from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pyotp
import web_identity
import investor_access
import web_workspace
import web_secondfactor

os.environ.update({"WEB_IDENTITY_MODE": "web_sessions", "WEB_REQUIRE_MFA": "true", "WEB_PUBLIC_ORIGIN": "https://127.0.0.1:8443", "WEB_REGISTRATION_ENABLED": "true",
    "WEB_PRIVACY_VERSION": "QA-NOT-LEGAL", "WEB_TERMS_VERSION": "QA-NOT-LEGAL", "WEB_SMTP_HOST": "qa.invalid", "WEB_HOSTING_SMTP_AVAILABLE": "true", "WEB_SMTP_USER": "qa", "WEB_SMTP_PASSWORD": "qa-not-real",
    "WEB_MAIL_FROM": "qa@example.invalid", "WEB_FACTOR_ENCRYPTION_KEY": Fernet.generate_key().decode(), "WEB_PAYMENTS_ENABLED": "false", "WEB_PERSONAL_UPLOADS_ENABLED": "false"})
db = DB(); mails = []; app = FastAPI(); app.state.web_db = db
async def send(to, title, body): mails.append({"to": to, "title": title, "body": body})
web_identity.send_transactional = send
@app.on_event('startup')
async def initialize(): await web_identity.ensure_indexes(db)
router = APIRouter(prefix='/api');web_identity.register_identity_routes(router,db);investor_access.register_investor_routes(router,db);web_workspace.register_workspace_routes(router,db);web_secondfactor.register_secondfactor_routes(router,db);app.include_router(router)
@app.get('/__qa/mail')
async def mailbox(): return mails
@app.get('/__qa/totp')
async def otp(secret: str): return {"code": pyotp.TOTP(secret).now()}
@app.get('/cuenta')
async def account(): return FileResponse('/vercel/web/frontend/public/cuenta.html')
@app.get('/mi-oportuniia')
async def private(): return FileResponse('/vercel/web/frontend/public/mi-oportuniia.html')
app.mount('/',StaticFiles(directory='/vercel/web/frontend/public',html=True),name='static')
