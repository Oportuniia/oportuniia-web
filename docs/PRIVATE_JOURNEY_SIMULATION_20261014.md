# Simulación privada de alta y contratación · 14/10/2026

Regla aprobada por Rafa: Mi OPORTUNIIA integra los formularios originales. Inversor/colaborador y física/jurídica son ejes independientes. Premium y reservas requieren perfil al 100% y revisión y contraste por OPORTUNIIA; reservar añade los requisitos de la operación. Los datos verificados se reutilizan en la oferta.

## Cambios encontrados y corregidos
- El perfil provisional no contenía todos los campos de las capturas. Se integran datos personales, fiscales, de entidad y representación y declaraciones por relación. Teléfono opcional. Modelo de compra del inversor por operación; A/B del colaborador en el perfil.
- Se retira el formulario extenso duplicado de la página pública de registro y se remite al perfil privado.
- La reserva DEMO anterior podía crear registros sin revisión. Ahora se bloquea; rellenar el perfil o cambiar un rol DEMO no lo aprueba.
- Se sustituye el enlace de contratación Premium desde el popup por estado bloqueado y acceso al perfil.
- Backend: estado de elegibilidad calculado sobre snapshot verificado del mismo usuario y versión, campos completos, documentos revisados y revisión vigente. Ni flags enviados por el usuario, ni archivo, ni OCR, ni rol de navegador conceden aprobación.
- El paso de reserva comprueba además readiness autorizado, vigente y específico de usuario/OP/modalidad. Las dos rutas de checkout se detienen con `payment_gateway_not_activated` después de superar los requisitos: no hay cobro ni sesión de pago ficticia.

## Alcance de las simulaciones
- Navegador: cuatro casos (inversor PF/PJ y colaborador PF/PJ), borrador incompleto, datos completos, archivos ficticios, declaraciones, 100% pendiente de revisión, recarga, intentos Premium/reserva bloqueados, móvil 390/768 y sin subidas ni errores JS.
- Servidor: los cuatro casos recorren borrador -> revisión autorizada simulada en DB aislada -> elegibilidad -> bloqueo por falta de readiness -> readiness aprobado -> límite de pasarela. Ediciones pendientes no alteran snapshot verificado de oferta; retirar aprobación documental, caducar revisión o eliminar un campo obligatorio vuelve a bloquear.
- La revisión positiva se introduce exclusivamente como fixture de test, sin endpoint ni control público de autoaprobación. Base de datos mongomock, archivos y personas ficticios; no correo, fondos ni documentos reales.
- Se conservan pruebas de aislamiento de inversores, JWT, permisos, PDF íntegro y hash, acceso Premium separado, mensajes y cola de email idempotente, filtros y navegación privada. OCR digital y escaneado conserva procesamiento local.

## Qué significa el 100% en Preview
Es un indicador de que están rellenados los campos, declaraciones y referencias de archivos de prueba correspondientes al perfil. No certifica autenticidad ni suficiencia. En esta DEMO los archivos del perfil solo se representan por metadatos locales, sin subir sus bytes ni guardarlos como expediente real. Los requisitos adicionales se fijan en la revisión según caso y operación. No introducir datos reales.

## Límites para publicación operativa
La Preview es frontend y demostración; el backend probado sigue en rama y Render producción sigue main. No se ha creado login real ni expediente persistente con custodia documental. Faltan conexión de identidad, backend/base/almacenamiento aislados, circuito autorizado de revisión y PBC, documentos aprobados de productores, términos/consentimientos versionados aprobados, plantilla/firma, correo y pasarela con importes/condiciones. Los textos de declaraciones y las modalidades no sustituyen contratos. Premium DEMO permite explorar servicios ficticios, no acredita compra ni estado de usuario real.

No existe todavía una prueba integrada contra servicios reales. Las simulaciones positivas de servidor y el recorrido de navegador se verifican por separado; no se presentan como un pago ni una activación real de extremo a extremo.

## Incidencia de la suite heredada
Una ejecución amplia de backend/tests incluyó pruebas antiguas dependientes de frontend/.env y una URL de despliegue ajena al sandbox; fallan por entorno ausente/página distinta. No se contabilizan como verificadas. Se ejecuta de forma explícita la suite aislada de gateway, búsqueda, motor, contratos M2M, OPORTUNIIAPP y publicación PRESENTACIÓN; las rutas públicas se validan aparte contra esta Preview.

## Resultado de las comprobaciones de esta entrega
- Cuatro recorridos de perfil PF/PJ inversor/colaborador: correctos en navegador.
- Dieciséis comprobaciones privadas: correctas.
- Extracción PDF, OCR escaneado, separación y ZIP: correctos, sin subidas.
- Suite aislada: 49 casos; la ejecución amplia heredada tiene incidencias de entorno descritas arriba.
- Publicación: solo rama Preview, sin merge ni cambios de configuración de producción.
