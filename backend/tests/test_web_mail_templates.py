from web_mail_templates import registration_confirmation, html_alternative


def test_confirmation_is_escaped_and_link_is_usable():
    _, text = registration_confirmation('<img src=x onerror=alert(1)>', 'https://portal.test/cuenta#verify=fictitious-token')
    html = html_alternative(text)
    assert '<img' not in html
    assert '&lt;img' in html
    assert 'href="https://portal.test/cuenta#verify=fictitious-token"' in html
    assert '>Confirmar mi correo</a>' in html
    assert '30 minutos' in html
    assert 'no activa ninguna suscripción de pago ni genera cargos' in html


def test_blank_name_and_no_tracking():
    subject, text = registration_confirmation('', 'https://portal.test/cuenta#verify=test')
    assert text.startswith('Hola,')
    assert subject == 'Confirma tu correo y prepara tu acceso a OPORTUNIIA'
    assert '<img' not in html_alternative(text)
