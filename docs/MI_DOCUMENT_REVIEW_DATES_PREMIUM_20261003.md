# MI OPORTUNIIA · Fechas de revisión documental Premium

Avance sandbox 2026-10-03. No desplegado ni conectado a notificaciones reales.

## Implementado

- En el área privada, cada documento limpio y disponible presenta un selector de próxima fecha de revisión. El titular puede guardarla o eliminarla.
- `PUT /api/mi/private/documents/{file_id}/review-date` requiere sesión autenticada, protección de origen y suscripción Premium verificada vigente.
- Actualización Mongo con filtro de `actor_id`, `file_id`, estado AVAILABLE y resultado antivirus CLEAN: ningún usuario puede modificar documentos ajenos, en cuarentena o sin verificación.
- La fecha es proporcionada expresamente por el titular, futura y limitada a dos años; no se deduce por OCR ni se identifica como fecha legal de caducidad.
- Al borrar la fecha, se desactivan los recordatorios para ese documento.
- La lista privada muestra solo campos autorizados `next_review_at` y `review_reminders`; nunca devuelve rutas R2 ni metadatos internos.
- Los avisos Premium siguen sujetos al consentimiento general y la comprobación de suscripción previa a cada envío.

## Pendiente

- Activación de R2/ClamAV/OCR/entitlement con proveedores reales.
- Correo `info.web@oportuniia.com`: buzón real, SMTP privado en Render y pruebas de entrega.
- Worker/n8n que procese fechas y cola de notificaciones sin duplicados; pruebas con calendarios, renovación y revocación de suscripción y opt-out.
- Revisión LEGAL de textos y tratamiento documental; pruebas de extremo a extremo con datos ficticios.
