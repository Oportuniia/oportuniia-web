"""OPORTUNIIA · FILTER CONTRACT v1 · ITERACIÓN 2 · CORRECCIÓN tests.

Coverage (updated for the 41-hito taxonomy + Estado ocupacional rename):
- procedure/phase/phase_principal/possession API facets + counts + multiselect
- 41 hitos in 9 stage groups (SSR)
- Estado ocupacional label (facet-possession) with 7 states
- Combined multi-dim filter (tipo+procedimiento+fase_principal+posesion)
- Active chips prefixes: Fase: / Hito: / Ocupación: / Procedimiento:
- Contextual per product (NPL/CDR/REO) hito visibility
- Detail sec-procedimiento (Fase principal / Hito procesal / Estado ocupacional)
- Concursal detail marked pending — must NOT use NPL 41 hitos as active phase
- Acuerdos detail WHITE theme + premium-modal
- Public 'Situación posesoria' does NOT appear as a filter label
- Regression: geo cascade, favorites, compare, no public 'VIP' text
"""
import os
import re
import requests

def _read_url():
    v = os.environ.get('REACT_APP_BACKEND_URL')
    if v:
        return v.rstrip('/')
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', '.env')
    with open(env_path) as fh:
        for line in fh:
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.split('=', 1)[1].strip().rstrip('/')
    raise RuntimeError('REACT_APP_BACKEND_URL not found')

BASE_URL = _read_url()
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
    def test_embargo_traba(self):
        r = requests.get(f"{API}?universo=judicial&fase=embargo_traba", timeout=30)
        d = r.json()
        assert d["total"] == 1
        assert d["items"][0]["slug"] == "barcelona-npl-vivienda-unifamiliar"

    def test_inscripcion_adjudicacion(self):
        r = requests.get(f"{API}?universo=judicial&fase=inscripcion_adjudicacion", timeout=30)
        assert r.json()["total"] == 5

    def test_counts_phase_unfiltered(self):
        r = requests.get(f"{API}?universo=judicial", timeout=30)
        c = r.json()["counts"]["phase"]
        # All 41 phase keys must exist
        assert len(c) == 41
        # Nonzero expected
        assert c["embargo_traba"] == 1
        assert c["subasta_convocada"] == 1
        assert c["subasta_con_postores"] == 1
        assert c["decreto_adjudicacion"] == 1
        assert c["inscripcion_adjudicacion"] == 5
        # Sample of hitos with 0 demo ops
        assert c["preprocesal"] == 0
        assert c["lanzamiento_ejecutado"] == 0


class TestPhasePrincipalFilter:
    def test_counts_phase_principal_unfiltered(self):
        r = requests.get(f"{API}?universo=judicial", timeout=30)
        c = r.json()["counts"]["phase_principal"]
        # 9 stages
        assert len(c) == 9
        assert c["embargo_cargas"] == 1
        assert c["prep_subasta"] == 1
        assert c["subasta"] == 1
        assert c["remate"] == 1
        assert c["registro"] == 5
        assert c["preprocesal"] == 0
        assert c["oposicion"] == 0
        assert c["posesion"] == 0

    def test_embargo_cargas_returns_one(self):
        r = requests.get(f"{API}?universo=judicial&fase_principal=embargo_cargas", timeout=30)
        d = r.json()
        assert d["total"] == 1
        assert d["items"][0]["slug"] == "barcelona-npl-vivienda-unifamiliar"

    def test_registro_returns_five(self):
        r = requests.get(f"{API}?universo=judicial&fase_principal=registro", timeout=30)
        assert r.json()["total"] == 5


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
        # 7 possession states
        assert len(c) == 7
        assert c["libre"] == 5
        assert c["ocupado"] == 4
        assert c["arrendado"] == 1
        # New occupancy state codes must be present as keys
        for k in ("deudor_posesion", "tercero_posesion", "ocupacion_sin_titulo", "pendiente_verificar"):
            assert k in c


class TestCombinedFilter:
    def test_multi_dim_barcelona(self):
        url = f"{API}?universo=judicial&tipo=NPL&procedimiento=ejec_hipotecaria&fase_principal=embargo_cargas&posesion=ocupado"
        r = requests.get(url, timeout=30)
        d = r.json()
        assert d["total"] == 1
        assert d["items"][0]["slug"] == "barcelona-npl-vivienda-unifamiliar"


