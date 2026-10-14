# OPORTUNIIA · Acceso progresivo, fichas y Secretaría · 14/10/2026

## Alcance y autoridad
Implementación de revisión en `feat/ultima-milla-consolidacion-20261014`. Producción y main no autorizados para modificación. Se conserva navy, menú aprobado y separación Premium/verificación. Fuentes: instrucciones de Rafa del 14/10, `SECRETARIA_PBC_EXPERIENCE_MODEL_20261005.md`, `MASTER_OPERATION_MODALITIES_PBC_TRAINING_20261004.md`, contrato PRESENTACIÓN v3.0 y salida real `PRESENTATION_WEB_PUBLICATION_v1` de PRESENTACIÓN.

## Funcional en Preview
- Toda la ficha abre el expediente; favorito independiente y accesibilidad de teclado.
- Apertura por Portada comercial. Pestañas PC, RE, IC, RF y LEGAL. RF exige Premium DEMO. Sin archivos oficiales conectados se muestra estado no disponible, sin fabricar PDF ni presentar la maqueta como documento de PRESENTACIÓN.
- El «informe ejecutivo» solicitado no tiene código en el contrato disponible (solo PC, RE, IC, RF). Se deja explícitamente pendiente de producto/contrato, separado del RE.
- Contacto rápido por email con referencia OP y consulta privada DEMO. No se envían mensajes durante las pruebas.
- Datos precompletados de oferta visibles como borrador no contractual. No firma ni envío a proveedor.
- Reserva DEMO A/B/C/D conserva modalidad por operación. Pago real bloqueado por identidad/expediente/PBC/permiso, proveedor e importe/condiciones pendientes.
- Aviso público ampliado: escaparate ficticio e información real sujeta a confianza progresiva. Nombre/email y pago no conceden acceso.
- Perfil propuesto: inversor/colaborador, PF/PJ y actividad independientes; datos de entidad/representación según PJ; A/B solo para colaborador. Estado siempre pendiente de revisión.
- Secretaría Premium: PDF digital, PDF escaneado e imágenes PNG/JPG/WebP; extracción de texto y OCR español/inglés; sugerencias de categoría; detección orientativa de fechas de caducidad explícitas; revisión obligatoria; separación por páginas completas; generación de PDF individuales y ZIP con índice. Procesamiento en navegador y recursos del mismo origen; sin envío de documentos a un servidor o modelo externo. Los originales, texto y resultados no se guardan en localStorage. Se borran de memoria al salir del módulo.
- Máximos operativos: 10 archivos, 20 MB totales, 30 páginas, 18 megapíxeles por imagen. No se recortan dos documentos que estén dentro de una sola página. No hay aprendizaje histórico inventado ni validación de identidad/PBC por OCR.

## Formularios originales
`https://registro.oportuniia.com/inversores` y `/colaboradores`: lectura web no disponible, navegador ERR_BLOCKED_BY_CLIENT, lectura del entorno de pruebas HTTP 403. No se enviaron formularios ni se intentó crear cuentas. Se mantienen enlaces y se marca la nueva propuesta como no contrastada con todos los campos originales. Falta el inventario autorizado del formulario original para afirmar equivalencia.

## Gateway privado implementado y probado en sandbox
`backend/investor_access.py`, registrado en `server.py`:
- OIDC RS256 con JWKS HTTPS, issuer, audience, exp, iat y sub obligatorios. Sin proveedor configurado devuelve 503; token falso/caducado devuelve 401. Roles enviados por el navegador no se usan como autorización.
- Propuesta de fases: 0 pendiente; 1 identidad VERIFIED vigente; 2 expediente APPROVED vigente; 3 documentación judicial con permiso específico y PBC CLEARED de sujeto y operación. La matriz concreta necesita validación operativa antes de conceder permisos reales. No hay endpoint público que apruebe revisiones.
- Premium depende de un entitlement de servidor vigente; no de pago enviado por el cliente. Subir archivos, editar perfil y OCR no modifican los estados revisados.
- Catálogo real solo para expedientes verificados y OP expresamente asignadas con permiso CATALOG. Acuerdos exige además Premium. Las APIs públicas conservan únicamente datos sintéticos.
- OP pública ↔ identificación interna se resuelve en `web_operation_bindings`. Catálogo y documentos requieren revisión explícita de seguridad de referencia; la WEB no reescribe ni asume anonimizado un PDF de un productor.
- PRESENTACIÓN: consumidor real de metadatos PC/RE/IC/RF y descarga M2M desde `/api/m2m/outputs/web/{output_id}/artifacts/{product}`. HTTPS fijo, sin redirecciones, límite 50 MB y SHA-256 verificado. El cliente nunca recibe la clave M2M ni identificadores del proveedor.
- LEGAL: archivo aprobado de almacenamiento privado configurado por el responsable. No se inventa un endpoint soberano de LEGAL.
- Descarga/visualización con comprobación por usuario, OP, producto, propietario, vigencia y permiso en cada petición. PDF íntegro, nombre público OP_PRODUCTO.pdf, no-store y auditoría.
- Borrador de datos de oferta desde snapshot verificado de perfil, no desde el último borrador editable.
- Mensajes privados ligados al sujeto. Respuestas por M2M protegido, idempotencia por evento y cola de copia por email OPERATIONAL_ONLY. Email permanece PENDING_EMAIL_PROVIDER; no se afirma entrega.
- El sync de readiness ya no confía en el texto público `X-OPORTUNIIA-M2M: authoritative`: requiere secreto de servidor y fecha de vigencia. Su consulta requiere identidad y filtra por inversor.
- Checkout cerrado hasta readiness vigente por modalidad/inversor/operación y configuración comercial. No se ha seleccionado pasarela ni creado una sesión de pago ficticia.

## Lo que NO está activado
La Preview Vercel es el frontend. El backend de Render del repositorio está configurado para main. No se cambió Render ni se conectó esta rama a producción. La rama Preview consultada no tiene variables privadas configuradas. El gateway está implementado/testeado, pero no se ha hecho handshake con usuarios/documentos reales ni se ha integrado un SDK de login real en la interfaz.

Pendientes concretos para activación: proveedor de identidad y sesión segura; backend aislado y base privada para pruebas con configuración propia; conexión M2M y documentos aprobados de PRESENTACIÓN/LEGAL; matriz de acceso y campos originales confirmados; modelo de oferta aprobado/firma; proveedor de correo; pasarela, importe de reserva y condiciones aprobados. Ninguna subida ni compra activa estos requisitos automáticamente.

## Pruebas
- Suite backend: ingreso/publicación PRESENTACIÓN, contratos M2M, motor privado, OPORTUNIIAPP, búsqueda y gateway de inversor. Comprueba falsificación de roles/sesión, expiración, aislamiento entre inversores, Premium sin identidad, propietario incorrecto, integridad de bytes, referencia pública, mensajes e idempotencia y snapshot de oferta.
- `tests/document-workflow.cjs`: clic completo/favorito, productos bloqueados veraces, email con OP, alta PF/PJ y colaborador A/B, PDF digital mixto → tres PDF separados en ZIP, OCR real sobre PDF escaneado, revisión obligatoria, borrado de sesión, cero subidas y bloqueo RF para normal. Los archivos de prueba son sintéticos.
- `tests/private-e2e.cjs` adaptado: conserva los 16 recorridos y sustituye la antigua muestra TXT por comprobación de bloqueo documental real.
- Pruebas de escritorio, 390 y 768 px. No certifica dispositivos físicos ni Safari/iOS.
