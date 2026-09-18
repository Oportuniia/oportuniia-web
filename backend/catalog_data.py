"""OPORTUNIIA · Fase 2 · FILTER CONTRACT v1 — taxonomía + geografía + faceted search.

TODOS LOS DATOS DE OPERACIONES SON DEMO / FIXTURE (no soberanos).
Geografía: dataset oficial INE (codeforspain) — 19 CCAA · 52 provincias · 8132 municipios.
  · La taxonomía geográfica es ESTRUCTURAL (una ubicación existe aunque tenga 0 activos).
Taxonomía producto = NPL | CDR | REO. Universo = judicial | acuerdos (transversal, no producto).
FINDING: no hay acceso a la fuente soberana / HEADER_MAP en este repo WEB; las taxonomías
jurídicas avanzadas (fases, concursal, posesión, documentación) quedan DIFERIDAS a auditoría.
"""
import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

with open(os.path.join(_DATA_DIR, "geo_es.json"), encoding="utf-8") as _f:
    GEO = json.load(_f)  # {ccaa_slug:{name, provincias:{prov_slug:{name, municipios:{muni_slug:name}}}}}

# ---- Taxonomía producto ----
PRODUCTS = [
    {"code": "NPL", "name": "Préstamo impagado"},
    {"code": "CDR", "name": "Cesión de Remate"},
    {"code": "REO", "name": "Inmueble adjudicado"},
]

# ---- Tipo de activo (taxonomía extensible, agrupada) ----
ASSET_GROUPS = [
    {"group": "Residencial", "items": [
        ("piso", "Piso"), ("atico", "Ático"), ("duplex", "Dúplex"), ("estudio", "Estudio"),
        ("casa", "Casa / chalet"), ("adosado", "Adosado / pareado"), ("villa", "Villa"),
        ("edificio", "Edificio residencial")]},
    {"group": "Aparcamiento / anexos", "items": [
        ("garaje", "Plaza de garaje / garaje"), ("trastero", "Trastero")]},
    {"group": "Comercial", "items": [("local", "Local comercial"), ("oficina", "Oficina")]},
    {"group": "Industrial / logístico", "items": [("nave", "Nave industrial / logística")]},
    {"group": "Suelo", "items": [
        ("solar", "Solar / suelo urbano"), ("terreno", "Suelo urbanizable / rústico")]},
    {"group": "Terciario / otros", "items": [
        ("hotel", "Hotel / alojamiento"), ("mixto", "Activo mixto"), ("otros", "Otros")]},
]
ASSET_TYPES = [{"code": c, "name": n} for g in ASSET_GROUPS for c, n in g["items"]]
_ASSET_NAME = {a["code"]: a["name"] for a in ASSET_TYPES}
_PROD_NAME = {p["code"]: p["name"] for p in PRODUCTS}

# ---- Rangos rápidos de capital / inversión ----
PRICE_RANGES = [
    {"code": "0-100000", "name": "Hasta 100k", "min": 0, "max": 100000},
    {"code": "100000-250000", "name": "100k – 250k", "min": 100000, "max": 250000},
    {"code": "250000-500000", "name": "250k – 500k", "min": 250000, "max": 500000},
    {"code": "500000-1000000", "name": "500k – 1M", "min": 500000, "max": 1000000},
    {"code": "1000000-", "name": "+1M", "min": 1000000, "max": None},
]

SORT_OPTIONS = [
    {"code": "recientes", "name": "Más recientes"},
    {"code": "roi-desc", "name": "ROI: mayor a menor"},
    {"code": "roi-asc", "name": "ROI: menor a mayor"},
    {"code": "precio-asc", "name": "Inversión: menor a mayor"},
    {"code": "precio-desc", "name": "Inversión: mayor a menor"},
    {"code": "plazo-asc", "name": "Plazo: menor a mayor"},
]

DATE_OPTIONS = [
    {"code": "", "name": "Cualquier fecha"},
    {"code": "7", "name": "Últimos 7 días"},
    {"code": "30", "name": "Últimos 30 días"},
]


def product_name(code):
    return _PROD_NAME.get(code, code)


def asset_name(code):
    return _ASSET_NAME.get(code, code)


def geo_label(kind, ccaa=None, provincia=None, municipio=None):
    try:
        if kind == "ccaa":
            return GEO[ccaa]["name"]
        if kind == "provincia":
            return GEO[ccaa]["provincias"][provincia]["name"]
        if kind == "municipio":
            return GEO[ccaa]["provincias"][provincia]["municipios"][municipio]
    except KeyError:
        return None
    return None


def provincias_of(ccaa):
    c = GEO.get(ccaa)
    return [{"code": k, "name": v["name"]} for k, v in c["provincias"].items()] if c else []


