# Fuentes jurídicas recuperadas

Origen: conversación «3.0 LEGAL», 7 de octubre de 2026, mensaje
`598de57f-3939-4199-9be0-1635772a46b6`.

Se conservan literalmente las secciones completas de aviso legal y privacidad.
No son páginas públicas: contienen datos de identificación pendientes.
El extracto recibido de cookies está truncado y no se incorpora como documento completo.

Antes de publicar: completar titular, NIF/CIF, domicilio y datos registrales con
información confirmada; comprobar que no se activa analítica opcional. La fuente
condicionaba la política de cookies a retirar PostHog.

Comprobación de código del 22 de octubre: la rama de publicación
`feat/coming-soon-20261022` no contiene inicialización PostHog en sus HTML públicos.
La rama anterior `feat/web-acceso-anticipado-20261020` sí contiene PostHog en
`frontend/public/index.html`; no debe incorporarse ese archivo sin corregirlo.
Esta última rama también contiene identidad WEB real en `backend/web_identity.py`;
reutilizar y contrastar ese contrato antes de introducir otro sistema de cuentas.
