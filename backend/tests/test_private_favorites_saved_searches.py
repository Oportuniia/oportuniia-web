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


def test_private_navigation_exposes_favorites_and_saved_searches():
    r = _client().get("/mi-oportuniia/oportunidades")
    assert r.status_code == 200
    assert "/mi-oportuniia/favoritos" in r.text
    assert "/mi-oportuniia/busquedas-guardadas" in r.text
    assert "Guardar búsqueda" in r.text
    assert "data-fav-slug=" in r.text


def test_favorites_workspace_renders_compact_cards_hidden_until_session_lookup():
    r = _client().get("/mi-oportuniia/favoritos")
    assert r.status_code == 200
    assert "Tus oportunidades guardadas" in r.text
    assert 'id="favGrid"' in r.text
    assert "/api/favorites" in r.text
    assert "data-fav-card=" in r.text


def test_saved_searches_workspace_executes_back_into_professional_search():
    r = _client().get("/mi-oportuniia/busquedas-guardadas")
    assert r.status_code == 200
    assert "Recupera en un clic" in r.text
    assert "/api/saved-searches" in r.text
    assert "/mi-oportuniia/oportunidades" in r.text
