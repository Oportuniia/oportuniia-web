# MI OPORTUNIIA · Análisis contextual Premium con revisión del titular

Implementado en sandbox (2026-10-03). No desplegado en la web pública ni conectado al envío de recordatorios reales.

## Flujo privado incorporado

1. Usuario Premium autenticado selecciona un archivo PDF ya clasificado como `NOMINA` o `RENTA` y autoriza explícitamente **ese** análisis desde MI OPORTUNIIA.
2. El backend valida de nuevo la suscripción, comprueba que el documento privado es suyo y que superó el antivirus y verifica la integridad SHA-256 antes de leerlo. Extrae texto/OCR localmente con presupuesto limitado, nunca lo transmite a correo ni proveedores de IA externos.
3. Solo propone campos acotados como día histórico de abono, periodicidad explícita o residencia fiscal histórica declarada. Conserva temporalmente propuestas escalares y huella del documento, no el texto de nóminas ni declaraciones.
4. Devuelve propuestas al propietario con advertencias. Para confirmar una, el backend exige sesión Premium vigente, documento inalterado y propuesta vigente de un solo uso (20 minutos). El dato confirmado se guarda en colección separada; `calendar_enabled=False`.
5. No se emite aviso ni se genera fecha fiscal automáticamente. Si el documento cambia o el consentimiento no existe, falla sin alterar datos.

Rutas nuevas:
- `POST /api/mi/private/premium/secretary/{file_id}/analyze` con `analysis_consent:true`
- `POST /api/mi/private/premium/secretary/confirm` para confirmar una propuesta pendiente
- `GET /api/mi/private/premium/secretary/signals` para consultar las señales confirmadas

**Límite del prototipo:** la propuesta es de un solo uso; para confirmar otro campo del mismo documento hay que repetir el análisis. Aún no se activa el calendario de nóminas ni los avisos de obligaciones tributarias; estos requerirán interfaz de edición y revocación de confirmaciones, reglas oficiales versionadas por jurisdicción y pruebas E2E.

## Puertas pendientes

- Crear índice único por `proposal_id`, índice de expiración TTL de propuestas y política de limpieza sobre datos confirmados al implementar Mongo real.
- Validar el diseño de consentimiento analítico, revisión y supresión de datos privados con LEGAL.
- Activar R2 privado, antivirus, OCR y proveedor de suscripciones Premium reales.
- Crear buzón `info.web@oportuniia.com`, configurar secretos SMTP privados en Render y enlazar n8n/outbox solo tras pruebas y permisos.
- Logotipo oficial del PDF, por actualizar cuando esté disponible su archivo original.
