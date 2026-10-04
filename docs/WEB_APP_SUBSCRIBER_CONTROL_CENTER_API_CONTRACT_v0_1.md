# WEB ↔ OPORTUNIIAPP · Contrato de integración v0.1 (SANDBOX)
Estado: PROPUESTA DE CONTRATO. NO existe aún endpoint HTTP operativo ni comunicación activa. Coordinación APP: https://github.com/Oportuniia/oportuniiapp/issues/42

## Identidad y confianza
- APP autentica al suscriptor y WEB verifica mediante un vínculo registrado y aprobado app_subject ↔ web_referrer_code (OI-SUB-...), suscripción activa y alcance específico. Nunca confiar en un referrer_code aportado por el navegador.
- Transporte canónico: M2M DIRECTO OPORTUNIIAPP ↔ WEB conforme a docs/ARQUITECTURA_M2M_MASTER_v1.md. n8n no será intermediario obligatorio; solo se conservará donde exista orquestación real no sustituida. Credencial M2M dedicada por relación en variable de entorno, autorización por recurso/suscriptor, TLS, anti-replay, rate limiting, outbox/inbox persistentes, ACK, correlación, hash y secretos fuera del repositorio. No compartir bases de datos.
- El centro de control APP es un agregador visual; APP y WEB conservan datos y responsabilidades separados.

## ENTRADA WEB: solicitud APP «Vendido por mí»
Propuesta: POST /api/integrations/oportuniiapp/v1/referral-intakes
Headers: x-oportuniia-web-app-m2m-key: <n8n-m2m-secret>, Idempotency-Key: <opaque-event-key>, x-app-subject: <authenticated-app-subject>
Body (mínimo, sujeto a LEGAL): schema_version, app_event_id, app_report_id, app_subject, investor_email y/o investor_phone, consent_evidence_ref, captured_at.
APP debe verificar actor y propiedad del informe en su servidor. Consentimiento verificable en servidor; una casilla enviada por navegador no es prueba suficiente. No almacenar ni enviar PII del comprador mientras LEGAL no autorice la recogida; cerrar primero el posible bypass del guard de collaborator_sale en rutas APP.
- Validación WEB: autenticidad, idempotencia, vinculación APP↔WEB, identidad normalizada email O teléfono; cotejo contra registros WEB y fuentes APP legalmente autorizadas. Comprobación atómica en persistencia y revalidación al aprobar.
- Respuesta 202: intake_id, status=WEB_CHECK_PENDING|INDEX_UNAVAILABLE|INVESTOR_VERIFICATION_PENDING|HUMAN_REVIEW_PENDING, retryable, correlation_id. Sin código definitivo antes de verificación personal y aprobación humana.
- Si hay coincidencia en cualquiera de las fuentes: DUPLICATE_BLOCKED sin nueva atribución ni transferencia de cartera. Fallo de índice: INDEX_UNAVAILABLE, fail-closed, reintento seguro. No revelar existencia de terceros por enlace público.
- Eventos repetidos con misma clave y carga retornan el mismo resultado; misma clave con carga diferente: conflicto. Reintentos con backoff, reconciliación manual de excepciones.

## SALIDA WEB: proyección privada de cartera
Propuesta: GET /api/integrations/oportuniiapp/v1/subscriber-portfolio
La identidad de suscriptor se deriva de la autenticación servidor a servidor y de una referencia APP autenticada, jamás de un identificador libre de la URL del cliente.
Respuesta propuesta: schema_version, generated_at, web_referrer_code, investors:[{investor_code, attribution_status, operations:[{operation_ref,status}]}], earnings:[{operation_ref,verification_status,recognized_amount?,settlement_status?,paid_amount?}], sync_status.
- Solo inversores atribuidos de forma verificada al suscriptor solicitante. Modelo A únicamente. Sin datos documentales personales de MI inversor ni de otras carteras.
- Importes solo si verificados por LEGAL, OPERACIONES y CONTABILIDAD, según reconocimiento firmado y condiciones vigentes; separar reconocidos, liquidados y pagados. No calcular ni emitir facturas ni iniciar pagos.
- WEB devuelve códigos/estados y referencias permitidas; APP fusiona con informes propios y muestra origen y fecha de actualización. Si WEB está indisponible: mostrar estado desactualizado, no presentar importes como vigentes.

## Resultado de entrada para APP
Propuesta: GET /api/integrations/oportuniiapp/v1/referral-intakes/{intake_id}
Solo APP autenticada y vinculada al evento. Estados: WEB_CHECK_PENDING, DUPLICATE_BLOCKED, INDEX_UNAVAILABLE, INVESTOR_VERIFICATION_PENDING, HUMAN_REVIEW_PENDING, APPROVED_WITH_WEB_CODE, REJECTED. APPROVED_WITH_WEB_CODE exige código creado por WEB en transacción tras comprobación final. APP report submission es independiente de WEB attribution.

## Criterios de aceptación compartidos
1. Suscriptor A no puede consultar ni modificar datos del suscriptor B; colaborador y personal MI inversor quedan separados.
2. Reintentos offline y eventos duplicados no generan códigos ni atribuciones duplicadas.
3. Coincidencia por correo O teléfono bloquea asignación; caída de índices bloquea hasta recuperación.
4. Sin verificación personal del inversor y revisión humana no hay código ni atribución definitiva.
5. PII del comprador bloqueada hasta LEGAL y almacenamiento offline seguro aprobado; no usar localStorage sin protección para nueva captura.
6. Pruebas de integración, observabilidad sin PII en logs, revisión de seguridad, migraciones/índices y aprobación antes de despliegue.

Responsables: APP implementa UX, cola offline y autenticación APP; WEB implementa endpoints, índice de identidad, proyección privada y estados. Nombres de rutas y campos sujetos a revisión conjunta; NO anunciar conexión operativa hasta pruebas reales.
