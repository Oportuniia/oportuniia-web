"""
OPORTUNIIA · WordPress REST READ-ONLY precheck.

SECURITY CONTRACT (enforced by design):
- HTTP GET only. No POST/PUT/PATCH/DELETE helpers exist in this module.
- Target host is derived exclusively from the WP_SITE_URL environment variable.
  No client-supplied URL, host, path, or method is ever accepted.
- Not a generic proxy: callers can only trigger the fixed precheck routine.
- Secrets (WP_USERNAME, WP_APPLICATION_PASSWORD) live server-side only.
  They are never returned, printed, logged, sent to the frontend, or stored.
- Authorization headers are never logged.
- Redirects are NOT followed; any attempt to leave the WP host => FAIL + STOP.
- Nothing here auto-executes. It runs only when its endpoint is called explicitly.
"""

import base64
import logging
import os
import time
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("wp_precheck")

_ROOT_DISCOVERY = "/wp-json/"
_WP_V2 = "/wp-json/wp/v2"

_TIMEOUT = httpx.Timeout(20.0, connect=10.0)


def _get_env():
    site = os.environ.get("WP_SITE_URL", "").strip()
    user = os.environ.get("WP_USERNAME", "").strip()
    app_pw = os.environ.get("WP_APPLICATION_PASSWORD", "").strip()
    return site, user, app_pw


