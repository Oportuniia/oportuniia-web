# Puerta N0 · Dos circuitos de pago físicamente separados (sandbox)

El código `backend/mi_payment_rails.py` modela exclusivamente estados internos y **no transfiere dinero**.

- **NOTARIAL_ESCROW**: exclusivamente compraventa vinculada a firma notarial. La vinculación con un proveedor requiere contrato aprobado por LEGAL y elegibilidad B2B. Se exige referencia independiente de firma notarial, validación jurídica y validación de operaciones antes de producir una propuesta de instrucción para revisión humana. Firmar no equivale a liberar fondos. La API real todavía no está integrada.
- **RESERVATION_BANK**: exclusivamente la eventual cuenta bancaria de reservas que estudian LEGAL y TESORERÍA. La referencia de transferencia no demuestra cobro; únicamente la evidencia bancaria verificada permite marcar conciliación. No se configura IBAN ni se afirma que exista la cuenta.
- **Separación garantizada por código**: las funciones de un circuito rechazan los registros del otro. Los eventos del cliente no pueden activar una transferencia notarial y ninguna reserva abre una instrucción de escrow. Todo empieza en `DRAFT`.

## Próximas dependencias

1. LEGAL aprobará hojas/contratos diferentes para reserva y compraventa, con consecuencias de devolución, aplicación de fondos, disputas, impuestos y distinción empresa/consumidor.
2. TESORERÍA determinará titularidad, entidad bancaria y requisitos de cuenta exclusiva para reservas y conciliación.
3. PAGOS/ARQUITECTURA MASTER seleccionará y validará un proveedor apto para pagos condicionados vinculados al cierre notarial y definirá reglas de segregación de autorizaciones.
4. Integración real: contratos API, idempotencia persistente Mongo, verificación de webhooks, firma/verificación de evidencias notariales, auditoría y pruebas de fallo; prohibido habilitar mediante interfaz pública hasta superar todo el proceso.
5. Confirmar cómo se imputa una reserva al precio final, si procede; la conciliación de ambos circuitos no implica transferencia automática entre cuentas.

La implantación de sandbox es un contrato técnico preventivo y no un servicio de pago activo.
