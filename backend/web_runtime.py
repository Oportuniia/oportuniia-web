"""Isolated real-account API; reuses the existing investor gateway and Mongo model.
It can be deployed before credentials exist, but cannot open accounts or access.
No public demo catalog, CORE roles or producer credentials are exposed here.
"""
import os
import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

load_dotenv(Path(__file__).parent / ".env")

from investor_access import register_investor_routes
from web_identity import register_identity_routes, ensure_indexes, enabled, public_origin
from web_accounts import bootstrap_accounts, register_account_admin_routes
from web_identity import register_password_change_routes
from web_secondfactor import register_secondfactor_routes, cipher
from web_workspace import register_workspace_routes
from web_security import BodyLimitMiddleware
from web_review import register_review_routes
from web_payments import register_payment_routes
from web_workers import register_worker_routes
from web_quarantine import register_quarantine_routes
from web_funds import register_fund_routes, ensure_fund_indexes

mongo_url, database_name = os.getenv("MONGO_URL", ""), os.getenv("DB_NAME", "")
client = db = None
if mongo_url and database_name:
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000, tz_aware=True)
    db = client[database_name]


@asynccontextmanager
async def lifespan(app):
    if enabled():
        if db is None: raise RuntimeError("WEB identity requires an isolated configured database")
        public_origin()
        if os.getenv("WEB_REQUIRE_MFA", "true") == "true": cipher()
        await db.command("ping")
        await ensure_indexes(db)
        await ensure_fund_indexes(db)
        await bootstrap_accounts(db)
    from web_quarantine import configured, quarantine_worker
    task = asyncio.create_task(quarantine_worker(db)) if db is not None and configured() else None
    from web_auto_registration import worker
    registration_task = asyncio.create_task(worker(db)) if db is not None and configured() else None
    try:
        yield
    finally:
        if registration_task:
            registration_task.cancel()
            with suppress(asyncio.CancelledError):await registration_task
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        if client: client.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.state.web_db = db
app.add_middleware(BodyLimitMiddleware)


@app.middleware("http")
async def private_policy(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.url.path != "/api/account/config" and db is None:
        response = JSONResponse({"detail": {"code": "identity_database_not_configured"}}, status_code=503)
    else:
        response = await call_next(request)
    response.headers.update({"Cache-Control": "private, no-store", "Vary": "Cookie, Authorization", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Robots-Tag": "noindex, nofollow"})
    return response


@app.get("/health")
async def health():
    return {"process": "ok", "accounts_activated": enabled() and db is not None}


@app.get("/ready")
async def ready():
    if db is None or not enabled(): return JSONResponse({"ready": False}, status_code=503)
    try: await db.command("ping")
    except Exception: return JSONResponse({"ready": False}, status_code=503)
    return {"ready": True}


router = APIRouter(prefix="/api")
register_identity_routes(router, db)
register_password_change_routes(router, db)
register_account_admin_routes(router, db)
register_secondfactor_routes(router, db)
register_investor_routes(router, db)
register_workspace_routes(router, db)
register_review_routes(router, db)
register_review_routes(router, db, prefix="/account/reviews")
register_payment_routes(router, db)
register_worker_routes(router, db)
register_quarantine_routes(router, db)
register_fund_routes(router, db)
app.include_router(router)

