# oportuniia-web · Manual único

Este es el punto de consulta de esta aplicación. Cada app conserva su repositorio. Los capítulos reúnen el contenido anterior sin cambiar sus decisiones, fechas ni contratos. Las afirmaciones históricas no certifican el estado actual de producción.

## Estado actual

Revisión del 21/10/2026.

Diez pruebas locales de contratos y control pasan. Vercel completó el despliegue de la nueva WEB de esta entrega, pero oportuniia.com sigue siendo la web antigua de WordPress. No se ha sustituido esa web. El icono del sitio en WordPress requiere una carga independiente del PNG oficial de 512 píxeles. Fecha de inauguración, aviso de apertura y cuenta atrás aplazados por el propietario.

Publicación: la primera entrega de iconos llegó a GitHub. Siete proyectos fueron bloqueados por Vercel porque la firma no se asociaba a un usuario GitHub; la firma de esta entrega se configura con la dirección oficial de la cuenta autenticada Oportuniia. Pendiente comprobar la aceptación de este nuevo despliegue. No se certifica el funcionamiento completo de producción hasta resolver los accesos y pruebas pendientes.

## Índice

- [README.md](MANUAL.md#doc-001)
- [docs/ARQUITECTURA_M2M_MASTER_v1.md](MANUAL.md#doc-002)
- [docs/BASE_CONTRACTUAL_FUNCIONAL_20261004.md](MANUAL.md#doc-003)
- [docs/CONTRACTUAL_MASTER_FINAL_GATE_20261005.md](MANUAL.md#doc-004)
- [docs/FINAL_CANONICAL_CONTRACT_PACKAGE_20261005.md](MANUAL.md#doc-005)
- [docs/FINAL_CONTRACT_PACKAGE_MANIFEST_20261005.md](MANUAL.md#doc-006)
- [docs/IMPLEMENTATION_CONTRACT_CORRESPONDENCE_MATRIX_20261005.md](MANUAL.md#doc-007)
- [docs/INDICE_CONTRACTUAL_OPERATIVO_20261005.md](MANUAL.md#doc-008)
- [docs/LEGALLAB_FINAL_GATE_REQUEST_20261005.md](MANUAL.md#doc-009)
- [docs/LEGALLAB_POST_IMPLEMENTATION_CORRESPONDENCE_REQUEST_20261005.md](MANUAL.md#doc-010)
- [docs/LEGAL_BLOCKERS_CLOSURE_20261004.md](MANUAL.md#doc-011)
- [docs/LEGAL_FINAL_GATE_IMPLEMENTATION_ACCEPTANCE_20261005.md](MANUAL.md#doc-012)
- [docs/LEGAL_PARTNER_SERVICE_MODEL_20261005.md](MANUAL.md#doc-013)
- [docs/M2M_TRANSPORT_MASTER_v1.md](MANUAL.md#doc-014)
- [docs/MASTER_OPERATION_MODALITIES_PBC_TRAINING_20261004.md](MANUAL.md#doc-015)
- [docs/PREMIUM_B2C_CLOSURE_20261004.md](MANUAL.md#doc-016)
- [docs/PRIVACY_OPERATIONAL_ONLY_20261004.md](MANUAL.md#doc-017)
- [docs/SECRETARIA_PBC_EXPERIENCE_MODEL_20261005.md](MANUAL.md#doc-018)
- [frontend/README.md](MANUAL.md#doc-019)

Los archivos de `memory/` son antecedentes e informes históricos. Los anexos leídos por pruebas o configuración conservan su ruta por compatibilidad; no son nuevos documentos de trabajo. El inventario y las huellas originales están en `docs/documentacion.json`.


<a id="doc-001"></a>

## README.md

<!-- BEGIN doc-001 -->
# Here are your Instructions
<!-- END doc-001 -->

<a id="doc-002"></a>

## docs/ARQUITECTURA_M2M_MASTER_v1.md

<!-- BEGIN doc-002 -->
# OPORTUNIIA · ARQUITECTURA M2M MASTER v1

**Autoridad Master:** Rafa  
**Estado:** norma obligatoria para diseño, desarrollo, adaptación y pruebas SANDBOX.  
**Producción:** NO autorizada por esta directriz.

## Principio

M2M DIRECTO es el estándar general de comunicación interna del ecosistema OPORTUNIIA. n8n no será intermediario obligatorio cuando emisor y receptor puedan comunicarse directamente con garantías iguales o mayores.

Ningún sistema actual se retira hasta que el sustituto M2M esté construido, probado y demuestre equivalencia o mejora.

## Alcance obligatorio

Toda conexión entrante y saliente entre herramientas OPORTUNIIA debe inventariar: emisor, receptor, sentido, finalidad, datos, contrato y versión, autenticación, transporte, persistencia, reintentos, idempotencia, correlation_id, payload_hash, ACK, trazabilidad, seguridad, errores, recuperación y dependencia de n8n.

Clasificación: **M2M DIRECTA / n8n / OTRA / NO IMPLEMENTADA**.

## Estándar M2M

Cada relación M2M debe disponer de:

- outbox persistente en emisor;
- inbox o registro persistente de idempotencia en receptor;
- 1 intento inicial y 5 reintentos automáticos: +5, +15, +30, +60 y +90 minutos;
- event_id único, estable e inmutable durante todos los intentos;
- correlation_id;
- payload_hash SHA-256 sobre JSON canónico UTF-8, claves ordenadas, separadores compactos, sin espacios no significativos; el campo hash queda fuera de su propio cálculo;
- payload de negocio inmutable desde el primer intento;
- ACK explícito de recepción válida;
- separación entre ACK de transporte y aprobación/estado de negocio;
- trazabilidad y recuperación automática;
- fail-closed;
- HTTPS/TLS;
- credencial específica por relación y secretos fuera del código;
- protección anti-replay;
- rate limiting cuando corresponda;
- auditoría;
- deny-by-default y need-to-know.

## Idempotencia

Mismo `event_id` + mismo `payload_hash` = mismo evento; el receptor no repite el efecto de negocio y responde ACK idempotente.

Mismo `event_id` + payload/hash diferente = **CONFLICTO**, fail-closed.

Si cambia contenido relevante se genera un nuevo `event_id`.

## ACK

HTTP 200 no equivale por sí solo a operación completada. El receptor debe devolver un ACK estructurado que vincule `event_id`, `payload_hash`, recepción y resultado de transporte. El estado de negocio viaja separado.

## Migración desde n8n

Para cualquier A → n8n → B se determinará si n8n orquesta negocio o solo transporta. Si solo aporta transporte, persistencia, reintentos, ACK, idempotencia, correlación o trazabilidad, se sustituirá por M2M directo.

Orden: construir M2M → persistencia → automatización → reintentos → idempotencia → correlación → integridad → ACK → trazabilidad → seguridad → pruebas → comparación → retirada del intermediario solo con equivalencia o mejora demostrada.

## Pruebas SANDBOX mínimas

Entrega normal; receptor caído; emisor reiniciado; receptor reiniciado; timeout; pérdida y recuperación de conexión; reintentos; duplicado; ACK perdido; evento procesado con respuesta perdida; mismo ID con payload distinto; hash incorrecto; credencial incorrecta; replay; agotamiento de reintentos; recuperación posterior.

Criterios obligatorios: **no se pierde el evento** y **no se duplica el efecto de negocio**.

## Soberanía

Ninguna herramienta accede directamente a la base de datos de otra. Cada sistema conserva BD, lógica, permisos, credenciales y autoridad. Solo se intercambia la información mínima necesaria.

## Límites

Autorizado: auditoría, diseño, desarrollo, adaptación, migración técnica, coordinación y pruebas SANDBOX.

No autorizado por esta directriz: producción, PII real no autorizada, pagos automáticos, cambios de autoridad de negocio o retirada del sistema anterior sin sustituto probado.
<!-- END doc-002 -->

<a id="doc-003"></a>

## docs/BASE_CONTRACTUAL_FUNCIONAL_20261004.md

<!-- BEGIN doc-003 -->
# OPORTUNIIA · BASE CONTRACTUAL FUNCIONAL · 2026-10-04

Estado: OFICIAL COMO BASE FUNCIONAL PARA CIERRE JURÍDICO. No sustituye la validación/redacción final de LEGAL.

## Fuente de verdad revisada
Revisión transversal de WEB, OPORTUNIIAPP, VISUAL, IA, CORE y LEGAL. Las cláusulas civiles/mercantiles deben describir prestaciones y reglas de negocio, no detalles técnicos M2M.

## Reglas que deben reflejar los contratos

### Transversales
- Área privada / MI OPORTUNIIA: documentación, operaciones, comunicaciones y trazabilidad según perfil y permisos.
- Recomendación expresa de mantener documentación identificativa, societaria, bancaria, PBC y acreditativa digitalizada, vigente y preparada.
- Cuando una operación active el protocolo documental, el plazo aplicable puede ser de 3 días / 72 horas según el circuito comunicado. La consecuencia concreta de incumplimiento debe quedar en condiciones particulares y validarse por LEGAL.
- Evidencia: distinguir documental, verbal, visual, indicio y no verificada. Una observación de campo no equivale a certificación.
- Trazabilidad digital: accesos, asignaciones, entregas, validaciones, comunicaciones y versiones pueden dejar registro técnico/auditable.
- Las herramientas tecnológicas apoyan el análisis y la operativa; no garantizan rentabilidad, adjudicación, resultado jurídico ni cierre.
- Imágenes: VISUAL puede aplicar mejoras técnicas/estéticas conservadoras (encuadre, exposición, color, enderezado, rectificación cuando proceda) sin inventar elementos ni alterar la realidad material del activo. Original y versiones deben mantener trazabilidad. Si una mejora no es fiable debe diferirse a revisión humana/no aplicarse.
- Datos y contactos: minimización, finalidad operativa y permisos; no convertir declaraciones de terceros en hechos certificados.
- Firma/aceptación electrónica y evidencias digitales sujetas al circuito aplicable.

### Inversor
- Modalidades A/B/C coherentes con WEB: compra directa; compra con acompañamiento jurídico; gestión integral, siempre según condiciones particulares.
- MI OPORTUNIIA como espacio personal de documentación y seguimiento cuando esté habilitado.
- Reserva universal OPORTUNIIA: documento frente al inversor sin revelar la identidad del proveedor/servicer; adaptación interna posterior al formulario requerido por éste y envío únicamente de los datos necesarios.
- Protocolo documental/PBC y recomendación de expediente digital preparado.
- Material visual y de campo sujeto a nivel de evidencia y a la regla de fidelidad anterior.

### Colaborador
- Modalidades A/B y reconocimiento/atribución de intervención.
- Alta y atribución de inversores con trazabilidad; conflictos de atribución no deben resolverse por apropiación automática.
- Área privada comercial separada de la documentación privada del inversor.
- Devengo económico condicionado a operación real y cobro efectivo según contrato/condiciones particulares.
- Antielusión, confidencialidad, trazabilidad y documentación/PBC.

### Suscriptor
- OPORTUNIIAPP como herramienta operativa de campo: asignaciones, visitas, informes, fotografías, notas, comunidad/ITE-IEE, estados e histórico.
- El actor queda atribuido por su identidad autenticada; acceso solo a recursos asignados.
- Calidad: Quality Score/Quality Star versionados y revisables. La Quality Star no debe confundirse con una certificación del activo.
- Regla comercial Quality Star → rappel v2 ÚNICA VIGENTE: revisión semestral; umbral >=3,75/5; variación de +0,5 puntos por semestre completo favorable y -0,5 por semestre completo desfavorable; primer periodo proporcional con mínimo de 3 meses computables; reversibilidad; suelo 5%; techo 10%; al alcanzar el techo, venta de crédito con reparto 60% suscriptor / 40% OPORTUNIIA. Las variaciones producen efectos hacia futuro desde su comunicación. Queda retirada la fórmula v1.
- Protocolo de 3 días para documentación/PBC cuando el circuito de venta propia lo active.
- Incidencias, avisos, suspensión/desactivación y consecuencias por falta de diligencia: la APP ya conserva evidencia operativa, pero NO existe en repos una escala contractual automática de penalizaciones. LEGAL debe definir proporcionalidad, preaviso, subsanación, reincidencia y efectos económicos antes de convertirlo en sanción.
- Fotos/informes: origen, evidencia y trazabilidad; VISUAL puede mejorar presentación sin falsear hechos.

### PREMIUM
- Precio aprobado de negocio: 1.000 EUR/mes + impuestos. Doce mensualidades = 12.000 EUR/año + impuestos.
- Modalidad anual anticipada: 10.000 EUR/año + impuestos. Ahorro frente a 12 mensualidades: 2.000 EUR, equivalente a 2 mensualidades y 16,67%.
- Debe mostrarse de forma destacada en contrato y WEB.
- Prestaciones a consolidar: Universo Acuerdos para perfiles autorizados; perímetros personalizados/actualizados; screening avanzado; peticiones a la carta; documentación/reportajes ampliados; MI OPORTUNIIA y organización documental; recordatorios; motor IA; apoyo LEGAL cuando proceda; Secretaría MI OPORTUNIIA; preparación/coordinación ágil de ofertas y reservas; solicitudes de visita/comprobación de campo cuando estén disponibles y autorizadas.
- Distinguir siempre incluido / bajo petición / sujeto a disponibilidad, autorización o viabilidad. No prometer resultado.

## Puntos que NO deben cerrarse sin LEGAL
1. Régimen de incidencias, avisos, suspensión y resolución del suscriptor: debe existir evidencia, notificación, alegación/subsanación razonable y decisión trazable; no pérdida automática de derechos económicos ya devengados.
2. Consecuencias exactas del incumplimiento del plazo 72h y régimen de pérdida/devolución de reservas.
3. Redacción de atribución/conflictos de inversores aportados.
4. Encaje contractual definitivo del rappel Quality Star y transición desde porcentajes históricos.
5. Régimen de cancelación/no devolución de PREMIUM anual y derechos imperativos aplicables.
6. Texto de información a terceros/contactos: OPORTUNIIAPP mantiene esta activación cerrada hasta aprobación legal.
7. Alcance de acompañamiento LEGAL para evitar confundir apoyo/revisión con representación o garantía de resultado.

## Hallazgo WEB
La WEB main revisada contiene beneficios Premium, pero todavía no publica el precio 1.000/10.000/12.000 ni todas las prestaciones consolidadas (MI OPORTUNIIA, Secretaría, IA, LEGAL, visitas y ahorro anual). Por tanto, no debe afirmarse que WEB y contrato están todavía totalmente sincronizados hasta aplicar esa actualización.

## Criterio de cierre
Esta matriz es la base funcional oficial a fecha 2026-10-04. Si después de esta fecha se aprueba una nueva regla de negocio material, deberá abrirse nueva revisión contractual antes de considerarla vigente.
\n\n## GATE LEGAL 04/10/2026\nLEGALLAB: APTO CON CORRECCIONES. Fuente: `docs/LEGAL_CONTRACTUAL_REVIEW_20261004.md` del repositorio `Oportuniia/oportuniia-legal-lab`, commit `9886fb120e9cd6ca9c7789e37e89f55c2384a8b6`. Quality v1 queda expresamente retirada de esta base. Producción seguirá cerrada para los gates condicionados hasta prueba técnica y GATE FINAL CONTRACTUAL.\n
<!-- END doc-003 -->

<a id="doc-004"></a>

## docs/CONTRACTUAL_MASTER_FINAL_GATE_20261005.md

<!-- BEGIN doc-004 -->
# OPORTUNIIA · CONSOLIDACIÓN CONTRACTUAL MASTER · GATE FINAL
Fecha: 05/10/2026
Autoridad de negocio: RAFA
Estado: CANDIDATO A GATE FINAL LEGALLAB · NO PRODUCCIÓN

## 1. Regla de prevalencia
Este documento consolida las decisiones de negocio y criterios legales/técnicos aprobados para regenerar y revisar el paquete contractual. Si una plantilla anterior contradice este documento, debe actualizarse antes de producción.

## 2. Modalidades por operación del inversor
El inversor NO elige A/B/C/D al registrarse. Elige una modalidad independientemente en cada reserva/operación.
A = compra/operación.
B = compra + servicio jurídico facilitado por OPORTUNIIA mediante despacho/profesional externo independiente.
C = compra + comercialización/compraventa posterior gestionada por equipo OPORTUNIIA.
D = integral: compra + servicio jurídico externo + comercialización/compraventa posterior OPORTUNIIA.
La modalidad queda vinculada a la operación, no al perfil permanente del inversor.

## 3. Colaborador
La modalidad A/B propia del colaborador es un concepto distinto de A/B/C/D de la operación del inversor y debe usar nomenclatura/campo separado. Las reglas económicas internas de premios por volumen no se convierten automáticamente en derecho contractual externo.

## 4. Servicio jurídico
OPORTUNIIA no presta abogacía como despacho ni emplea abogados internos para asumir el asunto. En B/D facilita acceso a profesionales/despachos externos independientes. La relación profesional, encargo, conflicto, alcance, honorarios y responsabilidad profesional corresponden al cliente y al profesional/despacho elegido. OPORTUNIIA conserva la responsabilidad legalmente atribuible por sus propios actos.
La negociación interna de precios por volumen y eventuales rappels/comisiones futuras NO se promete al cliente ni se incorpora como regla económica externa. Cualquier futura remuneración por referral/derivación requiere revisión LEGALLAB previa.

## 5. Comercialización posterior
En C/D la comercialización posterior es servicio operativo OPORTUNIIA, ejecutable mediante suscriptores/equipo asignado. Es una misión posterior e independiente, con aceptación, alcance, evidencias y trazabilidad propias.

## 6. PBC/Compliance y Secretaría
TODAS las operaciones A/B/C/D requieren expediente documental vigente + Gate PBC/Compliance CLEARED antes de avanzar.
El expediente se adapta a PF/PJ, estructura jurídica/económica, jurisdicción y operación. Distingue identidad, representación, titularidad real, origen de fondos, PBC/FT y capacidad/viabilidad financiera.
Secretaría ayuda a digitalizar, mantener, actualizar y subsanar el expediente. Su aprendizaje de expedientes reales puede recomendar formatos/documentos según servicer, estructura y operación, pero es advisory only: no elimina requisitos, no rebaja controles, no pone CLEARED y no garantiza aceptación.

## 7. Premium
Mensual: 1.000 EUR + impuestos/mes, sin permanencia; meses no necesariamente consecutivos.
Anual: 10.000 EUR + impuestos, prepago voluntario por exactamente 12 meses desde activación/contratación; ahorro de 2.000 EUR frente a 12 mensualidades. No termina el 31 de diciembre ni se renueva obligatoriamente.
En B2C: información precontractual, desistimiento cuando proceda, ejecución anticipada cuando proceda, pago proporcional cuando proceda, aceptación inequívoca de obligación de pago y copia/evidencia contractual. No usar exclusión absoluta de reembolso contra derechos imperativos.

## 8. Contratación electrónica
Versionado estable, hash de contenido, información/copia precontractual, casilla no premarcada, aceptación expresa, identidad, canal, fecha/hora, evidencia de entrega/acuse e histórico inmutable. En B2C, confirmación inequívoca de obligación de pago cuando corresponda.

## 9. Suscriptor · relación mercantil
Relación civil/mercantil, acceso voluntario a misiones; aceptada una misión nacen obligaciones contractuales. Usar: incidencia contractual, aviso de incumplimiento, requerimiento de subsanación, suspensión de acceso, resolución contractual, terminación de suscripción, exclusión de plataforma. Evitar terminología laboral disciplinaria.
TRADE se trata individualmente: autonomía, no exclusividad, comunicación/revisión de posible dependencia económica y sin renuncia de derechos.

## 10. Quality / Rappel v2
Revisión semestral objetivo 15 junio / 15 diciembre. Umbral 3,75/5 (75%). Semestre completo favorable +0,5; desfavorable -0,5. Primer periodo proporcional con mínimo 3 meses computables: 3m ±0,25; 4m ±0,33; 5m ±0,42; 6m ±0,50. Reversible; suelo 5%, techo 10%; efectos futuros desde comunicación. En techo, monetización/venta de crédito: 60% suscriptor / 40% OPORTUNIIA. Quality v1 queda retirada.

## 11. GEO y evidencia de visita
Captura exclusivamente puntual durante uso de la app y vinculada a misión; nunca tracking permanente, segundo plano, reconstrucción de rutas ni control de jornada.
Antes de aceptar evidencia: misión existente, activa, asignada al suscriptor y evento permitido.
Radio ordinario: 100 m. Fuera de radio no equivale a incumplimiento: requiere evidencia/revisión.
La prueba visual principal se captura desde la cámara integrada de OPORTUNIIAPP, no desde galería: vinculada a misión/usuario, sello temporal de servidor, hash, coordenadas y precisión cuando estén disponibles. Puede usarse reto de captura de servidor. Sin GPS válido, la fotografía/evidencia alternativa puede acreditar la visita y queda marcada para la lógica de revisión.
La evidencia se archiva con el expediente durante el régimen de conservación aplicable al propio expediente, con acceso restringido y trazabilidad.

## 12. Privacidad
Uso de datos OPORTUNIIA exclusivamente para finalidades operativas/contractuales/legales/compliance correspondientes. No marketing ni comunicaciones comerciales bajo este sistema.

## 13. Quality, PBC, GEO y reglas internas
No trasladar a contratos externos secretos operativos innecesarios, heurísticas de Secretaría, negociación con despachos, economics internos de volumen ni lógica antifraude detallada. Sí deben constar las obligaciones, finalidades, tratamientos, responsabilidades, consecuencias contractuales y derechos que legalmente deban informarse.

## 14. Condición de producción
Ningún merge/deploy/apertura de válvula se autoriza por este documento. Antes de producción:
1) regenerar/actualizar todas las plantillas afectadas;
2) revisar coherencia cruzada;
3) LEGALLAB debe emitir GATE FINAL CONTRACTUAL;
4) resolver únicamente correcciones concretas;
5) autorización expresa de RAFA para producción.


## 15. GATE FINAL LEGALLAB · APTO CON CORRECCIONES
Dictamen LEGALLAB de 05/10/2026: el modelo completo es jurídicamente implementable y no requiere cambios de negocio. Las siguientes cuatro correcciones son obligatorias en implementación:

### 15.1 PBC propio cuando OPORTUNIIA sea sujeto obligado
Cuando OPORTUNIIA actúe materialmente como agencia, comisión o intermediación profesional en compraventa inmobiliaria y resulte sujeto obligado conforme a la normativa PBC/FT aplicable, debe ejecutar y acreditar sus propias obligaciones PBC. Un CLEARED de servicer/tercero no sustituye el cumplimiento propio de OPORTUNIIA. El Gate universal existente se mantiene y debe distinguir soberanía/origen del CLEARED y obligaciones propias/terceras.

### 15.2 Gate territorial de intermediación inmobiliaria
Antes de activar comercialización/intermediación C/D en una comunidad autónoma, Compliance debe verificar y registrar los requisitos territoriales aplicables: registros, habilitaciones, garantías, seguros, información u otros requisitos exigibles. Estado por territorio: PENDING_REVIEW / CLEARED / BLOCKED. Sin CLEARED territorial no se activa la actividad afectada en ese territorio.

### 15.3 Secretaría · aprendizaje privacy-preserving
El aprendizaje histórico de Secretaría sigue ADVISORY ONLY. Para patrones, métricas y recomendaciones se usarán preferentemente datos anonimizados/agregados. La seudonimización no convierte los datos en anónimos y, cuando se usen datos personales seudonimizados, siguen sujetos al RGPD y a finalidad, minimización, acceso y retención aplicables. Ningún patrón puede identificar innecesariamente a una persona ni sustituir el Gate Compliance.

### 15.4 Retención por categoría
La evidencia puede permanecer vinculada al expediente, pero no existe una regla única de conservación eterna para todo su contenido. Cada categoría documental/dato tendrá retention_policy_code, finalidad/base y plazo jurídicamente justificable. La documentación PBC se someterá a su régimen específico aplicable (incluido el plazo legal de 10 años cuando corresponda). Fotos y coordenadas conservarán sólo el plazo justificable por su finalidad contractual/probatoria/legal, sin heredar automáticamente el plazo PBC. Al vencer: supresión, anonimización o bloqueo cuando jurídicamente proceda.

## 16. Estado del diseño
GATE FINAL CONTRACTUAL = APTO CON CORRECCIONES / MODELO APROBADO PARA IMPLEMENTACIÓN.
Las cuatro correcciones anteriores son requisitos de implementación, no reapertura del modelo comercial.
PRODUCCIÓN = NO AUTORIZADA.
<!-- END doc-004 -->

<a id="doc-005"></a>

## docs/FINAL_CANONICAL_CONTRACT_PACKAGE_20261005.md

<!-- BEGIN doc-005 -->
# OPORTUNIIA · PAQUETE CONTRACTUAL CANÓNICO v2026-10-05
Estado: CANDIDATO FINAL POST-IMPLEMENTACIÓN · REQUIERE VALIDACIÓN LEGALLAB ANTES DE PRODUCCIÓN
Autoridad de negocio: RAFA
Prevalencia: CONTRACTUAL_MASTER_FINAL_GATE_20261005 + LEGAL_FINAL_GATE_IMPLEMENTATION_ACCEPTANCE_20261005 + IMPLEMENTATION_CONTRACT_CORRESPONDENCE_MATRIX_20261005

> Este documento es la fuente textual consolidada para regenerar plantillas. Los datos identificativos, fiscales, domicilios, jurisdicción concreta, importes variables y anexos particulares se completarán en la plantilla/operación correspondiente. No activar en producción sin validación final.

# I · CONDICIONES MARCO DEL INVERSOR

## 1. Objeto y acceso
OPORTUNIIA facilita al inversor acceso a oportunidades y servicios asociados. Cada reserva u operación constituye una relación identificable y trazable. La disponibilidad, condiciones económicas, riesgos, plazos y documentación particular de cada activo se informarán en su expediente.

## 2. Modalidad elegida por operación
El inversor elige separadamente para cada operación una modalidad:
A: compra/operación.
B: compra/operación + acceso a servicio jurídico prestado por profesional o despacho externo e independiente.
C: compra/operación + servicio posterior de comercialización/compraventa organizado por OPORTUNIIA.
D: combinación de B y C.
La elección no crea una modalidad permanente en el perfil del inversor y puede ser distinta en operaciones futuras.

## 3. Gate documental y PBC/Compliance
Ninguna operación avanza mientras el expediente documental exigible no esté vigente y el Gate PBC/Compliance aplicable no conste CLEARED. El expediente puede adaptarse a persona física o jurídica, estructura, jurisdicción, operación, titularidad real, representación, origen de fondos y demás circunstancias relevantes.
Cuando OPORTUNIIA resulte sujeto obligado por la actividad materialmente desarrollada, realizará y acreditará sus propias obligaciones PBC/FT. La validación de un servicer, despacho u otro tercero no sustituye el cumplimiento propio que legalmente corresponda a OPORTUNIIA.

## 4. Territorialidad
Cuando la modalidad o servicio implique intermediación o comercialización inmobiliaria sujeta a requisitos territoriales, su activación queda condicionada a que OPORTUNIIA haya verificado y marcado como CLEARED los requisitos aplicables en el territorio correspondiente. Si el estado es PENDING_REVIEW o BLOCKED, la actividad afectada no se inicia.

## 5. Servicio jurídico B/D
OPORTUNIIA no actúa como despacho de abogados. En B/D facilita acceso y coordinación con un abogado o despacho externo e independiente. Antes de la prestación deberán quedar definidos, según proceda, profesional/despacho, comprobación de conflicto, encargo, alcance, honorarios y expediente profesional.
La independencia técnica, secreto y responsabilidad profesional corresponden al profesional/despacho conforme a su encargo y normativa. OPORTUNIIA mantiene las responsabilidades legalmente atribuibles por sus propios actos, información, sistemas y servicios.

## 6. Comercialización posterior C/D
La comercialización posterior es un servicio operativo diferenciado de OPORTUNIIA. Su inicio, alcance, precio/condiciones cuando proceda, misión operativa, evidencias y terminación se documentarán separadamente. No forma parte del encargo jurídico salvo pacto expreso.

# II · SUSCRIPTOR / COLABORADOR

## 7. Naturaleza de la relación
La relación del suscriptor es civil/mercantil. El acceso a misiones es voluntario; aceptada una misión nacen las obligaciones contractuales de ejecución, evidencia y diligencia correspondientes. No se establece por estas condiciones una relación laboral ni un sistema de control de jornada.
Los supuestos TRADE se analizarán individualmente conforme a sus circunstancias, sin renuncia de derechos imperativos.

## 8. Incidencias contractuales
Ante incumplimientos podrán utilizarse, según gravedad y contrato: incidencia contractual, aviso, requerimiento de subsanación, suspensión de acceso, resolución contractual, terminación de suscripción o exclusión de plataforma. Las consecuencias económicas devengadas se resolverán conforme al contrato y la ley aplicable.

## 9. Colaborador A/B
La clasificación A/B propia del colaborador es independiente de las modalidades A/B/C/D elegidas por el inversor para cada operación. Nunca deben compartirse como un mismo campo, derecho o categoría contractual.

## 10. Quality / Rappel v2
Cuando resulte aplicable al suscriptor, la revisión objetivo será semestral, 15 de junio y 15 de diciembre, con umbral 3,75/5. Semestre completo favorable: +0,5 puntos; desfavorable: -0,5. Primer periodo, mínimo tres meses computables: 3 meses ±0,25; 4 ±0,33; 5 ±0,42; 6 ±0,50. Sistema reversible, suelo 5% y techo 10%, con efectos futuros desde comunicación. En techo, cuando resulte aplicable la monetización/venta del crédito reconocido, distribución 60% suscriptor / 40% OPORTUNIIA. La versión v1 queda sin efecto.

# III · MISIONES, GEO Y EVIDENCIA

## 11. Geolocalización
La localización se captura puntualmente durante acciones de misión en OPORTUNIIAPP. No se utiliza este sistema para seguimiento permanente, segundo plano, reconstrucción de rutas ni control de jornada.
La evidencia se vincula a misión existente, activa y asignada. El radio ordinario de referencia es 100 metros. Estar fuera del radio, carecer de GPS o disponer de precisión insuficiente no acredita automáticamente incumplimiento: genera revisión de evidencia.

## 12. Evidencia fotográfica
La evidencia visual primaria de visita se captura mediante la cámara integrada de OPORTUNIIAPP y se vincula a misión, usuario, sello temporal de servidor, hash y, cuando estén disponibles, coordenadas y precisión. La ausencia de GPS puede suplirse mediante evidencia coherente sujeta a revisión. Se evitará captar innecesariamente personas o interiores.

# IV · SECRETARÍA, PRIVACIDAD Y CONSERVACIÓN

## 13. Secretaría
Secretaría puede asistir en digitalización, actualización, subsanación y preparación documental. Sus patrones y recomendaciones son exclusivamente orientativos: no sustituyen requisitos obligatorios, no conceden CLEARED y no garantizan aceptación por servicers, entidades, profesionales o autoridades.
Para aprendizaje y métricas se preferirán datos anonimizados/agregados. Los datos seudonimizados siguen siendo datos personales y quedan sujetos a la normativa aplicable.

## 14. Finalidad y privacidad
Los datos tratados bajo estos flujos se utilizan para finalidades operativas, contractuales, probatorias, legales y de compliance correspondientes. Este sistema no habilita por sí mismo marketing ni comunicaciones comerciales.

## 15. Conservación
Cada categoría documental o dato queda asociada a una política de conservación basada en finalidad y fundamento aplicable. La documentación PBC se conserva conforme a su régimen legal específico, incluido el plazo de diez años cuando resulte aplicable. Fotografías y coordenadas no heredan automáticamente ese plazo y se conservarán sólo durante el periodo jurídicamente justificable para su finalidad. Al vencimiento procederá supresión, anonimización o bloqueo cuando corresponda.

# V · PREMIUM

## 16. Modalidades económicas
Premium mensual: 1.000 EUR más impuestos aplicables por mes activado, sin permanencia obligatoria; pueden existir meses no consecutivos.
Premium anual: 10.000 EUR más impuestos aplicables, prepago voluntario por exactamente doce meses desde la activación, equivalente a un ahorro de 2.000 EUR respecto de doce mensualidades. No finaliza por año natural ni incorpora renovación obligatoria.

## 17. Consumidores
Cuando el contratante tenga condición de consumidor se facilitará la información precontractual exigible, régimen de desistimiento cuando proceda, reglas de ejecución anticipada y pago proporcional cuando procedan, y confirmación inequívoca de la obligación de pago. Ninguna cláusula limita derechos imperativos de reembolso, desistimiento o garantía.

# VI · CONTRATACIÓN ELECTRÓNICA

## 18. Evidencia
La contratación electrónica conserva versión exacta, hash, identidad, canal, fecha/hora, información y copia precontractual, aceptación expresa mediante control no premarcado, copia posterior, acuse y trazabilidad inmutable. Cuando corresponda a consumidor, la aceptación incluye confirmación inequívoca de obligación de pago.

# VII · REGLAS GENERALES

## 19. Información particular y prevalencia
Las condiciones particulares de cada operación, servicio o misión prevalecerán sobre estas condiciones marco en aquello que concreten válidamente, sin contradecir normas imperativas. Las reglas internas de antifraude, heurísticas, negociación con despachos, economics internos y sistemas técnicos no forman parte de promesas contractuales salvo incorporación expresa.

## 20. Responsabilidad
Cada parte responde conforme a las obligaciones asumidas y a la normativa aplicable. No se establece una exoneración absoluta de OPORTUNIIA ni del profesional externo respecto de responsabilidades que legalmente les correspondan.

## 21. Vigencia documental
Sólo la versión publicada y aceptada con su hash y evidencia electrónica será oponible como versión contractual concreta. Plantillas históricas, Quality v1 y documentos marcados como superados no deberán utilizarse para nuevas contrataciones.

# VIII · ANEXOS A MATERIALIZAR EN PLANTILLAS SEPARADAS
A. Ficha/condiciones particulares de operación y modalidad A/B/C/D.
B. Información/aceptación de partner jurídico B/D y referencia a hoja de encargo independiente.
C. Condiciones particulares de comercialización C/D.
D. Checklist/estado documental y comunicaciones PBC/Compliance, sin revelar heurísticas internas.
E. Información privacidad GEO/foto y política de conservación aplicable.
F. Premium + información precontractual B2C.
G. Evidencia de contratación electrónica.
H. Suscriptor/colaborador + Quality/Rappel v2 cuando proceda.
<!-- END doc-005 -->

<a id="doc-006"></a>

## docs/FINAL_CONTRACT_PACKAGE_MANIFEST_20261005.md

<!-- BEGIN doc-006 -->
# OPORTUNIIA · MANIFIESTO DE PAQUETE CONTRACTUAL FINAL
Fecha: 05/10/2026
Estado: PREPARADO PARA REGENERACIÓN Y REVISIÓN LEGALLAB

Fuente normativa interna de consolidación:
- docs/CONTRACTUAL_MASTER_FINAL_GATE_20261005.md
- docs/LEGAL_PARTNER_SERVICE_MODEL_20261005.md
- docs/MASTER_OPERATION_MODALITIES_PBC_TRAINING_20261004.md
- docs/SECRETARIA_PBC_EXPERIENCE_MODEL_20261005.md
- docs/PREMIUM_B2C_CLOSURE_20261004.md (WEB)
- docs/PRIVACY_OPERATIONAL_ONLY_20261004.md (WEB)
- cierre LEGALLAB 04/10/2026 y Quality/Rappel v2 aprobada.

Documentos/relaciones que deben quedar cubiertos por el paquete:
1. Suscripción / relación mercantil del suscriptor.
2. Inversor directo / condiciones de acceso y operación.
3. Colaborador / modelo de colaboración.
4. Reconocimiento/atribución colaborador-inversor cuando corresponda.
5. Condiciones Premium y precontractual B2C.
6. Condiciones por operación A/B/C/D.
7. Anexo/condiciones de servicio jurídico externo para B/D.
8. Condiciones de comercialización posterior OPORTUNIIA para C/D.
9. PBC/Compliance + Secretaría + expediente documental.
10. Privacidad operacional y evidencia GEO/fotográfica.
11. Evidencias de contratación electrónica.

Controles de coherencia obligatorios:
- A/B de colaborador nunca se confunde con A/B/C/D de operación.
- A/B/C/D nunca se fija permanentemente en perfil de inversor.
- PBC/Compliance es gate universal de operación.
- OPORTUNIIA no se presenta como despacho de abogados.
- No se promete al cliente economía interna con despachos.
- C/D comercialización posterior = OPORTUNIIA.
- Quality v1 no puede sobrevivir en ninguna plantilla.
- No marketing/comercial en privacidad.
- GEO nunca se redacta como tracking laboral.
- No exclusiones absolutas de derechos B2C.
- Evidencia electrónica identifica versión exacta aceptada.

Resultado esperado de LEGALLAB:
APTO PARA PRODUCCIÓN, o lista cerrada de correcciones textuales/documentales concretas.
<!-- END doc-006 -->

<a id="doc-007"></a>

## docs/IMPLEMENTATION_CONTRACT_CORRESPONDENCE_MATRIX_20261005.md

<!-- BEGIN doc-007 -->
# OPORTUNIIA · MATRIZ DE CORRESPONDENCIA FINAL · 2026-10-05
Estado: IMPLEMENTACIÓN EN RAMA · PRODUCCIÓN CERRADA

| Decisión aprobada | Implementación soberana | Consumidores | Verificación / contrato |
|---|---|---|---|
| Inversor A/B/C/D por operación | APP /operations/service-modality | WEB, CORE, IA, UI | operation_id + investor_id; nunca perfil permanente |
| Colaborador A/B separado | namespace contractual separado | CORE/IA/UI | no reutilizar campo modality de operación |
| Expediente vigente universal | APP /pbc/document-profile + checklist | WEB vía readiness | mandatory_documents_current |
| PBC universal | APP /pbc | WEB vía readiness | CURRENT + CLEARED |
| PBC propio OPORTUNIIA si obligado | APP PbcGate oportuniia_is_obliged_entity / own_status | WEB | tercero no sustituye own CLEARED |
| Gate territorial C/D | APP /territorial-compliance | WEB vía readiness | C/D bloqueado sin CLEARED |
| Secretaría PF/PJ adaptativa | APP /pbc/document-checklist | Secretaría/UI/IA | PF/PJ + legal_structure |
| Aprendizaje Secretaría | APP experience/pattern | Secretaría/IA | ADVISORY ONLY; preferir anonimizado/agregado |
| Legal externo B/D | APP /operations/legal-partner-matter | WEB/operaciones | cliente-despacho; conflicto+encargo+alcance+fees |
| Comercialización C/D | APP modality flags + territorial gate | operaciones | servicio OPORTUNIIA, no despacho externo |
| GEO puntual | APP /missions/check-in | OPORTUNIIAPP | misión real/activa/asignada; 100m; fuera=review |
| Foto visita | APP /missions/visit-evidence | OPORTUNIIAPP | IN_APP_CAMERA + hash + server timestamp |
| Retención por categoría | APP /retention-policies | todos los archivos/evidencias | PBC no extiende automáticamente GEO/foto |
| Quality/Rappel v2 | APP quality_rappel.py | CORE/IA/reporting | 3.75; 15/06,15/12; 3=.25,4=.33,5=.42,6=.50; floor5 cap10 |
| Premium | WEB /premium | contratación/pagos futuro | 1000 mensual; 10000 anual; 12 meses activación |
| Privacidad | APP operational-only preference | WEB/CORE/IA | sin marketing/commercial purpose |
| Contratación electrónica | APP contracts publish/accept | WEB/APP | version+hash+preinfo+copies+ack+explicit acceptance |
| B2C obligación pago | APP accept gate + WEB checkout UX | WEB | consumer_applicable exige payment_obligation_confirmed |
| Readiness único | APP /pbc/operation-readiness | WEB /operations/readiness-sync | fail closed; WEB no fabrica CLEARED |

## Regla de prevalencia
LEGALLAB Final Gate + CONTRACTUAL_MASTER_FINAL_GATE_20261005 prevalecen sobre documentación legacy. CORE/IA/Presentación/Visual no pueden redefinir estados soberanos.

## Condición antes de contratos definitivos
1. P0 APP verde en head con cambios finales.
2. WEB conserva fail-closed y sincronización autoritativa.
3. Contratos reflejan esta matriz sin prometer reglas internas.
4. Validación de correspondencia posterior a generación.
5. Sin merge/deploy/producción hasta autorización expresa de RAFA.
<!-- END doc-007 -->

<a id="doc-008"></a>

## docs/INDICE_CONTRACTUAL_OPERATIVO_20261005.md

<!-- BEGIN doc-008 -->
# OPORTUNIIA · ÍNDICE CONTRACTUAL OPERATIVO · 2026-10-05
Estado: aprobado para instauración por MASTER.

## Regla general
Cada aceptación debe conservar documento, versión, huella, identidad, fecha/hora y evidencia de entrega/aceptación. Las versiones históricas no se sobrescriben.

## Índice
1. CONDICIONES MARCO INVERSOR — alta/relación general del inversor y MI OPORTUNIIA.
2. CONDICIONES PARTICULARES OPERACIÓN A/B/C/D — por cada operación; modalidad elegida por operación.
3. ANEXO SERVICIO JURÍDICO B/D — sólo operaciones B o D y sujeto a aceptación profesional.
4. COMERCIALIZACIÓN POSTERIOR C/D — sólo operaciones C o D.
5. SUSCRIPTOR/COLABORADOR QUALITY V2 — alta y relación operativa/económica del suscriptor-colaborador.
6. PBC/SECRETARÍA/PRIVACIDAD/RETENCIÓN — expediente y circuitos donde proceda.
7. PREMIUM B2C — antes de contratar/pagar Premium mensual o anual.
8. EVIDENCIA CONTRATACIÓN ELECTRÓNICA — registro probatorio asociado automáticamente a cada aceptación.
9. CERTIFICADO CORRESPONDENCIA LEGALLAB PASS — interno/auditoría, no documento de aceptación ordinaria del cliente.

## Modalidad inversor
A = Compra.
B = Compra + servicio jurídico.
C = Compra + comercialización posterior OPORTUNIIA.
D = Integral: compra + servicio jurídico + comercialización posterior.

La modalidad A/B/C/D pertenece a la operación, no al perfil permanente del inversor. La clasificación A/B del colaborador es independiente.
<!-- END doc-008 -->

<a id="doc-009"></a>

## docs/LEGALLAB_FINAL_GATE_REQUEST_20261005.md

<!-- BEGIN doc-009 -->
# OPORTUNIIA · SOLICITUD GATE FINAL CONTRACTUAL
AUTORIDAD: RAFA
FECHA: 05/10/2026

LEGALLAB debe revisar el ecosistema contractual completo conforme a:
- docs/CONTRACTUAL_MASTER_FINAL_GATE_20261005.md
- docs/FINAL_CONTRACT_PACKAGE_MANIFEST_20261005.md
- docs/LEGAL_PARTNER_SERVICE_MODEL_20261005.md
- docs/MASTER_OPERATION_MODALITIES_PBC_TRAINING_20261004.md
- docs/SECRETARIA_PBC_EXPERIENCE_MODEL_20261005.md
- docs/PREMIUM_B2C_CLOSURE_20261004.md
- docs/PRIVACY_OPERATIONAL_ONLY_20261004.md
- cierre previo LEGALLAB 04/10/2026.

OBJETIVO:
Emitir GATE FINAL CONTRACTUAL del sistema completo, no una revisión aislada.

VALIDAR expresamente:
1. modelo mercantil del suscriptor y TRADE;
2. Quality/Rappel v2;
3. contratación electrónica;
4. Premium mensual/anual y B2C;
5. modalidades A/B/C/D por operación;
6. despacho/profesional externo independiente B/D;
7. comercialización posterior OPORTUNIIA C/D;
8. PBC/Compliance universal + Secretaría + expediente PF/PJ adaptativo;
9. aprendizaje de Secretaría sólo advisory;
10. privacidad exclusivamente operacional;
11. GEO puntual + fotografía/cámara app + evidencia de visita;
12. conservación de la evidencia GEO/fotográfica bajo el régimen de conservación aplicable al expediente;
13. coherencia de responsabilidades, información al usuario y derechos imperativos.

CRITERIO GEO CERRADO DE NEGOCIO:
- no tracking;
- captura puntual;
- radio ordinario 100 m;
- fuera de radio = revisión/evidencia, no incumplimiento automático;
- fotografía principal capturada en OPORTUNIIAPP, vinculada a misión, usuario, sello temporal y hash;
- coordenadas/precisión cuando estén disponibles;
- ausencia/fallo GPS puede suplirse con evidencia visual suficiente;
- archivo junto al expediente durante el régimen de conservación que legalmente corresponda.

SALIDA REQUERIDA:
A) APTO PARA PRODUCCIÓN; o
B) APTO CON CORRECCIONES, enumerando exclusivamente cada corrección concreta, documento/cláusula afectada y texto/criterio de sustitución; o
C) NO APTO, identificando bloqueo legal real y solución requerida.

No reabrir decisiones comerciales ya cerradas salvo incompatibilidad jurídica concreta y motivada.
<!-- END doc-009 -->

<a id="doc-010"></a>

## docs/LEGALLAB_POST_IMPLEMENTATION_CORRESPONDENCE_REQUEST_20261005.md

<!-- BEGIN doc-010 -->
# OPORTUNIIA · SOLICITUD LEGALLAB · VALIDACIÓN FINAL DE CORRESPONDENCIA POST-IMPLEMENTACIÓN
Fecha: 05/10/2026
Autoridad: RAFA
Estado: SOLICITUD DE REVISIÓN · NO PRODUCCIÓN

LEGALLAB debe revisar exclusivamente la correspondencia jurídica/documental del paquete canónico post-implementación, sin reabrir decisiones comerciales ya aprobadas salvo incompatibilidad legal real.

## Fuentes obligatorias
- docs/LEGAL_FINAL_CONTRACTUAL_GATE_20261005.md (dictamen APTO CON CORRECCIONES, rama LEGALLAB)
- docs/CONTRACTUAL_MASTER_FINAL_GATE_20261005.md
- docs/IMPLEMENTATION_CONTRACT_CORRESPONDENCE_MATRIX_20261005.md
- docs/FINAL_CANONICAL_CONTRACT_PACKAGE_20261005.md
- docs/LEGAL_PARTNER_SERVICE_MODEL_20261005.md
- docs/FINAL_CONTRACT_PACKAGE_MANIFEST_20261005.md

## Confirmar expresamente
1. Las cuatro correcciones del Gate Final están correctamente trasladadas al paquete canónico: PBC propio; gate territorial; Secretaría privacy-preserving; retención por categoría.
2. A/B/C/D por operación, y separación del A/B colaborador.
3. B/D = profesional/despacho externo independiente; C/D = servicio operativo OPORTUNIIA.
4. PBC/Compliance universal y documentación vigente antes de avance.
5. GEO puntual, 100 m como referencia/revisión y fotografía in-app sin tracking.
6. Quality/Rappel v2 exacto.
7. Premium 1.000 mensual / 10.000 anual por 12 meses desde activación, sin renovación obligatoria, con salvaguardas B2C.
8. Contratación electrónica y obligación de pago B2C.
9. Ausencia de exoneraciones absolutas y de promesas externas sobre economics internos.
10. Que el texto canónico sea apto como fuente para generar plantillas DOCX finales.

## Respuesta requerida
Uno de:
- APTO PARA GENERACIÓN DOCUMENTAL FINAL
- APTO CON CORRECCIONES TEXTUALES CERRADAS
- BLOQUEADO, indicando incompatibilidad jurídica concreta

Si hay correcciones, devolver texto sustitutorio exacto y documento/sección afectada. No proponer cambios funcionales si no son jurídicamente imprescindibles.

PRODUCCIÓN = NO AUTORIZADA.
<!-- END doc-010 -->

<a id="doc-011"></a>

## docs/LEGAL_BLOCKERS_CLOSURE_20261004.md

<!-- BEGIN doc-011 -->
# CIERRE DE BLOQUEOS LEGALLAB · 2026-10-04

Fuente jurídica inicial: Oportuniia/oportuniia-legal-lab @ 9886fb120e9cd6ca9c7789e37e89f55c2384a8b6.\nCierre suscriptor/geo/TRADE: `docs/LEGAL_GATE_CLOSURE_SUBSCRIBER_GEO_TRADE_20261004.md` @ ca2a82104d77f62607770aed329be9d48897f458.

## Estado ejecutado
- Quality/Rappel: v1 retirada de la base WEB; v2 declarada única vigente.
- Contratación electrónica: control técnico implementado en OPORTUNIIAPP con contract_id, contract_version, SHA-256 content_hash, identidad, canal, evidencia precontractual, copia descargable/referenciada antes de aceptación, aceptación expresa mediante control no premarcado, copia posterior, acuse, accepted_at e histórico inmutable. Regla única para Suscriptor, Inversor, Colaborador, PREMIUM y demás contratos electrónicos OPORTUNIIA.
- Suscriptor: ledger de incidencia → alegación → decisión; efectos económicos explícitos y sin pérdida automática.
- Geolocalización: endpoint exclusivo de check-in puntual de misión; no existe ruta de tracking continuo.
- Privacidad: ledger versionado de preferencias/opt-out por finalidad.
- PBC/FT: gate transaccional explícito, separado del mero registro.
- PREMIUM: la evidencia contractual permite distinguir consumidor, obligación de pago e inicio anticipado. La UI B2C no debe abrirse hasta probar el flujo completo.
- LEGAL/abogado: sigue condicionado a identificación profesional y hoja de encargo cuando exista servicio profesional real.

## Gates que requieren validación externa/documental
- Laboralidad: PASS WITH CONDITIONS / NON-BLOCKING según cierre LEGALLAB ca2a82104d77f62607770aed329be9d48897f458; mantener coherencia entre contrato y operativa real.
- TRADE: PASS WITH CONDITIONS / NON-BLOCKING; control individual, declaración de autonomía/no exclusividad y revisión ante posible dependencia económica, sin renuncia de derechos.
- Geolocalización: PASS; exclusivamente puntual y vinculada a misión, sin tracking/background/rutas/control horario.
- EIPD: PASS WITH CONDITIONS / NON-BLOCKING; no se exige EIPD completa por la mera geolocalización puntual bajo el diseño aprobado. Mantener análisis de riesgo RGPD y reabrir ante nuevos factores de alto riesgo.
- Abogado: completar lawyer_id, colegiación, encargo, alcance y honorarios en cada asunto profesional.
- GATE FINAL CONTRACTUAL de LEGALLAB tras integrar contratos finales y evidencias de prueba.

## Regla de producción
Ningún cambio de esta rama abre por sí mismo tráfico M2M ni gates jurídicos cerrados.
<!-- END doc-011 -->

<a id="doc-012"></a>

## docs/LEGAL_FINAL_GATE_IMPLEMENTATION_ACCEPTANCE_20261005.md

<!-- BEGIN doc-012 -->
# OPORTUNIIA · LEGAL FINAL GATE · IMPLEMENTATION ACCEPTANCE
Fecha: 05/10/2026
Autoridad: RAFA
Fuente: LEGALLAB docs/LEGAL_FINAL_CONTRACTUAL_GATE_20261005.md
Dictamen fuente: APTO CON CORRECCIONES
Commit LEGALLAB: 08d5153759c47818996292f77fa322d053dce77b

## Decisión Master
MODELO FUNCIONAL/COMERCIAL/CONTRACTUAL = APROBADO PARA IMPLEMENTACIÓN.
No existe incompatibilidad jurídica que obligue a modificar las decisiones de negocio aprobadas.

## Correcciones obligatorias incorporadas al Master
1. PBC propio OPORTUNIIA cuando materialmente resulte sujeto obligado; CLEARED tercero no sustituye obligación propia.
2. Gate territorial previo a intermediación/comercialización C/D según comunidad autónoma.
3. Aprendizaje Secretaría preferentemente anonimizado/agregado; seudonimizado sigue RGPD.
4. Retención diferenciada por categoría/finalidad; PBC bajo su régimen específico y GEO/foto bajo plazo justificable propio.

## PASS confirmado
- relación mercantil / TRADE;
- Quality/Rappel v2;
- contratación electrónica;
- Premium 1.000/10.000;
- A/B/C/D por operación;
- separación A/B colaborador;
- abogado/despacho externo B/D;
- comercialización OPORTUNIIA C/D;
- Secretaría documental;
- privacidad operacional;
- GEO puntual, radio 100 m, cámara APP, hash/timestamp;
- incidencias contractuales;
- reglas internas de negociación/incentivos/heurísticas/antifraude/métricas.

## Próxima fase autorizada
IMPLEMENTACIÓN -> CONTRATOS DEFINITIVOS -> PRUEBAS -> VALIDACIÓN DE CORRESPONDENCIA -> AUTORIZACIÓN DE PRODUCCIÓN.

Este cierre NO autoriza merge a main, deploy ni apertura de válvulas de producción.
<!-- END doc-012 -->

<a id="doc-013"></a>

## docs/LEGAL_PARTNER_SERVICE_MODEL_20261005.md

<!-- BEGIN doc-013 -->
# OPORTUNIIA · CIERRE CONTRACTUAL BLOQUE 4
## Servicio jurídico mediante partners independientes · Modalidades B/D
**Autoridad:** RAFA
**Fecha:** 05/10/2026
**Estado:** APROBADO PARA INTEGRACIÓN CONTRACTUAL · PRE-DEPLOY

## 1. Regla
OPORTUNIIA no presta por sí misma asesoramiento jurídico reservado ni presenta a LEGALLAB/IA como abogado ejerciente. Cuando una operación B o D incorpora servicio jurídico facilitado por OPORTUNIIA, la prestación profesional corresponde a un abogado/despacho/gabinete externo e independiente debidamente identificado.

## 2. Elección y encargo profesional
Antes de comenzar la prestación jurídica deberán quedar trazados, según proceda:
- identidad del cliente y de la operación;
- partner jurídico seleccionado/aceptado;
- identidad profesional y datos colegiales que correspondan;
- comprobación de conflicto de intereses;
- alcance del encargo/hoja de encargo o instrumento equivalente;
- honorarios y condiciones que deban comunicarse al cliente;
- matter_id/expediente y evidencia de aceptación.

La relación profesional, deber de secreto, independencia técnica y responsabilidad profesional por la actuación jurídica corresponden al profesional/despacho conforme a la normativa aplicable y al encargo celebrado.

## 3. Papel de OPORTUNIIA
OPORTUNIIA puede facilitar acceso, selección/derivación, coordinación operativa y trazabilidad del servicio, pero no sustituye el criterio profesional del abogado ni emite asesoramiento jurídico como si fuera el despacho. OPORTUNIIA conserva las responsabilidades que legalmente le correspondan por sus propios actos, servicios, información, sistemas o incumplimientos.

No se utilizará una exoneración absoluta de responsabilidad de OPORTUNIIA.

## 4. Modalidades por operación
- A = compra/operación.
- B = compra/operación + servicio jurídico partner independiente.
- C = compra/operación + compraventa/comercialización posterior por OPORTUNIIA.
- D = compra/operación + servicio jurídico partner independiente + compraventa/comercialización posterior por OPORTUNIIA.

La modalidad se elige en cada operación y no queda fijada permanentemente en el perfil del inversor.

## 5. Compraventa posterior
La comercialización/compraventa posterior de C/D pertenece al servicio operativo OPORTUNIIA y podrá materializarse mediante una misión independiente asignada a un suscriptor de la zona. No debe confundirse con el servicio jurídico externo.

## 6. Reglas internas excluidas del contrato externo
No forman parte del derecho contractual del inversor ni deben prometerse en contratos externos:
- negociación interna de OPORTUNIIA con despachos por volumen;
- objetivos de precio interno;
- posibles rappels, honorarios o comisiones futuras por volumen;
- reglas internas de incentivos/premios a colaboradores.

Si se activase en el futuro una remuneración a OPORTUNIIA vinculada a derivación de asuntos jurídicos, su estructura deberá superar revisión LEGALLAB/deontológica específica antes de activarse.

## 7. Texto base para contratos con inversor
Cuando la modalidad elegida incluya servicio jurídico (B/D), OPORTUNIIA facilitará al cliente el acceso a un profesional o despacho jurídico externo e independiente. La prestación jurídica se desarrollará bajo la independencia profesional del abogado/despacho seleccionado y quedará sujeta al correspondiente encargo profesional, comprobación de conflictos, alcance, honorarios y demás condiciones aplicables. OPORTUNIIA no sustituye al profesional en la prestación del asesoramiento jurídico y responderá únicamente en los términos que legalmente correspondan por sus propios actos, servicios y obligaciones.

Cuando la modalidad incluya comercialización posterior (C/D), dicha prestación será organizada por OPORTUNIIA como servicio operativo diferenciado y no forma parte del encargo profesional del despacho salvo pacto expreso distinto.

## 8. Condición de cierre
Este bloque queda funcional y contractualmente definido. El GATE FINAL sigue condicionado a la consolidación del paquete contractual completo y revisión final de LEGALLAB.
<!-- END doc-013 -->

<a id="doc-014"></a>

## docs/M2M_TRANSPORT_MASTER_v1.md

<!-- BEGIN doc-014 -->
# OPORTUNIIA · CONTRATO UNIVERSAL DE TRANSPORTE M2M v1

Autoridad MASTER: Rafa
Ámbito: transporte interno entre herramientas OPORTUNIIA
Entorno: SANDBOX

Los contratos soberanos de negocio se conservan. Se transportan dentro de OPORTUNIIA_M2M_EVENT_v1 y se confirman con OPORTUNIIA_M2M_ACK_v1.

Hash único: SHA-256 del payload tras aplicar el método universal y determinista de serialización JSON. La terminología “canónico/canonical” queda retirada del estándar MASTER.

Idempotencia: mismo event_id + mismo payload_hash = replay seguro; mismo event_id + hash distinto = CONFLICT y fail-closed.

Persistencia: M2M_OUTBOX antes de enviar y M2M_INBOX/ledger equivalente antes de confirmar el efecto.

Reintentos: inmediato, +5, +15, +30, +60, +90 minutos. Agotados: REQUIRES_INTERVENTION o equivalencia documentada; nunca borrar el evento.

Seguridad: TLS, credencial específica por relación/dirección, secretos runtime, anti-replay, deny-by-default, fail-closed, rate limiting cuando proceda.

Una relación solo es MASTER PASS tras E2E de ambos extremos con 0 eventos perdidos y 0 efectos duplicados.
<!-- END doc-014 -->

<a id="doc-015"></a>

## docs/MASTER_OPERATION_MODALITIES_PBC_TRAINING_20261004.md

<!-- BEGIN doc-015 -->
# OPORTUNIIA · DECISIÓN FUNCIONAL MASTER · OPERACIONES / LEGAL / PBC / FORMACIÓN
## Aprobada por RAFA · 04/10/2026 · PRE-DEPLOY

### 1. Modalidad del inversor
El inversor se registra SIN modalidad permanente. En cada reserva/operación elige de nuevo:
- A: compra/operación.
- B: compra/operación + servicio jurídico mediante despacho/gabinete partner independiente.
- C: compra/operación + compraventa/comercialización posterior por equipo OPORTUNIIA mediante suscriptor asignado.
- D: integral/full equip = compra/operación + servicio jurídico partner + compraventa/comercialización OPORTUNIIA.
La elección pertenece a la operación y puede variar entre activos del mismo inversor.

### 2. Colaborador
El colaborador sí elige A/B en su alta conforme a su modelo de relación con sus inversores. Esta clasificación del colaborador no sustituye ni condiciona la modalidad A/B/C/D que el inversor elige para cada operación.

### 3. Servicio jurídico
OPORTUNIIA facilita varios despachos/gabinetes partners independientes. En modalidades B/D el despacho seleccionado lleva jurídicamente el caso bajo su propia relación profesional y responsabilidad, sin perjuicio de responsabilidades propias de OPORTUNIIA. No se presupone abogado en plantilla.
La negociación interna de tarifas, volumen, posibles rappels/honorarios futuros u otras condiciones con partners es regla interna y NO genera por sí sola un derecho contractual del inversor. Cualquier remuneración futura vinculada a derivación jurídica debe superar revisión LEGALLAB antes de activarse.

### 4. Compraventa posterior
En C/D la compraventa/comercialización posterior es servicio del equipo OPORTUNIIA, normalmente mediante suscriptor asignado de la zona. No es un servicio del despacho jurídico ni un partner externo por defecto.

### 5. Gate documental + PBC/Compliance
TODAS las operaciones A/B/C/D deben pasar por control documental y PBC/Compliance antes de avanzar.
Regla funcional: SIN EXPEDIENTE DOCUMENTAL VIGENTE + GATE PBC/COMPLIANCE CLEARED, LA OPERACIÓN NO AVANZA.
La profundidad/documentación concreta podrá variar según sujeto, operación y obligación legal. Esta regla operativa universal no pretende por sí sola declarar que OPORTUNIIA sea sujeto obligado en todos los supuestos legales.

### 6. Secretaría OPORTUNIIA
La Secretaría facilita que inversores/intervinientes mantengan documentación digitalizada, completa y vigente, evitando reiniciar el expediente en cada operación. Debe detectar faltas/caducidades y dirigir subsanación/revisión.

### 7. Formación OPORTUNIIA
El Curso de Formación OPORTUNIIA debe actualizarse con las nuevas funcionalidades y contener un capítulo específico PBC/FT y compliance: expediente documental, gate obligatorio, rol de Secretaría, señales de escalado, actuación/no actuación del suscriptor y evaluación final con evidencia de formación.

### 8. Despliegue
Decisiones aprobadas para implementación en repositorios y comunicación M2M/documental a sistemas afectados. NO DEPLOY, NO MERGE A PRODUCCIÓN hasta orden expresa de RAFA.
<!-- END doc-015 -->

<a id="doc-016"></a>

## docs/PREMIUM_B2C_CLOSURE_20261004.md

<!-- BEGIN doc-016 -->
# PREMIUM B2C · CIERRE TÉCNICO SANDBOX · 04/10/2026

## Decisión comercial definitiva
- Premium mensual: 1.000 EUR + impuestos por mes.
- Premium anual: 10.000 EUR + impuestos por 12 meses.
- La modalidad anual dura 12 meses desde la activación. El cierre fiscal a 31 de diciembre no corta ni modifica la vigencia.
- No existe permanencia adicional ni renovación obligatoria. Meses mensuales no consecutivos son admisibles mediante nuevas contrataciones.
- El pago anual es voluntario y supone 2.000 EUR de ahorro frente a doce mensualidades.

## Controles B2C preparados
- Selección expresa de modalidad.
- Información precontractual antes del paso de pago.
- Aceptación contractual mediante checkbox no premarcado.
- Botón inequívoco: «Contratar Premium y pagar … + impuestos».
- Solicitud separada y expresa de ejecución anticipada durante el plazo de desistimiento cuando resulte aplicable.
- No se utiliza una cláusula general de «no devolución» contra derechos imperativos del consumidor.
- La trazabilidad contractual debe conservar versión, hash, identidad, timestamp, canal, evidencia precontractual, copia y acuse.
- Cuando legalmente corresponda, el backend deberá registrar desistimiento/cancelación y los metadatos necesarios para eventual cálculo proporcional.

## Estado de cobro
PREPARED / VALVE CLOSED.

La interfaz no realiza cobros reales, no activa entitlement Premium y no contiene credenciales de pasarela. La apertura del cobro y del entitlement requiere autorización separada y conexión con el proveedor de pagos elegido.

## Gate
El diseño B2C y la interfaz de checkout quedan preparados en sandbox. El gate no autoriza producción ni sustituye la revisión final de LEGALLAB.


## Integración contractual posterior · Modalidades por operación (05/10/2026)

La contratación Premium no fija una modalidad A/B/C/D permanente al inversor. La modalidad de servicio se selecciona separadamente para cada reserva/operación.

Cuando la operación sea B o D, el componente jurídico será prestado por profesional/despacho externo e independiente bajo su correspondiente encargo profesional. Cuando sea C o D, la comercialización posterior será un servicio operativo OPORTUNIIA diferenciado.

Toda operación queda además condicionada al expediente documental vigente y al gate PBC/Compliance CLEARED conforme a la decisión MASTER vigente.
<!-- END doc-016 -->

<a id="doc-017"></a>

## docs/PRIVACY_OPERATIONAL_ONLY_20261004.md

<!-- BEGIN doc-017 -->
# PRIVACIDAD · FINALIDAD OPERATIVA · CIERRE 04/10/2026

## Decisión OPORTUNIIA
Los datos personales tratados dentro de este modelo se destinan a finalidades operativas vinculadas a la relación con OPORTUNIIA. No se habilitan finalidades de marketing ni comunicaciones comerciales mediante este gate.

## Finalidades operativas
Incluyen, según corresponda, alta y gestión de cuenta, relación y ejecución contractual, prestación y administración del servicio, misiones y evidencias operativas, comunicaciones necesarias para el servicio, facturación/pagos cuando proceda, seguridad, prevención y gestión de incidencias, cumplimiento de obligaciones legales y trazabilidad/auditoría.

## Base jurídica y derechos
Cada tratamiento deberá apoyarse en la base jurídica que corresponda. No se fuerza un consentimiento cuando el tratamiento sea necesario para ejecutar la relación contractual o cumplir una obligación legal. Se facilitarán los derechos previstos por la normativa de protección de datos en función de la base y tratamiento aplicables.

## Regla técnica
PRIVACY PURPOSE = OPERATIONAL ONLY.

COMMERCIAL_EMAIL, COMMERCIAL_SMS y COMMERCIAL_OTHER quedan fuera del modelo y no deben utilizarse como finalidades habilitadas.

Este cierre no autoriza usos incompatibles, cesiones indiscriminadas ni reutilización comercial de los datos.
<!-- END doc-017 -->

<a id="doc-018"></a>

## docs/SECRETARIA_PBC_EXPERIENCE_MODEL_20261005.md

<!-- BEGIN doc-018 -->
# OPORTUNIIA · SECRETARÍA + PBC/COMPLIANCE · MODELO OPERATIVO v1
**Autoridad:** RAFA
**Fecha:** 05/10/2026
**Estado:** APROBADO / PRE-DEPLOY

## Regla maestra
Todas las operaciones A/B/C/D requieren expediente documental vigente y Gate PBC/Compliance CLEARED antes de avanzar.

## Expediente adaptativo
El expediente se parametriza por tipo de sujeto (PF/PJ), estructura jurídica/económica (por ejemplo SL u otras), jurisdicción y características de la operación.

Los documentos se clasifican por finalidad: identidad, representación, titularidad real, origen de fondos, capacidad/viabilidad financiera, PBC/FT u otros. También se clasifican como obligatorios, condicionales o de apoyo y se controla su vigencia.

PBC/FT y viabilidad financiera son conceptos distintos aunque se presenten al usuario mediante un único expediente operativo.

## Secretaría OPORTUNIIA
Secretaría facilita recopilación, digitalización, actualización, detección de caducidades, subsanación y preparación del expediente. No sustituye Compliance ni la decisión del servicer/entidad.

## Memoria de experiencia propia
Secretaría aprende exclusivamente de expedientes reales tramitados por OPORTUNIIA. Registra por servicer/contraparte, estructura del sujeto y tipo de operación:
- documentos aceptados/rechazados;
- requerimientos adicionales;
- preferencias documentales observadas;
- patrones de tramitación más fluida;
- evidencia que soporta cada observación.

Ejemplo: si en expedientes comparables una póliza de crédito concedida por una entidad bancaria ha facilitado la acreditación documental de disponibilidad/procedencia/capacidad financiera, Secretaría puede recomendar preparar esa evidencia cuando sea pertinente.

## Límites del aprendizaje
La experiencia histórica es ADVISORY ONLY:
- no elimina documentos obligatorios;
- no rebaja controles PBC/FT;
- no puede poner el gate en CLEARED;
- no garantiza aceptación;
- distingue observación de patrón confirmado;
- conserva evidencia y nivel de confianza.

La autoridad final de Compliance/servicer permanece separada.

## Formación
El Curso OPORTUNIIA debe enseñar esta arquitectura: expediente adaptativo, PF/PJ, finalidad documental, viabilidad financiera, Gate PBC, Secretaría, escalado y diferencia entre recomendación histórica y requisito obligatorio.
<!-- END doc-018 -->

<a id="doc-019"></a>

## frontend/README.md

<!-- BEGIN doc-019 -->
# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
<!-- END doc-019 -->

## Integracion del circuito de 72 horas — 2026-10-21 (en desarrollo)

Un replay de la misma publicacion ya PUBLISHED devuelve idempotent=true sin modificar fechas, orden ni registros. Una version nueva de la misma OP conserva su internal_id. Pruebas locales ejecutadas test_presentation_publish y test_presentation_ingress: 12 passed, 0 failed, incluyendo igualdad de todos los registros antes/despues del replay.

Pendiente: transporte y publicacion automatica de la version individual tardia con su provenance de cierre, prueba real de extremo a extremo y revision de requisitos legales/cookies antes de apertura publica. No se ha desplegado.
