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

# ═══════════════════════════════════════════════════════════════════════════
# FILTER CONTRACT v1 · ITERACIÓN 2 — Procedimiento / Fase / Posesión / Concursal
# DIMENSIONES DISTINTAS (hard rule):
#   PRODUCTO      = NPL | CDR | REO
#   PROCEDIMIENTO = tipo de procedimiento
#   FASE          = momento del procedimiento
#   UNIVERSO      = judicial | acuerdos
# Datos de operaciones = DEMO/fixture (no soberanos). Las fases NPL son el
# MODELO FUNCIONAL aprobado por Rafa. La taxonomía concursal NO se inventa.
# ═══════════════════════════════════════════════════════════════════════════

# ---- Tipo de procedimiento (activos ahora) ----
PROCEDURE_TYPES = [
    {"code": "ejec_hipotecaria", "name": "Ejecución hipotecaria"},
    {"code": "ejec_titulos_judiciales", "name": "Ejecución de títulos judiciales"},
    {"code": "ejec_titulos_no_judiciales", "name": "Ejecución de títulos no judiciales"},
    {"code": "otras_ejec_civiles", "name": "Otras ejecuciones civiles"},
    {"code": "concursal", "name": "Procedimiento concursal", "branch": "concursal"},
]
# Ramas preparadas en el modelo pero NO activadas en esta iteración (extensible
# sin rehacer el buscador). No se muestran ni se filtran todavía.
PROCEDURE_TYPES_FUTURE = [
    {"code": "aeat", "name": "Apremio AEAT / Hacienda"},
    {"code": "seguridad_social", "name": "Apremio Seguridad Social"},
    {"code": "notarial", "name": "Ejecución notarial"},
]

