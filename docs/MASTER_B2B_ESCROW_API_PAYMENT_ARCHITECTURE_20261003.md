# DIRECTRIZ MASTER · Arquitectura de pagos OPORTUNIIA

**Decisión del propietario — 2026-10-03:** el sistema previsto de pagos para operaciones empresariales seguirá un modelo de **Pago B2B con Infraestructura Escrow (vía API)**.

**Estado:** decisión de arquitectura y propuesta de cláusula, no contrato jurídico aprobado, reserva operativa ni proveedor ya contratado.

## Cláusula matriz propuesta para contratos (sujeta a aprobación de LEGAL)

«Las partes acuerdan que, cuando la operación contemple pagos, garantías o cantidades condicionadas, su gestión se realizará mediante una infraestructura tecnológica de pago entre empresas (B2B), con funcionalidad escrow o mecanismo equivalente jurídicamente validado, prestada por un proveedor tercero debidamente habilitado para los servicios que correspondan y conectado mediante API a la plataforma OPORTUNIIA.

La identidad del proveedor, la modalidad jurídica y operativa del servicio, la titularidad y salvaguarda de los fondos, las verificaciones exigibles, los hitos que autorizan la liberación y/o devolución, los plazos de ejecución, las tarifas, el procedimiento de resolución de incidencias, las obligaciones KYC/KYB y las responsabilidades de las partes se concretarán en el documento particular de la operación y en las condiciones del proveedor, que deberán entregarse y aceptarse antes de ordenar el pago.

OPORTUNIIA actuará exclusivamente en el papel que legalmente le corresponda conforme al modelo finalmente aprobado. En ningún caso esta cláusula permitirá presentar a OPORTUNIIA como entidad depositaria, prestadora autorizada de servicios de pago o garante de la devolución mientras no exista habilitación legal expresa para ello. Ningún cobro, bloqueo, transferencia o liberación se ejecutará antes de la selección, integración y validación del proveedor y de las condiciones contractuales.»

**Notas esenciales para LEGAL**
- El término comercial escrow **no sustituye** la definición jurídica exacta del mecanismo que ofrezca el proveedor. Comprobar si se trata de custodia condicional, salvaguarda regulatoria, cuenta de pago, retención de tarjeta, mandato o mecanismo contractual diferente y usar la denominación correcta.
- La analogía de la fianza del coche de alquiler es solo divulgativa y NO implica devolución automática o íntegra ni retención en tarjeta. Los supuestos de pérdida, devolución parcial, adjudicación y controversia deben especificarse.
- Diferenciar **oferta comercial**, **aprobación**, **documentación en 72 horas**, **hoja de reserva** y **pago condicionado**; una oferta presentada o aprobada no autoriza por sí sola captura de fondos.
- Fijar si el importe objetivo de 5.000 EUR (mínimo comercial debatido de 3.000 EUR) resulta exigible en una modalidad de operación determinada, si es fianza, depósito, arras u otra figura, y quién lo recibe; no presentarlo como tarifa ni como cobro activo sin validación.
- Revisar el carácter realmente B2B: inversores personas físicas no son necesariamente empresas; habilitar la modalidad correspondiente solo para perfiles elegibles y preparar un circuito diferente si se admiten consumidores.
- Adecuar KYC/KYB, prevención de blanqueo, información previa, protección de datos, registro de evidencias, disputas, reversos, insolvencia del proveedor, conciliación, retención y comisiones.
- Verificar autorizaciones del proveedor y ámbitos de actividad con registro y asesoría; no inferir que cualquier pasarela API equivale a escrow regulado.

## Arquitectura de integración que deberá desarrollarse

1. LEGAL emite `payment_terms_version` por tipo de operación: partes, importe, mecanismo, eventos verificables y condiciones de devolución y conflicto.
2. WEB presenta los términos vigentes y obtiene aceptación expresa y trazable antes del pago; nunca deriva importes o identidad del beneficiario de datos editables del navegador.
3. Backend prepara una intención de pago idempotente (`offer_id`, `operation_id`, `provider_reference`) solo tras aprobación documental y autorización aplicable, sin almacenar credenciales bancarias ni saldos como custodio.
4. API del proveedor autorizado ejecuta recepción/custodia condicional y emite callbacks firmados. WEB verifica autenticidad, idempotencia, correlación, versiones y reconciliación diaria. Ningún callback del cliente libera fondos.
5. Las instrucciones de liberación o devolución requieren condiciones acreditadas, segregación de funciones y autorización conforme a LEGAL, evitando que un único operador o una automatización no autorizada decida unilateralmente.
6. n8n coordina notificaciones y tareas técnicas sin custodiar fondos, ni sustituir al proveedor o la decisión jurídica.
7. Auditoría: estados de pago, evidencias de entrega/notificación, respuesta API, discrepancias, rechazo y disputa; datos y permisos mínimos.

## Bloqueos antes de activar

- Selección comercial y validación por LEGAL del proveedor y modalidad real (autorización/registro y API condicional, cobertura geográfica y precio).
- Contratos finales, reparto de roles, requisitos operacionales, términos particulares y política de reclamaciones.
- Aprobación de seguridad y ensayos integrales en entorno de pruebas: webhooks, idempotencia, doble evento, reverso, disputa, proveedor caído, conciliación, perfiles físicos y jurídicos.
- Validación expresa del circuito real de reserva, comisiones e impuestos.
- Hasta finalizar lo anterior, «Cómo funciona» describe el **modelo previsto**, sin afirmar disponibilidad comercial, custodia actual ni devoluciones garantizadas.

## Referencia regulatoria a contrastar con LEGAL

Banco de España: los servicios de pago regulados requieren, según actividad y excepciones aplicables, proveedores autorizados o registrados. La custodia y salvaguarda de fondos se rigen por requisitos concretos; un mero nombre comercial «escrow» no acredita el cumplimiento. Documentar validación legal antes de contratar.
