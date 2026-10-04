# MASTER · Oferta, reserva y adaptadores de proveedores · diseño 2026-10-02

Estado: propuesta funcional en sandbox originada por instrucciones del propietario. NO es una aprobación jurídica, integración CRM, garantía de pago, ni funcionalidad desplegada. Requiere revisión LEGAL LAB y del propietario antes de activar cualquier compromiso o cobro.

## 1. Datos reutilizables / oferta prerrellenada
- Área MI OPORTUNIIA: perfil progresivo, identidad verificada bajo el sistema soberano, expediente documental personal con originales/versiones y acceso granular. Solicitar solo los datos exigibles para cada acción.
- Nueva oferta muestra referencia pública de oportunidad (p.ej. OP-09870) **y la referencia externa del proveedor solo a nivel interno**. Referencia interna pública y correspondencia con terceros inmutable, versionada y auditada; nunca sustituir sin registro.
- Prerrellenar desde perfil *validado vigente* datos declarados/autorizados: razón social o nombre, identificación, representación acreditada, contacto, domicilio si pertinente, identificación del activo y datos de oferta. Marcar explícitamente qué falta y si algún documento ha caducado; permitir rectificar e informar sobre efectos legales del envío. Nunca transformar datos personales incorrectos en declaraciones automáticas.
- Vista previa final inteligible antes de firmar, resumen de oferta y trazabilidad de las versiones del perfil y expediente usadas.

## 2. Precios y ofertas
- Separar deuda nominal, importe orientativo anunciado, coste/condiciones del proveedor, objetivo OPORTUNIIA, piso comercial autorizado y margen económico; piso, coste, márgenes, estructura y proveedor según nivel de confidencialidad jamás públicos.
- UX: «Ofertar precio orientativo [importe]» o «Proponer otro importe» con explicación de que está sujeto a estudio, disponibilidad y aceptación. No ofrecer públicamente menú de descuentos.
- Validaciones públicas solo sintaxis e importes positivos/razonables; protección antibot, rate limit, duplicados y autenticación. Los límites privados permanecen del lado servidor; no usar rechazos diferenciados para revelar el mínimo por tanteo.
- Motor de reglas privado por operación y universo (con acuerdo de proveedor o judicial/no acordado); políticas de decisión *configuradas por responsables humanos*: viabilidad, revisión, negociación, excepción, rechazo. Un importe menor que objetivo (ej. 190k vs 210k) puede estudiarse si la operación lo permite; nunca inferir regla global del ejemplo.
- Ninguna oferta supone aceptación firme, disponibilidad garantizada, adjudicación ni precio final por mero envío. Historial de estado y revisión humana cuando corresponda.
- Proteger acuerdos y datos frente a fondos/proveedores con acceso al catálogo: visibilidad comercial segmentada si contractualmente permitida, no confiar solo en ocultar campos de interfaz (control servidor).
- Estudiar estrategia de precio y exposición frente a proveedores y competidores con LEGAL y equipo comercial sin prometer blindaje total ante inferencias.

## 3. Hoja de reserva y pagos
- Flujo de reserva separado del formulario de oferta y de la firma de condiciones de confidencialidad. Estados sugeridos: borrador -> oferta enviada -> propuesta en estudio -> propuesta aceptada condicionada -> condiciones de reserva informadas -> reserva firmada -> pago recibido/confirmado -> tramitación -> formalización / desistimiento / incidencia / devolución / cierre. Solo generar cada estado desde hechos acreditados.
- Modelo de intermediación y alcance de representación/mandato *dependiente de contrato real*, relación con proveedor y condiciones del producto. No afirmar que OPORTUNIIA «solo sigue política del proveedor» si cobra importe propio, dicta términos, custodia fondos o asume compromisos. Evaluación LEGAL obligatoria.
- Importe orientativo planteado por propietario: **5.000 €**. No implementar como cargo fijo general sin validar por tipo de activo, contrato, proveedor, derechos del usuario, fiscalidad, custodia, facturación y transparencia.
- Documento de reserva debe informar *antes de firma y pago*: quién cobra y por qué concepto, a favor de quién, a quién se factura, momento exigible, si computa a precio, exclusividad/plazo, eventos concretos de devolución total/parcial y no devolución, causas atribuibles a proveedor, OPORTUNIIA, usuario, terceros o expediente judicial, pruebas y plazos de resolución, derecho aplicable y canales de reclamación. Evitar «causas ajenas a nosotros» ambiguas.
- Registrar consentimiento separado y huella del documento exacto firmado; pago solamente mediante proveedor y backend autorizado, sin recoger tarjetas propias, reconciliación y recibos. No activar antes de revisión legal por posible normativa consumidores/contratos, intermediación y pagos.
- No prometer que la reserva bloquea jurídicamente el activo si el proveedor no asume esa obligación.

## 4. Master OPORTUNIIA / adaptadores por fondo
- Canonical Offer / Reservation schema versionado (inversor y representante; IDs interno y externo; activo; condiciones; oferta; fechas; garantías; consentimientos; evidencias de firma; anexos; reglas de proveedor). Permisos minimizados según destino.
- Cada proveedor obtiene adaptador versionado «master -> plantilla/casillas/códigos/referencias/formulario»; Anticipa, Servihabitat, etc. solo como ejemplos, NO asumir que existe contrato ni acceso API con ellos.
- Firmar maestro por SMS OTP / correo verificado / firma electrónica apropiada a riesgo, contrato y jurisdicción; no equiparar «un código SMS» automáticamente a firma suficiente ni asumir equivalencia formal con documento del proveedor.
- Firma y transformación **NO** son intercambiables por defecto: cuando el proveedor exija su propio documento o firma, generar formulario precargado para aceptación/firma adicional exigida. Mantener inalterados hash, versión, consentimiento y evidencias del documento realmente firmado. No cambiar condiciones sustantivas después de la firma mediante «darle la vuelta» al documento.
- Confirmar con cada proveedor sus plantillas, requisitos, referencias, integración y aceptación de documentación electrónica; adjuntar anexos no transmitidos cuando no sean necesarios. Pruebas contractuales antes de homologar adaptador.

## 5. Flujos y gates
- Desde ficha: oferta prerrellenada y específica de activo -> review -> aceptación de condiciones de presentación -> firma si procedente -> submission -> revisión -> respuesta -> reserva condicional si aplica -> firma de reserva exacta -> pago si jurídicamente habilitado -> integración proveedor y expediente.
- Seguridad: autenticación efectiva de inversor (no tokens OPORTUNIIAPP), autorización por operación, R2 documental privado separado, auditoría inmutable relativa, cifrado, protección frente a spam y filtraciones, comunicaciones con minimización de datos y retención aprobada.
- Tests sandbox: oferta 210k, 190k y extremadamente baja sin revelar umbral; proveedor con y sin precio cerrado; caducidad documento; firma y modificación postfirma; adaptador incompatibilidad y campos faltantes; devolución/no devolución por supuestos aprobados; idempotencia pagos; inexistencia de acceso entre inversores.
- Pendientes del propietario: hoja actual de reserva, acuerdos/formularios efectivamente vigentes de cada proveedor, política comercial por operación, qué entidad contrata y cobra y rol concreto de OPORTUNIIA. Decisiones finales LEGAL LAB/comercial antes de uso efectivo.
