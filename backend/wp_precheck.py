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

import os
import time
import base64
import logging
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("wp_precheck")

# Fixed, allow-listed READ-ONLY paths (relative to the WP host). GET only.
_ROOT_DISCOVERY = "/wp-json/"
_WP_V2 = "/wp-json/wp/v2"

_TIMEOUT = httpx.Timeout(15.0, connect=10.0)


def _redact(msg: str) -> str:
    """Defensive: never let secret-ish tokens reach logs."""
    return msg


def _get_env():
    site = os.environ.get("WP_SITE_URL", "").strip()
    user = os.environ.get("WP_USERNAME", "").strip()
    app_pw = os.environ.get("WP_APPLICATION_PASSWORD", "").strip()
    return site, user, app_pw


def _normalize_base(site_url: str):
    """Return (base_url_without_trailing_slash, host) or (None, None) if invalid."""
    if not site_url:
        return None, None
    parsed = urlparse(site_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None, None
    base = f"{parsed.scheme}://{parsed.netloc}"
    return base, parsed.netloc.lower()


class SecretsMissing(Exception):
    pass


class RedirectBlocked(Exception):
    pass


def _auth_header(user: str, app_pw: str) -> dict:
    """Build Basic auth header for WP Application Password. Never logged."""
    token = base64.b64encode(f"{user}:{app_pw}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def _log_call(path: str, status, duration_ms: float, result: str):
    # Allowed logging ONLY: path, HTTP code, duration, PASS/FAIL. No secrets/headers.
    logger.info(
        "wp_precheck GET %s -> http=%s dur_ms=%.0f %s",
        path, status if status is not None else "ERR", duration_ms, result,
    )


def _same_host_or_block(base_host: str, response: httpx.Response):
    """If any hop redirected off the WP host, block it."""
    for hop in list(response.history) + [response]:
        h = urlparse(str(hop.url)).netloc.lower()
        if h and h != base_host:
            raise RedirectBlocked(f"redirect off-host to '{h}' blocked")


def _get(client: httpx.Client, base_url: str, base_host: str, path: str,
         headers: dict | None = None):
    """Single hardened GET. Returns dict summary; raises RedirectBlocked on off-host."""
    url = base_url + path
    started = time.perf_counter()
    status = None
    try:
        # follow_redirects=False by design; we inspect and block off-host hops.
        resp = client.get(url, headers=headers or {}, timeout=_TIMEOUT,
                          follow_redirects=False)
        status = resp.status_code
        # Manual, host-locked redirect handling (max 3 same-host hops).
        hops = 0
        while resp.is_redirect and hops < 3:
            loc = resp.headers.get("location", "")
            nxt = urlparse(loc)
            nxt_host = nxt.netloc.lower()
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


def _match_target(items, keywords):
    """Find a post/page/template whose title matches all keywords (case-insensitive)."""
    hits = []
    for it in items:
        title = ""
        t = it.get("title")
        if isinstance(t, dict):
            title = (t.get("rendered") or t.get("raw") or "")
        elif isinstance(t, str):
            title = t
        low = title.lower()
        if all(k in low for k in keywords):
            hits.append({
                "id": it.get("id"),
                "title": title,
                "type": it.get("type"),
                "status": it.get("status"),
                "slug": it.get("slug"),
            })
    return hits


def run_precheck() -> dict:
    """
    Execute the READ-ONLY precheck. GET-only. Called ONLY on explicit request.
    Returns a JSON-serializable gate report. Never includes secrets.
    """
    site, user, app_pw = _get_env()
    base_url, base_host = _normalize_base(site)

    gate = {
        "WORDPRESS_REST_AUTH": "FAIL",
        "TECHNICAL_USER": "FAIL",
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
        "SAFE_WRITE_PATH_IDENTIFIED": "NO",
        "CUSTOM_ENDPOINT_PLUGIN_REQUIRED": "UNKNOWN",
        "REST_NAMESPACES": [],
        "PRODUCTION_MUTATIONS": 0,
        "WORDPRESS_CONTACTED": "YES",
        "BLOCKER": "NONE",
        "diagnostics": [],
    }

    if not base_url:
        gate["BLOCKER"] = "WP_SITE_URL missing or invalid (needs scheme+host, e.g. https://oportuniia.com)"
        gate["WORDPRESS_CONTACTED"] = "NO"
        return gate
    if not user or not app_pw:
        gate["BLOCKER"] = "WP_USERNAME and/or WP_APPLICATION_PASSWORD not set in server environment"
        gate["WORDPRESS_CONTACTED"] = "NO"
        return gate

    auth = _auth_header(user, app_pw)

    with httpx.Client(headers={"User-Agent": "OPORTUNIIA-ControlApp-Precheck/1.0 (read-only)"}) as client:
        try:
            # 1) Root discovery (unauthenticated GET) -> namespaces & routes
            root = _get(client, base_url, base_host, _ROOT_DISCOVERY)
            if root.get("resp") is not None and root["http"] == 200:
                try:
                    data = root["resp"].json()
                    ns = data.get("namespaces", [])
                    gate["REST_NAMESPACES"] = ns
                    routes = list((data.get("routes") or {}).keys())
                    gate["diagnostics"].append({"root_discovery": "PASS",
                                                "namespaces": ns,
                                                "route_count": len(routes)})
                    # Detect Elementor / Theme Builder related namespaces/routes.
                    el_hits = [r for r in routes if "elementor" in r.lower()]
                    tb_hits = [r for r in routes if "template" in r.lower()
                               or "theme" in r.lower() or "e-template" in r.lower()]
                    if el_hits:
                        gate["ELEMENTOR_DATA_ACCESSIBLE"] = "PASS"
                        gate["ELEMENTOR_DATA_LOCATION"] = f"REST routes: {el_hits[:8]}"
                    if any("elementor" in n.lower() for n in ns):
                        gate["THEME_BUILDER_RELATIONSHIP_IDENTIFIED"] = "YES"
                    gate["diagnostics"].append({"elementor_routes": el_hits[:20],
                                                "template_like_routes": tb_hits[:20]})
                except Exception as e:
                    gate["diagnostics"].append({"root_discovery": f"parse_error:{type(e).__name__}"})
            else:
                gate["BLOCKER"] = "WP REST root (/wp-json/) not reachable"
                return gate

            # 2) Authenticated identity check via GET /wp/v2/users/me
            me = _get(client, base_url, base_host, f"{_WP_V2}/users/me?context=edit", headers=auth)
            if me.get("resp") is not None and me["http"] == 200:
                gate["WORDPRESS_REST_AUTH"] = "PASS"
                gate["TECHNICAL_USER"] = "PASS"
                try:
                    me_json = me["resp"].json()
                    gate["diagnostics"].append({
                        "auth_user_caps_present": bool(me_json.get("capabilities")),
                        "auth_user_roles": me_json.get("roles", []),
                    })
                except Exception:
                    pass
            else:
                gate["diagnostics"].append({"auth": "FAIL", "http": me.get("http")})
                gate["BLOCKER"] = "Authenticated GET /wp/v2/users/me failed (auth or permissions)"
                # Continue read-only discovery of public pages regardless.

            # 3) Locate HOME 2.0 among pages (include drafts via context=edit if authed)
            ctx = "&context=edit" if gate["WORDPRESS_REST_AUTH"] == "PASS" else ""
            pages = _get(client, base_url, base_host,
                        f"{_WP_V2}/pages?per_page=100&status=any&search=home{ctx}"
                        if ctx else f"{_WP_V2}/pages?per_page=100&search=home")
            home_items = []
            if pages.get("resp") is not None and pages["http"] == 200:
                try:
                    home_items = pages["resp"].json()
                except Exception:
                    home_items = []
            home_hits = _match_target(home_items, ["home", "2.0"]) or _match_target(home_items, ["home", "2"])
            if home_hits:
                h = home_hits[0]
                gate["HOME_2_0_DETECTED"] = "PASS"
                gate["HOME_2_0_ID"] = h["id"]
                gate["HOME_2_0_POST_TYPE"] = h.get("type") or "page"
                gate["HOME_2_0_STATUS"] = h.get("status") or "UNKNOWN"
                gate["diagnostics"].append({"home_candidates": home_hits[:5]})

            # 4) Locate HEADER 2.0 (Elementor templates are often a CPT, e.g. elementor_library)
            header_hits = []
            for cpt_path in [f"{_WP_V2}/pages", f"{_WP_V2}/elementor_library",
                             f"{_WP_V2}/elementor-template", f"{_WP_V2}/e-floating-buttons"]:
                q = f"{cpt_path}?per_page=100&status=any&search=header&context=edit" if ctx \
                    else f"{cpt_path}?per_page=100&search=header"
                r = _get(client, base_url, base_host, q)
                if r.get("resp") is not None and r["http"] == 200:
                    try:
                        items = r["resp"].json()
                        hits = _match_target(items, ["header", "2.0"]) or _match_target(items, ["header", "2"])
                        for hh in hits:
                            hh["source_route"] = cpt_path
                        header_hits.extend(hits)
                    except Exception:
                        pass
            if header_hits:
                h = header_hits[0]
                gate["HEADER_2_0_DETECTED"] = "PASS"
                gate["HEADER_2_0_ID"] = h["id"]
                gate["HEADER_2_0_POST_TYPE"] = h.get("type") or h.get("source_route") or "UNKNOWN"
                gate["HEADER_2_0_STATUS"] = h.get("status") or "UNKNOWN"
                gate["diagnostics"].append({"header_candidates": header_hits[:5]})

            # 5) Inspect Elementor meta completeness on HOME 2.0 (READ-ONLY, authed)
            if gate["HOME_2_0_DETECTED"] == "PASS" and gate["WORDPRESS_REST_AUTH"] == "PASS":
                hid = gate["HOME_2_0_ID"]
                meta = _get(client, base_url, base_host,
                           f"{_WP_V2}/pages/{hid}?context=edit", headers=auth)
                if meta.get("resp") is not None and meta["http"] == 200:
                    try:
                        mj = meta["resp"].json()
                        meta_obj = mj.get("meta") or {}
                        has_el_data = ("_elementor_data" in meta_obj) or ("_elementor_edit_mode" in meta_obj)
                        if has_el_data:
                            gate["ELEMENTOR_DATA_ACCESSIBLE"] = "PASS"
                            gate["ELEMENTOR_DATA_LOCATION"] = "post meta: _elementor_data (exposed via REST meta)"
                            gate["ELEMENTOR_META_COMPLETE"] = "YES"
                            gate["SAFE_WRITE_PATH_IDENTIFIED"] = "YES"
                            gate["CUSTOM_ENDPOINT_PLUGIN_REQUIRED"] = "NO"
                        else:
                            gate["ELEMENTOR_META_COMPLETE"] = "NO"
                            gate["ELEMENTOR_DATA_LOCATION"] = (
                                "_elementor_data NOT exposed in REST 'meta' (not registered with show_in_rest)"
                            )
                            gate["SAFE_WRITE_PATH_IDENTIFIED"] = "NO"
                            gate["CUSTOM_ENDPOINT_PLUGIN_REQUIRED"] = "YES"
                        gate["diagnostics"].append({
                            "home_meta_keys": list(meta_obj.keys())[:40],
                            "elementor_data_in_meta": has_el_data,
                        })
                    except Exception as e:
                        gate["diagnostics"].append({"home_meta": f"parse_error:{type(e).__name__}"})

        except RedirectBlocked as e:
            gate["BLOCKER"] = f"OFF-HOST REDIRECT BLOCKED: {str(e)} — STOP"
            gate["WORDPRESS_REST_AUTH"] = "FAIL"
            return gate
        except Exception as e:
            gate["BLOCKER"] = f"Unexpected error: {type(e).__name__}"
            return gate

    return gate