# ---- Taxonomía procesal NPL · BASE FUNCIONAL AMPLIA (41 hitos · 9 grupos) ----
# Modelo FASE PRINCIPAL (stage) + HITO / SUBESTADO (code). Aportada por Rafa como
# base funcional WEB para el filtro profesional. NO son 41 fases soberanas
# independientes: cuando exista HEADER_MAP/contrato soberano se mapea 1:1
# (fase soberana + subestado), sin duplicar taxonomías. prods = filtro contextual.
PHASE_STAGES = [
    ("preprocesal", "Preprocesal / preparación"),
    ("inicio", "Inicio de ejecución"),
    ("oposicion", "Oposición / incidencias"),
    ("embargo_cargas", "Embargo / garantía / cargas"),
    ("prep_subasta", "Valoración y preparación de subasta"),
    ("subasta", "Subasta"),
    ("remate", "Remate / adjudicación"),
    ("registro", "Registro / cargas"),
    ("posesion", "Posesión"),
]
_STAGE_PRODS = {
    "preprocesal": ["NPL"], "inicio": ["NPL"], "oposicion": ["NPL"],
    "embargo_cargas": ["NPL"], "prep_subasta": ["NPL"], "subasta": ["NPL"],
    "remate": ["NPL", "CDR"], "registro": ["NPL", "CDR", "REO"], "posesion": ["NPL", "CDR", "REO"],
}
NPL_PHASES = [
    # A · PREPROCESAL
    {"code": "preprocesal", "name": "Preprocesal / preparación del procedimiento", "stage": "preprocesal", "pre_litigation": True},
    # B · INICIO DE EJECUCIÓN
    {"code": "demanda_presentada", "name": "Demanda de ejecución presentada", "stage": "inicio"},
    {"code": "demanda_admitida", "name": "Demanda / ejecución admitida", "stage": "inicio"},
    {"code": "despacho_ejecucion", "name": "Despacho de ejecución", "stage": "inicio"},
    {"code": "requerimiento_pago", "name": "Requerimiento de pago", "stage": "inicio"},
    # C · OPOSICIÓN / INCIDENCIAS
    {"code": "plazo_oposicion", "name": "Plazo de oposición", "stage": "oposicion"},
    {"code": "oposicion_presentada", "name": "Oposición presentada", "stage": "oposicion"},
    {"code": "oposicion_tramitacion", "name": "Oposición en tramitación", "stage": "oposicion"},
    {"code": "oposicion_estimada", "name": "Oposición estimada", "stage": "oposicion"},
    {"code": "oposicion_desestimada", "name": "Oposición desestimada", "stage": "oposicion"},
    {"code": "ejecucion_suspendida", "name": "Ejecución suspendida", "stage": "oposicion"},
    {"code": "ejecucion_reanudada", "name": "Ejecución reanudada", "stage": "oposicion"},
    # D · EMBARGO / GARANTÍA / CARGAS
    {"code": "embargo_traba", "name": "Embargo / traba de bienes", "stage": "embargo_cargas"},
    {"code": "anotacion_embargo", "name": "Anotación de embargo", "stage": "embargo_cargas"},
    {"code": "certificacion_cargas", "name": "Certificación de dominio y cargas", "stage": "embargo_cargas"},
    {"code": "analisis_cargas", "name": "Análisis / depuración de cargas", "stage": "embargo_cargas"},
    {"code": "comunicacion_titulares", "name": "Comunicación a titulares / acreedores / ocupantes", "stage": "embargo_cargas"},
    # E · VALORACIÓN Y PREPARACIÓN DE SUBASTA
    {"code": "tasacion", "name": "Tasación / valoración", "stage": "prep_subasta"},
    {"code": "preparacion_subasta", "name": "Preparación de subasta", "stage": "prep_subasta"},
    {"code": "subasta_solicitada", "name": "Subasta solicitada", "stage": "prep_subasta"},
    {"code": "subasta_convocada", "name": "Subasta convocada", "stage": "prep_subasta"},
    {"code": "subasta_publicada", "name": "Subasta publicada / anunciada", "stage": "prep_subasta"},
    # F · SUBASTA
    {"code": "subasta_en_curso", "name": "Subasta abierta / en curso", "stage": "subasta"},
    {"code": "subasta_finalizada", "name": "Subasta finalizada", "stage": "subasta"},
    {"code": "subasta_con_postores", "name": "Subasta con postores", "stage": "subasta"},
    {"code": "subasta_desierta", "name": "Subasta sin postores / desierta", "stage": "subasta"},
    # G · REMATE / ADJUDICACIÓN
    {"code": "aprobacion_remate", "name": "Aprobación del remate", "stage": "remate"},
    {"code": "remate_pendiente_pago", "name": "Remate pendiente de pago / consignación", "stage": "remate"},
    {"code": "adjudicacion", "name": "Adjudicación", "stage": "remate"},
    {"code": "decreto_adjudicacion", "name": "Decreto de adjudicación", "stage": "remate"},
    {"code": "adjudicacion_firme", "name": "Adjudicación firme", "stage": "remate"},
    # H · REGISTRO / CARGAS
    {"code": "testimonio_mandamiento", "name": "Testimonio / mandamiento para inscripción", "stage": "registro"},
    {"code": "inscripcion_adjudicacion", "name": "Inscripción registral de la adjudicación", "stage": "registro"},
    {"code": "cancelacion_cargas", "name": "Cancelación de cargas", "stage": "registro"},
    # I · POSESIÓN
    {"code": "posesion_solicitada", "name": "Posesión solicitada", "stage": "posesion"},
    {"code": "incidente_ocupantes", "name": "Incidente sobre ocupantes / situación posesoria", "stage": "posesion"},
    {"code": "lanzamiento_solicitado", "name": "Lanzamiento solicitado", "stage": "posesion"},
    {"code": "lanzamiento_senalado", "name": "Lanzamiento señalado", "stage": "posesion"},
    {"code": "lanzamiento_suspendido", "name": "Lanzamiento suspendido", "stage": "posesion"},
    {"code": "lanzamiento_ejecutado", "name": "Lanzamiento ejecutado", "stage": "posesion"},
    {"code": "posesion_entregada", "name": "Posesión entregada / recuperada", "stage": "posesion"},
]
for _p in NPL_PHASES:
    _p["prods"] = _STAGE_PRODS[_p["stage"]]
