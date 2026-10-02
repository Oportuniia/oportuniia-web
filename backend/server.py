from fastapi import FastAPI, APIRouter, Request, Response, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConfigurationError, OperationFailure, ServerSelectionTimeoutError
import os
import json
import secrets
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from wp_precheck import run_precheck, run_capability_discovery, run_item_read, run_bridge_read, _get_env, _normalize_base
import catalog_data as cat
from presentation_ingress import register_routes as register_presentation_routes
from presentation_publish import register_publish_routes as register_presentation_publish_routes
from mi_auth import register_routes as register_mi_auth_routes, register_index_lifecycle
from mi_subscription_bridge import verify_signed_event, apply_signed_event, ensure_subscription_indexes
from presentation_e2e import run_presentation_e2e_if_enabled


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Disabled by default. No genuine investor accounts or routes are activated
# until WEB has SMTP, domain/cookie origin, admin provisioning and indexes.
app.include_router(register_mi_auth_routes(db))
@app.post("/api/mi/internal/subscriptions/events", include_in_schema=False)
async def trusted_subscription_bridge(request: Request):
    # Server-to-server only. A fresh HMAC signature covers exact payload bytes.
    raw = await request.body()
    event = verify_signed_event(
        raw, timestamp=request.headers.get("x-mi-timestamp", ""),
        signature=request.headers.get("x-mi-signature", ""),
    )
    return await apply_signed_event(db, event)


@app.on_event("startup")
async def _mi_auth_indexes_if_enabled():
    if os.getenv("MI_AUTH_ENABLED") == "1":
        await register_index_lifecycle(db)()
    if os.getenv('MI_BILLING_BRIDGE_ENABLED') == '1':
        await ensure_subscription_indexes(db)



@app.on_event("startup")
async def _runtime_presentation_e2e_startup():
    """Run isolated PRESENTACIÓN → WEB E2E in background when explicitly enabled."""
    if (os.environ.get("WEB_PRESENTATION_E2E") or "").strip() != "1":
        return
    import asyncio
    asyncio.create_task(run_presentation_e2e_if_enabled(db))

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


@api_router.get("/health")
async def health():
    """Healthcheck productivo: proceso + Mongo Atlas."""
    try:
        await db.command("ping")
    except OperationFailure:
        logging.error("mongo health ping failed: auth")
        return JSONResponse(
            {"status": "degraded", "mongo": "auth_failed"},
            status_code=503,
        )
    except ConfigurationError:
        logging.error("mongo health ping failed: configuration")
        return JSONResponse(
            {"status": "degraded", "mongo": "configuration_error"},
            status_code=503,
        )
    except ServerSelectionTimeoutError:
        logging.error("mongo health ping failed: network_or_dns")
        return JSONResponse(
            {"status": "degraded", "mongo": "network_or_dns"},
            status_code=503,
        )
    except Exception as exc:
        logging.error("mongo health ping failed: %s", type(exc).__name__)
        return JSONResponse(
            {"status": "degraded", "mongo": "unavailable"},
            status_code=503,
        )
    return {
        "status": "ok",
        "mongo": "ok",
        "presentation_contract": "PRESENTATION_WEB_PUBLICATION_v1",
    }

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


@api_router.get("/wp-precheck/item")
async def wp_precheck_item(authorize: str = "", id: int = 0, rest_base: str = "elementor_library"):
    """READ-ONLY single-item GET probe. GET-only, integer id, allow-listed rest_base."""
    if authorize != "RAFA":
        return {"executed": False,
                "message": "Not authorized. Append ?authorize=RAFA to run the READ-ONLY item probe."}
    report = run_item_read(id, rest_base)
    return {"executed": True, "requested_id": id, "rest_base": rest_base, **report}


@api_router.get("/wp-precheck/bridge")
async def wp_precheck_bridge(authorize: str = ""):
    """READ-ONLY validation of the custom HEADER 2.0 bridge route. GET-only."""
    if authorize != "RAFA":
        return {"executed": False,
                "message": "Not authorized. Append ?authorize=RAFA to run the READ-ONLY bridge validation."}
    report = run_bridge_read()
    return {"executed": True, **report}


