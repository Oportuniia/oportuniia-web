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
