"""OPORTUNIIA Fase 2 - Opportunity Engine backend tests.

Covers: opportunities catalog + universes, locations cascade, favorites (cookie session),
compare, operations intent DEMO, saved-searches, interest-signals, readiness, SSR pages.
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://master-deploy-2.preview.emergentagent.com').rstrip('/')


# ---------- SSR page tests ----------
class TestSSRPages:
    def test_home_serves_v54(self):
        r = requests.get(f"{BASE_URL}/", timeout=30)
        assert r.status_code == 200
        assert "Humanizamos la deuda" in r.text
        # Nav & CTA cabled to /oportunidades
        assert 'data-testid="main-nav"' in r.text
        assert 'data-testid="hero-cta-primary"' in r.text
        assert "/oportunidades" in r.text

    def test_catalog_ssr_judicial_default(self):
        r = requests.get(f"{BASE_URL}/oportunidades", timeout=30)
        assert r.status_code == 200
        # 10 judicial cards
        cards = re.findall(r'data-testid="opp-card"', r.text)
        assert len(cards) == 10, f"expected 10 cards, got {len(cards)}"
        assert 'data-testid="universe-switch"' in r.text
        assert 'data-testid="uni-judicial"' in r.text
        assert 'data-testid="uni-acuerdos"' in r.text

    def test_catalog_ssr_acuerdos_locked(self):
        # ITER2: acuerdos catalog now renders 3 blurred/locked acuerdos cards behind premium-modal (WHITE theme)
        r = requests.get(f"{BASE_URL}/oportunidades?universo=acuerdos", timeout=30)
        assert r.status_code == 200
        assert 'theme-acuerdos' in r.text
        assert 'data-testid="premium-modal"' in r.text or 'data-testid="vip-locked"' in r.text

    def test_detalle_judicial_ok(self):
        r = requests.get(f"{BASE_URL}/oportunidades/sevilla-npl-edificio-viviendas", timeout=30)
        assert r.status_code == 200
        assert 'data-testid="action-panel"' in r.text
        assert 'data-testid="cta-reservar"' in r.text
        assert 'data-testid="cta-comprar"' in r.text

    def test_detalle_acuerdos_locked_with_premium_modal(self):
        # ITER2: acuerdos detail now renders WHITE theme + premium-modal (no redirect)
        r = requests.get(f"{BASE_URL}/oportunidades/marbella-reo-villa-piscina",
                         timeout=30, allow_redirects=False)
        assert r.status_code == 200
        assert 'theme-acuerdos' in r.text
        assert 'data-testid="premium-modal"' in r.text

    def test_detalle_404(self):
        r = requests.get(f"{BASE_URL}/oportunidades/no-existe-xxx", timeout=30)
        assert r.status_code == 404


# ---------- Opportunities API ----------
class TestOpportunitiesAPI:
    def test_judicial_default(self):
        r = requests.get(f"{BASE_URL}/api/opportunities?universo=judicial", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["locked"] is False
        assert data["total"] == 10
        assert len(data["items"]) == 10

    def test_filter_npl(self):
        r = requests.get(f"{BASE_URL}/api/opportunities?universo=judicial&tipo=NPL", timeout=30)
        data = r.json()
        assert data["locked"] is False
        assert data["total"] > 0
        for it in data["items"]:
            assert it["product"] == "NPL"

    def test_filter_reo(self):
        r = requests.get(f"{BASE_URL}/api/opportunities?universo=judicial&tipo=REO", timeout=30)
        data = r.json()
        for it in data["items"]:
            assert it["product"] == "REO"
        assert data["total"] < 10

    def test_acuerdos_locked(self):
        r = requests.get(f"{BASE_URL}/api/opportunities?universo=acuerdos", timeout=30)
        data = r.json()
        assert data["locked"] is True
        assert data["total"] == 0
        assert data["items"] == []

    def test_order_price_asc(self):
        r = requests.get(f"{BASE_URL}/api/opportunities?universo=judicial&orden=precio-asc", timeout=30)
        prices = [it["price"] for it in r.json()["items"]]
        assert prices == sorted(prices)

    def test_order_price_desc(self):
        r = requests.get(f"{BASE_URL}/api/opportunities?universo=judicial&orden=precio-desc", timeout=30)
        prices = [it["price"] for it in r.json()["items"]]
        assert prices == sorted(prices, reverse=True)


# ---------- Locations cascade ----------
class TestLocations:
    def test_ccaa(self):
        r = requests.get(f"{BASE_URL}/api/locations/ccaa", timeout=30)
        codes = [c["code"] for c in r.json()]
        assert "andalucia" in codes

    def test_provincias_andalucia(self):
        r = requests.get(f"{BASE_URL}/api/locations/provincias?ccaa=andalucia", timeout=30)
        codes = [c["code"] for c in r.json()]
        assert "sevilla" in codes and "malaga" in codes

    def test_municipios_malaga(self):
        r = requests.get(f"{BASE_URL}/api/locations/municipios?ccaa=andalucia&provincia=malaga", timeout=30)
        codes = [c["code"] for c in r.json()]
        assert "malaga" in codes and "marbella" in codes


# ---------- Favorites (cookie session) ----------
class TestFavorites:
    def test_toggle_and_get(self):
        s = requests.Session()
        # toggle on
        r = s.post(f"{BASE_URL}/api/favorites/toggle",
                   json={"slug": "sevilla-npl-edificio-viviendas"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["favorited"] is True
        assert data["count"] >= 1
        # GET favorites via same session
        r2 = s.get(f"{BASE_URL}/api/favorites", timeout=30)
        assert r2.status_code == 200
        assert "sevilla-npl-edificio-viviendas" in r2.json()["slugs"]
        # toggle off
        r3 = s.post(f"{BASE_URL}/api/favorites/toggle",
                    json={"slug": "sevilla-npl-edificio-viviendas"}, timeout=30)
        assert r3.json()["favorited"] is False

    def test_toggle_unknown_slug_404(self):
        r = requests.post(f"{BASE_URL}/api/favorites/toggle",
                          json={"slug": "no-existe"}, timeout=30)
        assert r.status_code == 404


# ---------- Compare ----------
class TestCompare:
    def test_compare_judicial(self):
        ids = "sevilla-npl-edificio-viviendas,zaragoza-reo-nave-logistica,madrid-npl-piso-centrico"
        r = requests.get(f"{BASE_URL}/api/opportunities/compare?ids={ids}", timeout=30)
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 3
        # objective fields present
        keys = {"universe_label", "product", "loc", "price_label", "timeframe_label",
                "situation", "occupancy", "strategy", "roi"}
        assert keys.issubset(set(items[0].keys()))

    def test_compare_excludes_acuerdos(self):
        ids = "sevilla-npl-edificio-viviendas,marbella-reo-villa-piscina"
        r = requests.get(f"{BASE_URL}/api/opportunities/compare?ids={ids}", timeout=30)
        items = r.json()["items"]
        slugs = [i["slug"] for i in items]
        assert "marbella-reo-villa-piscina" not in slugs
        assert "sevilla-npl-edificio-viviendas" in slugs


# ---------- Operations intent (DEMO) ----------
class TestOperationsIntent:
    def test_reservar_demo(self):
        r = requests.post(f"{BASE_URL}/api/operations/intent",
                          json={"slug": "sevilla-npl-edificio-viviendas", "action": "reservar"},
                          timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "demo"
        assert data["transactional"] is False

    def test_comprar_demo(self):
        r = requests.post(f"{BASE_URL}/api/operations/intent",
                          json={"slug": "sevilla-npl-edificio-viviendas", "action": "comprar"},
                          timeout=30)
        assert r.status_code == 200
        assert r.json()["transactional"] is False

    def test_invalid_action_400(self):
        r = requests.post(f"{BASE_URL}/api/operations/intent",
                          json={"slug": "sevilla-npl-edificio-viviendas", "action": "hackear"},
                          timeout=30)
        assert r.status_code == 400

    def test_unknown_slug_404(self):
        r = requests.post(f"{BASE_URL}/api/operations/intent",
                          json={"slug": "no-existe", "action": "reservar"}, timeout=30)
        assert r.status_code == 404


# ---------- Saved searches ----------
class TestSavedSearches:
    def test_prepared(self):
        r = requests.post(f"{BASE_URL}/api/saved-searches",
                          json={"query": "REO Andalucia"}, timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] == "prepared"


# ---------- Interest signals ----------
class TestInterestSignals:
    def test_below_threshold_null(self):
        r = requests.get(f"{BASE_URL}/api/interest-signals/madrid-npl-piso-centrico", timeout=30)
        assert r.status_code == 200
        data = r.json()
        # Below threshold expected → signal null, truthful (fake=False)
        assert data["fake"] is False
        assert data["aggregate_only"] is True

    def test_unknown_slug_404(self):
        r = requests.get(f"{BASE_URL}/api/interest-signals/no-existe", timeout=30)
        assert r.status_code == 404


# ---------- Readiness ----------
class TestReadiness:
    def test_readiness(self):
        r = requests.get(f"{BASE_URL}/api/readiness", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "catalogue" in data["implemented"]
        assert "reserve_buy_demo_cta" in data["implemented"]
        assert "payment" in data["no_real"]