PHASE_GROUPS = [
    {"stage": code, "name": name, "items": [p for p in NPL_PHASES if p["stage"] == code]}
    for code, name in PHASE_STAGES
]
# Fase principal (9 grupos) como dimensión de filtrado amplia (FASE PRINCIPAL)
PHASE_PRINCIPAL = [{"code": code, "name": name} for code, name in PHASE_STAGES]
_PHASE_ORDER = {p["code"]: i for i, p in enumerate(NPL_PHASES)}
_PHASE_STAGE = {p["code"]: p["stage"] for p in NPL_PHASES}
_STAGE_NAME = {code: name for code, name in PHASE_STAGES}

# ---- Rama concursal · SUBTAXONOMY ADAPTER ----
# La taxonomía concursal definitiva NO se inventa: queda pendiente de fuente
# soberana. La rama existe en el modelo y en la UI; sus fases se resolverán
# mediante este adapter cuando exista la fuente.
CONCURSAL_PHASE_TAXONOMY = "PENDING_SOVEREIGN_SOURCE"


def concursal_phases():
    """SUBTAXONOMY ADAPTER. Devuelve [] hasta que la fuente soberana defina las fases."""
    return []


# ---- Estado ocupacional (dimensión independiente de la fase / hito procesal) ----
# NOMBRE PÚBLICO DEL FILTRO = "Estado ocupacional". El concepto jurídico
# "posesión" se conserva en la dimensión PROCESAL (incidente sobre ocupantes,
# lanzamiento, posesión entregada). Estado ocupacional ≠ fase/hito procesal.
POSSESSION_STATES = [
    {"code": "libre", "name": "Libre"},
    {"code": "ocupado", "name": "Ocupado"},
    {"code": "arrendado", "name": "Arrendado"},
    {"code": "deudor_posesion", "name": "Propietario/deudor ocupante"},
    {"code": "tercero_posesion", "name": "Tercero ocupante"},
    {"code": "ocupacion_sin_titulo", "name": "Ocupación sin título"},
    {"code": "pendiente_verificar", "name": "Pendiente de verificar"},
]

# ---- Filtros contextuales por producto (peso/énfasis en UI) ----
CONTEXT_FILTERS = {
    "NPL": ["procedure", "phase", "occupancy", "npl_debt"],
    "CDR": ["procedure", "phase", "occupancy"],
    "REO": ["procedure", "occupancy"],
}

_PROC_NAME = {p["code"]: p["name"] for p in PROCEDURE_TYPES}
_PHASE_NAME = {p["code"]: p["name"] for p in NPL_PHASES}
_POSS_NAME = {p["code"]: p["name"] for p in POSSESSION_STATES}

# ---- Geografía · modelo de refresco INE (preparado, NO auto en producción) ----
GEO_META = {
    "source": "INE",
    "authority": "Instituto Nacional de Estadística — relación oficial de municipios",
    "reference_date": "2024-01-01",
    "dataset_origin": "codeforspain (mirror de INE) · a sustituir por fichero de autoridad INE directo",
    "last_sync": "2026-06-01",
    "counts": {"ccaa": 19, "provincias": 52, "municipios": 8132},
    "refresh_model": {
        "annual_full_refresh": "Relación oficial INE a 1 de enero (altas, bajas, renombrados). Manual y autorizado.",
        "in_year_delta_check": "Comprobación de altas / bajas / cambios de denominación / correcciones oficiales. Manual y autorizado.",
        "auto_activation": False,
        "note": "Mecanismo documentado y preparado. No se activan automatizaciones externas en producción todavía.",
    },
}


def procedure_name(code):
    return _PROC_NAME.get(code, code)


def phase_name(code):
    return _PHASE_NAME.get(code, code)


