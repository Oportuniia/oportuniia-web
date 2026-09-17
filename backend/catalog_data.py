"""OPORTUNIIA · Fase 2 — Opportunity Engine demo dataset + taxonomy + geo cascade.

TODOS LOS DATOS SON DEMO. No representan operaciones reales de OPORTUNIIA.
Taxonomía canónica:
  PRODUCT  = NPL | CDR | REO            (tipos de producto)
  UNIVERSE = judicial | acuerdos        (universos/catálogos; ACUERDOS es premium/VIP)
"""

# ---- Taxonomía ----
PRODUCTS = [
    {"code": "NPL", "name": "Préstamo impagado"},
    {"code": "CDR", "name": "Cesión de Remate"},
    {"code": "REO", "name": "Inmueble adjudicado"},
]

ASSET_TYPES = [
    {"code": "piso", "name": "Piso / apartamento"},
    {"code": "casa", "name": "Casa / chalet"},
    {"code": "local", "name": "Local"},
    {"code": "nave", "name": "Nave"},
    {"code": "terreno", "name": "Terreno"},
    {"code": "edificio", "name": "Edificio"},
    {"code": "garaje", "name": "Garaje"},
]

SORT_OPTIONS = [
    {"code": "recientes", "name": "Más recientes"},
    {"code": "precio-asc", "name": "Inversión: menor a mayor"},
    {"code": "precio-desc", "name": "Inversión: mayor a menor"},
    {"code": "plazo-asc", "name": "Plazo estimado: menor"},
]

# ---- Cascada geográfica (subconjunto real que cubre el dataset demo) ----
GEO = {
    "andalucia": {
        "name": "Andalucía",
        "provincias": {
            "sevilla": {"name": "Sevilla", "municipios": {"sevilla": "Sevilla", "dos-hermanas": "Dos Hermanas"}},
            "malaga": {"name": "Málaga", "municipios": {"malaga": "Málaga", "marbella": "Marbella"}},
        },
    },
    "comunidad-valenciana": {
        "name": "Comunidad Valenciana",
        "provincias": {
            "alicante": {"name": "Alicante", "municipios": {"alicante": "Alicante", "torrevieja": "Torrevieja"}},
            "valencia": {"name": "Valencia", "municipios": {"valencia": "Valencia"}},
        },
    },
    "aragon": {
        "name": "Aragón",
        "provincias": {
            "zaragoza": {"name": "Zaragoza", "municipios": {"zaragoza": "Zaragoza"}},
        },
    },
    "madrid": {
        "name": "Comunidad de Madrid",
        "provincias": {
            "madrid": {"name": "Madrid", "municipios": {"madrid": "Madrid", "alcala-de-henares": "Alcalá de Henares"}},
        },
    },
    "cataluna": {
        "name": "Cataluña",
        "provincias": {
            "barcelona": {"name": "Barcelona", "municipios": {"barcelona": "Barcelona", "hospitalet": "L'Hospitalet"}},
        },
    },
    "pais-vasco": {
        "name": "País Vasco",
        "provincias": {
            "bizkaia": {"name": "Bizkaia", "municipios": {"bilbao": "Bilbao"}},
        },
    },
    "murcia": {
        "name": "Región de Murcia",
        "provincias": {
            "murcia": {"name": "Murcia", "municipios": {"murcia": "Murcia"}},
        },
    },
}

_PROD_NAME = {p["code"]: p["name"] for p in PRODUCTS}
_ASSET_NAME = {a["code"]: a["name"] for a in ASSET_TYPES}


def _loc(ccaa, provincia, municipio):
    return {"ccaa": ccaa, "provincia": provincia, "municipio": municipio}


