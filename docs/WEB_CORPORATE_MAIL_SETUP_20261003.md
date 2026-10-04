# WEB 5.0 · identidad corporativa de correo

Directriz MASTER: cada herramienta utiliza `info.nombreherramienta@oportuniia.com`.
WEB 5.0 asume exclusivamente `info.web@oportuniia.com` como remitente de sus
comunicaciones de autenticación y futuras notificaciones.

## Código entregado

- `backend/mi_corporate_mail.py` centraliza origen corporativo, STARTTLS/SSL TLS,
  validación de destinatarios y configuración sin credenciales en repositorio.
- `backend/mi_auth.py` llama al transporte corporativo para verificación y
  recuperación de cuenta; no acepta como remitente otro buzón de herramienta.
- Activación **cerrada por defecto**: `MI_SMTP_ENABLED=0`. No hay envíos reales.
- Tests de identidad y configuración segura en la CI.

## Pasos del propietario/administrador de correo

1. Crear en Webempresa o el proveedor corporativo el buzón o alias
   `info.web@oportuniia.com`. Si es alias, confirmar que la cuenta autenticada
   tiene permiso explícito para ENVIAR COMO esa dirección y recibir las respuestas.
2. Comprobar SPF, DKIM y DMARC para el dominio `oportuniia.com` antes de
   habilitar envíos comerciales. No publicar credenciales en GitHub, chat ni
   documentos de trabajo.
3. En Render (secretos de WEB, no variables públicas frontend):
   - `MI_SMTP_HOST` = servidor SMTP dado por el proveedor;
   - `MI_SMTP_PORT` = 587 STARTTLS (o 465 SSL);
   - `MI_SMTP_USER` y `MI_SMTP_PASSWORD` = credenciales o token de envío;
   - `MI_SMTP_FROM` = `info.web@oportuniia.com`;
   - `MI_PUBLIC_ORIGIN` = origen HTTPS verdadero de la WEB;
   - `MI_SMTP_ENABLED` = `1` **solo tras prueba controlada**.
4. Enviar a una bandeja de ensayo propia y comprobar recepción y respuesta;
   validar recuperación/verificación en una cuenta ficticia y evitar notificar
   usuarios de producción durante las pruebas.

## Independencia del protocolo de tres días

La entrega al servidor SMTP NO inicia por sí sola el plazo documental de
72 horas. El evento de comunicación acreditada de la aprobación requiere el
procedimiento y medio probatorio validados por LEGAL.
Los recordatorios transaccionales y Premium aún están en cola sandbox sin
adaptador de transporte habilitado.

## Bloqueos

Falta crear/verificar el buzón, la prueba autorizada SMTP en Render, el
programador real de avisos, consentimiento operativo y pruebas E2E.
La web WordPress pública sigue sin sustituirse.
