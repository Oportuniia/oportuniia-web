import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.templating import Jinja2Templates

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from private_area import register_private_area_routes  # noqa: E402


def _client():
    app = FastAPI()
    templates = Jinja2Templates(directory=str(BACKEND / "templates"))
    register_private_area_routes(app, templates)
    return TestClient(app)


def test_private_opportunities_reuses_professional_facets_and_compact_cards():
    c = _client()
    r = c.get("/mi-oportuniia/oportunidades?universo=judicial&tipo=NPL&roi_min=20")
    assert r.status_code == 200
    html = r.text
    assert "Tipo de procedimiento" in html
    assert "Fase principal" in html
    assert "Fase / hito procesal" in html
    assert "Estado ocupacional" in html
    assert "op-grid" in html
    assert "/mi-oportuniia/oportunidades/" in html


def test_private_search_is_real_not_cosmetic():
    c = _client()
    r = c.get("/mi-oportuniia/oportunidades?universo=judicial&q=Sevilla")
    assert r.status_code == 200
    assert "Edificio de viviendas" in r.text
    assert "Apartamentos turísticos" not in r.text


def test_perimeter_builder_uses_same_professional_filter_surface():
    c = _client()
    r = c.get("/mi-oportuniia/perimetros?universo=judicial")
    assert r.status_code == 200
    html = r.text
    for label in (
        "Comunidad autónoma", "Provincia", "Municipio", "Tipo de activo",
        "Tipo de procedimiento", "Fase principal", "Fase / hito procesal",
        "Estado ocupacional", "Plazo máximo",
    ):
        assert label in html
    assert "Un perímetro es una búsqueda profesional guardada" in html


def test_private_detail_is_large_consumption_surface_with_real_slots_only():
    c = _client()
    r = c.get("/mi-oportuniia/oportunidades/sevilla-npl-edificio-viviendas")
    assert r.status_code == 200
    html = r.text
    assert "Informe ejecutivo" in html
    assert "Portada comercial" in html
    assert "Informe completo" in html
    assert "Fotografías / reportaje" in html
    assert "Pendiente de integración de fuente real" in html
    assert "Slot preparado · no simular contenido" in html