# ── OPORTUNIIA · FASE 2 · OPPORTUNITY ENGINE ─────────────────────────────────
# Todos los datos de catálogo son DEMO. Sin identidad paralela, sin pagos,
# sin reservas/compras reales, sin envíos. Favoritos = sesión anónima (cookie).

SID_COOKIE = "opp_sid"


def _to_int_or_none(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def _get_sid(request: Request) -> Optional[str]:
    return request.cookies.get(SID_COOKIE)


def _ensure_sid(request: Request, response: Response) -> str:
    sid = request.cookies.get(SID_COOKIE)
    if not sid:
        sid = secrets.token_urlsafe(16)
        response.set_cookie(SID_COOKIE, sid, max_age=60 * 60 * 24 * 180,
                            httponly=True, samesite="lax")
    return sid


def _public_base(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}".rstrip("/")


async def _vip_active(request: Request) -> bool:
    # Entitlement VIP se valida SIEMPRE en servidor. En esta fase no hay pago
    # ni identidad soberana → entitlement INACTIVO. El inventario ACUERDOS no se
    # entrega sin autorización.
    return False


async def _published_catalog_items() -> list[dict]:
    docs = await db.presentation_web_published.find(
        {"publication_state": "PUBLISHED"},
        {"_id": 0, "item": 1},
    ).to_list(1000)
    return [d["item"] for d in docs if isinstance(d.get("item"), dict)]


# ---- Modelos (contratos) ----
class FavoriteToggle(BaseModel):
    slug: str

class SavedSearchIn(BaseModel):
    query: str

class OperationIntentIn(BaseModel):
    slug: str
    action: str  # "reservar" | "comprar"


# ==== APIs FUNCIONALES ====
@api_router.get("/locations/ccaa")
async def loc_ccaa():
    return [{"code": k, "name": v["name"]} for k, v in cat.GEO.items()]

@api_router.get("/locations/provincias")
async def loc_provincias(ccaa: str = ""):
    c = cat.GEO.get(ccaa)
    if not c:
        return []
    return [{"code": k, "name": v["name"]} for k, v in c["provincias"].items()]

@api_router.get("/locations/municipios")
async def loc_municipios(ccaa: str = "", provincia: str = "", q: str = ""):
    return cat.municipios_of(ccaa, provincia, q)


@api_router.get("/opportunities")
async def api_opportunities(request: Request, universo: str = "judicial",
                            tipo: List[str] = Query(default=[]), activo: List[str] = Query(default=[]),
                            ccaa: str = "", provincia: str = "", municipio: str = "",
                            precio_min: Optional[str] = None, precio_max: Optional[str] = None,
                            roi_min: Optional[str] = None, plazo_max: Optional[str] = None,
                            procedimiento: List[str] = Query(default=[]), fase: List[str] = Query(default=[]),
                            posesion: List[str] = Query(default=[]), fase_principal: List[str] = Query(default=[]),
                            orden: str = "recientes"):
    if universo == "acuerdos" and not await _vip_active(request):
        return {"universe": "acuerdos", "locked": True, "items": [], "total": 0,
                "message": "Inventario Acuerdos reservado a Experiencia Premium activa."}
    f = cat.normalize_filters(universe=universo, products=tipo, assets=activo, ccaa=ccaa,
                              provincia=provincia, municipio=municipio,
                              price_min=_to_int_or_none(precio_min), price_max=_to_int_or_none(precio_max),
                              roi_min=_to_int_or_none(roi_min), term_max=_to_int_or_none(plazo_max),
                              procedures=procedimiento, phases=fase, possessions=posesion,
                              phases_principal=fase_principal)
    published = await _published_catalog_items()
    items = cat.filter_opportunities(f, order=orden, extra=published)
    return {"universe": universo, "locked": False, "items": items, "total": len(items),
            "counts": cat.facet_counts(f, extra=published)}


@api_router.get("/geo/meta")
async def geo_meta():
    """Fuente y modelo de refresco geográfico (INE). Preparado, sin auto en producción."""
    return cat.GEO_META


@api_router.get("/opportunities/compare")
async def api_compare(request: Request, ids: str = ""):
    vip = await _vip_active(request)
    published = await _published_catalog_items()
    out = []
    for slug in [s for s in ids.split(",") if s][:3]:
        o = cat.get_by_slug(slug, extra=published)
        if not o:
            continue
        if o["universe"] == "acuerdos" and not vip:
            continue  # no exponer inventario protegido
        out.append({
            "slug": o["slug"], "title": o["title"], "product": o["product"],
            "universe_label": "Universo Acuerdos" if o["universe"] == "acuerdos" else "Ejecuciones Judiciales",
            "loc": f"{o['municipio_name']}, {o['provincia_name']}",
            "asset_name": o["asset_name"], "price_label": o["price_label"],
            "timeframe_label": f"{o['timeframe']} meses", "situation": o["situation"],
            "occupancy": o["occupancy"], "strategy": o["strategy"], "roi": o["roi"],
        })
    return {"items": out}


@api_router.get("/favorites")
async def get_favorites(request: Request):
    sid = _get_sid(request)
    if not sid:
        return {"slugs": []}
    doc = await db.demo_favorites.find_one({"session_id": sid}, {"_id": 0, "slugs": 1})
    return {"slugs": (doc or {}).get("slugs", [])}


@api_router.post("/favorites/toggle")
async def toggle_favorite(payload: FavoriteToggle, request: Request, response: Response):
    sid = _ensure_sid(request, response)
    published = await _published_catalog_items()
    if not cat.get_by_slug(payload.slug, extra=published):
        return JSONResponse({"error": "unknown slug"}, status_code=404)
    doc = await db.demo_favorites.find_one({"session_id": sid})
    slugs = (doc or {}).get("slugs", [])
    if payload.slug in slugs:
        slugs = [s for s in slugs if s != payload.slug]
        favorited = False
    else:
        slugs = slugs + [payload.slug]
        favorited = True
    await db.demo_favorites.update_one({"session_id": sid},
        {"$set": {"slugs": slugs, "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    return {"favorited": favorited, "count": len(slugs)}


@api_router.post("/saved-searches")
async def save_search(payload: SavedSearchIn, request: Request, response: Response):
    # PREPARED / demo: se guarda un registro de sesión no autoritativo.
    # El contrato final asocia la búsqueda a actor_id en Mi OPORTUNIIA.
    sid = _ensure_sid(request, response)
    await db.demo_saved_searches.insert_one({
        "session_id": sid, "query": payload.query,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "prepared", "stored": "demo",
            "note": "Contrato listo para actor_id · notificaciones futuras opt-in."}


@api_router.post("/operations/intent")
async def operation_intent(payload: OperationIntentIn, request: Request, response: Response):
    # DEMO / NO TRANSACCIONAL. No crea reserva/compra reales, ni cobro, ni contrato.
    sid = _ensure_sid(request, response)
    if payload.action not in ("reservar", "comprar"):
        return JSONResponse({"error": "invalid action"}, status_code=400)
    published = await _published_catalog_items()
    if not cat.get_by_slug(payload.slug, extra=published):
        return JSONResponse({"error": "unknown slug"}, status_code=404)
    await db.demo_operation_intents.insert_one({
        "session_id": sid, "slug": payload.slug, "action": payload.action,
        "state": "DEMO", "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "demo", "action": payload.action, "transactional": False,
            "future_flow": ["actor_id", "opportunity", "operation", "mi_oportuniia", "documentation"],
            "note": "Interacción DEMO. Reservar y Comprar son acciones distintas; reglas contractuales no definidas en esta fase."}


async def _interest_signal(slug: str) -> Optional[str]:
    # Señal de interés VERAZ y agregada (privacy-safe). 0 evidencia = 0 mensaje.
    count = await db.demo_favorites.count_documents({"slugs": slug})
    THRESHOLD = 3
    if count >= THRESHOLD:
        return f"{count} inversores han guardado esta operación"
    return None


# ==== APIs PREPARED (contratos, sin acciones reales) ====
@api_router.get("/readiness")
async def readiness():
    return {
        "phase": "2-opportunity-engine",
        "implemented": ["catalogue", "filters", "location_cascade", "url_state", "sorting",
                        "cards", "detail", "favorites_demo", "compare", "vip_locked",
                        "reserve_buy_demo_cta"],
        "prepared_contract_only": {
            "saved_searches": {"model": ["actor_id", "query", "created_at"], "notifications": "future/opt-in"},
            "match_engine": {"signal_sources": ["explicit_preferences", "saved_searches", "favorites",
                             "behavioral_history", "transactional_history"],
                             "signal_strength": ["weak", "medium", "strong", "high_intent"],
                             "explainable": True, "fake_score": False},
            "para_ti": "future",
            "new_since_last_visit": "future",
            "interest_signals": {"aggregate_only": True, "privacy_safe": True, "fake_urgency": False},
            "notifications": {"email": "future/not-active", "whatsapp": "future/not-active",
                              "telegram": "future/not-active", "provider_selected": False, "consent_required": True},
            "operations_history": "future",
            "documentation_exchange": {"directions": ["actor->oportuniia", "oportuniia->actor"],
                                        "deadline_model": "prepared/no-hardcoded-rule", "upload": "not-implemented"},
            "mi_oportuniia": "compatible/not-fully-implemented",
            "presentacion_output": {"contract": "PRESENTATION_WEB_PUBLICATION_v1",
                                    "draft_ingress": True, "controlled_publish": True,
                                    "pdf_ejecutivo": "compatible", "pdf_completo": "compatible",
                                    "ficha_web": "integrated", "reportaje": "compatible",
                                    "real_transport": "pending_orchestration"},
            "vip_entitlement": {"product": "OPORTUNIIA_VIP", "status": ["ACTIVE", "INACTIVE", "EXPIRED"],
                                "billing_period": ["MONTHLY", "ANNUAL"], "real_price": False,
                                "payment_provider": None, "real_payment": False, "global_role": False},
            "identity": "integration-point-only (sovereign actor_id)",
        },
        "no_real": ["payment", "reservation", "purchase", "identity", "notification_send", "invented_contract_rules"],
    }

@api_router.get("/match/preview")
async def match_preview(request: Request):
    # PREPARED: explicable, sin score inventado. Cruza señales -> matches (futuro).
    return {"status": "prepared", "explainable": True, "fake_score": False,
            "sources": ["explicit_preferences", "saved_searches", "favorites",
                        "behavioral_history", "transactional_history"],
            "para_ti": []}

@api_router.get("/interest-signals/{slug}")
async def interest_signal(slug: str):
    published = await _published_catalog_items()
    if not cat.get_by_slug(slug, extra=published):
        return JSONResponse({"error": "unknown slug"}, status_code=404)
    sig = await _interest_signal(slug)
    return {"slug": slug, "signal": sig, "aggregate_only": True, "fake": False}


# Register sovereign PRESENTACIÓN → WEB M2M ingress/publication routes.
register_presentation_routes(api_router, db)
register_presentation_publish_routes(api_router, db)

# Include the router in the main app
app.include_router(api_router)

# ── SSR (Jinja2) · páginas públicas servidas por el backend a través del proxy CRA ──
TEMPLATES_DIR = ROOT_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
HOME_HTML = ROOT_DIR.parent / "frontend" / "public" / "web2.html"
PUBLIC_DIR = ROOT_DIR.parent / "frontend" / "public"

def _public_html(name: str) -> HTMLResponse:
    return HTMLResponse((PUBLIC_DIR / name).read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
async def home():
    # HOME V54 (freeze). Servida tal cual desde el archivo aprobado.
    return HTMLResponse(HOME_HTML.read_text(encoding="utf-8"))

@app.get("/nuestra-filosofia", response_class=HTMLResponse)
async def nuestra_filosofia():
    return _public_html("nuestra-filosofia.html")

@app.get("/como-funciona", response_class=HTMLResponse)
async def como_funciona():
    return _public_html("como-funciona.html")

@app.get("/grupo-oportuniia", response_class=HTMLResponse)
async def grupo_oportuniia():
    return _public_html("grupo-oportuniia.html")

@app.get("/contacto", response_class=HTMLResponse)
async def contacto():
    return _public_html("contacto.html")

@app.get("/servicers", response_class=HTMLResponse)
async def servicers():
    return _public_html("servicers.html")

@app.get("/mi-oportuniia", response_class=HTMLResponse)
async def mi_oportuniia():
    # UI is public shell only; all private data/API calls require WEB session.
    return _public_html("mi-oportuniia.html")


@app.get("/acceso", response_class=HTMLResponse)
async def acceso():
    return _public_html("acceso.html")

@app.get("/tecnologia")
async def tecnologia_redirect():
    return RedirectResponse(url="/como-funciona", status_code=307)


@app.get("/oportunidades", response_class=HTMLResponse)
async def oportunidades(request: Request, universo: str = "judicial",
                        tipo: List[str] = Query(default=[]), activo: List[str] = Query(default=[]),
                        ccaa: str = "", provincia: str = "", municipio: str = "",
                        precio_min: Optional[str] = None, precio_max: Optional[str] = None,
                        roi_min: Optional[str] = None, plazo_max: Optional[str] = None,
                        procedimiento: List[str] = Query(default=[]), fase: List[str] = Query(default=[]),
                        posesion: List[str] = Query(default=[]), fase_principal: List[str] = Query(default=[]),
                        orden: str = "recientes", q: str = ""):
    if universo not in ("judicial", "acuerdos"):
        universo = "judicial"
    vip = await _vip_active(request)
    locked = (universo == "acuerdos" and not vip)
    f = cat.normalize_filters(universe=universo, products=tipo, assets=activo, ccaa=ccaa,
                              provincia=provincia, municipio=municipio,
                              price_min=_to_int_or_none(precio_min), price_max=_to_int_or_none(precio_max),
                              roi_min=_to_int_or_none(roi_min), term_max=_to_int_or_none(plazo_max),
                              procedures=procedimiento, phases=fase, possessions=posesion,
                              phases_principal=fase_principal)
    published = await _published_catalog_items()
    opps = cat.filter_opportunities(f, order=orden, extra=published)
    total = len(opps)
    counts = cat.facet_counts(f, extra=published)
    sid = _get_sid(request)
    fav_slugs = []
    if sid:
        doc = await db.demo_favorites.find_one({"session_id": sid}, {"_id": 0, "slugs": 1})
        fav_slugs = (doc or {}).get("slugs", [])

    # chips de filtros activos
    chips = []
    for p in f["products"]:
        chips.append({"key": "tipo", "val": p, "label": f"Producto: {p}"})
    for a in f["assets"]:
        chips.append({"key": "activo", "val": a, "label": f"Activo: {cat.asset_name(a)}"})
    if f["ccaa"]:
        chips.append({"key": "ccaa", "val": f["ccaa"], "label": cat.geo_label('ccaa', f['ccaa']) or f['ccaa']})
    if f["provincia"]:
        chips.append({"key": "provincia", "val": f["provincia"], "label": cat.geo_label('provincia', f['ccaa'], f['provincia']) or f['provincia']})
    if f["municipio"]:
        chips.append({"key": "municipio", "val": f["municipio"], "label": cat.geo_label('municipio', f['ccaa'], f['provincia'], f['municipio']) or f['municipio']})
    if f["price_min"] is not None:
        chips.append({"key": "precio_min", "val": str(f["price_min"]), "label": f"Desde {f['price_min']:,} €".replace(',', '.')})
    if f["price_max"] is not None:
        chips.append({"key": "precio_max", "val": str(f["price_max"]), "label": f"Hasta {f['price_max']:,} €".replace(',', '.')})
    if f["roi_min"] is not None:
        chips.append({"key": "roi_min", "val": str(f["roi_min"]), "label": f"ROI ≥ {f['roi_min']}%"})
    if f["term_max"] is not None:
        chips.append({"key": "plazo_max", "val": str(f["term_max"]), "label": f"Plazo ≤ {f['term_max']} m"})
    for pr in f["procedures"]:
        chips.append({"key": "procedimiento", "val": pr, "label": f"Procedimiento: {cat.procedure_name(pr)}"})
    for st in f["phases_principal"]:
        chips.append({"key": "fase_principal", "val": st, "label": f"Fase: {cat.phase_principal_name(st)}"})
    for ph in f["phases"]:
        chips.append({"key": "fase", "val": ph, "label": f"Hito: {cat.phase_name(ph)}"})
    for ps in f["possessions"]:
        chips.append({"key": "posesion", "val": ps, "label": f"Ocupación: {cat.possession_name(ps)}"})

    ctx = {
        "request": request, "base_url": _public_base(request),
        "universe": universo, "vip_active": vip, "locked": locked, "opps": opps, "total": total,
        "counts": counts, "chips": chips,
        "products": cat.PRODUCTS, "asset_groups": cat.ASSET_GROUPS, "sort_options": cat.SORT_OPTIONS,
        "price_ranges": cat.PRICE_RANGES, "fav_slugs": fav_slugs,
        "procedure_types": cat.PROCEDURE_TYPES, "phase_groups": cat.PHASE_GROUPS,
        "phase_principal": cat.PHASE_PRINCIPAL, "possession_states": cat.POSSESSION_STATES,
        "concursal_pending": cat.CONCURSAL_PHASE_TAXONOMY == "PENDING_SOVEREIGN_SOURCE",
        "ccaa_list": [{"code": k, "name": v["name"]} for k, v in cat.GEO.items()],
        "provincias_cur": cat.provincias_of(ccaa) if ccaa else [],
        "municipios_cur": cat.municipios_of(ccaa, provincia) if (ccaa and provincia) else [],
        "f": f, "orden": orden, "q": q,
    }
    resp = templates.TemplateResponse("catalogo.html", ctx)
    _ensure_sid(request, resp)
    return resp


@app.get("/oportunidades/{slug}", response_class=HTMLResponse)
async def oportunidad_detalle(request: Request, slug: str):
    published = await _published_catalog_items()
    o = cat.get_by_slug(slug, extra=published)
    if not o:
        return HTMLResponse(
            "<div style='font-family:Poppins,sans-serif;padding:80px;text-align:center'>"
            "<h1 style='font-size:40px'>404</h1><p>Operación no encontrada. "
            "<a href='/oportunidades' style='color:#1F6588'>Volver a Oportunidades</a></p></div>",
            status_code=404)
    vip = await _vip_active(request)
    locked = (o["universe"] == "acuerdos" and not vip)
    interest = await _interest_signal(slug)
    # Only published backend records carry sovereign PRESENTACIÓN document metadata.
    from presentation_document_view import public_document_status
    # Fail closed: do not expose documentary inventory of restricted Acuerdos.
    raw_published_item = next((item for item in published if item.get("slug") == slug), None)
    presentation_docs = [] if locked and raw_published_item else public_document_status(raw_published_item)
    resp = templates.TemplateResponse("detalle.html", {
        "request": request, "base_url": _public_base(request), "o": o,
        "interest": interest, "locked": locked, "vip_active": vip,
        "docs": cat.documentation_for(o) if presentation_docs is None else [],
        "presentation_docs": presentation_docs, "concursal_pending": cat.CONCURSAL_PHASE_TAXONOMY == "PENDING_SOVEREIGN_SOURCE",
    })
    _ensure_sid(request, resp)
    return resp


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