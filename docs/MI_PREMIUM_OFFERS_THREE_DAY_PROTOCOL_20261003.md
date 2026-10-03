# WEB 5.0 · Oferta premium y regla de los tres días · decisión 2026-10-03

## Política comercial comunicada por propietario
- Existe la misma exigencia de tres días para **cada** ofertante, sin excepciones comerciales.
- El plazo documental se inicia cuando la aprobación de una oferta **se comunica** y queda acreditada, no al realizar una propuesta ni al preparar un borrador.
- El beneficiario debe facilitar **toda la documentación requerida** dentro del plazo. La entrega debe verificarse y quedar evidenciada; un simple upload de archivo incompleto no cuenta como finalización.
- Si vence el plazo sin paquete completo, pierde la oferta. La oportunidad se reactiva comercialmente conforme al expediente vigente.
- Un segundo ofertante puede pasar a consideración; **no** obtiene adjudicación automática: su oferta necesita la misma revisión y aprobación independiente. Una vez comunicada su aprobación, obtiene su propio plazo de tres días.
- Implantación técnica del concepto de tres días: **72 horas exactas a partir del timestamp de la comunicación acreditada**. Confirmar con LEGAL el texto exacto, medio válido de notificación, hora legal, fuerza mayor/normas imperativas y prueba de entrega antes de producción; no crear excepciones comerciales arbitrarias.
- Los 3 días que OPORTUNIIAPP concede para acudir a una misión son otro proceso, con su propio contador y política de faltas. No mezclarlos ni conceder al comprador faltas de misión.

## Avance implementado en la rama
- `frontend/public/preparar-oferta.html`: nueva experiencia premium en Poppins y branding, campos cliente e inmueble, revisión de importe, explicación del protocolo y generación de PDF no vinculante de revisión.
- `/preparar-oferta?op=...`: pantalla nueva desde backend WEB. El WordPress anterior permanece sin cambios hasta paridad y despliegue verificados.
- `GET /api/mi/private/offers/prefill?op=...`: requiere inversor WEB validado; solo rellena campos del cliente previamente validados y la ficha publicada con `item.public_reference` exacta y `offer_enabled=true`. No devuelve referencias confidenciales ni permite resolver un identificador arbitrario.
- `POST /api/mi/private/offers/{op}/preview-pdf`: PDF borrador con datos revisados y referencia/propiedad recuperadas del servidor, no firma ni oferta presentada.
- `mi_offer_deadlines.py`: política determinista testada de aprobación por responsable, entrega de notificación, deadline 72 horas, documentación verificada, caducidad y siguiente candidato no adjudicado.

## Trabajos pendientes para operación real
1. Publicar mapeo **real** de referencia comercial -> oportunidad, incluida `OP0001`, y habilitar ofertas en el registro publicado solo tras el visto bueno de operaciones. Ni DEMO ni datos de ejemplo son operaciones reales.
2. Campos personales de oferta en el perfil progresivo, validaciones por responsable y permisos granulares; la UI permite corregir datos declarados, no los marca falsamente como verificados.
3. Conectar alta efectiva de oferta privada a Mongo/CRM de operaciones con idempotencia, antiabuso, evidencia de consentimientos, notificación y revisión humana.
4. Integrar el motor 72 horas con avisos reales de email/n8n y un scheduler confiable; usar comparaciones atómicas en Mongo para evitar vencimientos cuando exista recepción documental acreditada. Vincular con cola de segundos ofertantes autorizada por operaciones; no reasignar automáticamente.
5. Definir lista documental exacta por operación, recepción, verificación de completitud y tratamiento de documentación ya archivada en MI OPORTUNIIA (reutilización únicamente con consentimiento).
6. Validación jurídica de plazos, comunicación, efectos de pérdida de oferta, privacidad, mecanismos de reclamación y texto contractual. Documentar todas las notificaciones.
7. **Hoja de reserva** separada del formulario de oferta, firma electrónica/OTP jurídicamente adecuada, reglas de depósito/devolución y pasarela de cobro. No activar los 5.000 EUR ni ninguna reserva sin condiciones finales.
8. Adaptadores reales por proveedor y equivalencia con LeadConnector; preservar el formulario activo hasta sustitución segura.
9. Pruebas E2E reales con correos, Mongo y CRM en sandbox, ejecución del scheduler, observabilidad y reversión.
