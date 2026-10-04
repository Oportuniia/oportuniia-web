# WEB 5.0 · Avance sin proveedores: agenda Premium a cola de notificaciones

2026-10-03: **pagos aparcados** por instrucción del propietario hasta disponer de proveedor escrow notarial y banco para reservas. No conectar ni simular cobros reales.

Trabajo alternativo en rama sandbox:

- Los recordatorios de cobro se planifican SOLO con un día de nómina confirmado expresamente por la persona, calendario habilitado y una ventana horaria de 1 h (10:00 Europe/Madrid, con 0–7 días de antelación).
- El scheduler consulta usuario verificado, consentimiento vigente de recordatorios y suscripción Premium activa verificada. Guarda en outbox exclusivamente actor, identificador de señal, versión y fechas; sin sueldo, empresa, documento o dirección de correo.
- Clave determinista por señal + versión de calendario + mes objetivo: las repeticiones del cron no generan duplicados. Cualquier cambio de preferencias incrementa la versión, por lo que invalidará los avisos antiguos al revisarse antes del transporte.
- El adaptador de envío futuro DEBE llamar a `revalidate_claimed_notice` inmediatamente antes de entregar; si se ha retirado el consentimiento o ha caducado Premium, no enviar.
- La plantilla de correo será neutra: «Tienes una tarea programada en tu agenda privada» y enlace a MI OPORTUNIIA. El contenido personal solo aparece dentro de sesión autenticada.
- No se ha conectado SMTP, n8n, ni trabajador real. No hay correos ni transferencias activos.

Pendientes para activación: indexar Mongo, aprovisionar `info.web@oportuniia.com`, Render/n8n, pruebas reales de idempotencia y cancelaciones, protección ante workers retrasados y caducidades. Fiscalidad: sin reglas generales inferidas; habrá que usar fuentes oficiales y situación confirmada de cada usuario.
