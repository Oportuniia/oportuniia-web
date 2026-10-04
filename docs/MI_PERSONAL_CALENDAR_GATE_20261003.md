# MI OPORTUNIIA · Calendario de cobros confirmados (sandbox)

El usuario Premium, después del análisis autorizado de su nómina, puede confirmar expresamente un día histórico de cobro. Esa confirmación NO activa notificaciones.

Novedad: módulo `backend/mi_personal_calendar.py`, rutas privadas autenticadas `PUT /api/mi/private/premium/calendar/{signal_id}` y `GET /api/mi/private/premium/calendar`, y controles en MI OPORTUNIIA para activar/desactivar un recordatorio, elegir la antelación de 0–7 días y ver la próxima fecha.

Solo se admite un día confirmado del 1 al 28, con eventos a las 10:00, zona Europe/Madrid. Aún no se contemplan nóminas variables, fin de mes ni festivos y desplazamientos bancarios. El calendario está separado de la propuesta original y requiere acción explícita del titular; al desactivarlo deja de figurar en próximas fechas. Verificación de cuenta y suscripción Premium vigente se exige en cada ruta.

**Limitación deliberada:** por ahora se calcula y visualiza el calendario privado, sin programar ni enviar mensajes de cobro en la cola. La futura integración debe respetar el consentimiento de correo, comprobar la vigencia del dato confirmado justo antes de entrega, deduplicar por mes, permitir editar/revocar los datos y detener avisos si Premium caduca.

No se infiere situación fiscal ni se generan plazos oficiales a partir de declaraciones antiguas. Las obligaciones fiscales requerirán normas oficiales versionadas para la jurisdicción y el ejercicio, y confirmación específica del inversor.

Otros pendientes: cuenta real `info.web@oportuniia.com` y secretos de Render, orquestación n8n, R2/ClamAV/OCR de producción, servicios de suscripción y logotipo oficial del PDF.
