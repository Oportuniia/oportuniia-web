# WEB · Auditoría Arquitectura M2M Directo v1

Fecha: 2026-10-04 · Rama: sandbox/presentacion-web-ui-validation-20261001 · Producción: sin cambios.

## A-D · mapa actual
| Conexión | Sentido | Finalidad | Estado/transporte | Persistencia/idempotencia |
|---|---|---|---|---|
| PRESENTACIÓN_WEB_PUBLICATION_v1 | PRESENTACIÓN → WEB | borradores catálogo + artefactos | M2M DIRECTA | Mongo drafts; output_id+output_hash; conflicto hash; hash SHA-256 |
| MI billing bridge | middleware facturación → WEB | estado Premium verificado | OTRA/M2M webhook firmado | mi_billing_events event_id; HMAC timestamp; anti-replay 5m |
| OPORTUNIIAPP control center v1 | APP ↔ WEB | vendido-por-mí, estado, cartera | M2M DIRECTA EN CONSTRUCCIÓN | intake idempotente parcial; cartera read-only |
| Notificaciones externas | WEB → correo/proveedores | notificaciones | OTRA / adapters | outbox local existente |
| WordPress precheck/bridge | WEB → WordPress | lectura/bridge controlado | OTRA | no es bus interno entre herramientas |

## E · desviaciones
PRESENTACIÓN→WEB ya es M2M directo, con credencial, hash y persistencia, pero no demuestra todavía el estándar completo de outbox del emisor ni calendario 0/5/15/30/60/90 desde WEB. APP↔WEB tiene endpoints sandbox e idempotencia básica, pero carece aún de outbox WEB/APP común, envelope MASTER, correlation_id obligatorio, ACK normalizado, anti-replay firmado y worker de reintentos completo. Billing tiene HMAC/anti-replay/inbox, pero su productor es middleware externo y no se migra sin proveedor definitivo.

## F-G · n8n
En el código WEB auditado no existe una conexión n8n implementada que deba conservarse como transporte obligatorio. La decisión anterior de imponer n8n a APP↔WEB queda revocada por MASTER v1. Si fuera descubierto un workflow n8n fuera de este repo, solo se retirará tras inventario, prueba de equivalencia y autorización de retirada.

## H-J · contratos y persistencia necesarios
APP↔WEB debe evolucionar a envelope M2M v1, outbox persistente en cada emisor para eventos push, inbox/idempotencia persistente en receptor, event_id estable, correlation_id, payload_hash canónico, ACK de transporte y estado de negocio separados. GET de cartera puede seguir request/response autenticado y scoped; los cambios/eventos deben usar outbox.

## K · seguridad
Credencial específica APP↔WEB; secreto fuera de código; TLS; firma/anti-replay; tenant scope server-side; deny-by-default; rate limit; PII de terceros bloqueada hasta LEGAL. No DB compartida.

## L-M · pruebas/evidencias actuales
Existen tests sandbox de autenticación, aislamiento entre suscriptores, idempotencia, conflicto y bloqueo LEGAL para APP↔WEB. PRESENTACIÓN tiene consumer gate y E2E opt-in. Estas evidencias NO cubren todavía todos los fallos MASTER (reinicios, ACK perdido, seis intentos, recuperación posterior) para APP↔WEB.

## N-O · bloqueos/riesgos
Bloqueo real: APP↔WEB aún no cumple íntegramente MASTER v1 ni tiene E2E directo conjunto. PII real continúa bloqueada por LEGAL. Fuentes financieras verificadas y enlaces reales de suscriptor no están conectados. Riesgo principal: declarar listo antes de probar persistencia/reintentos/replay bajo fallos.

## P · resultado
BLOCKED para declarar integración completa.
READY para continuar desarrollo y pruebas SANDBOX M2M directo.