def possession_name(code):
    return _POSS_NAME.get(code, code)


def phase_stage(code):
    return _PHASE_STAGE.get(code)


def phase_stage_name(code):
    return _STAGE_NAME.get(_PHASE_STAGE.get(code), None)


def phase_principal_name(stage):
    return _STAGE_NAME.get(stage, stage)


def _phase_ge(phase, target):
    """True si la fase de la operación ha alcanzado (o superado) `target`."""
    if not phase:
        return False
    return _PHASE_ORDER.get(phase, -1) >= _PHASE_ORDER.get(target, 10 ** 9)


def documentation_for(o):
    """Modelo de documentación CONTEXTUAL (producto + procedimiento + fase).
    DEMO/aislado. Documentos SENSIBLES = protegidos (autorización server-side)."""
    prod = o.get("product")
    proc = o.get("procedure")
    phase = o.get("phase")

    def doc(name, kind, target=None, access="protected"):
        status = "Disponible" if (target is None or _phase_ge(phase, target)) else "Prevista"
        return {"name": name, "kind": kind, "status": status, "access": access}

    groups = [{"group": "Información registral", "items": [
        doc("Nota simple / información registral", "Registral"),
        doc("Certificación de dominio y cargas", "Registral"),
    ]}]

    if prod == "NPL" and proc != "concursal":
        groups.append({"group": "Documentación judicial", "items": [
            doc("Informe de situación jurídica", "Jurídico"),
            doc("Título / contrato de préstamo", "Deuda"),
            doc("Demanda de ejecución", "Judicial", "demanda_presentada"),
            doc("Auto de despacho de ejecución", "Judicial", "despacho_ejecucion"),
            doc("Diligencia de embargo", "Judicial", "embargo_traba"),
            doc("Certificación de dominio y cargas", "Cargas", "certificacion_cargas"),
            doc("Tasación para subasta", "Subasta", "tasacion"),
            doc("Decreto de adjudicación", "Adjudicación", "decreto_adjudicacion"),
        ]})
    if prod == "CDR":
        groups.append({"group": "Remate, adjudicación y cesión", "items": [
            doc("Acta / resultado de subasta", "Subasta", "subasta_finalizada"),
            doc("Decreto de adjudicación", "Adjudicación", "decreto_adjudicacion"),
            doc("Documentación de cesión de remate", "Cesión", "decreto_adjudicacion"),
            doc("Situación posesoria y entrega", "Posesión", "posesion_solicitada"),
        ]})
    if prod == "REO":
        groups.append({"group": "Documentación del activo", "items": [
            doc("Escritura / título de propiedad", "Inmobiliario"),
            doc("Certificado energético", "Inmobiliario"),
            doc("Cédula de habitabilidad / ITE", "Inmobiliario"),
            doc("Situación posesoria del activo", "Posesión"),
            doc("Dossier de comercialización", "Comercial"),
        ]})
    if proc == "concursal":
        groups.append({"group": "Documentación concursal", "items": [
            {"name": "Documentación del procedimiento concursal",
             "kind": "Concursal", "status": "Pendiente de fuente soberana", "access": "protected"},
        ], "pending_source": True})

    groups.append({"group": "Dossier económico", "items": [
        doc("Dossier económico de la operación", "Económico"),
    ]})
    return groups


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

# ---- Metadatos ITERACIÓN 2 por operación (DEMO/fixture · procedimiento/fase/posesión) ----
_POSS_FROM_OCC = {"Libre": "libre", "Ocupada": "ocupado", "Ocupado": "ocupado",
                  "Arrendado": "arrendado", "Parcialmente ocupado": "ocupado"}
