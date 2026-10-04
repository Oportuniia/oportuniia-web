# DIRECTRIZ MASTER · Dos circuitos de pago independientes

**Corrección del propietario (2026-10-03):** el modelo **Pago B2B con Infraestructura Escrow (vía API)** se aplica específicamente a los **pagos de operaciones formalizadas mediante firma ante notario**, no a las reservas. La opción preferida para reservas es estudiar **una cuenta bancaria separada y exclusiva para reservas**, con sus propias condiciones y conciliación.

**Estado:** decisión de arquitectura pendiente de aprobación y concreción por LEGAL, TESORERÍA y ARQUITECTURA MASTER; ni proveedor escrow ni cuenta de reservas se consideran activos.

## 1 · Firma ante notario: pago B2B mediante infraestructura escrow vía API

### Cláusula matriz propuesta para contratos (sujeta a aprobación de LEGAL)

«Las partes acuerdan que el pago correspondiente a la operación de compraventa que deba formalizarse ante notario se articulará, cuando resulte jurídica y operativamente aplicable, mediante una infraestructura de pagos entre empresas (B2B) con funcionalidad escrow o mecanismo condicional equivalente, gestionada por un proveedor tercero debidamente habilitado e integrada mediante API con los sistemas de OPORTUNIIA.

Las condiciones particulares identificarán al proveedor, la modalidad exacta de tratamiento y salvaguarda de fondos, las partes y el importe, los requisitos previos, los hitos verificables asociados a la firma notarial y el procedimiento para liberar, devolver o resolver controversias sobre las cantidades, incluidos los plazos y comisiones aplicables. Ninguna liberación se producirá por una instrucción unilateral no autorizada de la plataforma: se verificará la evidencia notarial y contractual que proceda.

OPORTUNIIA desempeñará únicamente su función contractual y tecnológica autorizada. No se presenta como entidad depositaria, entidad de pago ni garante de la devolución. La selección, contratación y revisión jurídica del proveedor y las condiciones particulares son requisitos previos a cualquier cobro real por este mecanismo.»

**IMPORTANTE:** el servicio comercial descrito como escrow no constituye por sí mismo una modalidad regulatoria: LEGAL debe verificar la solución exacta ofrecida y las autorizaciones exigibles. El circuito B2B no se atribuirá automáticamente a inversores personas físicas o consumidores.

### Arquitectura de integración notarial

1. LEGAL y OPERACIONES fijan el protocolo de la operación y los hitos verificables de la firma notarial, con reglas de excepción y controversias.
2. WEB presenta y registra la aceptación de las condiciones particulares del pago notarial; el backend valida y fija importes y destinatarios, nunca el navegador.
3. Backend comunica a la API del proveedor especializado una intención idempotente y conserva referencias operativas, no custodia ni credenciales bancarias.
4. Eventos del proveedor con autenticidad verificada y evidencias del hito notarial permiten solicitar liberación o devolución conforme a la autoridad y condiciones pactadas. Firma notarial no significa automáticamente liberación si quedan requisitos contractuales pendientes.
5. Conciliación, auditoría, gestión de conflictos, seguridad de webhooks y segregación de funciones; n8n solo orquesta información y tareas.

## 2 · Reservas: cuenta bancaria dedicada, separada del escrow notarial

**Propuesta del propietario:** estudiar una cuenta exclusiva para recibir y administrar las cantidades de reserva; no compartirla con ingresos generales ni con el circuito de pago notarial.

Antes de implantarla, LEGAL y TESORERÍA deberán concretar: titularidad de la cuenta, si existe obligación de cuenta segregada o tercero custodio, naturaleza jurídica de la reserva (depósito, arras u otra figura), cuantía por operación, recibo e identificación bancaria, conciliación, fecha y criterios de aplicación al precio, supuestos de devolución/pérdida, impuestos, comisiones, controles de acceso y protección ante incidencias o insolvencia.

Una cuenta exclusiva para reservas **no equivale automáticamente a una cuenta escrow ni garantiza por sí sola la protección legal o devolución de los fondos**. No cobrar reservas hasta que las condiciones contractuales y bancarias estén aprobadas.

La cifra comercial antes debatida de 5.000 EUR (mínimo 3.000 EUR) queda sujeta a definición específica y aprobación legal de la hoja de reserva: NO se incorpora como importe del pago notarial por defecto. Oferta, aceptación, documentación en 72 horas, reserva y firma notarial son etapas distintas.

## Para «Cómo funciona»

Se explica la firma notarial con la analogía limitada de la garantía del coche de alquiler: fondos sujetos a condiciones y verificación previa a su destino. Debe aclararse que una fianza/retención de tarjeta y escrow no son lo mismo. Aparte, se presenta el proyecto de cuenta exclusiva para reservas, sin mezclarlos.

## Pendiente antes del despliegue

- LEGAL: validar cláusulas separadas de compraventa notarial y reserva, y adecuación a perfiles empresariales o consumidores.
- TESORERÍA: definir banco y titularidad de la cuenta de reservas, política de conciliación y devolución; ninguna cuenta afirmada como existente.
- PAGOS: verificar proveedor habilitado, condiciones de custodia y API, pruebas sandbox de webhooks e idempotencia.
- ARQUITECTURA MASTER: reflejar la separación de procesos, hitos, permisos y contabilización en el ecosistema.
