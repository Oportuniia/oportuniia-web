# MI OPORTUNIIA · Cola de avisos (sandbox)

Estado: especificación ejecutable y pruebas unitarias. **No hay transportista SMTP ni cron n8n desplegados**.

## Dos clases distintas de aviso

- Avisos operativos del protocolo de tres días: quedan sujetos a la obligación documental desde la comunicación acreditada de aprobación. Los recordatorios se planifican cuando restan 48 y 24 horas, no se emiten si se acreditó recepción documental o el plazo expiró. La regla del vencimiento de 72 horas es independiente de que el recordatorio llegue.
- Avisos optativos Premium: únicamente si el inversor mantiene suscripción verificada, marcó expresamente su consentimiento y fijó la fecha de revisión de un documento. Nunca se adivinan fechas de caducidad de DNI, nóminas, etc.

## Garantías del diseño

- `mi_document_notifications.py`: claves deterministas por evento; ningún dato personal ni contenido del archivo en el mensaje planificado.
- `mi_notification_outbox.py`: registro Mongo único por clave, reserva de envío por trabajador y estados PENDING / CLAIMED / SENT / RECONCILE / CANCELLED. Tras un timeout de resultado incierto **no se reenvía a ciegas**; se concilia con el proveedor.
- `mi_notification_validation.py`: comprobación justo antes del transporte de que la oferta sigue pendiente o el actor conserva opt-in/suscripción y el documento está disponible.
- El destinatario y texto del correo deberán resolverse en un adaptador interno **después** de esa comprobación; no guardar correo, DNI, archivos ni nombres de documentos en la cola.
- Un registro SENT confirma aceptación verificada del proveedor, no llegada a la bandeja de entrada. No iniciar el plazo de 72 horas con un simple resultado SENT: el proceso de aprobación necesita una prueba específica de comunicación conforme al procedimiento aprobado por LEGAL.

## Condiciones antes de conectar envíos

1. SMTP transaccional configurado y probado con STARTTLS y autenticación, gestión de errores, rebotes y firmas SPF/DKIM/DMARC.
2. Worker/n8n con secreto interno y permisos mínimos, mecanismo de exclusión y pruebas de varias ejecuciones simultáneas; control de periodos horarios y zonas según condiciones aprobadas.
3. Probar outbox, transporte, recibos de proveedor, recepción documental y expiración real contra Mongo sandbox, incluida pérdida de conexión a mitad de envío.
4. Preferencias documentales: fechas manuales de revisión, edición y revocación del consentimiento, política de retención y protección de datos.
5. Documentar y homologar con LEGAL la prueba válida de comunicación de aprobación y la fórmula exacta de las 72 horas; verificar texto de pérdida de oferta.

No activar el envío real ni reemplazar el circuito WordPress/LeadConnector hasta cerrar estas pruebas.