# ---- Dataset DEMO ----
# order = índice de publicación (para orden "recientes": mayor = más nuevo)
OPPORTUNITIES = [
    # ===== JUDICIALES (catálogo público) =====
    {
        "slug": "sevilla-npl-edificio-viviendas", "order": 10, "universe": "judicial", "product": "NPL",
        "title": "Edificio de viviendas", "asset_type": "edificio", "category": "Residencial · Garantía hipotecaria",
        **_loc("andalucia", "sevilla", "sevilla"), "price": 640000, "timeframe": 18,
        "situation": "Ejecución en curso", "occupancy": "Parcialmente ocupado", "strategy": "Vía hipotecaria",
        "roi": "27,5%", "surface": 1120, "bedrooms": None, "bathrooms": None,
        "image": "https://images.unsplash.com/photo-1755441067629-8755d974a90b?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Edificio residencial con garantía hipotecaria en proceso de ejecución. Recorrido judicial con potencial de reposicionamiento.",
    },
    {
        "slug": "alicante-cdr-apartamentos-turisticos", "order": 9, "universe": "judicial", "product": "CDR",
        "title": "Apartamentos turísticos", "asset_type": "piso", "category": "Residencial · Cesión de remate",
        **_loc("comunidad-valenciana", "alicante", "alicante"), "price": 385000, "timeframe": 24,
        "situation": "En proceso judicial", "occupancy": "Ocupada", "strategy": "Cesión de remate",
        "roi": "34,0%", "surface": 210, "bedrooms": 6, "bathrooms": 4,
        "image": "https://images.unsplash.com/photo-1663293761246-56a9b0693052?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Conjunto de apartamentos en zona turística mediante cesión de remate. Salida orientada a explotación o venta.",
    },
    {
        "slug": "zaragoza-reo-nave-logistica", "order": 8, "universe": "judicial", "product": "REO",
        "title": "Nave logística", "asset_type": "nave", "category": "Industrial · Activo adjudicado",
        **_loc("aragon", "zaragoza", "zaragoza"), "price": 910000, "timeframe": 16,
        "situation": "Disponible", "occupancy": "Libre", "strategy": "Venta directa",
        "roi": "45,0%", "surface": 3400, "bedrooms": None, "bathrooms": None,
        "image": "https://images.unsplash.com/photo-1758789667762-56175fe4601c?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Nave logística ya adjudicada, libre de ocupantes. Adquisición directa sin recorrido previo de deuda.",
    },
    {
        "slug": "madrid-npl-piso-centrico", "order": 7, "universe": "judicial", "product": "NPL",
        "title": "Piso céntrico", "asset_type": "piso", "category": "Residencial · Garantía hipotecaria",
        **_loc("madrid", "madrid", "madrid"), "price": 295000, "timeframe": 20,
        "situation": "Ejecución en curso", "occupancy": "Ocupada", "strategy": "Vía hipotecaria",
        "roi": "22,0%", "surface": 96, "bedrooms": 3, "bathrooms": 2,
        "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Vivienda en zona céntrica con garantía hipotecaria. Recorrido judicial en curso.",
    },
    {
        "slug": "barcelona-reo-local-comercial", "order": 6, "universe": "judicial", "product": "REO",
        "title": "Local comercial a pie de calle", "asset_type": "local", "category": "Comercial · Activo adjudicado",
        **_loc("cataluna", "barcelona", "barcelona"), "price": 460000, "timeframe": 12,
        "situation": "Disponible", "occupancy": "Arrendado", "strategy": "Venta directa",
        "roi": "26,5%", "surface": 180, "bedrooms": None, "bathrooms": 1,
        "image": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Local comercial adjudicado, actualmente arrendado. Rentabilidad por explotación o reventa.",
    },
    {
        "slug": "malaga-cdr-chalet-parcela", "order": 5, "universe": "judicial", "product": "CDR",
        "title": "Chalet con parcela", "asset_type": "casa", "category": "Residencial · Cesión de remate",
        **_loc("andalucia", "malaga", "malaga"), "price": 520000, "timeframe": 22,
        "situation": "En proceso judicial", "occupancy": "Libre", "strategy": "Cesión de remate",
        "roi": "31,0%", "surface": 340, "bedrooms": 5, "bathrooms": 3,
        "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Chalet independiente con parcela mediante cesión de remate. Salida residencial premium.",
    },
    {
        "slug": "murcia-reo-terreno-urbanizable", "order": 4, "universe": "judicial", "product": "REO",
        "title": "Terreno urbanizable", "asset_type": "terreno", "category": "Suelo · Activo adjudicado",
        **_loc("murcia", "murcia", "murcia"), "price": 175000, "timeframe": 28,
        "situation": "Disponible", "occupancy": "Libre", "strategy": "Venta directa",
        "roi": "38,0%", "surface": 5200, "bedrooms": None, "bathrooms": None,
        "image": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Suelo urbanizable adjudicado. Oportunidad de desarrollo a medio plazo.",
    },
    {
        "slug": "madrid-reo-garaje-plazas", "order": 3, "universe": "judicial", "product": "REO",
        "title": "Conjunto de plazas de garaje", "asset_type": "garaje", "category": "Garaje · Activo adjudicado",
        **_loc("madrid", "madrid", "alcala-de-henares"), "price": 88000, "timeframe": 10,
        "situation": "Disponible", "occupancy": "Libre", "strategy": "Venta directa",
        "roi": "19,5%", "surface": 320, "bedrooms": None, "bathrooms": None,
        "image": "https://images.unsplash.com/photo-1590674899484-d5640e854abe?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Lote de plazas de garaje adjudicadas, libres. Entrada de bajo ticket.",
    },
    {
        "slug": "alicante-reo-piso-costa", "order": 2, "universe": "judicial", "product": "REO",
        "title": "Piso en primera línea", "asset_type": "piso", "category": "Residencial · Activo adjudicado",
        **_loc("comunidad-valenciana", "alicante", "torrevieja"), "price": 168000, "timeframe": 9,
        "situation": "Disponible", "occupancy": "Libre", "strategy": "Venta directa",
        "roi": "24,0%", "surface": 78, "bedrooms": 2, "bathrooms": 1,
        "image": "https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Vivienda adjudicada en costa, libre de ocupantes. Salida rápida por reventa.",
    },
    {
        "slug": "barcelona-npl-vivienda-unifamiliar", "order": 1, "universe": "judicial", "product": "NPL",
        "title": "Vivienda unifamiliar", "asset_type": "casa", "category": "Residencial · Garantía hipotecaria",
        **_loc("cataluna", "barcelona", "hospitalet"), "price": 240000, "timeframe": 21,
        "situation": "Ejecución en curso", "occupancy": "Ocupada", "strategy": "Vía hipotecaria",
        "roi": "29,5%", "surface": 145, "bedrooms": 4, "bathrooms": 2,
        "image": "https://images.unsplash.com/photo-1449844908441-8829872d2607?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Vivienda unifamiliar con garantía hipotecaria, recorrido judicial en curso.",
    },

    # ===== ACUERDOS (inventario PREMIUM · solo con entitlement VIP activo) =====
    {
        "slug": "marbella-reo-villa-piscina", "order": 20, "universe": "acuerdos", "product": "REO",
        "title": "Vivienda unifamiliar con piscina", "asset_type": "casa", "category": "Residencial · Activo adjudicado",
        **_loc("andalucia", "malaga", "marbella"), "price": 780000, "timeframe": 10,
        "situation": "Acuerdo estructurado", "occupancy": "Libre", "strategy": "Venta pactada",
        "roi": "24,5%", "surface": 420, "bedrooms": 5, "bathrooms": 4,
        "image": "https://images.pexels.com/photos/8134745/pexels-photo-8134745.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=1100",
        "summary": "Villa con salida previamente estructurada. Capital, plazo y resultado previsto definidos de inicio.",
    },
    {
        "slug": "valencia-cdr-local-calle", "order": 19, "universe": "acuerdos", "product": "CDR",
        "title": "Local comercial a pie de calle", "asset_type": "local", "category": "Comercial · Cesión de remate",
        **_loc("comunidad-valenciana", "valencia", "valencia"), "price": 410000, "timeframe": 14,
        "situation": "Acuerdo estructurado", "occupancy": "Arrendado", "strategy": "Entrega pactada",
        "roi": "29,0%", "surface": 160, "bedrooms": None, "bathrooms": 1,
        "image": "https://images.pexels.com/photos/8649799/pexels-photo-8649799.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=1100",
        "summary": "Local con entrega pactada. Operación con visibilidad sobre plazo y resultado.",
    },
    {
        "slug": "bilbao-npl-adosados", "order": 18, "universe": "acuerdos", "product": "NPL",
        "title": "Viviendas adosadas", "asset_type": "casa", "category": "Residencial · Garantía hipotecaria",
        **_loc("pais-vasco", "bizkaia", "bilbao"), "price": 560000, "timeframe": 7,
        "situation": "Acuerdo estructurado", "occupancy": "Ocupada", "strategy": "Dación pactada",
        "roi": "37,5%", "surface": 380, "bedrooms": 8, "bathrooms": 6,
        "image": "https://images.unsplash.com/photo-1771350957359-9788d786e80e?crop=entropy&cs=srgb&fm=jpg&q=85&w=1100",
        "summary": "Conjunto de adosados con dación pactada. Salida estructurada de plazo corto.",
    },
]

