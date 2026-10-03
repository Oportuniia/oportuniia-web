"""Privacy-safe Spanish transactional message templates for WEB notifications.

Never include identities, document filenames, balances, cloud storage links or
a document's content in emails. A verified delivery adapter must read actor
email from the WEB registry after revalidating the queued notification.
"""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo

WEB_AREA_URL = "https://oportuniia.com/mi-oportuniia"
MADRID = ZoneInfo("Europe/Madrid")


def render_notice(notice: dict, *, web_area_url: str = WEB_AREA_URL):
    if web_area_url != WEB_AREA_URL:
        raise ValueError("Only approved WEB private-area URL permitted")
    kind = notice.get("kind")
    if kind == "OFFER_DOCUMENT_DEADLINE":
        if notice.get("threshold_hours") not in (24, 48):
            raise ValueError("invalid offer notice")
        deadline = notice.get("deadline")
        if not isinstance(deadline, datetime) or deadline.tzinfo is None:
            raise ValueError("deadline must be timezone aware")
        local = deadline.astimezone(MADRID).strftime("%d/%m/%Y a las %H:%M")
        subject = "OPORTUNIIA · Plazo documental de tu oferta"
        body = (
            "Te recordamos que tienes una oferta aprobada pendiente de documentación.\n\n"
            f"Según los datos del expediente, faltan aproximadamente {notice['threshold_hours']} "
            "horas para el vencimiento.\n"
            f"Fecha y hora previstas: {local} (hora peninsular).\n\n"
            "Accede a tu área privada para comprobar y completar los requisitos:\n"
            + web_area_url
            + "\n\nSi la documentación requerida no se recibe completa dentro del plazo "
              "de tres días desde la comunicación de la aprobación, se perderá la oferta "
              "conforme a las condiciones aplicables. Si ya has entregado la "
              "documentación, consulta el estado de validación en tu área privada.\n\n"
              "OPORTUNIIA · WEB"
        )
        return subject, body
    if kind == "PREMIUM_DOCUMENT_REVIEW":
        subject = "OPORTUNIIA Premium · Revisión documental"
        body = (
            "Tienes una revisión documental programada en MI OPORTUNIIA.\n"
            "Accede de forma segura para revisar tus documentos y preferencias:\n"
            + web_area_url
            + "\n\nPuedes desactivar los recordatorios documentales en tu área privada.\n"
              "Por tu seguridad, este mensaje no identifica ni adjunta documentos.\n\n"
              "OPORTUNIIA · WEB"
        )
        return subject, body
    if kind == "PREMIUM_PAYROLL_REMINDER":
        # Do not disclose day, employer, salary, tax status or document names.
        return ("OPORTUNIIA Premium · Tu agenda personal",
                "Tienes una tarea programada en tu agenda privada de MI OPORTUNIIA.\n"
                "Consulta los detalles y modifica o cancela tus preferencias en:\n"
                + web_area_url + "\n\nOPORTUNIIA · WEB")
    raise ValueError("unsupported notice")
