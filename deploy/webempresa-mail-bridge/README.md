# Puente HTTPS de correo para Webempresa

Preparado para revisión; no se ha instalado en la web antigua ni se han cambiado DNS.

El backend gratuito de Render bloquea SMTP 25/465/587. Este puente permite reutilizar el MTA del hosting por HTTPS. No sustituye un buzón ni expone su contraseña.

1. Crear `info.web@oportuniia.com` en Webempresa y verificar envío, SPF y DKIM desde el hosting.
2. Usar un subdominio específico de correo/servicios alojado en Webempresa, con HTTPS. La web principal podrá apuntar a Vercel conservando MX y demás registros de correo.
3. Colocar `bridge.php` bajo `public_html/mail-bridge/`. Instalar la configuración real fuera de `public_html`, en `/home/<usuario>/private/oportuniia-mail.php`; permisos 0600. Crear el directorio privado de nonces con permisos 0700.
4. La clave compartida ya está generada y guardada en el entorno privado de staging de Render como `WEB_MAIL_BRIDGE_KEY`. Copiarla de servidor a configuración privada, nunca al repositorio ni al chat. El ejemplo está desactivado por defecto.
5. Probar una solicitud firmada, su rechazo sin firma y el rechazo de la misma firma/nonce repetidos. Comprobar recepción real y autenticación del remitente. `mail()` solo acredita aceptación por el MTA, no entrega.
6. Configurar `WEB_MAIL_BRIDGE_URL` con la URL HTTPS exacta, sin redirecciones. Activar solo después de la prueba autorizada. Dejar SMTP directo desactivado en Render Free.

No se han contratado recursos de correo, enviado emails ni modificado el hosting existente. El despliegue requiere acceso a Webempresa. PHP 8.1+; lint y pruebas HTTP locales de firma/replay/límites superados con MTA simulado. Pendiente la prueba de entrega en el hosting.
