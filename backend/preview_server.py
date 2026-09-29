from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List, Optional
import catalog_data as cat

ROOT = Path(__file__).parent
PUBLIC = ROOT.parent / "frontend" / "public"
templates = Jinja2Templates(directory=str(ROOT / "templates"))
app = FastAPI()

def _base(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}".rstrip("/")

def _int(v):
    try: return int(v) if v not in (None,"") else None
    except: return None

@app.get("/health")
async def health():
    return {"status":"ok","service":"oportuniia-web-review"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse((PUBLIC / "web2.html").read_text(encoding="utf-8"))

@app.get("/tecnologia", response_class=HTMLResponse)
async def tecnologia():
    return HTMLResponse((PUBLIC / "tecnologia.html").read_text(encoding="utf-8"))

@app.get("/api/locations/ccaa")
async def ccaa():
    return [{"code":k,"name":v["name"]} for k,v in cat.GEO.items()]

@app.get("/api/locations/provincias")
async def prov(ccaa:str=""):
    c=cat.GEO.get(ccaa)
    return [] if not c else [{"code":k,"name":v["name"]} for k,v in c["provincias"].items()]

@app.get("/api/locations/municipios")
async def muni(ccaa:str="",provincia:str="",q:str=""):
    return cat.municipios_of(ccaa,provincia,q)

@app.post("/api/favorites/toggle")
async def fav(payload:dict):
    return {"favorited":True,"count":1,"demo":True}

@app.post("/api/saved-searches")
async def save(payload:dict):
    return {"status":"prepared","stored":"demo"}

@app.get("/api/opportunities/compare")
async def compare(ids:str=""):
    out=[]
    for slug in [s for s in ids.split(",") if s][:3]:
        o=cat.get_by_slug(slug)
        if not o or o.get("universe")=="acuerdos": continue
        out.append({
            "slug":o["slug"],"title":o["title"],"product":o["product"],
            "universe_label":"Ejecuciones Judiciales",
            "loc":f"{o['municipio_name']}, {o['provincia_name']}",
            "asset_name":o["asset_name"],"price_label":o["price_label"],
            "timeframe_label":f"{o['timeframe']} meses",
            "situation":o["situation"],"occupancy":o["occupancy"],
            "strategy":o["strategy"],"roi":o["roi"]
        })
    return {"items":out}

@app.get("/oportunidades",response_class=HTMLResponse)
async def oportunidades(
    request:Request, universo:str="judicial",
    tipo:List[str]=Query(default=[]), activo:List[str]=Query(default=[]),
    ccaa:str="", provincia:str="", municipio:str="",
    precio_min:Optional[str]=None, precio_max:Optional[str]=None,
    roi_min:Optional[str]=None, plazo_max:Optional[str]=None,
    procedimiento:List[str]=Query(default=[]), fase:List[str]=Query(default=[]),
    posesion:List[str]=Query(default=[]), fase_principal:List[str]=Query(default=[]),
    orden:str="recientes", q:str=""
):
    if universo not in ("judicial","acuerdos"): universo="judicial"
    f=cat.normalize_filters(
        universe=universo, products=tipo, assets=activo, ccaa=ccaa,
        provincia=provincia, municipio=municipio,
        price_min=_int(precio_min), price_max=_int(precio_max),
        roi_min=_int(roi_min), term_max=_int(plazo_max),
        procedures=procedimiento, phases=fase, possessions=posesion,
        phases_principal=fase_principal
    )
    opps=cat.filter_opportunities(f,order=orden)
    counts=cat.facet_counts(f)
    chips=[]
    for p in f["products"]: chips.append({"key":"tipo","val":p,"label":f"Producto: {p}"})
    for a in f["assets"]: chips.append({"key":"activo","val":a,"label":f"Activo: {cat.asset_name(a)}"})
    for pr in f["procedures"]: chips.append({"key":"procedimiento","val":pr,"label":f"Procedimiento: {cat.procedure_name(pr)}"})
    for st in f["phases_principal"]: chips.append({"key":"fase_principal","val":st,"label":f"Fase: {cat.phase_principal_name(st)}"})
    for ph in f["phases"]: chips.append({"key":"fase","val":ph,"label":f"Hito: {cat.phase_name(ph)}"})
    for ps in f["possessions"]: chips.append({"key":"posesion","val":ps,"label":f"Ocupación: {cat.possession_name(ps)}"})
    ctx={
        "request":request,"base_url":_base(request),"universe":universo,
        "vip_active":False,"locked":universo=="acuerdos","opps":opps,
        "total":len(opps),"counts":counts,"chips":chips,
        "products":cat.PRODUCTS,"asset_groups":cat.ASSET_GROUPS,
        "sort_options":cat.SORT_OPTIONS,"price_ranges":cat.PRICE_RANGES,
        "fav_slugs":[],"procedure_types":cat.PROCEDURE_TYPES,
        "phase_groups":cat.PHASE_GROUPS,"phase_principal":cat.PHASE_PRINCIPAL,
        "possession_states":cat.POSSESSION_STATES,
        "concursal_pending":cat.CONCURSAL_PHASE_TAXONOMY=="PENDING_SOVEREIGN_SOURCE",
        "ccaa_list":[{"code":k,"name":v["name"]} for k,v in cat.GEO.items()],
        "provincias_cur":cat.provincias_of(ccaa) if ccaa else [],
        "municipios_cur":cat.municipios_of(ccaa,provincia) if ccaa and provincia else [],
        "f":f,"orden":orden,"q":q
    }
    return templates.TemplateResponse("catalogo.html",ctx)

@app.get("/oportunidades/{slug}",response_class=HTMLResponse)
async def detalle(request:Request,slug:str):
    o=cat.get_by_slug(slug)
    if not o: return HTMLResponse("<h1>404</h1>",status_code=404)
    return templates.TemplateResponse("detalle.html",{
        "request":request,"base_url":_base(request),"o":o,"interest":None,
        "locked":o["universe"]=="acuerdos","vip_active":False,
        "docs":cat.documentation_for(o),
        "concursal_pending":cat.CONCURSAL_PHASE_TAXONOMY=="PENDING_SOVEREIGN_SOURCE"
    })
