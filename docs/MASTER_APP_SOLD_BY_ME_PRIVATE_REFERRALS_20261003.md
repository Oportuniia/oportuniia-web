# MASTER · Privacidad de cartera, duplicados y APP «Vendido por mí»

**Decisión 2026-10-03:** las carteras WEB del colaborador y del suscriptor son completamente privadas y solo accesibles por el actor aprobado y autenticado. Su código público de invitación NO es credencial ni autoriza consulta, gestión o reasignación. WEB es la autoridad de atribución comercial; APP es la autoridad de sus informes y de la identidad e historial del suscriptor. No compartir la base de datos completa ni trasladar contraseñas APP a WEB.

## Alta protegida contra captación de inversores preexistentes

- Tanto botón de alta asistida como enlace difundible y QR desembocan en el mismo control del servidor, nunca una atribución directa.
- **Primero búsqueda fiable por email normalizado O por teléfono internacional normalizado** en el registro WEB y, cuando esté habilitada la integración aprobada, en el índice de identidades de inversores que sea jurídicamente compartible desde APP. No usar datos de terceros cuya recogida esté bloqueada. Si cualquiera coincide con una identidad ya registrada, no se concede la relación al nuevo aportador. Ningún solicitante puede alterar la atribución previa mediante otro correo o enlace.
- Como aplicación práctica, para un colaborador o suscriptor **autenticado** que solicite el alta, mostrar «Este inversor ya está registrado. No puedes incorporarlo a tu cartera». Un enlace de campaña PÚBLICO solo debería mostrar un resultado genérico de registro para no permitir enumeración de teléfonos/correos ni revelar si un tercero es cliente.
- Sin certeza de la búsqueda, índices ausentes, APP inaccesible o discordancias, **bloquear la nueva atribución y enviar a revisión privada**, nunca dar por libre al inversor.
- Para un inversor nuevo, deberá verificar personalmente su correo, confirmar vinculación y superar comprobación OPORTUNIIA. Su teléfono, si participa en deduplicación, necesita formato internacional y validación según política acordada; no equiparar texto tecleado a posesión acreditada.
- El control definitivo debe usar índices únicos adecuados, reserva transaccional, control de concurrencia y conciliación auditada para evitar dos altas simultáneas. El código sandbox `mi_referral_identity_guard.py` implementa un **guard sin efectos**, NO sustituye los índices ni conecta con APP.

## «Vendido por mí» observado en el repositorio de OPORTUNIIAPP

Inspección del código `Oportuniia/oportuniiapp` en `main` (2026-10-03):
- `backend/models/report.py`: `CollaboratorSale` incluye `sold_by_collaborator`, nombre, contacto y empresa del inversor. `FieldReport` incluye `property_id`, `collaborator_id` y `collaborator_sale`.
- `backend/routes/reports.py`: el informe creado por un suscriptor vincula `collaborator_id` a `ctx.actor_id` desde la sesión del servidor, y limita el listado de informes del suscriptor a sus propios informes.
- `backend/contact_guard.py`: `THIRD_PARTY_CONTACT_COLLECTION_ENABLED` permanece **desactivado por defecto** hasta la puerta LEGAL. Es obligatorio revisar también toda ruta de `CollaboratorSale` para garantizar que el nuevo flujo no eluda esta protección antes de activar datos de terceros.
- **No se ha confirmado que exista una conexión WEB–APP de atribuciones, ni un webhook de «Vendido por mí» listo para ese propósito.** No asumir que las colecciones ni los contactos históricos coinciden semánticamente.

## Integración recomendada: API privada mínima / evento validado

1. APP genera un evento interno `SUBSCRIBER_SOLD_BY_ME_SUBMITTED` solo tras autorizar la sesión del suscriptor, verificar `sold_by_collaborator=True`, comprobar activación LEGAL de recogida de contacto, normalizar datos y disponer de referencia auténtica del informe/activo. Ese evento **no crea inversores ni ventas verificadas en WEB**.
2. APP→WEB a través de API servidor-servidor autenticada (credencial de máquina en gestor de secretos; firma y rotación), con `event_id` único, `app_actor_id`, `report_id`, `property_id`, fecha y solo datos de contacto para cuya transmisión exista base jurídica y necesidad. Evaluar alternativa sin datos personales: identificador opaco y posterior resolución por personal autorizado. Versionar esquema y no almacenar documentos/contraseñas en n8n.
3. WEB valida remitente y consulta en APP estado actual de suscripción; relaciona actor APP con código de aportación WEB en tabla **controlada exclusivamente por OPORTUNIIA**; comprueba con su registro si el inversor ya existe por teléfono o email, sin exponer los resultados a terceros. No permite autorreferencias del navegador ni reasignaciones silenciosas.
4. Si ya existe o hay conflicto, bloquear alta/asignación y abrir revisión interna. Si es nuevo, preparar invitación de confirmación WEB; solo el inversor dueño del correo puede aceptar, y la asignación se verifica y aprueba manualmente. El usuario suscriptor verá únicamente estado genérico de su trámite y operaciones atribuibles autorizadas.
5. Controles: idempotencia por `event_id`/informe, firma/autenticación del servicio, identidad APP propietaria del informe, revocación, mínimo privilegio, logs no sensibles, tiempos de retención, fallos APP, pruebas de concurrencia y eliminación; sin accesos directos WEB a las colecciones internas APP.

**Por qué no DB compartida:** compartir colecciones saltaría las políticas de cada aplicación, facilitaría visibilidad transversal y acoplaría migraciones. Una consulta puntual o evento API permite que cada servicio revise y decida sobre sus propios datos.

## Puertas aún pendientes

LEGAL y APP deben resolver si `CollaboratorSale` recoge datos personales de terceros durante «Vendido por mí», cómo aplica la puerta de contactos, qué base jurídica y qué transparencia habilitan transmitirlos a WEB; decidir índice común apto para deduplicación y verificación telefónica. WEB/APP deben pactar contrato API, mapeo de sujetos, índices únicos, tratamiento de inversores ya presentes y ensayar no apropiación con dos altas simultáneas. Sin activar API, correo ni altas hasta completar todo lo anterior.
