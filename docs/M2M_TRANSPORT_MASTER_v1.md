# OPORTUNIIA · CONTRATO UNIVERSAL DE TRANSPORTE M2M v1

Autoridad MASTER: Rafa
Ámbito: transporte interno entre herramientas OPORTUNIIA
Entorno: SANDBOX

Los contratos soberanos de negocio se conservan. Se transportan dentro de OPORTUNIIA_M2M_EVENT_v1 y se confirman con OPORTUNIIA_M2M_ACK_v1.

Hash único: SHA-256 del payload tras aplicar el método universal y determinista de serialización JSON. La terminología “canónico/canonical” queda retirada del estándar MASTER.

Idempotencia: mismo event_id + mismo payload_hash = replay seguro; mismo event_id + hash distinto = CONFLICT y fail-closed.

Persistencia: M2M_OUTBOX antes de enviar y M2M_INBOX/ledger equivalente antes de confirmar el efecto.

Reintentos: inmediato, +5, +15, +30, +60, +90 minutos. Agotados: REQUIRES_INTERVENTION o equivalencia documentada; nunca borrar el evento.

Seguridad: TLS, credencial específica por relación/dirección, secretos runtime, anti-replay, deny-by-default, fail-closed, rate limiting cuando proceda.

Una relación solo es MASTER PASS tras E2E de ambos extremos con 0 eventos perdidos y 0 efectos duplicados.
