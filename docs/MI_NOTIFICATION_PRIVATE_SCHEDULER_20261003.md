# MI OPORTUNIIA · Programador privado de recordatorios (sandbox)

Estado 2026-10-03: lógica incorporada a PR #9. **No hay cron, n8n ni
proveedor de email activados**.

`backend/mi_notification_scheduler.py` aporta una ejecución privada
`schedule_notifications(db, now=..., limit=50)` con dos recorridos:

- Ofertas: únicamente aprobadas, con comunicación previamente acreditada y
  documentación aún pendiente, dentro de la ventana de las próximas 48 h.
  Planifica avisos de umbrales 48 h y 24 h; si el cron llega tarde y coinciden
  ambas ventanas, conserva solo el aviso de 24 h para no bombardear.
- Premium: detecta fechas de revisión explícitas dentro de los próximos siete
  días, consulta usuario verificado y consentimiento actual y comprueba
  suscripción activa emitida por fuente verificada.

Ambos recorridos utilizan `mi_notification_outbox.enqueue` con claves únicas:
repetir la misma ejecución no duplica un aviso. Ningún correo, documento ni
nombre de archivo se introduce en la cola. El adaptador de envío deberá pasar
por `mi_notification_validation.revalidate_claimed_notice` justo antes
de enviar para descartar fechas borradas, consentimiento revocado, documentación
recibida o suscripciones vencidas.

## Bloqueos de activación

- Crear y validar `info.web@oportuniia.com` y sus credenciales SMTP privadas.
- Aprovisionar MongoDB y ejecutar `ensure_outbox_indexes` antes de programar
  cron; verificar los índices/consistencia reales.
- Crear cron privado en Render o invocación autenticada y de privilegio mínimo
  desde n8n; no exponer la programación como una ruta pública.
- Integrar el envío con recibos de proveedor y conciliación de resultados
  inciertos, no reintentar a ciegas.
- Realizar pruebas E2E con usuario ficticio, consentimientos, fechas, dos
  instancias de cron y fallo de correo. El hito de notificación que arranca las
  72 horas requiere prueba jurídica de comunicación, nunca solo aceptación SMTP.

La web pública y las reservas/cobros permanecen sin modificación.
