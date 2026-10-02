# GATE FUNCIONAL · Migración de la WEB WordPress a WEB de código

Estado: auditoría READ-ONLY de WordPress del 2026-10-01. Especificación de traslado, NO aprobación para publicar ni para sustituir flujos actuales.

## Fuentes verificadas

WordPress público `https://oportuniia.com`, leído mediante WPVibe REST GET:
- `/registro/` (página 552) informa la secuencia **Rellenar formulario → Firmar contrato → Obtener código OPORTUNIIA** y ofrece dos accesos:
  - Inversores: `https://registro.oportuniia.com/inversores`
  - Colaboradores: `https://registro.oportuniia.com/colaboradores`.
  La lógica interna de ambas páginas de registro, los campos concretos, las firmas, validaciones, automatizaciones y credenciales de sus sistemas destino NO se verificaron.
- `/acceso/` (página 538): acceso exclusivo a usuarios validados, basado en el estado de la sesión WordPress que observa el usuario conectado. Falta auditar el contrato de interoperabilidad de identidad y sus permisos.
- `/preparar-oferta/` (página 1203): iframe de LeadConnector con form ID `CVtRSGMid1wsxIDVxPOs` y script `https://link.msgsndr.com/js/form_embed.js`. Está etiquetado «Formulario de Oferta»; no debe confundirse sin confirmación con una **hoja de reserva legalmente operativa**.
- `/oportunidades/` (página 189): página publicada; no se obtuvo evidencia de un flujo de reserva a partir de sus enlaces.
- WEB de código `frontend/public/acceso.html` muestra por ahora CTA de registro hacia `/contacto` y entrada hacia `/oportunidades`; **NO** reproduce el flujo completo antiguo. Backend `/operations/intent` es expresamente DEMO y no crea reservas, cobros ni contratos.

## Requisitos de paridad antes de reemplazar producción

1. Conservar accesos por perfil a Inversores y Colaboradores; identificar el recorrido completo de registro, firma y emisión/validación del código.
2. Definir quién valida la identidad en WEB y cómo reconoce usuario validado, roles, Premium y permisos por operación/documento; no inferir que sesiones de OPORTUNIIAPP (colaboradores) equivalen a identidad del inversor.
3. Preservar el formulario de ofertas existente y su destino LeadConnector hasta disponer de una alternativa verificada que mantenga sus campos, consentimiento, identificador de activo, CRM, avisos y trazabilidad. Inspeccionar el contenido real del formulario con acceso autorizado al proveedor; jamás copiar datos privados de usuarios.
4. Auditar la **hoja de reserva** concreta, sus versiones y efectos jurídicos, firma, identificadores, condiciones, aceptación, estados, notificaciones, archivo y relaciones con OPORTUNIIAPP / CRM antes de implementarla. La oferta y la reserva pueden ser actos distintos.
5. Implementar mejoras de experiencia y nuevos textos solo tras incorporar los cambios comerciales/jurídicos que apruebe el propietario; registrar diferencias frente a la funcionalidad anterior.
6. Probar usando personas y activos ficticios, CRM aislado/entorno de prueba y bandeja de correo de pruebas, con accesos por perfil, envío, firma, códigos, duplicados, denegaciones, expiración y evidencia de historial. No enviar formularios de prueba a CRM productivo.
7. Producir pruebas de equivalencia y plan de reversión; solo migrar el dominio público después de autorización explícita.

## Fronteras no negociables

- WordPress público NO se modifica durante la auditoría.
- PDF y versión documental soberanos pertenecen a PRESENTACIÓN y permanecen almacenados en Cloudflare R2; WEB consume por servicio protegido.
- No publicar operaciones ni habilitar registro operativo o reserva real desde DEMO.
- Las URL de registro actuales son conexiones descubiertas, **no** evidencia de que sus sistemas externos hayan sido auditados.

## Decisión del propietario — hoja de reserva (2026-10-01)

El propietario confirma que la **hoja de reserva existe como documento/flujo propio y se va a modificar**. NO identificarla ni reemplazarla por el «Formulario de Oferta» de LeadConnector; son piezas distintas hasta que se verifique contractualmente la relación entre ambas.

- Mantener el mecanismo de reserva actual intacto hasta disponer de la nueva versión aprobada.
- Solicitar el ejemplar vigente para extraer campos, condiciones, firmas, referencias y efectos; documentar propuestas de cambio por separado, sin suponer cláusulas ni importes.
- Implementar la nueva hoja en la rama DEMO y verificar con operaciones ficticias el vínculo operación → inversor validado → hoja → firma/aceptación → trazabilidad, sujeto al contrato legal aprobado.
- El formulario de oferta mantiene su integración actual mientras se audita, sin confundirse con la reserva.
- La migración del registro de inversores/colaboradores puede prepararse paralelamente, manteniendo los destinos hoy verificados.

## Referencias aportadas por el propietario (2026-10-02)
- Registro inversores: https://registro.oportuniia.com/inversores (página LeadConnector externa; mantener integración activa).
- Registro colaboradores: https://registro.oportuniia.com/colaboradores (página LeadConnector externa; mantener integración activa).
- Oferta vinculada a operación de ejemplo: https://oportuniia.com/preparar-oferta/?op=OP0001. WordPress integra el iframe LeadConnector `CVtRSGMid1wsxIDVxPOs`. **No se ha verificado que el parámetro op se transfiera al formulario incrustado**: el iframe público inspeccionado usa src fijo sin query. Requiere prueba funcional controlada o acceso autorizado a configuración del formulario antes de dar por válida la trazabilidad.
- Contacto de referencia estética aprobado por propietario: https://oportuniia.com/contacto/. Estructura: sección «Contáctanos», datos a un lado y «¿Hablamos?» con Nombre, Correo electrónico, Categoría (Inmobiliaria, Colaborador, Inversor), Mensaje y Enviar. WordPress observado contiene lorem ipsum y teléfono provisional; no copiar como datos definitivos. Mantener estructura y adaptar tipografía Poppins/branding OPORTUNIIA en nueva WEB.
- La hoja de reserva futura sigue siendo un documento diferente de la oferta y requiere rediseño/aprobación por separado.
- Se ha corregido en la rama la pantalla `frontend/public/acceso.html` para mostrar ambos destinos reales de registro. No desplegado.
