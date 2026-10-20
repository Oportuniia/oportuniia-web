# Mi OPORTUNIIA — servicios de contratación adicional

## Alcance entregado

Interfaces IA, LEGAL y visita/información de vivienda dentro del área privada. Logos existentes originales, fondo oscuro, adaptación 390/768/1440 px, navegación con teclado, estados anunciados y movimiento reducido. Sin enlaces a aplicaciones internas.

La suscripción Premium permite descubrir/solicitar estos servicios. No constituye pago de un encargo. Los detalles no aparecen en el menú ni en el descubrimiento Premium para usuarios normales. El acceso real usa la suscripción verificada ya existente del servidor.

- IA: selector Excel/CSV (20 MB), prioridad, consulta, alcance y presupuesto. Entrega prevista: ranking, motivos, riesgos y siguientes pasos; sin cálculos o ponderaciones internos.
- LEGAL: operación autorizada, objeto de consulta, pregunta y documentación existente del expediente. Entrega prevista: viabilidad, alternativas, recomendación y condicionantes.
- Visita a la carta: encargo a la red, información de vivienda o visita de suscriptor. Disponibilidad y permisos de acceso deben confirmarse.

## Separación de prueba y servicio real

`?demo=1&service-preview=1#ia` (también `#legal` y `#visitas`) permite al responsable revisar las interfaces sin activar una suscripción. No persiste permisos ni cambia la cuenta real. La DEMO permite seleccionar un archivo local: no lo lee, procesa, sube ni persiste. Solo mantiene la selección nativa del navegador mientras permanece abierta la vista.

Los resultados de ejemplo son fijos, explícitamente ficticios e independientes del archivo o expediente seleccionado. El flujo no marca un pago como confirmado. No simula que un motor esté conectado.

El adaptador real permite solicitar un presupuesto mediante el hilo privado existente `/api/investor/messages`, únicamente tras el acceso Premium del servidor. Envía servicio, objetivo, pregunta y OP seleccionada; no envía archivos. La carga de perímetros y la ejecución real están deshabilitadas. La confirmación dice que no se ha cobrado ni iniciado el servicio.

## Pendiente antes de activar encargos pagados

Aprobación de tarifas, impuestos, condiciones y alcance. Órdenes de servicio persistidas en servidor; presupuesto aceptado y pago individual confirmado por webhook; separación respecto de la cuota Premium; carga privada autorizada y escaneada; credenciales M2M de IA/LEGAL; contrato de resultados mínimos de cada motor; estados y entrega final en Notificaciones. El precio nunca lo decide el navegador. No se ha consultado ni modificado la base de datos de IA ni LEGAL para esta entrega visual. Las altas reales siguen pendientes de la infraestructura documentada en REAL_ACCOUNTS_SECURITY_20261014.md.

## Validación

`tests/paid-services.cjs`: flujos IA y LEGAL completos de ejemplo, archivo requerido/tipo inválido, cierre de resultados, tres interfaces en 1440/768/390 sin desbordamiento, logos decodificables, bloqueo de usuario normal, bloqueo sin Premium real, solicitud aislada del adaptador real, ausencia de muestras en real, y cero subidas/pagos/escrituras de red. Comprobación de sintaxis de los tres módulos JS modificados. Revisión visual del escritorio IA mediante captura de navegador.