_OP_META = {
    "sevilla-npl-edificio-viviendas": {"procedure": "ejec_hipotecaria", "phase": "subasta_convocada", "possession": "ocupado",
                                        "debt_pending": 815000, "guarantee_type": "Hipotecaria", "num_debtors": 1, "num_guarantees": 1},
    "alicante-cdr-apartamentos-turisticos": {"procedure": "ejec_hipotecaria", "phase": "decreto_adjudicacion", "possession": "ocupado"},
    "zaragoza-reo-nave-logistica": {"procedure": "ejec_hipotecaria", "phase": "inscripcion_adjudicacion", "possession": "libre"},
    "madrid-npl-piso-centrico": {"procedure": "concursal", "phase": None, "possession": "ocupado",
                                 "debt_pending": 340000, "guarantee_type": "Hipotecaria", "num_debtors": 2, "num_guarantees": 1},
    "barcelona-reo-local-comercial": {"procedure": "ejec_hipotecaria", "phase": "inscripcion_adjudicacion", "possession": "arrendado"},
    "malaga-cdr-chalet-parcela": {"procedure": "ejec_hipotecaria", "phase": "subasta_con_postores", "possession": "libre"},
    "murcia-reo-terreno-urbanizable": {"procedure": "otras_ejec_civiles", "phase": "inscripcion_adjudicacion", "possession": "libre"},
    "madrid-reo-garaje-plazas": {"procedure": "ejec_hipotecaria", "phase": "inscripcion_adjudicacion", "possession": "libre"},
    "alicante-reo-piso-costa": {"procedure": "ejec_hipotecaria", "phase": "inscripcion_adjudicacion", "possession": "libre"},
    "barcelona-npl-vivienda-unifamiliar": {"procedure": "ejec_hipotecaria", "phase": "embargo_traba", "possession": "ocupado",
                                           "debt_pending": 275000, "guarantee_type": "Hipotecaria", "num_debtors": 1, "num_guarantees": 1},
    "marbella-reo-villa-piscina": {"procedure": "ejec_hipotecaria", "phase": "inscripcion_adjudicacion", "possession": "libre"},
    "valencia-cdr-local-calle": {"procedure": "ejec_hipotecaria", "phase": "decreto_adjudicacion", "possession": "arrendado"},
    "bilbao-npl-adosados": {"procedure": "concursal", "phase": None, "possession": "ocupado",
                            "debt_pending": 620000, "guarantee_type": "Hipotecaria", "num_debtors": 3, "num_guarantees": 2},
}

for _o in OPPORTUNITIES:
    _o["roi_num"] = _roi_num(_o["roi"])
    _meta = _OP_META.get(_o["slug"], {})
    _o["procedure"] = _meta.get("procedure")
    _o["phase"] = _meta.get("phase")
    _o["possession"] = _meta.get("possession") or _POSS_FROM_OCC.get(_o.get("occupancy"), "pendiente_verificar")
    for _k in ("debt_pending", "guarantee_type", "num_debtors", "num_guarantees"):
        if _k in _meta:
            _o[_k] = _meta[_k]

_BY_SLUG = {o["slug"]: o for o in OPPORTUNITIES}


def enrich(o):
    d = dict(o)
    d["product_name"] = product_name(o["product"])
    d["asset_name"] = asset_name(o["asset_type"])
    # Datos dinámicos de PRESENTACIÓN pueden traer nombres soberanos ya resueltos.
    d["ccaa_name"] = o.get("ccaa_name") or geo_label("ccaa", o["ccaa"])
    d["provincia_name"] = o.get("provincia_name") or geo_label("provincia", o["ccaa"], o["provincia"])
    d["municipio_name"] = o.get("municipio_name") or geo_label("municipio", o["ccaa"], o["provincia"], o["municipio"])
    d["price_label"] = f"{o['price']:,.0f} €".replace(",", ".") if o.get("price") else "—"
    d["procedure_name"] = procedure_name(o["procedure"]) if o.get("procedure") else None
    d["phase_name"] = phase_name(o["phase"]) if o.get("phase") else None
    d["phase_principal_name"] = phase_stage_name(o["phase"]) if o.get("phase") else None
    d["possession_name"] = possession_name(o["possession"]) if o.get("possession") else None
    d["is_concursal"] = o.get("procedure") == "concursal"
    if o.get("debt_pending"):
        d["debt_label"] = f"{o['debt_pending']:,.0f} €".replace(",", ".")
    return d


