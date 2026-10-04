"""Dedicated corporate mailbox identity for WEB 5.0 and MI OPORTUNIIA.

Configured sender is info.web@oportuniia.com. No SMTP traffic occurs without
explicit MI_SMTP_ENABLED=1, verified provider mailbox/alias and credentials.
Other OPORTUNIIA tools own their own mailboxes; never borrow an unverified
mailbox or fall back to a personal account.
"""
from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import parseaddr

CORPORATE_WEB_SENDER = "info.web@oportuniia.com"
PUBLIC_WEB_HOST = "oportuniia.com"


def mailbox_config():
    sender = os.getenv("MI_SMTP_FROM", CORPORATE_WEB_SENDER).strip().lower()
    display, parsed = parseaddr(sender)
    if display or parsed != CORPORATE_WEB_SENDER or sender != CORPORATE_WEB_SENDER:
        raise RuntimeError("WEB corporate sender must be info.web@oportuniia.com")
    if os.getenv("MI_SMTP_ENABLED", "0") != "1":
        raise RuntimeError("WEB corporate mailbox awaiting explicit activation")
    host = os.getenv("MI_SMTP_HOST", "").strip()
    user = os.getenv("MI_SMTP_USER", "").strip()
    password = os.getenv("MI_SMTP_PASSWORD", "")
    raw_port = os.getenv("MI_SMTP_PORT", "587")
    if not (host and user and password and raw_port.isdecimal()):
        raise RuntimeError("Corporate SMTP provider not configured")
    port = int(raw_port)
    if port not in (465, 587):
        raise RuntimeError("Approved TLS-only SMTP port required")
    return {"sender": sender, "host": host, "user": user,
            "password": password, "port": port}


def send_corporate_message(*, to: str, subject: str, body: str):
    """Synchronously submit one transactional email using authenticated TLS.

    SMTP acceptance is not evidence of inbox receipt or legally effective
    communication. The sender's SMTP alias permissions must be verified
    externally with a non-production recipient before enabling.
    """
    if not isinstance(to, str) or "\n" in to or "\r" in to:
        raise ValueError("invalid recipient")
    _, parsed = parseaddr(to.strip())
    if parsed != to.strip() or not parsed or "@" not in parsed:
        raise ValueError("invalid recipient")
    if any(char in subject for char in "\r\n"):
        raise ValueError("invalid subject")
    cfg = mailbox_config()
    msg = EmailMessage()
    msg["From"] = cfg["sender"]
    msg["To"] = parsed
    msg["Subject"] = subject
    msg.set_content(body)
    context = ssl.create_default_context()
    if cfg["port"] == 465:
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"],
                              timeout=15, context=context) as smtp:
            smtp.login(cfg["user"], cfg["password"])
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(cfg["user"], cfg["password"])
            smtp.send_message(msg)
