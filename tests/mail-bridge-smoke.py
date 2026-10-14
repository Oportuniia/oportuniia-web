"""Loopback-only PHP bridge check. Run with mail() replaced by /bin/true.
The fixture key is synthetic; this file never addresses a real mail host.
"""
import hashlib
import hmac
import json
import secrets
import time
import requests

URL = 'http://127.0.0.1:8091/mail-bridge/bridge.php'
KEY = b'synthetic-qa-mail-key-123456789012345678901234567890'


def send(raw, nonce=None, timestamp=None, bad_signature=False):
    nonce = nonce or secrets.token_hex(16)
    timestamp = str(timestamp or int(time.time()))
    signature = hmac.new(KEY, timestamp.encode()+b'.'+nonce.encode()+b'.'+raw, hashlib.sha256).hexdigest()
    return requests.post(URL, data=raw, headers={'X-OPP-Mail-Timestamp': timestamp, 'X-OPP-Mail-Nonce': nonce, 'X-OPP-Mail-Signature': 'bad' if bad_signature else signature}, timeout=5)


raw = json.dumps({'to': 'synthetic@example.com', 'subject': 'Prueba ficticia', 'body': 'No se envía: MTA sustituido por /bin/true.'}).encode()
nonce = secrets.token_hex(16)
assert send(raw, nonce=nonce).json() == {'accepted': True}
assert send(raw, nonce=nonce).status_code == 409
assert send(raw, bad_signature=True).status_code == 401
assert send(raw, timestamp=int(time.time())-600).status_code == 401
assert send(b'{invalid-json').status_code == 422
assert send(b'x'*65537).status_code == 413
assert send(json.dumps({'to': 'a@example.com\r\nBcc: b@example.com', 'subject': 'Test', 'body': 'Test'}).encode()).status_code == 422
assert send(json.dumps({'to': 'a@example.com', 'subject': 'Test\r\nX-Header: injected', 'body': 'Test'}).encode()).status_code == 422
print('PASS PHP bridge: accepted local stub, replay, signature, expiry, JSON, size, recipient and header injection; no email sent')
