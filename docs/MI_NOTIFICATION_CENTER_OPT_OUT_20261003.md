# MI OPORTUNIIA · Centro privado de notificaciones (sandbox)

Avance del 2026-10-03: estado y revocaciones de recordatorios independientes de servicios externos.

- `GET /api/mi/private/notifications` exige la sesión WEB vigente y consulta exclusivamente el actor autenticado. Devuelve únicamente el nombre genérico del tipo de aviso, su estado genérico y fecha de creación. Nunca revela dirección de correo, datos de nóminas, documentos, ID de ofertas o recibos de transporte. «Procesado» no constituye acreditación de entrega al destinatario.
- MI OPORTUNIIA muestra su propio panel de estados en el área privada, distinto del calendario Premium.
- Al retirar el consentimiento general de recordatorios Premium se cancelan proactivamente sus avisos pendientes en cola, dejando intactas las notificaciones esenciales de las ofertas.
- Al cambiar o eliminar la fecha de revisión de un archivo se cancelan solo los avisos pendientes de ese archivo; al modificar o desactivar el calendario de cobros, únicamente los de esa señal de calendario.
- Los avisos **ya reclamados** pueden estar en proceso: siguen sometidos a una comprobación de permisos inmediatamente antes de cualquier transporte. No se promete retirada de mensajes ya aceptados por un proveedor.
- La cola conserva auditoría de cancelación y no reutiliza claves anteriores. Los cambios de versión generan una clave nueva si el usuario confirma un evento futuro.

**Sin proveedores activos:** esto permanece en sandbox, no hay SMTP, n8n ni cron real. El contrato de n8n y el código de simulación existente siguen siendo los puntos de integración posteriores, no una entrega real. El escrow notarial y las reservas se mantienen pendientes de proveedores.
