"""One-time operator authorization; localhost only, gmail.send only.

Run locally with a downloaded Desktop OAuth client JSON. The output is a
SECRET JSON for the hosting environment, never a file to commit or share.
No mail is sent by this helper. Authorization codes and tokens are not logged.
"""
import argparse
import base64
import hashlib
import json
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

SCOPE = "https://www.googleapis.com/auth/gmail.send"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit("Output already exists; refusing to overwrite credentials.")
    client = json.loads(Path(args.client_file).read_text(encoding="utf-8"))["installed"]
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    response = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            valid = parsed.path == "/" and secrets.compare_digest(query.get("state", [""])[0], state)
            if not valid:
                self.send_response(400); self.end_headers(); return
            response.update({"code": query.get("code", [""])[0], "error": query.get("error", [""])[0]})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write("Autorización recibida. Puedes volver al chat de OPORTUNIIA.".encode())

    with HTTPServer(("127.0.0.1", 0), Callback) as server:
        server.timeout = 1
        redirect = f"http://127.0.0.1:{server.server_port}/"
        params = {"client_id": client["client_id"], "redirect_uri": redirect, "response_type": "code",
                  "scope": SCOPE, "state": state, "access_type": "offline", "prompt": "consent",
                  "login_hint": "info@oportuniia.com", "code_challenge_method": "S256",
                  "code_challenge": base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")}
        print("AUTHORIZE_URL=https://accounts.google.com/o/oauth2/v2/auth?"+urlencode(params), flush=True)
        deadline = time.monotonic() + 600
        while not response and time.monotonic() < deadline:
            server.handle_request()
    if response.get("error") or not response.get("code"):
        raise SystemExit("Authorization declined or timed out; credentials were not saved.")
    result = requests.post("https://oauth2.googleapis.com/token", data={
        "grant_type": "authorization_code", "code": response["code"], "redirect_uri": redirect,
        "client_id": client["client_id"], "client_secret": client["client_secret"], "code_verifier": verifier,
    }, timeout=20, allow_redirects=False)
    if result.status_code != 200:
        raise SystemExit("Google authorization exchange failed; credentials were not saved.")
    token = result.json()
    if not token.get("refresh_token") or set(token.get("scope", "").split()) != {SCOPE}:
        raise SystemExit("Google did not grant the exact send-only offline authorization.")
    values = {"WEB_MAIL_TRANSPORT": "gmail", "WEB_GOOGLE_CLIENT_ID": client["client_id"],
              "WEB_GOOGLE_CLIENT_SECRET": client["client_secret"], "WEB_GOOGLE_REFRESH_TOKEN": token["refresh_token"],
              "WEB_MAIL_FROM": "OPORTUNIIA <web@oportuniia.com>"}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as target:
        json.dump(values, target)
    print("Authorization saved to the specified SECRET local output. No mail sent.")


if __name__ == "__main__":
    main()
