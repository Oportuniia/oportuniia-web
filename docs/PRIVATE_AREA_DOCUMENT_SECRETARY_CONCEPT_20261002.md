# OPORTUNIIA · Área privada del inversor y secretaría documental

Estado: visión funcional consensuada por el propietario, pendiente de desarrollo, prototipado y revisión jurídica/privacidad. Fecha: 2026-10-02.

## Experiencia aprobada
- Al darse de alta, cada usuario obtiene su **área privada personal** (el área puede existir desde el registro, pero la documentación confidencial de oportunidades solo se desbloquea mediante validación y autorización expresa por operación).
- Diseño **OPORTUNIIA PREMIUM**, Poppins, logotipos y azules corporativos, compacto, elegante, responsive; indicador de progreso para registro, perfil, validaciones y preparación documental.
- Tono cercano y no coercitivo; hacer explícito que la confianza se construye progresivamente y que la documentación sensible solo se pide cuando hace falta.

## Área documental personal
- Buzón seguro y permanente para consultar la documentación **propia** cargada, el estado de revisión, la versión y vencimientos; acceso seguro recuperable con inicio de sesión robusto (valorar MFA).
- Zona distinta para documentación **de operaciones** autorizadas: comprobar derechos efectivos por inversor y operación en el servidor en cada acceso; la identidad verificada no confiere permiso general.
- Permitir fotos tomadas con móvil, varios archivos y PDF único. Herramienta tipo escáner: corrección de orientación/recorte, detección y clasificación sugeridas, división de PDF, agrupación, orden cronológico y nomenclatura; previsualización y confirmación humana antes de guardar o sustituir documentos. Nunca alterar originales sin conservar trazabilidad/versiones.
- Señalar claramente qué documentos están pendientes, recibidos, por revisar, aceptados, rechazados, caducados, sin forzar a subir documentos que no correspondan al perfil.

## Secretaría y recordatorios personalizados
- Perfil documental configurable con consentimiento: persona física o jurídica, representación de sociedad y tipología societaria, situación fiscal/tributación cuando sea pertinente, empleo y existencia de nómina si aplica. Minimización y justificación de cada dato; no inferir atributos económicos sensibles ni imponer itinerarios rígidos.
- Motor de reglas configurable por documento: periodicidad, vencimiento, ventana real de disponibilidad, situación y excepciones. **Ejemplo aportado:** quien declara voluntariamente que recibe nómina entre días 1 y 5 puede optar por aviso el día 6 para actualizarla. No imponer esa cadencia al resto.
- Avisos cercanos, orientados a facilitar la participación: «Ya puedes actualizar tu nómina de este mes. Tenerla al día te ayudará a estar preparado si aparece una oportunidad que te interese». No prometer acceso, urgencia artificial, ni afirmar que un expediente se perderá automáticamente.
- Preferencias de canal y frecuencia; controles para posponer/silenciar y evitar insistencia si el documento ya está actualizado; registro de notificaciones y tratamiento de zonas horarias/festivos. Nunca enviar DNI, nóminas ni enlaces públicos al archivo por notificación.
- Reglas, mensajes y exigencias documentales definitivas sujetas a revisión legal/privacidad, adaptación según finalidad y requerimientos regulatorios aplicables.

## Diseño de superficie (área privada)
1. Inicio: estado de perfil, próxima acción sugerida y oportunidades guardadas; distinguir progreso de acreditación real.
2. Mis documentos: originales y organizados, carga desde móvil, escáner/organizador, estado y actualización.
3. Mi perfil: categoría y datos aportados, permisos, revisión y documentación aplicable.
4. Mis oportunidades: guardadas, solicitudes de acceso, concesiones explícitas, ofertas y reservas cuando existan.
5. Notificaciones: secretaría documental, ajustes de recordatorios y trazabilidad.

## Límites técnicos de migración
- No crear identidades paralelas hasta definir vínculo con la validación y registro soberanos de WordPress/LeadConnector; auditar integración y migración de consentimiento.
- Archivo personal separado de artefactos PDF soberanos de PRESENTACIÓN en R2, control estricto de acceso, cifrado, antivirus, límites, borrado/retención según política y auditoría; nada de publicar adjuntos o claves R2.
- Prototipar en sandbox con datos ficticios y validar aceptación del propietario antes de integrar recordatorios reales o automatizaciones.
