# Decisión: códigos OPORTUNIIA soberanos de WEB

2026-10-02. Decisión del propietario. Estado: mandato de arquitectura; pendiente de implementación y pruebas, sin cambios en producción.

- **GoHighLevel solo se conserva temporalmente para el embudo de captación de suscriptores**. Su papel para inversores, colaboradores y generación de códigos se eliminará una vez migrados y verificados los datos necesarios. No dejar GHL como dependencia del área privada WEB.
- **WEB es autoridad soberana de registro y códigos de inversores y colaboradores**. Cada alta crea un actor_id interno estable. El código OPORTUNIIA único se asigna tras la validación aprobada, no como consecuencia de comprobar solo el correo. Código NO es token de acceso, contraseña, ni permiso a expedientes.
- MongoDB WEB conserva actores, perfiles, estado de validación, código, índices de unicidad, auditoría y metadatos de documentos. Documentos personales binarios exclusivamente en espacio R2 privado dedicado MI OPORTUNIIA.
- n8n orquesta comunicaciones y avisos a partir de eventos autorizados, sin generar códigos ni decidir validaciones de identidad. LEGAL no interviene en la documentación personal.
- Conservar correspondencia y evitar colisiones con códigos históricos generados por GHL. Antes de la migración, auditar patrón histórico, registros y titularidad; importar con control de duplicados y sin reexpedir códigos distintos a usuarios ya existentes.
- Establecer asignación atómica y reintentable de códigos en backend con índice único Mongo; separar identificador interno inmutable del código visible. Elegir formato y proceso de validación con el propietario antes de habilitar producción.
- Proteger las altas con controles antifraude, consentimiento, minimización de datos y trazabilidad; no confundir usuarios inversores WEB con suscriptores OPORTUNIIAPP.