def municipios_of(ccaa, provincia, q="", limit=400):
    try:
        muns = GEO[ccaa]["provincias"][provincia]["municipios"]
    except KeyError:
        return []
    q = (q or "").strip().lower()
    out = [{"code": k, "name": v} for k, v in muns.items() if not q or q in v.lower()]
    return out[:limit]


def _roi_num(s):
    try:
        return float(str(s).replace("%", "").replace(",", ".").strip())
    except (ValueError, AttributeError):
        return 0.0


def _loc(ccaa, provincia, municipio):
    return {"ccaa": ccaa, "provincia": provincia, "municipio": municipio}


# ---- Dataset DEMO (order = índice de publicación) · slugs geográficos oficiales ----
OPPORTUNITIES = [
    # ===== JUDICIALES (catálogo público) =====
    {"slug": "sevilla-npl-edificio-viviendas", "order": 10, "universe": "judicial", "product": "NPL",
     "title": "Edificio de viviendas", "asset_type": "edificio", "category": "Residencial · Garantía hipotecaria",
     **_loc("andalucia", "sevilla", "sevilla"), "price": 640000, "timeframe": 18,
     "situation": "Ejecución en curso", "occupancy": "Parcialmente ocupado", "strategy": "Vía hipotecaria",
     "roi": "27,5%", "surface": 1120, "bedrooms": None, "bathrooms": None,
     "image": "https://images.unsplash.com/photo-1755441067629-8755d974a90b?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Edificio residencial con garantía hipotecaria en proceso de ejecución. Recorrido judicial con potencial de reposicionamiento."},
    {"slug": "alicante-cdr-apartamentos-turisticos", "order": 9, "universe": "judicial", "product": "CDR",
     "title": "Apartamentos turísticos", "asset_type": "piso", "category": "Residencial · Cesión de remate",
     **_loc("comunitat-valenciana", "alicante", "alacant"), "price": 385000, "timeframe": 24,
     "situation": "En proceso judicial", "occupancy": "Ocupada", "strategy": "Cesión de remate",
     "roi": "34,0%", "surface": 210, "bedrooms": 6, "bathrooms": 4,
     "image": "https://images.unsplash.com/photo-1663293761246-56a9b0693052?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Conjunto de apartamentos en zona turística mediante cesión de remate. Salida orientada a explotación o venta."},
    {"slug": "zaragoza-reo-nave-logistica", "order": 8, "universe": "judicial", "product": "REO",
     "title": "Nave logística", "asset_type": "nave", "category": "Industrial · Activo adjudicado",
     **_loc("aragon", "zaragoza", "zaragoza"), "price": 910000, "timeframe": 16,
     "situation": "Disponible", "occupancy": "Libre", "strategy": "Venta directa",
     "roi": "45,0%", "surface": 3400, "bedrooms": None, "bathrooms": None,
     "image": "https://images.unsplash.com/photo-1758789667762-56175fe4601c?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Nave logística ya adjudicada, libre de ocupantes. Adquisición directa sin recorrido previo de deuda."},
    {"slug": "madrid-npl-piso-centrico", "order": 7, "universe": "judicial", "product": "NPL",
     "title": "Piso céntrico", "asset_type": "piso", "category": "Residencial · Garantía hipotecaria",
     **_loc("madrid-comunidad-de", "madrid", "madrid"), "price": 295000, "timeframe": 20,
     "situation": "Ejecución en curso", "occupancy": "Ocupada", "strategy": "Vía hipotecaria",
     "roi": "22,0%", "surface": 96, "bedrooms": 3, "bathrooms": 2,
     "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Vivienda en zona céntrica con garantía hipotecaria. Recorrido judicial en curso."},
    {"slug": "barcelona-reo-local-comercial", "order": 6, "universe": "judicial", "product": "REO",
     "title": "Local comercial a pie de calle", "asset_type": "local", "category": "Comercial · Activo adjudicado",
     **_loc("cataluna", "barcelona", "barcelona"), "price": 460000, "timeframe": 12,
     "situation": "Disponible", "occupancy": "Arrendado", "strategy": "Venta directa",
     "roi": "26,5%", "surface": 180, "bedrooms": None, "bathrooms": 1,
     "image": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Local comercial adjudicado, actualmente arrendado. Rentabilidad por explotación o reventa."},
    {"slug": "malaga-cdr-chalet-parcela", "order": 5, "universe": "judicial", "product": "CDR",
     "title": "Chalet con parcela", "asset_type": "casa", "category": "Residencial · Cesión de remate",
     **_loc("andalucia", "malaga", "malaga"), "price": 520000, "timeframe": 22,
     "situation": "En proceso judicial", "occupancy": "Libre", "strategy": "Cesión de remate",
     "roi": "31,0%", "surface": 340, "bedrooms": 5, "bathrooms": 3,
     "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Chalet independiente con parcela mediante cesión de remate. Salida residencial premium."},
    {"slug": "murcia-reo-terreno-urbanizable", "order": 4, "universe": "judicial", "product": "REO",
     "title": "Terreno urbanizable", "asset_type": "terreno", "category": "Suelo · Activo adjudicado",
     **_loc("murcia-region-de", "murcia", "murcia"), "price": 175000, "timeframe": 28,
     "situation": "Disponible", "occupancy": "Libre", "strategy": "Venta directa",
     "roi": "38,0%", "surface": 5200, "bedrooms": None, "bathrooms": None,
     "image": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Suelo urbanizable adjudicado. Oportunidad de desarrollo a medio plazo."},
    {"slug": "madrid-reo-garaje-plazas", "order": 3, "universe": "judicial", "product": "REO",
     "title": "Conjunto de plazas de garaje", "asset_type": "garaje", "category": "Garaje · Activo adjudicado",
     **_loc("madrid-comunidad-de", "madrid", "alcala-de-henares"), "price": 88000, "timeframe": 10,
     "situation": "Disponible", "occupancy": "Libre", "strategy": "Venta directa",
     "roi": "19,5%", "surface": 320, "bedrooms": None, "bathrooms": None,
     "image": "https://images.unsplash.com/photo-1590674899484-d5640e854abe?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Lote de plazas de garaje adjudicadas, libres. Entrada de bajo ticket."},
    {"slug": "alicante-reo-piso-costa", "order": 2, "universe": "judicial", "product": "REO",
     "title": "Piso en primera línea", "asset_type": "piso", "category": "Residencial · Activo adjudicado",
     **_loc("comunitat-valenciana", "alicante", "torrevieja"), "price": 168000, "timeframe": 9,
     "situation": "Disponible", "occupancy": "Libre", "strategy": "Venta directa",
     "roi": "24,0%", "surface": 78, "bedrooms": 2, "bathrooms": 1,
     "image": "https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Vivienda adjudicada en costa, libre de ocupantes. Salida rápida por reventa."},
    {"slug": "barcelona-npl-vivienda-unifamiliar", "order": 1, "universe": "judicial", "product": "NPL",
     "title": "Vivienda unifamiliar", "asset_type": "casa", "category": "Residencial · Garantía hipotecaria",
     **_loc("cataluna", "barcelona", "hospitalet-de-llobregat-l"), "price": 240000, "timeframe": 21,
     "situation": "Ejecución en curso", "occupancy": "Ocupada", "strategy": "Vía hipotecaria",
     "roi": "29,5%", "surface": 145, "bedrooms": 4, "bathrooms": 2,
     "image": "https://images.unsplash.com/photo-1449844908441-8829872d2607?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Vivienda unifamiliar con garantía hipotecaria, recorrido judicial en curso."},

    # ===== ACUERDOS (inventario PREMIUM · solo con entitlement VIP activo) =====
    {"slug": "marbella-reo-villa-piscina", "order": 20, "universe": "acuerdos", "product": "REO",
     "title": "Vivienda unifamiliar con piscina", "asset_type": "casa", "category": "Residencial · Activo adjudicado",
     **_loc("andalucia", "malaga", "marbella"), "price": 780000, "timeframe": 10,
     "situation": "Acuerdo estructurado", "occupancy": "Libre", "strategy": "Venta pactada",
     "roi": "24,5%", "surface": 420, "bedrooms": 5, "bathrooms": 4,
     "image": "https://images.pexels.com/photos/8134745/pexels-photo-8134745.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=1100",
     "summary": "Villa con salida previamente estructurada. Capital, plazo y resultado previsto definidos de inicio."},
    {"slug": "valencia-cdr-local-calle", "order": 19, "universe": "acuerdos", "product": "CDR",
     "title": "Local comercial a pie de calle", "asset_type": "local", "category": "Comercial · Cesión de remate",
     **_loc("comunitat-valenciana", "valencia", "valencia"), "price": 410000, "timeframe": 14,
     "situation": "Acuerdo estructurado", "occupancy": "Arrendado", "strategy": "Entrega pactada",
     "roi": "29,0%", "surface": 160, "bedrooms": None, "bathrooms": 1,
     "image": "https://images.pexels.com/photos/8649799/pexels-photo-8649799.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=1100",
     "summary": "Local con entrega pactada. Operación con visibilidad sobre plazo y resultado."},
    {"slug": "bilbao-npl-adosados", "order": 18, "universe": "acuerdos", "product": "NPL",
     "title": "Viviendas adosadas", "asset_type": "adosado", "category": "Residencial · Garantía hipotecaria",
     **_loc("pais-vasco", "bizkaia", "bilbao"), "price": 560000, "timeframe": 7,
     "situation": "Acuerdo estructurado", "occupancy": "Ocupada", "strategy": "Dación pactada",
     "roi": "37,5%", "surface": 380, "bedrooms": 8, "bathrooms": 6,
     "image": "https://images.unsplash.com/photo-1771350957359-9788d786e80e?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
     "summary": "Conjunto de adosados con dación pactada. Salida estructurada de plazo corto."},
]

for _o in OPPORTUNITIES:
    _o["roi_num"] = _roi_num(_o["roi"])

_BY_SLUG = {o["slug"]: o for o in OPPORTUNITIES}


def enrich(o):
    d = dict(o)
    d["product_name"] = product_name(o["product"])
    d["asset_name"] = asset_name(o["asset_type"])
    d["ccaa_name"] = geo_label("ccaa", o["ccaa"])
    d["provincia_name"] = geo_label("provincia", o["ccaa"], o["provincia"])
    d["municipio_name"] = geo_label("municipio", o["ccaa"], o["provincia"], o["municipio"])
    d["price_label"] = f"{o['price']:,.0f} €".replace(",", ".") if o.get("price") else "—"
    return d


def get_by_slug(slug):
    o = _BY_SLUG.get(slug)
    return enrich(o) if o else None


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [x for x in v if x]
    return [x for x in str(v).split(",") if x]


def _match(o, f, skip=None):
    """f = active filter dict. skip = facet name to ignore (for faceted counts)."""
    if o["universe"] != f["universe"]:
        return False
    if skip != "product" and f.get("products") and o["product"] not in f["products"]:
        return False
    if skip != "asset" and f.get("assets") and o["asset_type"] not in f["assets"]:
        return False
    if skip != "ccaa" and f.get("ccaa") and o["ccaa"] != f["ccaa"]:
        return False
    if skip != "provincia" and f.get("provincia") and o["provincia"] != f["provincia"]:
        return False
    if skip != "municipio" and f.get("municipio") and o["municipio"] != f["municipio"]:
        return False
    if skip != "price":
        if f.get("price_min") is not None and o["price"] < f["price_min"]:
            return False
        if f.get("price_max") is not None and o["price"] > f["price_max"]:
            return False
    if skip != "roi" and f.get("roi_min") is not None and o["roi_num"] < f["roi_min"]:
        return False
    if skip != "term" and f.get("term_max") is not None and o["timeframe"] > f["term_max"]:
        return False
    return True


def normalize_filters(universe="judicial", products=None, assets=None, ccaa=None,
                      provincia=None, municipio=None, price_min=None, price_max=None,
                      roi_min=None, term_max=None):
    return {
        "universe": universe if universe in ("judicial", "acuerdos") else "judicial",
        "products": _as_list(products), "assets": _as_list(assets),
        "ccaa": ccaa or None, "provincia": provincia or None, "municipio": municipio or None,
        "price_min": price_min, "price_max": price_max,
        "roi_min": roi_min, "term_max": term_max,
    }


def filter_opportunities(f, order="recientes"):
    res = [o for o in OPPORTUNITIES if _match(o, f)]
    if order == "roi-desc":
        res.sort(key=lambda o: o["roi_num"], reverse=True)
    elif order == "roi-asc":
        res.sort(key=lambda o: o["roi_num"])
    elif order == "precio-asc":
        res.sort(key=lambda o: o["price"])
    elif order == "precio-desc":
        res.sort(key=lambda o: o["price"], reverse=True)
    elif order == "plazo-asc":
        res.sort(key=lambda o: o["timeframe"])
    else:
        res.sort(key=lambda o: o["order"], reverse=True)
    return [enrich(o) for o in res]


def facet_counts(f):
    """Counts per option for current filtered set (excluding the facet's own selection)."""
    counts = {"universe": {}, "product": {}, "asset": {}, "ccaa": {}}
    for u in ("judicial", "acuerdos"):
        fu = dict(f, universe=u)
        counts["universe"][u] = sum(1 for o in OPPORTUNITIES if _match(o, fu, skip="universe") and o["universe"] == u)
    for p in PRODUCTS:
        counts["product"][p["code"]] = sum(1 for o in OPPORTUNITIES if _match(o, f, skip="product") and o["product"] == p["code"])
    for a in ASSET_TYPES:
        counts["asset"][a["code"]] = sum(1 for o in OPPORTUNITIES if _match(o, f, skip="asset") and o["asset_type"] == a["code"])
    for c in GEO:
        n = sum(1 for o in OPPORTUNITIES if _match(o, f, skip="ccaa") and o["ccaa"] == c)
        if n:
            counts["ccaa"][c] = n
    return counts