def _normalize_base(site_url: str):
    if not site_url:
        return None, None
    parsed = urlparse(site_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None, None
    base = f"{parsed.scheme}://{parsed.netloc}"
    return base, parsed.netloc.lower()


class RedirectBlocked(Exception):
    pass


def _auth_header(user: str, app_pw: str) -> dict:
    token = base64.b64encode(f"{user}:{app_pw}".encode()).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def _log_call(path: str, status, duration_ms: float, result: str):
    logger.info("wp_precheck GET %s -> http=%s dur_ms=%.0f %s",
                path, status if status is not None else "ERR", duration_ms, result)


def _get(client: httpx.Client, base_url: str, base_host: str, path: str,
         headers: dict | None = None):
    """Single hardened GET. Host-locked, no auto redirect off-host."""
    url = base_url + path
    started = time.perf_counter()
    status = None
    try:
        resp = client.get(url, headers=headers or {}, timeout=_TIMEOUT,
                          follow_redirects=False)
        status = resp.status_code
        hops = 0
        while resp.is_redirect and hops < 3:
            loc = resp.headers.get("location", "")
            nxt_host = urlparse(loc).netloc.lower()
            if nxt_host and nxt_host != base_host:
                raise RedirectBlocked(f"redirect off-host to '{nxt_host}' blocked")
            follow_path = loc if loc.startswith("http") else base_url + loc
            resp = client.get(follow_path, headers=headers or {}, timeout=_TIMEOUT,
                              follow_redirects=False)
            status = resp.status_code
            hops += 1
        dur = (time.perf_counter() - started) * 1000
        result = "PASS" if 200 <= status < 400 else "FAIL"
        _log_call(path, status, dur, result)
        return {"path": path, "http": status, "resp": resp}
    except RedirectBlocked:
        dur = (time.perf_counter() - started) * 1000
        _log_call(path, status, dur, "FAIL")
        raise
    except httpx.HTTPError as e:
        dur = (time.perf_counter() - started) * 1000
        _log_call(path, status, dur, "FAIL")
        return {"path": path, "http": None, "error": type(e).__name__, "resp": None}


def _title_of(it):
    t = it.get("title")
    if isinstance(t, dict):
        return t.get("rendered") or t.get("raw") or ""
    if isinstance(t, str):
        return t
    return ""


def _match(items, keyword_sets):
    """items: list of dicts. keyword_sets: list of keyword-lists (OR of ANDs)."""
    hits = []
    for it in items:
        low = _title_of(it).lower()
        for ks in keyword_sets:
            if all(k in low for k in ks):
                hits.append({
                    "id": it.get("id"),
                    "title": _title_of(it),
                    "type": it.get("type"),
                    "status": it.get("status"),
                    "slug": it.get("slug"),
                })
                break
    return hits


def _as_list(resp):
    try:
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


# Valid WordPress REST statuses (NEVER 'any' -> that returns HTTP 400).
_STATUSES = "publish,draft,pending,private,future"

# Fallback REST bases if /wp/v2/types enumeration is unavailable.
_FALLBACK_TYPES = ["pages", "posts", "elementor_library"]


def _list_type(client, base_url, base_host, rest_base, ctx, headers):
    """GET a collection with valid statuses; retry without status on 400. Read-only."""
    q = f"{_WP_V2}/{rest_base}?{ctx}per_page=100&status={_STATUSES}"
    r = _get(client, base_url, base_host, q, headers=headers)
    if r.get("http") == 400:
        q2 = f"{_WP_V2}/{rest_base}?{ctx}per_page=100"
        r = _get(client, base_url, base_host, q2, headers=headers)
    return r


def run_precheck() -> dict:
    site, user, app_pw = _get_env()
    base_url, base_host = _normalize_base(site)

    gate = {
        "WORDPRESS_REST_AUTH": "FAIL",
        "TECHNICAL_USER": "FAIL",
        "TECHNICAL_USER_CAPS": {},
        "HOME_2_0_DETECTED": "FAIL",
        "HOME_2_0_ID": "NOT FOUND",
        "HOME_2_0_POST_TYPE": "UNKNOWN",
        "HOME_2_0_STATUS": "UNKNOWN",
        "HEADER_2_0_DETECTED": "FAIL",
        "HEADER_2_0_ID": "NOT FOUND",
        "HEADER_2_0_POST_TYPE": "UNKNOWN",
        "HEADER_2_0_STATUS": "UNKNOWN",
        "ELEMENTOR_DATA_ACCESSIBLE": "FAIL",
        "ELEMENTOR_DATA_LOCATION": "UNKNOWN",
        "ELEMENTOR_META_COMPLETE": "UNKNOWN",
        "THEME_BUILDER_RELATIONSHIP_IDENTIFIED": "NO",
        "THEME_BUILDER_GET": "FAIL",
        "SAFE_WRITE_PATH_IDENTIFIED": "NO",
        "CUSTOM_ENDPOINT_PLUGIN_REQUIRED": "UNKNOWN",
        "REST_NAMESPACES": [],
        "WORDPRESS_REQUESTS_EXECUTED": 0,
        "WRITE_REQUESTS_EXECUTED": 0,
        "PRODUCTION_MUTATIONS": 0,
        "WORDPRESS_CONTACTED": "YES",
        "BLOCKER": "NONE",
        "diagnostics": [],
    }

    if not base_url:
        gate["BLOCKER"] = "WP_SITE_URL missing/invalid"
        gate["WORDPRESS_CONTACTED"] = "NO"
        return gate
    if not user or not app_pw:
        gate["BLOCKER"] = "WP_USERNAME/WP_APPLICATION_PASSWORD not set"
        gate["WORDPRESS_CONTACTED"] = "NO"
        return gate

    auth = _auth_header(user, app_pw)
    req = 0

    with httpx.Client(headers={"User-Agent": "OPORTUNIIA-ControlApp-Precheck/1.1 (read-only)"}) as client:
        try:
            # 1) Root discovery
            root = _get(client, base_url, base_host, _ROOT_DISCOVERY); req += 1
            if not (root.get("resp") is not None and root["http"] == 200):
                gate["BLOCKER"] = "WP REST root (/wp-json/) not reachable"
                gate["WORDPRESS_REQUESTS_EXECUTED"] = req
                return gate
            try:
                rj = root["resp"].json()
                ns = rj.get("namespaces", [])
                routes = list((rj.get("routes") or {}).keys())
                gate["REST_NAMESPACES"] = ns
                el_routes = [r for r in routes if "elementor" in r.lower()]
                tb_routes = [r for r in routes if "site-editor" in r.lower()
                             or "templates" in r.lower()]
                if el_routes:
                    gate["ELEMENTOR_DATA_ACCESSIBLE"] = "PASS"
                    gate["ELEMENTOR_DATA_LOCATION"] = f"Elementor REST namespaces present ({len(el_routes)} routes)"
                if any("elementor" in n.lower() for n in ns) and \
                   any("site-editor" in r.lower() for r in routes):
                    gate["THEME_BUILDER_RELATIONSHIP_IDENTIFIED"] = "YES"
                gate["diagnostics"].append({"route_count": len(routes),
                                            "elementor_routes_sample": el_routes[:12],
                                            "theme_builder_routes_sample": tb_routes[:12]})
            except Exception as e:
                gate["diagnostics"].append({"root_parse_error": type(e).__name__})

            # 2) Auth + capabilities
            me = _get(client, base_url, base_host, f"{_WP_V2}/users/me?context=edit", headers=auth); req += 1
            authed = me.get("resp") is not None and me["http"] == 200
            if authed:
                gate["WORDPRESS_REST_AUTH"] = "PASS"
                gate["TECHNICAL_USER"] = "PASS"
                try:
                    mj = me["resp"].json()
                    caps = mj.get("capabilities") or {}
                    watch = ["edit_posts", "edit_pages", "edit_others_pages",
                             "edit_others_posts", "publish_pages", "publish_posts",
                             "manage_options", "edit_theme_options", "edit_published_pages"]
                    gate["TECHNICAL_USER_CAPS"] = {c: bool(caps.get(c)) for c in watch}
                    gate["diagnostics"].append({"roles": mj.get("roles", [])})
                except Exception:
                    pass
            else:
                gate["BLOCKER"] = f"Auth GET /users/me failed (http={me.get('http')})"

            # 3) Enumerate real post types (READ-ONLY) then scan each for the drafts.
            ctx = "context=edit&" if authed else ""
            home_kw = [["home", "2.0"], ["home", "2"], ["home 2"], ["inicio", "2"]]
            header_kw = [["header", "2.0"], ["header", "2"], ["header 2"],
                         ["cabecera", "2"], ["encabezado", "2"]]
            scan_report = {}
            all_home_hits, all_header_hits = [], []

            # 3a) Discover registered post types + their REST base.
            types_r = _get(client, base_url, base_host, f"{_WP_V2}/types?context=edit",
                          headers=auth); req += 1
            rest_bases = []
            if types_r.get("resp") is not None and types_r["http"] == 200:
                try:
                    tj = types_r["resp"].json()
                    type_map = {}
                    for slug, meta in (tj or {}).items():
                        rb = meta.get("rest_base") or slug
                        type_map[slug] = rb
                        rest_bases.append(rb)
                    gate["diagnostics"].append({"registered_types": type_map})
                except Exception as e:
                    gate["diagnostics"].append({"types_parse_error": type(e).__name__})
            if not rest_bases:
                rest_bases = list(_FALLBACK_TYPES)
                gate["diagnostics"].append({"types_enumeration": f"fallback http={types_r.get('http')}"})

            # Dedupe, keep it bounded.
            seen = set()
            rest_bases = [x for x in rest_bases if not (x in seen or seen.add(x))]

            for rb in rest_bases:
                r = _list_type(client, base_url, base_host, rb, ctx, auth); req += 1
                http = r.get("http")
                items = _as_list(r["resp"]) if r.get("resp") is not None and http == 200 else []
                titles = [{"id": i.get("id"), "t": _title_of(i), "s": i.get("status")} for i in items]
                scan_report[rb] = {"http": http, "count": len(items),
                                   "titles": [f'{x["id"]}:{x["t"]}({x["s"]})' for x in titles][:60]}
                for x in _match(items, home_kw):
                    x["source_type"] = rb
                    all_home_hits.append(x)
                for x in _match(items, header_kw):
                    x["source_type"] = rb
                    all_header_hits.append(x)
            gate["diagnostics"].append({"scan": scan_report})

            # 3b) Theme Builder documents (Elementor) — GET read-only, may 403 on minimal role.
            tb = _get(client, base_url, base_host,
                     "/wp-json/elementor/v1/site-editor/templates", headers=auth); req += 1
            if tb.get("resp") is not None and tb["http"] == 200:
                try:
                    tbj = tb["resp"].json()
                    tb_items = tbj if isinstance(tbj, list) else tbj.get("data") or tbj.get("templates") or []
                    if isinstance(tb_items, dict):
                        tb_items = list(tb_items.values())
                    norm = []
                    for it in (tb_items or []):
                        if isinstance(it, dict):
                            norm.append({"id": it.get("id") or it.get("template_id"),
                                         "title": it.get("title") or it.get("name") or "",
                                         "type": it.get("type") or it.get("doc_type"),
                                         "status": it.get("status")})
                    gate["THEME_BUILDER_GET"] = "PASS"
                    gate["diagnostics"].append({"theme_builder_templates":
                                                [f'{x["id"]}:{x["title"]}({x.get("type")})' for x in norm][:60]})
                    all_header_hits += _match(norm, header_kw)
                    all_home_hits += _match(norm, home_kw)
                except Exception as e:
                    gate["diagnostics"].append({"tb_parse_error": type(e).__name__})
            else:
                gate["THEME_BUILDER_GET"] = "FAIL"
                gate["diagnostics"].append({"theme_builder_templates_http": tb.get("http"),
                                            "theme_builder_note": "403 => role lacks edit_theme_options/manage_options"})

            # Resolve HOME
            if all_home_hits:
                h = all_home_hits[0]
                gate["HOME_2_0_DETECTED"] = "PASS"
                gate["HOME_2_0_ID"] = h["id"]
                gate["HOME_2_0_POST_TYPE"] = h.get("type") or h.get("source_type") or "page"
                gate["HOME_2_0_STATUS"] = h.get("status") or "UNKNOWN"
                gate["diagnostics"].append({"home_candidates": all_home_hits[:6]})
            # Resolve HEADER
            if all_header_hits:
                h = all_header_hits[0]
                gate["HEADER_2_0_DETECTED"] = "PASS"
                gate["HEADER_2_0_ID"] = h["id"]
                gate["HEADER_2_0_POST_TYPE"] = h.get("type") or h.get("source_type") or "UNKNOWN"
                gate["HEADER_2_0_STATUS"] = h.get("status") or "UNKNOWN"
                gate["diagnostics"].append({"header_candidates": all_header_hits[:6]})

            # 4) Elementor meta completeness on HOME 2.0 (READ-ONLY)
            if gate["HOME_2_0_DETECTED"] == "PASS" and authed and \
               gate["HOME_2_0_POST_TYPE"] in ("page", "pages", "post", "posts"):
                hid = gate["HOME_2_0_ID"]
                pt = "pages" if gate["HOME_2_0_POST_TYPE"] in ("page", "pages") else "posts"
                meta = _get(client, base_url, base_host,
                           f"{_WP_V2}/{pt}/{hid}?context=edit", headers=auth); req += 1
                if meta.get("resp") is not None and meta["http"] == 200:
                    try:
                        mj = meta["resp"].json()
                        meta_obj = mj.get("meta") or {}
                        has_el = ("_elementor_data" in meta_obj) or ("_elementor_edit_mode" in meta_obj)
                        gate["diagnostics"].append({"home_meta_keys": list(meta_obj.keys())[:40],
                                                    "elementor_data_in_rest_meta": has_el})
                        if has_el:
                            gate["ELEMENTOR_DATA_ACCESSIBLE"] = "PASS"
                            gate["ELEMENTOR_DATA_LOCATION"] = "post meta _elementor_data exposed via REST 'meta'"
                            gate["ELEMENTOR_META_COMPLETE"] = "YES"
                            gate["SAFE_WRITE_PATH_IDENTIFIED"] = "YES"
                            gate["CUSTOM_ENDPOINT_PLUGIN_REQUIRED"] = "NO"
                        else:
                            gate["ELEMENTOR_META_COMPLETE"] = "NO"
                            gate["ELEMENTOR_DATA_LOCATION"] = "_elementor_data NOT in REST 'meta' (not registered show_in_rest)"
                            gate["SAFE_WRITE_PATH_IDENTIFIED"] = "NO"
                            gate["CUSTOM_ENDPOINT_PLUGIN_REQUIRED"] = "YES"
                    except Exception as e:
                        gate["diagnostics"].append({"home_meta_parse_error": type(e).__name__})

            if gate["HOME_2_0_DETECTED"] == "FAIL" or gate["HEADER_2_0_DETECTED"] == "FAIL":
                missing = []
                if gate["HOME_2_0_DETECTED"] == "FAIL":
                    missing.append("HOME 2.0")
                if gate["HEADER_2_0_DETECTED"] == "FAIL":
                    missing.append("HEADER 2.0")
                gate["BLOCKER"] = f"Not located: {', '.join(missing)} (see diagnostics.scan for visible titles / permissions)"

        except RedirectBlocked as e:
            gate["BLOCKER"] = f"OFF-HOST REDIRECT BLOCKED: {e} — STOP"
            gate["WORDPRESS_REQUESTS_EXECUTED"] = req
            return gate
        except Exception as e:
            gate["BLOCKER"] = f"Unexpected error: {type(e).__name__}"
            gate["WORDPRESS_REQUESTS_EXECUTED"] = req
            return gate

    gate["WORDPRESS_REQUESTS_EXECUTED"] = req
    return gate



def run_capability_discovery() -> dict:
    """READ-ONLY discovery of the capability mapping protecting elementor_library.

    GET only: /wp/v2/types and /wp/v2/types/elementor_library?context=edit.
    Also does a harmless authenticated GET probe against the collection to record
    the exact 403 error code returned by WordPress. No writes, no role changes.
    """
    site, user, app_pw = _get_env()
    base_url, base_host = _normalize_base(site)

    out = {
        "ELEMENTOR_LIBRARY_REGISTERED": "NO",
        "ELEMENTOR_LIBRARY_REST_BASE": "UNKNOWN",
        "CAPABILITY_TYPE": "UNKNOWN",
        "CAPABILITIES_MAPPING": {},
        "COLLECTION_403_CODE": "UNKNOWN",
        "WORDPRESS_REQUESTS_EXECUTED": 0,
        "WRITE_REQUESTS_EXECUTED": 0,
        "PRODUCTION_MUTATIONS": 0,
        "BLOCKER": "NONE",
        "diagnostics": [],
    }
    if not base_url:
        out["BLOCKER"] = "WP_SITE_URL missing/invalid"
        return out
    if not user or not app_pw:
        out["BLOCKER"] = "secrets not set"
        return out

    auth = _auth_header(user, app_pw)
    req = 0
    with httpx.Client(headers={"User-Agent": "OPORTUNIIA-ControlApp-Precheck/1.3 (read-only)"}) as client:
        try:
            # 1) Full types list (edit context exposes 'capabilities' + 'capability_type').
            t = _get(client, base_url, base_host, f"{_WP_V2}/types?context=edit", headers=auth); req += 1
            if t.get("resp") is not None and t["http"] == 200:
                try:
                    tj = t["resp"].json()
                    el = tj.get("elementor_library")
                    if el:
                        out["ELEMENTOR_LIBRARY_REGISTERED"] = "YES"
                        out["ELEMENTOR_LIBRARY_REST_BASE"] = el.get("rest_base", "elementor_library")
                        # 'capabilities' present only in edit context.
                        caps = el.get("capabilities") or {}
                        out["CAPABILITIES_MAPPING"] = caps
                        out["CAPABILITY_TYPE"] = el.get("capability_type", "UNKNOWN")
                        out["diagnostics"].append({"elementor_library_type_keys": list(el.keys())})
                except Exception as e:
                    out["diagnostics"].append({"types_parse_error": type(e).__name__})

            # 2) Dedicated single-type endpoint (edit context).
            ts = _get(client, base_url, base_host,
                     f"{_WP_V2}/types/elementor_library?context=edit", headers=auth); req += 1
            if ts.get("resp") is not None and ts["http"] == 200:
                try:
                    tsj = ts["resp"].json()
                    caps = tsj.get("capabilities") or {}
                    if caps and not out["CAPABILITIES_MAPPING"]:
                        out["CAPABILITIES_MAPPING"] = caps
                    if tsj.get("capability_type"):
                        out["CAPABILITY_TYPE"] = tsj.get("capability_type")
                    out["ELEMENTOR_LIBRARY_REGISTERED"] = "YES"
                    if tsj.get("rest_base"):
                        out["ELEMENTOR_LIBRARY_REST_BASE"] = tsj.get("rest_base")
                except Exception as e:
                    out["diagnostics"].append({"type_single_parse_error": type(e).__name__})
            else:
                out["diagnostics"].append({"types_elementor_library_http": ts.get("http")})

            # 3) Probe the collection to capture the exact 403 error code (read-only).
            probe = _get(client, base_url, base_host,
                        f"{_WP_V2}/elementor_library?context=edit&per_page=1", headers=auth); req += 1
            if probe.get("resp") is not None:
                out["diagnostics"].append({"collection_probe_http": probe["http"]})
                try:
                    pj = probe["resp"].json()
                    if isinstance(pj, dict) and pj.get("code"):
                        out["COLLECTION_403_CODE"] = pj.get("code")
                        out["diagnostics"].append({"collection_error_message": pj.get("message", "")[:200]})
                except Exception:
                    pass
                # Also probe view context (public read) to see if drafts differ.
                probe_view = _get(client, base_url, base_host,
                                 f"{_WP_V2}/elementor_library?per_page=1", headers=auth); req += 1
                if probe_view.get("resp") is not None:
                    out["diagnostics"].append({"collection_view_http": probe_view["http"]})
        except RedirectBlocked as e:
            out["BLOCKER"] = f"OFF-HOST REDIRECT BLOCKED: {e}"
        except Exception as e:
            out["BLOCKER"] = f"Unexpected error: {type(e).__name__}"

    out["WORDPRESS_REQUESTS_EXECUTED"] = req
    return out
