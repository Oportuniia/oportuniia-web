"""OPORTUNIIA · FILTER CONTRACT v1 · ITERACIÓN 2 tests.

Coverage:
- procedure/phase/possession API facets + counts + multiselect
- contradictory combos → 0
- /api/geo/meta INE + refresh_model.auto_activation=false
- SSR /oportunidades: facet panels, DARK theme, active chips, Limpiar todos
- SSR /oportunidades detalle: sec-procedimiento, doc-groups, DARK theme
- Concursal detail marked pending
- Acuerdos detail WHITE theme + premium-modal
- No public 'VIP' text
"""
import os
import re
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://master-deploy-2.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api/opportunities"


# ---------- API: procedure / phase / possession facets ----------
class TestProcedureFilter:
    def test_concursal_returns_one(self):
        r = requests.get(f"{API}?universo=judicial&procedimiento=concursal", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["total"] == 1
        assert d["items"][0]["slug"] == "madrid-npl-piso-centrico"

    def test_ejec_hipotecaria_returns_eight(self):
        r = requests.get(f"{API}?universo=judicial&procedimiento=ejec_hipotecaria", timeout=30)
        assert r.json()["total"] == 8

    def test_counts_procedure_unfiltered(self):
        r = requests.get(f"{API}?universo=judicial", timeout=30)
        c = r.json()["counts"]["procedure"]
        assert c["ejec_hipotecaria"] == 8
        assert c["otras_ejec_civiles"] == 1
        assert c["concursal"] == 1


class TestPhaseFilter:
    def test_embargo(self):
        r = requests.get(f"{API}?universo=judicial&fase=embargo", timeout=30)
        d = r.json()
        assert d["total"] == 1
        assert d["items"][0]["slug"] == "barcelona-npl-vivienda-unifamiliar"

    def test_finalizado(self):
        r = requests.get(f"{API}?universo=judicial&fase=finalizado", timeout=30)
        assert r.json()["total"] == 5

    def test_counts_phase_unfiltered(self):
        r = requests.get(f"{API}?universo=judicial", timeout=30)
        c = r.json()["counts"]["phase"]
        assert c["finalizado"] == 5
        assert c["embargo"] == 1
        assert c["subasta_convocada"] == 1
        assert c["subasta_celebrada"] == 1
        assert c["cesion_remate"] == 1


class TestPossessionFilter:
    def test_arrendado(self):
        r = requests.get(f"{API}?universo=judicial&posesion=arrendado", timeout=30)
        assert r.json()["total"] == 1

    def test_libre(self):
        r = requests.get(f"{API}?universo=judicial&posesion=libre", timeout=30)
        assert r.json()["total"] == 5

    def test_multiselect_libre_arrendado(self):
        r = requests.get(f"{API}?universo=judicial&posesion=libre&posesion=arrendado", timeout=30)
        assert r.json()["total"] == 6

    def test_counts_possession_unfiltered(self):
        c = requests.get(f"{API}?universo=judicial", timeout=30).json()["counts"]["possession"]
        assert c["libre"] == 5
        assert c["ocupado"] == 4
        assert c["arrendado"] == 1


class TestFacetCountsRelative:
    def test_own_facet_excluded(self):
        # When product=NPL is selected, product counts still show CDR/REO options relative to other filters
        r = requests.get(f"{API}?universo=judicial&tipo=NPL", timeout=30)
        c = r.json()["counts"]["product"]
        # Own facet's counts should include all products (CDR/REO too) since 'product' is skipped in its own facet
        assert c["NPL"] >= 1
        assert c["CDR"] >= 1
        assert c["REO"] >= 1


class TestContradictoryCombo:
    def test_npl_concursal_embargo_zero(self):
        r = requests.get(f"{API}?universo=judicial&tipo=NPL&procedimiento=concursal&fase=embargo", timeout=30)
        assert r.json()["total"] == 0


# ---------- API: geo meta ----------
class TestGeoMeta:
    def test_source_ine_no_autoactivation(self):
        r = requests.get(f"{BASE_URL}/api/geo/meta", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["source"] == "INE"
        assert d["refresh_model"]["auto_activation"] is False


# ---------- SSR catalog ----------
class TestSSRCatalog:
    def test_facet_panels_dark_theme(self):
        r = requests.get(f"{BASE_URL}/oportunidades?universo=judicial", timeout=30)
        assert r.status_code == 200
        html = r.text
        assert 'data-testid="facet-procedure"' in html
        assert 'data-testid="facet-phase"' in html
        assert 'data-testid="facet-possession"' in html
        assert 'data-testid="facet-npl-debt"' in html
        assert 'theme-judicial' in html

    def test_active_chips_and_reset(self):
        r = requests.get(f"{BASE_URL}/oportunidades?universo=judicial&procedimiento=concursal&fase=embargo&posesion=libre",
                         timeout=30)
        html = r.text
        assert "Procedimiento:" in html
        assert "Fase:" in html
        assert "Posesión:" in html
        # 'Limpiar todos' link resets to base judicial
        assert 'Limpiar todos' in html or 'limpiar' in html.lower()

    def test_acuerdos_white_theme(self):
        r = requests.get(f"{BASE_URL}/oportunidades?universo=acuerdos", timeout=30)
        assert 'theme-acuerdos' in r.text


# ---------- SSR detail ----------
class TestSSRDetail:
    def test_judicial_detail_sec_procedimiento_and_docs(self):
        r = requests.get(f"{BASE_URL}/oportunidades/barcelona-npl-vivienda-unifamiliar", timeout=30)
        assert r.status_code == 200
        html = r.text
        assert 'data-testid="sec-procedimiento"' in html
        assert 'data-testid="doc-group"' in html
        assert 'data-testid="doc-item"' in html
        assert 'theme-judicial' in html
        # Contextual data present
        assert 'Embargo' in html or 'embargo' in html.lower()
        assert 'Hipotecaria' in html or 'hipotecaria' in html.lower()

    def test_concursal_detail_pending(self):
        r = requests.get(f"{BASE_URL}/oportunidades/madrid-npl-piso-centrico", timeout=30)
        assert r.status_code == 200
        html = r.text
        assert 'Concursal' in html
        assert 'pendiente' in html.lower() or 'Pendiente' in html
        assert 'Documentación concursal' in html

    def test_acuerdos_detail_white_and_premium_modal(self):
        # marbella detail — /oportunidades/{slug} handler renders with locked=True, premium modal
        r = requests.get(f"{BASE_URL}/oportunidades/marbella-reo-villa-piscina", timeout=30,
                         allow_redirects=False)
        # server.py returns a template with locked=True (no redirect on /oportunidades/{slug} path)
        assert r.status_code == 200
        html = r.text
        assert 'theme-acuerdos' in html
        assert 'data-testid="premium-modal"' in html


# ---------- Regression: geo cascade, favorites, compare, no 'VIP' public text ----------
class TestRegression:
    def test_provincias(self):
        r = requests.get(f"{BASE_URL}/api/locations/provincias?ccaa=andalucia", timeout=30)
        assert r.status_code == 200
        codes = [c["code"] for c in r.json()]
        assert "malaga" in codes

    def test_municipios_query(self):
        r = requests.get(f"{BASE_URL}/api/locations/municipios?ccaa=andalucia&provincia=malaga&q=marb",
                         timeout=30)
        assert r.status_code == 200
        names = [c["name"].lower() for c in r.json()]
        assert any("marbella" in n for n in names)

    def test_favorites_toggle(self):
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/favorites/toggle",
                   json={"slug": "sevilla-npl-edificio-viviendas"}, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json()["favorited"], bool)

    def test_compare(self):
        ids = "sevilla-npl-edificio-viviendas,madrid-npl-piso-centrico"
        r = requests.get(f"{BASE_URL}/api/opportunities/compare?ids={ids}", timeout=30)
        assert r.status_code == 200
        assert len(r.json()["items"]) == 2

    def test_no_public_vip_text_catalog(self):
        # 'VIP' should not appear as user-visible copy anywhere; only 'Experiencia Premium'/'Activar Premium'.
        # Strip <style>, <script> and all HTML tags to check user-visible text only.
        style_re = re.compile(r'<(style|script)[^>]*>.*?</\1>', re.DOTALL | re.IGNORECASE)
        tag_re = re.compile(r'<[^>]+>')
        for url in [f"{BASE_URL}/oportunidades",
                    f"{BASE_URL}/oportunidades?universo=acuerdos",
                    f"{BASE_URL}/oportunidades/marbella-reo-villa-piscina"]:
            html = requests.get(url, timeout=30).text
            visible = tag_re.sub(' ', style_re.sub(' ', html))
            hits = re.findall(r'\bVIP\b', visible)
            assert not hits, f"Public 'VIP' text found on {url}: {hits}"
        # 'Premium' must appear on acuerdos surfaces (locked messaging)
        acuerdos_html = requests.get(f"{BASE_URL}/oportunidades?universo=acuerdos", timeout=30).text
        assert 'Premium' in tag_re.sub(' ', style_re.sub(' ', acuerdos_html))
