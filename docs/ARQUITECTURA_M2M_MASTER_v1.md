# OPORTUNIIA · ARQUITECTURA M2M MASTER v1

**Autoridad Master:** Rafa  
**Estado:** norma obligatoria para diseño, desarrollo, adaptación y pruebas SANDBOX.  
**Producción:** NO autorizada por esta directriz.

## Principio

M2M DIRECTO es el estándar general de comunicación interna del ecosistema OPORTUNIIA. n8n no será intermediario obligatorio cuando emisor y receptor puedan comunicarse directamente con garantías iguales o mayores.

Ningún sistema actual se retira hasta que el sustituto M2M esté construido, probado y demuestre equivalencia o mejora.

## Alcance obligatorio

Toda conexión entrante y saliente entre herramientas OPORTUNIIA debe inventariar: emisor, receptor, sentido, finalidad, datos, contrato y versión, autenticación, transporte, persistencia, reintentos, idempotencia, correlation_id, payload_hash, ACK, trazabilidad, seguridad, errores, recuperación y dependencia de n8n.

Clasificación: **M2M DIRECTA / n8n / OTRA / NO IMPLEMENTADA**.

## Estándar M2M

Cada relación M2M debe disponer de:

- outbox persistente en emisor;
- inbox o registro persistente de idempotencia en receptor;
- 1 intento inicial y 5 reintentos automáticos: +5, +15, +30, +60 y +90 minutos;
- event_id único, estable e inmutable durante todos los intentos;
- correlation_id;
- payload_hash SHA-256 sobre JSON canónico UTF-8, claves ordenadas, separadores compactos, sin espacios no significativos; el campo hash queda fuera de su propio cálculo;
- payload de negocio inmutable desde el primer intento;
- ACK explícito de recepción válida;
- separación entre ACK de transporte y aprobación/estado de negocio;
- trazabilidad y recuperación automática;
- fail-closed;
- HTTPS/TLS;
- credencial específica por relación y secretos fuera del código;
- protección anti-replay;
- rate limiting cuando corresponda;
- auditoría;
- deny-by-default y need-to-know.

## Idempotencia

Mismo `event_id` + mismo `payload_hash` = mismo evento; el receptor no repite el efecto de negocio y responde ACK idempotente.

Mismo `event_id` + payload/hash diferente = **CONFLICTO**, fail-closed.

Si cambia contenido relevante se genera un nuevo `event_id`.

## ACK

HTTP 200 no equivale por sí solo a operación completada. El receptor debe devolver un ACK estructurado que vincule `event_id`, `payload_hash`, recepción y resultado de transporte. El estado de negocio viaja separado.

## Migración desde n8n

Para cualquier A → n8n → B se determinará si n8n orquesta negocio o solo transporta. Si solo aporta transporte, persistencia, reintentos, ACK, idempotencia, correlación o trazabilidad, se sustituirá por M2M directo.

Orden: construir M2M → persistencia → automatización → reintentos → idempotencia → correlación → integridad → ACK → trazabilidad → seguridad → pruebas → comparación → retirada del intermediario solo con equivalencia o mejora demostrada.

## Pruebas SANDBOX mínimas

Entrega normal; receptor caído; emisor reiniciado; receptor reiniciado; timeout; pérdida y recuperación de conexión; reintentos; duplicado; ACK perdido; evento procesado con respuesta perdida; mismo ID con payload distinto; hash incorrecto; credencial incorrecta; replay; agotamiento de reintentos; recuperación posterior.

Criterios obligatorios: **no se pierde el evento** y **no se duplica el efecto de negocio**.

## Soberanía

Ninguna herramienta accede directamente a la base de datos de otra. Cada sistema conserva BD, lógica, permisos, credenciales y autoridad. Solo se intercambia la información mínima necesaria.

## Límites

Autorizado: auditoría, diseño, desarrollo, adaptación, migración técnica, coordinación y pruebas SANDBOX.

No autorizado por esta directriz: producción, PII real no autorizada, pagos automáticos, cambios de autoridad de negocio o retirada del sistema anterior sin sustituto probado.