def _all_opportunities(extra=None):
    merged = {o["slug"]: o for o in OPPORTUNITIES}
    for item in extra or []:
        if isinstance(item, dict) and item.get("slug"):
            merged[item["slug"]] = item
    return list(merged.values())


def get_by_slug(slug, extra=None):
    o = next((x for x in _all_opportunities(extra) if x.get("slug") == slug), None)
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
    if skip != "procedure" and f.get("procedures") and o.get("procedure") not in f["procedures"]:
        return False
    if skip != "phase" and f.get("phases") and o.get("phase") not in f["phases"]:
        return False
    if skip != "phase_principal" and f.get("phases_principal") and _PHASE_STAGE.get(o.get("phase")) not in f["phases_principal"]:
        return False
    if skip != "possession" and f.get("possessions") and o.get("possession") not in f["possessions"]:
        return False
    return True


def normalize_filters(universe="judicial", products=None, assets=None, ccaa=None,
                      provincia=None, municipio=None, price_min=None, price_max=None,
                      roi_min=None, term_max=None, procedures=None, phases=None,
                      possessions=None, phases_principal=None):
    return {
        "universe": universe if universe in ("judicial", "acuerdos") else "judicial",
        "products": _as_list(products), "assets": _as_list(assets),
        "ccaa": ccaa or None, "provincia": provincia or None, "municipio": municipio or None,
        "price_min": price_min, "price_max": price_max,
        "roi_min": roi_min, "term_max": term_max,
        "procedures": _as_list(procedures), "phases": _as_list(phases),
        "phases_principal": _as_list(phases_principal),
        "possessions": _as_list(possessions),
    }


def filter_opportunities(f, order="recientes", extra=None):
    items = _all_opportunities(extra)
    res = [o for o in items if _match(o, f)]
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


def facet_counts(f, extra=None):
    """Counts per option for current filtered set (excluding the facet's own selection)."""
    items = _all_opportunities(extra)
    counts = {"universe": {}, "product": {}, "asset": {}, "ccaa": {}}
    for u in ("judicial", "acuerdos"):
        fu = dict(f, universe=u)
        counts["universe"][u] = sum(1 for o in items if _match(o, fu, skip="universe") and o["universe"] == u)
    for p in PRODUCTS:
        counts["product"][p["code"]] = sum(1 for o in items if _match(o, f, skip="product") and o["product"] == p["code"])
    for a in ASSET_TYPES:
        counts["asset"][a["code"]] = sum(1 for o in items if _match(o, f, skip="asset") and o["asset_type"] == a["code"])
    ccaa_codes = set(GEO) | {str(o.get("ccaa")) for o in items if o.get("ccaa")}
    for c in ccaa_codes:
        n = sum(1 for o in items if _match(o, f, skip="ccaa") and o["ccaa"] == c)
        if n:
            counts["ccaa"][c] = n
    counts["procedure"] = {}
    for pt in PROCEDURE_TYPES:
        counts["procedure"][pt["code"]] = sum(1 for o in items if _match(o, f, skip="procedure") and o.get("procedure") == pt["code"])
    counts["phase"] = {}
    for ph in NPL_PHASES:
        counts["phase"][ph["code"]] = sum(1 for o in items if _match(o, f, skip="phase") and o.get("phase") == ph["code"])
    counts["phase_principal"] = {}
    for st, _n in PHASE_STAGES:
        counts["phase_principal"][st] = sum(1 for o in items if _match(o, f, skip="phase_principal") and _PHASE_STAGE.get(o.get("phase")) == st)
    counts["possession"] = {}
    for ps in POSSESSION_STATES:
        counts["possession"][ps["code"]] = sum(1 for o in items if _match(o, f, skip="possession") and o.get("possession") == ps["code"])
    return counts
