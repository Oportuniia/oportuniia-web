# WEB 5.0 · OCR, correo, antivirus y suscripciones · activación real

Estado: implementado y sometido a CI en sandbox; no se han aprovisionado ni comprobado integraciones reales. No activar funciones incompletas en producción.

## OCR local (Premium)
- `backend/mi_ocr.py`: Tesseract offline con idiomas spa+eng; reserva máxima de 20 páginas OCR por trabajo, imagen máxima de 16 megapíxeles; clasificación siempre sujeta a confirmación.
- PDF mixto: PyMuPDF extrae texto y ejecuta OCR local solo en páginas sin texto suficiente.
- Fotos JPEG/PNG/WebP: transformación bajo sesión WEB verificada a PDF OCR de una página, con revisión manual de categoría, escaneo antivirus de salida y conservación de la fotografía original.
- `MI_OCR_ENABLED=0` hasta instalar y comprobar Tesseract + tesdata spa/eng **en el servicio que ejecuta WEB/worker**. Requiere capacidad CPU; para carga real, separar ejecución asíncrona en worker y medir cuotas y concurrencia. No lanzar OCR masivo dentro del proceso web sin pruebas de carga.

## Correo profesional
- Código SMTP del registro, reenvío y recuperación de contraseña listo en `mi_auth.py`.
- Hay que confirmar remitente corporativo, proveedor de correo, SMTP host, puerto STARTTLS (normalmente 587), usuario y contraseña de aplicación **exclusivamente en secretos Render**. No enviarlos por chat ni GitHub.
- Configurar SPF, DKIM y DMARC del dominio oficial, HTTPS `MI_PUBLIC_ORIGIN` y una `MI_TERMS_VERSION` aprobada jurídicamente.
- Probar entregas reales en buzones de prueba antes de `MI_AUTH_ENABLED=1`. Necesaria sustitución de `MI_ADMIN_BOOTSTRAP_TOKEN` por acceso administrador con MFA, tests integrados Mongo+SMTP y validación de IP confiable del proxy.

## Antivirus ClamAV
- Clientes ClamAV implementados para originales y derivados. Datos personales y originales siempre en bucket R2 separado.
- Provisionar servicio ClamAV privado, al alcance de WEB o worker, sin exponer puerto público 3310.
- Configurar `MI_CLAMD_HOST`, `MI_CLAMD_PORT`; comprobar actualizaciones de firmas, límites de CPU/memoria, respuesta ante caída y tiempos de análisis.
- Crear bucket Cloudflare R2 **nuevo privado**, distinto de LEGAL, CORE y PRESENTACIÓN. Configurar secretos `MI_R2_ENDPOINT`, `MI_R2_ACCESS_KEY_ID`, `MI_R2_SECRET_ACCESS_KEY`, `MI_R2_BUCKET` solo en entorno.
- Validar CORS exacto, políticas de retención, descarga temporal, sandbox de malware y pruebas de aislamiento entre usuarios. Entonces y solo entonces `MI_PRIVATE_FILES_ENABLED=1`.

## Suscripciones Premium (proveedor sin decidir)
- Bridge HMAC privado `/api/mi/internal/subscriptions/events`, desactivado con `MI_BILLING_BRIDGE_ENABLED=0`.
- Integración seleccionada (GHL, Stripe u otra) debe enviar desde middleware de confianza eventos firmados `mi-billing-v1`, no directamente desde el navegador. Exige `MI_BILLING_BRIDGE_SECRET` robusta, firma `HMAC-SHA256(timestamp + '.' + raw_json)`, cabeceras `x-mi-timestamp` y `x-mi-signature`, margen máximo cinco minutos.
- La asociación `provider_customer_id` -> `actor_id` se introduce únicamente después de verificación administrativa; nunca se crea automáticamente a partir de un webhook. Validar activaciones, renovaciones, impagos y cancelaciones contra contratos reales del proveedor. Configurar fuente y conciliación antes de `MI_BILLING_BRIDGE_ENABLED=1`.
- `MI_ORGANIZER_ENABLED=0` hasta conectar suscripciones, almacenamiento, OCR y antivirus; la verificación Premium se realiza en servidor por tarea.

## Información requerida del propietario
1. Confirmar espacio Render «My Workspace» (evitar tocar otro workspace accidentalmente).
2. Autorizar/activar en Cloudflare un nuevo bucket privado dedicado para MI OPORTUNIIA y asignar credenciales restringidas mediante Render.
3. Confirmar proveedor del correo transaccional y remitente corporativo.
4. Elegir fuente contractual de suscripciones Premium (GHL/LeadConnector, Stripe u otra) y su contrato de eventos.

Esta lista NO implica que producción esté lista. El WordPress público, registro antiguo y facturación existente no deben sustituirse hasta que pasen todas las pruebas y se tenga plan de reversión.
