# Referidos y cartera — revisión de 13 noviembre 2026

## Evidencia revisada

- WEB privada: Render `srv-db7q9ffavr4c7396bc3g`, último despliegue live `e10ee6c2d9332e9099c69083b469a596304a878b` (11 noviembre). Esta es la base de esta rama.
- OPORTUNIIAPP: Render `srv-d8p4u6jtqb8s73fqqo20`, live `64575f178b28a796fafe0900f959f304a5d13ffb` (12 noviembre), coincide con main clonado.
- WEB pública estática: último despliegue `748e77fe2f5366850475a3199064165ff3b6996f` (7 noviembre). Su código no se ha modificado aquí.
- Se revisó código y metadatos de despliegue. No se inspeccionaron cuentas ni cobros reales ni se probó un recorrido productivo autenticado.

## Lo que ya existía

APP: `subscriber_private_referrals` es un borrador privado «vendido por mí», con estado `PENDING_WEB_SYNC`; no constituye atribución de altas ni comisión. `control_center.py` consulta una cartera WEB mediante M2M y diferencia configuración ausente o respuesta no disponible.

WEB: cuentas, verificación por correo, registro documental, Premium con adaptador Stripe condicionado a configuración, recomendaciones y relaciones aceptadas de cliente (`web_client_links`). Esta relación comercial aceptada no es equivalente al origen de captación. No se encontraron enlaces o QR universales de captación ni un libro de incentivos de referidos en las bases revisadas. El QR de segundo factor no es un QR comercial.

## Implementado en esta propuesta, sin desplegar

- Enlace opaco estable y único por cuenta WEB autenticada y verificada; QR SVG descargable. Universal para los perfiles que tengan identidad WEB válida; no crea una nueva función de autorización «agente líder».
- Página «Mis referidos» en el área real. La demo continúa separada.
- Primer enlace/QR válido durante 30 días, cookie segura y HttpOnly; evidencia persistida, caducidad comprobada en servidor. No depende de que se ejecute el borrado TTL de Mongo.
- Origen `ORGANIC`, `LINK`, `QR`, `MANUAL`, `CORRECTED`, `UNRESOLVED` o histórico `LEGACY_UNKNOWN`. Un marcador inválido no se presenta como orgánico. El canal QR describe la URL usada, no prueba que hubo un escaneo físico.
- Registro de la atribución junto al alta por formulario WEB. Un nuevo intento con el mismo correo no altera el titular ni su origen; índices únicos arbitran concurrencia.
- Corrección administrativa con sesión, CSRF y segundo factor ya existentes; motivo, actor, estado anterior, revisión y evento idempotente. Cambio e historial se guardan en una única actualización atómica. Conflictos concurrentes producen 409.
- No se admiten autorreferidos directos. Un referido no concede acceso a contactos, documentos ni permisos de cliente. Cartera propia devuelve datos mínimos y avisa si está limitada a 100 registros.
- Puente WEB para APP mediante identidad explícitamente mapeada y clave M2M. APP incluye un enlace al QR/cartera WEB; no inventa un código cuando faltan configuración o identidad.
- Función de cálculo preliminar en céntimos, sin generar derechos ni pagar dinero.

## Modelo económico preservado

1. Partner: 15% de cuotas efectivamente cobradas de suscriptores y colaboradores Premium; recurrente por cada cuota elegible, no por simples altas ni sobre todas las operaciones. El cálculo preliminar descuenta devoluciones.
2. Reconocimiento: 15% una sola vez por la primera operación cobrada de cada colaborador referido. Base interpretada como honorarios netos cobrados por OPORTUNIIA, no precio del inmueble, inversión o honorarios de terceros. El usuario confirmó el porcentaje durante esta revisión. El cálculo exige evidencia de primera operación y no devuelve un segundo reconocimiento si ya figura registrado; todavía falta la reserva persistente y atómica que garantice esto bajo concurrencia.
3. Agencias suscriptoras: ningún 5% ni otro porcentaje automático por origen. Participación activa y resultados acreditados, con condiciones por operación; hasta entonces no hay importe liquidable.

## Falta antes de afirmar que funciona de extremo a extremo

- Integrar y desplegar ambas ramas y publicar los archivos privados estáticos; comprobar la ruta pública `/api/referrals/visit/...`, cookies y redirección en el dominio real. Los cambios no están desplegados.
- Confirmar las claves existentes `WEB_OPORTUNIIAPP_CONTROL_M2M_KEY` y `OPORTUNIIAPP_WEB_CONTROL_M2M_KEY`, el destino HTTPS y los mapeos personales para suscriptores, líderes y colaboradores. No se han leído ni cambiado secretos.
- Cubrir las altas alternativas (curso, aprovisionamiento de agencia y altas administrativas), con origen explícito y sin inventar una atribución histórica. La captura automática actual cubre el formulario WEB de alta.
- Definir y guardar concesión contractual de partner y su vigencia, sin deducirla del papel de usuario. Resolver si el 15% recurrente incluye impuestos o solo cuota neta, fecha de corte, bajas y cambios de origen.
- Libro financiero persistente conectado al cobro verificado: una entrada por factura/cuota, moneda, ambiente live/test, referencias, importe cobrado y base comisionable; reintentos idempotentes, renovaciones, devoluciones parciales, disputas y reversos. No confundir retención APP del 30% con cuota elegible ni generar doble comisión por factura y pago.
- Reconocimiento único: evidencia cronológica de primera operación realmente cobrada; índice/reserva único por colaborador, incluso tras cambio de referente; importe provisional, aprobación y liquidación separados; reversos sin reabrir automáticamente el premio. Hoy solo existe el cálculo preliminar.
- Incentivos de agencia: participante, acción, evidencia, resultado, acuerdo y aprobación por operación; no heredar porcentajes de otras políticas de calidad/rappel.
- Duplicados de persona/empresa entre correos distintos: conciliación por identidad documental verificada, revisión y fusión auditada antes de comisionar. El correo y sujeto únicos no garantizan deduplicación de persona jurídica.
- Separar captador histórico, gestor de cartera vigente y participantes de cada operación. Mantener la aceptación de relación comercial ya existente, gestionar disputas y evitar cambios retroactivos de liquidaciones.
- Prueba con Mongo real aislado: carreras de creación y corrección, reinicio, reintentos y reconstrucción de historial. Prueba visual móvil/escritorio, escaneo de QR y flujo autenticado APP→WEB→alta→cobro→liquidación.

## Validación realizada

16 pruebas WEB aprobadas (5 de referidos/política y 11 de acceso existentes) con Mongo simulado; FastAPI, Starlette, Pydantic y PyMongo ajustados a versiones del servicio. 4 pruebas aisladas del puente APP aprobadas. Sintaxis JavaScript de `live.js` y `referrals.js` y `git diff --check` comprobados. No se ha realizado build completo de APP, prueba visual ni pago real. Hay avisos de deprecación de dependencias de pruebas.

La propuesta es una primera fase revisable de captación y consulta. No es un sistema completo de liquidación y no debe anunciarse como activo.
