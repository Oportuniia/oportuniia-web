# MI OPORTUNIIA · Cierre de fase funcional y apertura de integración

**Decisión del propietario: 2026-10-03.** Congelar el alcance funcional implementado en la rama sandbox de WEB 5.0 y pasar a **INTEGRACIÓN Y VALIDACIÓN**. No fusionar PR #9 ni desplegar en producción solo por superar CI. Las pruebas automáticas validan componentes aislados, no una puesta en marcha real.

**Alcance congelado (implementado en sandbox, sujeto a validación):**
- Registro y autenticación de área privada con remitente corporativo configurable, cerrado por defecto.
- Archivo privado, carga y descarga con controles de titularidad, almacenamiento externo y verificación antivirus como dependencias de activación.
- Premium: organizador de PDF/fotos, OCR local, propuestas documentales revisadas por el titular y confirmación explícita.
- Fecha de revisión por documento, calendario de cobro simple confirmado por el usuario (días 1–28, Europe/Madrid), consentimiento y preferencias.
- Planificadores idempotentes de recordatorios documentales y de cobro, cola, cancelación y revalidación inmediatamente antes del transporte.
- Centro privado de notificaciones con estados genéricos y sin detalles económicos/documentales, y harness de entrega **MOCK**.
- Oferta WEB y protocolo documental de 72 horas diseñados en la rama, separados de reservas y pagos.

**No declarar terminadas o activas estas capacidades:**
- Fiscalidad personalizada y calendario tributario oficial por ejercicio/jurisdicción: hay propuestas conservadoras de datos y decisión arquitectónica; **no existe un motor fiscal integral operativo ni asesoramiento automatizado validado**.
- Envíos reales, comprobación de entrega, conexión operativa n8n, OCR/antivirus/almacenamiento y facturación Premium reales.
- Formularios de oferta con CRM y aprobaciones reales; no confundir la simulación del plazo con notificaciones jurídicamente eficaces.
- Diseño definitivo de todos los casos especiales del calendario (últimos días del mes, cambio de nómina, festivos, perfiles internacionales).
- Proveedores y circuitos financieros: escrow B2B exclusivamente en firma notarial y eventual cuenta separada de reservas, **ambos aparcados** por orden del propietario hasta tener proveedores y validación de LEGAL/TESORERÍA.
- Logo oficial definitivo del borrador PDF, pendiente del activo original.

**Directriz de identidad actualizada:** MI OPORTUNIIA **personal/documental** corresponde exclusivamente al inversor; el colaborador aprobado y el suscriptor dispondrán de un apartado **comercial** de aportación de inversores en WEB. El suscriptor conserva sus credenciales, perfil e historial soberanos en OPORTUNIIAPP, pero se le habilitará una sección WEB independiente de aportaciones, siempre modelo A, previa autenticación APP confiable. Ver `docs/MASTER_THREE_PROFILES_ACCESS_20261003.md`. La integración real de OPORTUNIIAPP, el botón de alta, el enlace masivo y el QR siguen pendientes; no se comparten contraseñas ni historiales.

## Plan secuencial de integración y criterios de aceptación

1. **Inventario y seguridad.** Revisar requisitos por servicio, perfiles y permisos, alcance GDPR/consentimiento, retención y supresión con LEGAL. Mantener `MI_SMTP_ENABLED=0` y bloqueos equivalentes de las otras integraciones. Confirmar que no se exponen servicios mock ni identificadores privados.
2. **Entorno real controlado.** Configurar entorno de pruebas aislado en Render, Mongo (índices de cola, propuestas únicas y TTL), almacenamiento R2 privado, análisis antivirus y OCR local. Credenciales solo en gestor de secretos, no GitHub ni chat. Ensayar acceso cruzado, falsos positivos, fallos de red, ficheros grandes y supresión.
3. **Identidad corporativa y Premium.** Crear/verificar `info.web@oportuniia.com`, autorización de envío, SPF/DKIM/DMARC y pruebas controladas de verificación y recuperación con usuario ficticio. Conectar fuente verificable de derechos Premium y ensayar expiración/revocación.
4. **n8n y correo.** Implementar worker de producción distinto de `mi_notification_mock_delivery.py`, cron privado autenticado con mínimos privilegios y sin datos sensibles en n8n. Pruebas de doble ejecución, consentimiento revocado, aviso reclamado, proveedor caído y recibos ambiguos; conciliación humana cuando proceda. La aceptación SMTP no es prueba de entrega final ni por sí sola inicia el plazo jurídico de 72 horas.
5. **E2E en sandbox.** Probar registro, validación, subida, seguridad y OCR, propuestas, confirmación, calendario, opt-out, cola, plantillas, auditoría, cambios simultáneos y restauración/rollback. Revisar accesibilidad, móvil y textos de transparencia; responsable designado aprueba resultados.
6. **Cierre legal y despliegue.** LEGAL verifica comunicación probatoria, política de archivo/consentimientos, términos Premium y límites de calendarios; Producto decide si el calendario fiscal se difiere expresamente o se abre nueva fase bajo cambio de alcance. Solo entonces autorizar PR, despliegue progresivo y monitorización.

## Gestión del congelamiento

- A partir de esta decisión, no añadir nuevas funcionalidades al alcance congelado por iniciativa propia: solo correcciones, pruebas, seguridad y conectores indispensables.
- Cualquier ampliación (como fiscalidad integral o casos especiales de cobro) exige acuerdo de alcance, requisitos, revisión LEGAL y plan de pruebas separado.
- El hito **FUNCIONAL EN SANDBOX** no equivale a **INTEGRADO**, **VALIDADO E2E** ni **PUBLICADO**. Mantener esos estados separados en GitHub y reportes.
- Referencias: `docs/MI_NOTIFICATION_CENTER_OPT_OUT_20261003.md`, `docs/MI_NOTIFICATION_N8N_DELIVERY_GATE_20261003.md`, `docs/MI_PREMIUM_SECRETARY_CONFIRMATION_GATE_20261003.md`, `docs/MASTER_B2B_ESCROW_API_PAYMENT_ARCHITECTURE_20261003.md`.
