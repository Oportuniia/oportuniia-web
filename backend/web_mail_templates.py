"""Transactional copy approved by the owner on 2026-10-22."""
from html import escape
import re


def html_alternative(body: str) -> str:
    """Escaped copy, no tracking assets; confirmation links get a clear button."""
    content = escape(body)
    content = re.sub(
        r"Confirmar mi correo: (https://[^\s<]+)",
        r'<a href="\1" style="display:inline-block;background:#087f8c;color:#fff;padding:14px 22px;border-radius:8px;text-decoration:none;font-weight:bold">Confirmar mi correo</a>',
        content,
    )
    return '<!doctype html><html lang="es"><body style="font-family:Arial,sans-serif;line-height:1.6;color:#163342"><div style="max-width:600px;margin:auto;padding:24px">'+content.replace("\n", "<br>")+"</div></body></html>"


def registration_confirmation(name: str, link: str) -> tuple[str, str]:
    name = " ".join(name.split())
    greeting = f"Hola {name}," if name else "Hola,"
    return (
        "Confirma tu correo y prepara tu acceso a OPORTUNIIA",
        f"{greeting}\n\n"
        "Gracias por registrarte en OPORTUNIIA.\n\n"
        "Confirma tu correo electrónico para preparar tu acceso:\n\n"
        f"Confirmar mi correo: {link}\n\n"
        "Este enlace es de un solo uso y caduca en 30 minutos.\n\n"
        "Estamos preparando el lanzamiento de la plataforma. Crear tu cuenta es gratuito "
        "y no activa ninguna suscripción de pago ni genera cargos.\n\n"
        "Si no has solicitado este registro, puedes ignorar este mensaje.\n\n"
        "Equipo OPORTUNIIA\nHumanizamos la deuda."
    )
