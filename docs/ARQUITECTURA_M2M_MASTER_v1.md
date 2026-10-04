# ARQUITECTURA M2M MASTER v1

Autoridad: RAFA · Estado WEB: SANDBOX · Producción: NO AUTORIZADA

## Norma
M2M directo es el transporte interno por defecto. n8n no es intermediario obligatorio cuando emisor y receptor pueden implementar directamente persistencia, reintentos, idempotencia, correlación, integridad, ACK, trazabilidad, seguridad y recuperación con equivalencia o mejora.

Cada herramienta conserva DB, lógica, permisos, credenciales y autoridad. Need-to-know. Nunca retirar un transporte anterior antes de probar su sustituto.

## Envelope canónico v1
Campos obligatorios: contract_version, event_id, correlation_id, occurred_at, source, destination, event_type, payload, payload_hash.
JSON canónico: UTF-8, ensure_ascii=false, claves ordenadas, separadores ',' y ':'. payload_hash = SHA-256 hexadecimal del objeto completo SIN payload_hash. Payload inmutable desde primer intento.

## Entrega
Outbox persistente en emisor + inbox/idempotency persistente en receptor. Un intento inicial y cinco reintentos: inmediato, +5, +15, +30, +60, +90 minutos. Un event_id + mismo hash = replay idempotente; mismo event_id + hash distinto = 409 CONFLICT y fail-closed. ACK de transporte explícito e independiente del estado de negocio.

## Seguridad
HTTPS/TLS, credencial M2M específica por relación fuera del código, deny-by-default, anti-replay, rate limiting cuando corresponda, auditoría y mínimo dato. Se recomienda firma HMAC-SHA256 sobre timestamp + '.' + bytes canónicos y ventana temporal, además de event_id persistente.

## Migración
Construir M2M → persistencia → automatización → reintentos → idempotencia → correlación → integridad → ACK → trazabilidad → seguridad → pruebas → comparación → retirar intermediario solo con equivalencia/mejora.

## Pruebas mínimas
Entrega normal; receptor/emisor reiniciado; receptor caído; timeout; pérdida/recuperación; reintentos; duplicado; ACK perdido; procesado+respuesta perdida; mismo ID+payload distinto; hash incorrecto; credencial incorrecta; replay; agotamiento; recuperación posterior. Demostrar no pérdida y no doble efecto.