_BY_SLUG = {o["slug"]: o for o in OPPORTUNITIES}


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


def enrich(o):
    """Add human labels used by templates."""
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


def filter_opportunities(universe="judicial", product=None, ccaa=None, provincia=None,
                         municipio=None, asset_type=None, price_min=None, price_max=None,
                         order="recientes"):
    """Server-side filtering. NOTE: 'acuerdos' inventory is only returned by callers
    that have verified VIP entitlement — this function itself just filters the dataset."""
    res = [o for o in OPPORTUNITIES if o["universe"] == universe]
    if product:
        res = [o for o in res if o["product"] == product]
    if ccaa:
        res = [o for o in res if o["ccaa"] == ccaa]
    if provincia:
        res = [o for o in res if o["provincia"] == provincia]
    if municipio:
        res = [o for o in res if o["municipio"] == municipio]
    if asset_type:
        res = [o for o in res if o["asset_type"] == asset_type]
    if price_min is not None:
        res = [o for o in res if o["price"] >= price_min]
    if price_max is not None:
        res = [o for o in res if o["price"] <= price_max]

    if order == "precio-asc":
        res.sort(key=lambda o: o["price"])
    elif order == "precio-desc":
        res.sort(key=lambda o: o["price"], reverse=True)
    elif order == "plazo-asc":
        res.sort(key=lambda o: o["timeframe"])
    else:  # recientes
        res.sort(key=lambda o: o["order"], reverse=True)

    return [enrich(o) for o in res]
