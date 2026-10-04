# MI OPORTUNIIA · Puerta de entrega controlada y contrato n8n (sandbox)

Este avance integra una **simulación sin SMTP**, con pruebas de aceptación ficticia, cancelación por pérdida de elegibilidad y resultado incierto. NO existe un trabajador de notificaciones productivo, ni prueba de recepción real, ni endpoints públicos nuevos.

## Recorrido y separación

1. Un cron privado, posteriormente orquestado por n8n, invocará el scheduler interno contra la BD WEB. El scheduler añade claves deterministas al outbox sin nombres de archivos, importes ni direcciones de correo.
2. Un trabajador privado hace claim atómico del aviso. Antes de conectar con el proveedor, llama a `revalidate_claimed_notice`: comprueba el consentimiento actual, la versión del calendario confirmado, la suscripción Premium o los requisitos del expediente.
3. Si las condiciones dejan de cumplirse, `cancel_claimed` anula de forma atómica el aviso reivindicado: jamás se envía un aviso caducado. La comprobación y el intento de transmisión real deben mantenerse lo más próximos posible.
4. Solo tras un envío real aceptado con recibo auténtico del proveedor se permite registrar `SENT`; un timeout incierto implica `RECONCILE` (no reintento ciego). Las pruebas `mi_notification_mock_delivery.py` utilizan exclusivamente referencias `MOCK-ACCEPTED`, **sin SMTP**. JAMÁS utilizar este módulo con bases de datos de producción.
5. El worker productivo deberá verificar rechazo/aceptación de SMTP sin interpretar la aceptación como entrega en bandeja ni comunicación jurídica efectiva. Un evento de oferta que inicia las 72 horas necesita el protocolo específico de LEGAL y prueba de notificación independiente.

## Contrato n8n pendiente de materializar al activar servicios

- Disparador: cron interno autenticado, frecuencia y lotes limitados, sin ruta web pública y con secretos gestionados por Render/n8n.
- n8n no almacena documentos privados, credenciales bancarias, nóminas ni contenido fiscal. Datos transportados: ID de ejecución y métricas de cola; los destinatarios se resuelven dentro del servidor WEB.
- Entrega: WEB controla la selección, revalidación, reclamación exclusiva y acuse. n8n registra solo estado y métricas no sensibles.
- Fallos: guardias para `RECONCILE`, observabilidad de trabajos bloqueados y conciliación manual por personal autorizado. Probar concurrencia, ausencia de índices y reversión con la BD real antes de habilitar cron.

## Pendientes

- Crear/verificar `info.web@oportuniia.com`, SPF/DKIM/DMARC y configurar credenciales privadas Render.
- Implementar adaptador SMTP verdadero y autorización técnica verificable, comprobar recibos del proveedor y correlación robusta, sin usar el harness mock con datos reales.
- Integración n8n autenticada, programación, límites y prueba de duplicados/cancelaciones con Mongo real.
- Activación gradual con destinatarios ficticios antes de usuarios reales. Las reservas y el escrow notarial permanecen pendientes de proveedores.
