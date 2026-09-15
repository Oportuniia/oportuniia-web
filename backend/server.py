from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone

from wp_precheck import run_precheck, run_capability_discovery, _get_env, _normalize_base


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# ── OPORTUNIIA · WordPress READ-ONLY precheck (Phase 2) ──────────────────────
# These endpoints NEVER auto-run. They execute only on an explicit HTTP call.
# Secrets stay server-side; only presence (SET/len) is ever reported.

@api_router.get("/wp-precheck/status")
async def wp_precheck_status():
    """Report ONLY whether the required env vars are present. No WordPress contact."""
    site, user, app_pw = _get_env()
    base_url, host = _normalize_base(site)
    return {
        "phase": "2A-prepared",
        "endpoint_ready": True,
        "wordpress_contacted": False,
        "secrets_present": {
            "WP_SITE_URL": {"set": bool(site), "valid_url": bool(base_url),
                             "host": host or None},
            "WP_USERNAME": {"set": bool(user), "len": len(user) if user else 0},
            "WP_APPLICATION_PASSWORD": {"set": bool(app_pw),
                                         "len": len(app_pw) if app_pw else 0},
        },
        "note": "READ-ONLY precheck is prepared but NOT executed. Call /api/wp-precheck/run?authorize=RAFA to run it explicitly.",
    }


@api_router.get("/wp-precheck/run")
async def wp_precheck_run(authorize: str = ""):
    """Execute the strictly READ-ONLY (GET-only) WordPress precheck.

    Requires explicit ?authorize=RAFA to prevent accidental/automated triggering.
    """
    if authorize != "RAFA":
        return {
            "executed": False,
            "wordpress_contacted": False,
            "message": "Not authorized to run. Append ?authorize=RAFA to explicitly execute the READ-ONLY precheck.",
        }
    report = run_precheck()
    return {"executed": True, **report}


@api_router.get("/wp-precheck/capability")
async def wp_precheck_capability(authorize: str = ""):
    """READ-ONLY capability discovery for the elementor_library CPT.

    GET-only. Requires ?authorize=RAFA. No role changes, no writes.
    """
    if authorize != "RAFA":
        return {
            "executed": False,
            "message": "Not authorized. Append ?authorize=RAFA to run the READ-ONLY capability discovery.",
        }
    report = run_capability_discovery()
    return {"executed": True, **report}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()