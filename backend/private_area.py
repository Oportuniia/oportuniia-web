from __future__ import annotations

from typing import List, Optional
from fastapi import Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
import catalog_data as cat


def _to_int(value: Optional[str]):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _chip_context(f):
    chips = []
    for p in f["products"]:
        chips.append({"key":"tipo","val":p,"label":f"Producto: {p}"})
    for a in f["assets"]:
        chips.append({"key":"activo","val":a,"label":f"Activo: {cat.asset_name(a)}"})
    if f["ccaa"]:
        chips.append({"key":"ccaa","val":f["ccaa"],"label":cat.geo_label("ccaa", f["ccaa"]) or f["ccaa"]})
    if f["provincia"]:
        chips.append({"key":"provincia","val":f["provincia"],"label":cat.geo_label("provincia", f["ccaa"], f["provincia"]) or f["provincia"]})
    if f["municipio"]:
        chips.append({"key":"municipio","val":f["municipio"],"label":cat.geo_label("municipio", f["ccaa"], f["provincia"], f["municipio"]) or f["municipio"]})
    if f["price_min"] is not None:
        chips.append({"key":"precio_min","val":str(f["price_min"]),"label":f"Desde {f['price_min']:,} €".replace(",", ".")})
    if f["price_max"] is not None:
        chips.append({"key":"precio_max","val":str(f["price_max"]),"label":f"Hasta {f['price_max']:,} €".replace(",", ".")})
    if f["roi_min"] is not None:
        chips.append({"key":"roi_min","val":str(f["roi_min"]),"label":f"ROI ≥ {f['roi_min']}%"})
    if f["term_max"] is not None:
        chips.append({"key":"plazo_max","val":str(f["term_max"]),"label":f"Plazo ≤ {f['term_max']} m"})
    for p in f["procedures"]:
        chips.append({"key":"procedimiento","val":p,"label":f"Procedimiento: {cat.procedure_name(p)}"})
    for p in f["phases_principal"]:
        chips.append({"key":"fase_principal","val":p,"label":f"Fase: {cat.phase_principal_name(p)}"})
    for p in f["phases"]:
        chips.append({"key":"fase","val":p,"label":f"Hito: {cat.phase_name(p)}"})
    for p in f["possessions"]:
        chips.append({"key":"posesion","val":p,"label":f"Ocupación: {cat.possession_name(p)}"})
    return chips


def _context(request: Request, universo: str, tipo: List[str], activo: List[str], ccaa: str,
             provincia: str, municipio: str, precio_min: Optional[str], precio_max: Optional[str],
             roi_min: Optional[str], plazo_max: Optional[str], procedimiento: List[str],
             fase: List[str], posesion: List[str], fase_principal: List[str], orden: str, q: str):
    f = cat.normalize_filters(
        universe=universo,
        products=tipo,
        assets=activo,
        ccaa=ccaa,
        provincia=provincia,
        municipio=municipio,
        price_min=_to_int(precio_min),
        price_max=_to_int(precio_max),
        roi_min=_to_int(roi_min),
        term_max=_to_int(plazo_max),
        procedures=procedimiento,
        phases=fase,
        possessions=posesion,
        phases_principal=fase_principal,
    )
    opps = cat.filter_opportunities(f, order=orden)
    counts = cat.facet_counts(f)
    return {
        "request": request,
        "universe": f["universe"],
        "opps": opps,
        "total": len(opps),
        "counts": counts,
        "chips": _chip_context(f),
        "products": cat.PRODUCTS,
        "asset_groups": cat.ASSET_GROUPS,
        "sort_options": cat.SORT_OPTIONS,
        "procedure_types": cat.PROCEDURE_TYPES,
        "phase_groups": cat.PHASE_GROUPS,
        "phase_principal": cat.PHASE_PRINCIPAL,
        "possession_states": cat.POSSESSION_STATES,
        "ccaa_list": [{"code": k, "name": v["name"]} for k, v in cat.GEO.items()],
        "provincias_cur": cat.provincias_of(ccaa) if ccaa else [],
        "municipios_cur": cat.municipios_of(ccaa, provincia) if (ccaa and provincia) else [],
        "f": f,
        "orden": orden,
        "q": q,
    }


def register_private_area_routes(app, templates):
    @app.get("/mi-oportuniia")
    async def mi_oportuniia_root():
        return RedirectResponse(url="/mi-oportuniia/oportunidades", status_code=307)

    @app.get("/mi-oportuniia/oportunidades", response_class=HTMLResponse)
    async def mi_oportuniia_oportunidades(
        request: Request,
        universo: str = "judicial",
        tipo: List[str] = Query(default=[]),
        activo: List[str] = Query(default=[]),
        ccaa: str = "",
        provincia: str = "",
        municipio: str = "",
        precio_min: Optional[str] = None,
        precio_max: Optional[str] = None,
        roi_min: Optional[str] = None,
        plazo_max: Optional[str] = None,
        procedimiento: List[str] = Query(default=[]),
        fase: List[str] = Query(default=[]),
        posesion: List[str] = Query(default=[]),
        fase_principal: List[str] = Query(default=[]),
        orden: str = "recientes",
        q: str = "",
    ):
        ctx = _context(request, universo, tipo, activo, ccaa, provincia, municipio, precio_min,
                       precio_max, roi_min, plazo_max, procedimiento, fase, posesion,
                       fase_principal, orden, q)
        return templates.TemplateResponse("mi_oportuniia_oportunidades.html", ctx)

    @app.get("/mi-oportuniia/perimetros", response_class=HTMLResponse)
    async def mi_oportuniia_perimetros(
        request: Request,
        universo: str = "judicial",
        tipo: List[str] = Query(default=[]),
        activo: List[str] = Query(default=[]),
        ccaa: str = "",
        provincia: str = "",
        municipio: str = "",
        precio_min: Optional[str] = None,
        precio_max: Optional[str] = None,
        roi_min: Optional[str] = None,
        plazo_max: Optional[str] = None,
        procedimiento: List[str] = Query(default=[]),
        fase: List[str] = Query(default=[]),
        posesion: List[str] = Query(default=[]),
        fase_principal: List[str] = Query(default=[]),
        q: str = "",
    ):
        ctx = _context(request, universo, tipo, activo, ccaa, provincia, municipio, precio_min,
                       precio_max, roi_min, plazo_max, procedimiento, fase, posesion,
                       fase_principal, "recientes", q)
        return templates.TemplateResponse("mi_oportuniia_perimetros.html", ctx)

    @app.get("/mi-oportuniia/oportunidades/{slug}", response_class=HTMLResponse)
    async def mi_oportuniia_detalle(request: Request, slug: str):
        o = cat.get_by_slug(slug)
        if not o:
            return HTMLResponse("Operación no encontrada", status_code=404)
        return templates.TemplateResponse("mi_oportuniia_detalle.html", {
            "request": request,
            "o": o,
            "docs": cat.documentation_for(o),
        })
