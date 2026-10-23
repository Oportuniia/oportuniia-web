"""HTTPS transactional mail, using an operator-authorized gmail.send token.

Credentials stay in the hosting secret store. Never log provider responses,
which can contain credentials or recipient data. No automatic send retries:
an ambiguous timeout must not silently duplicate a message.
"""
import base64
import os
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

import requests
from web_mail_templates import html_alternative

SCOPE = "https://www.googleapis.com/auth/gmail.send"
ENV_KEYS = ("WEB_GOOGLE_CLIENT_ID", "WEB_GOOGLE_CLIENT_SECRET", "WEB_GOOGLE_REFRESH_TOKEN", "WEB_MAIL_FROM")


def ready():
    return all(os.getenv(key, "").strip() for key in ENV_KEYS)


def deliver(recipient, subject, body):
    if not ready():
        raise RuntimeError("gmail_not_configured")
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={"grant_type": "refresh_token", "client_id": os.environ[ENV_KEYS[0]],
              "client_secret": os.environ[ENV_KEYS[1]], "refresh_token": os.environ[ENV_KEYS[2]]},
        timeout=15, allow_redirects=False,
    )
    if token_response.status_code != 200:
        raise RuntimeError("gmail_authorization_failed")
    token = token_response.json()
    if not token.get("access_token") or (token.get("scope") and set(token["scope"].split()) != {SCOPE}):
        raise RuntimeError("gmail_authorization_failed")
    message = EmailMessage()
    message["From"] = os.environ["WEB_MAIL_FROM"]
    message["To"] = recipient
    message["Subject"] = subject
    message["Date"] = formatdate(usegmt=True)
    message["Message-ID"] = make_msgid(domain="oportuniia.com")
    message.set_content(body)
    message.add_alternative(html_alternative(body), subtype="html")
    sent = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": "Bearer " + token["access_token"]},
        json={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")},
        timeout=20, allow_redirects=False,
    )
    if sent.status_code != 200 or not sent.json().get("id"):
        raise RuntimeError("gmail_delivery_failed")