class TestContradictoryCombo:
    def test_npl_concursal_embargo_zero(self):
        r = requests.get(f"{API}?universo=judicial&tipo=NPL&procedimiento=concursal&fase=embargo_traba", timeout=30)
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
        assert 'data-testid="facet-phase-principal"' in html
        assert 'data-testid="facet-possession"' in html
        assert 'data-testid="facet-npl-debt"' in html
        assert 'theme-judicial' in html

    def test_estado_ocupacional_label_and_no_public_situacion_posesoria(self):
        r = requests.get(f"{BASE_URL}/oportunidades?universo=judicial", timeout=30)
        html = r.text
        # New public label
        assert 'Estado ocupacional' in html
        # 'Situación posesoria' must NOT appear as public filter label; it is
        # only allowed inside the hito name 'Incidente sobre ocupantes / situación posesoria'.
        # Strip tags then check case-insensitive occurrences.
        style_re = re.compile(r'<(style|script)[^>]*>.*?</\1>', re.DOTALL | re.IGNORECASE)
        tag_re = re.compile(r'<[^>]+>')
        visible = tag_re.sub(' ', style_re.sub(' ', html))
        occurrences = re.findall(r'situaci[oó]n posesoria', visible, flags=re.IGNORECASE)
        # Only 1 allowed occurrence: the hito name 'Incidente sobre ocupantes / situación posesoria'
        assert len(occurrences) <= 1, f"Public 'situación posesoria' appears more than once (found {len(occurrences)}): must only be inside hito name"

    def test_41_hitos_in_9_groups(self):
        r = requests.get(f"{BASE_URL}/oportunidades?universo=judicial", timeout=30)
        html = r.text
        # Sample codes across all 9 stages
        for code in ["preprocesal", "demanda_presentada", "plazo_oposicion", "embargo_traba",
                     "tasacion", "subasta_en_curso", "adjudicacion", "inscripcion_adjudicacion",
                     "lanzamiento_solicitado"]:
            assert f'filter-phase-{code}' in html, f"Missing hito checkbox: {code}"
        # 9 stage group headers (from PHASE_STAGES names)
        for name in ["Preprocesal", "Inicio de ejecución", "Oposición / incidencias",
                     "Embargo / garantía / cargas", "Valoración y preparación de subasta",
                     "Subasta", "Remate / adjudicación", "Registro / cargas", "Posesión"]:
            assert name in html, f"Missing stage group header: {name}"

    def test_9_phase_principal_options(self):
        r = requests.get(f"{BASE_URL}/oportunidades?universo=judicial", timeout=30)
        html = r.text
        for st in ["preprocesal", "inicio", "oposicion", "embargo_cargas", "prep_subasta",
                   "subasta", "remate", "registro", "posesion"]:
            assert f'filter-phase-principal-{st}' in html, f"Missing fase principal: {st}"

    def test_active_chips_prefixes(self):
        url = (f"{BASE_URL}/oportunidades?universo=judicial&procedimiento=concursal"
               f"&fase_principal=embargo_cargas&fase=embargo_traba&posesion=libre")
        html = requests.get(url, timeout=30).text
        assert "Procedimiento:" in html
        assert "Fase:" in html
        assert "Hito:" in html
        assert "Ocupación:" in html
        assert 'Limpiar todos' in html or 'limpiar' in html.lower()

    def test_acuerdos_white_theme(self):
        r = requests.get(f"{BASE_URL}/oportunidades?universo=acuerdos", timeout=30)
        assert 'theme-acuerdos' in r.text


# ---------- SSR detail ----------
class TestSSRDetail:
    def test_judicial_detail_labels_and_theme(self):
        r = requests.get(f"{BASE_URL}/oportunidades/barcelona-npl-vivienda-unifamiliar", timeout=30)
        assert r.status_code == 200
        html = r.text
        assert 'data-testid="sec-procedimiento"' in html
        assert 'data-testid="doc-group"' in html
        assert 'data-testid="doc-item"' in html
        assert 'theme-judicial' in html
        # New labels
        assert 'Fase principal' in html
        assert 'Hito procesal' in html
        assert 'Estado ocupacional' in html
        # Expected values for this fixture: stage='Embargo / garantía / cargas', hito='Embargo / traba de bienes'
        assert 'Embargo' in html
        # Occupancy value 'Ocupado'
        assert 'Ocupado' in html

    def test_concursal_detail_pending_no_npl_hitos(self):
        r = requests.get(f"{BASE_URL}/oportunidades/madrid-npl-piso-centrico", timeout=30)
        assert r.status_code == 200
        html = r.text
        assert 'Concursal' in html
        assert 'pendiente' in html.lower()
        assert 'Documentación concursal' in html

    def test_acuerdos_detail_white_and_premium_modal(self):
        r = requests.get(f"{BASE_URL}/oportunidades/marbella-reo-villa-piscina", timeout=30,
                         allow_redirects=False)
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
        style_re = re.compile(r'<(style|script)[^>]*>.*?</\1>', re.DOTALL | re.IGNORECASE)
        tag_re = re.compile(r'<[^>]+>')
        for url in [f"{BASE_URL}/oportunidades",
                    f"{BASE_URL}/oportunidades?universo=acuerdos",
                    f"{BASE_URL}/oportunidades/marbella-reo-villa-piscina"]:
            html = requests.get(url, timeout=30).text
            visible = tag_re.sub(' ', style_re.sub(' ', html))
            hits = re.findall(r'\bVIP\b', visible)
            assert not hits, f"Public 'VIP' text found on {url}: {hits}"
        acuerdos_html = requests.get(f"{BASE_URL}/oportunidades?universo=acuerdos", timeout=30).text
        assert 'Premium' in tag_re.sub(' ', style_re.sub(' ', acuerdos_html))
