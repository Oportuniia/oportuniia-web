# Colaborador externo: reconocimiento y modalidad A

Decisión aprobada por Rafael Querol el 7 de noviembre de 2026. Sustituye las reglas anteriores incompatibles sobre el reconocimiento exigible; no altera el régimen de suscriptores.

- Se suprime la exigencia de hoja independiente inversor → OPORTUNIIA. No se suprimen los contratos económicos ni los documentos de custodia de la operación.
- Se conserva el reconocimiento inversor → colaborador externo. Debe identificar operación, partes, importe o fórmula determinable, hecho de devengo y vencimiento.
- Modalidad A: 50 % de los honorarios netos efectivamente recibidos por OPORTUNIIA por la operación inicial. No es el 50 % del precio del activo ni del beneficio del inversor.
- El inversor y colaborador deben firmar antes de formalizar la operación; si hay notaría, como límite en ese acto y antes de la firma de la operación. Una firma posterior no subsana el incumplimiento. Se conservan fecha, hora y evidencias; la mera coincidencia del día no prueba el orden.
- Falta de firma en plazo: sin derecho al 50 %. No convertir silenciosamente a modalidad B, que requiere elección expresa.
- Honorarios futuros inversor → colaborador: separados de aquella participación, conforme a su pacto concreto. OPORTUNIIA no los garantiza.
- Depósito previo en custodio independiente según condiciones de la operación; liberación con evidencia de formalización; instrucción de devolución si no se formaliza. El depósito no es cobro efectivo de OPORTUNIIA.
- Conservar contratos firmados e histórico. Eliminar plantillas obsoletas sólo después de sustituir sus referencias y comprobar que no son ejemplares firmados.

## Implantación comprobable

Fuentes y PDF vigentes en `backend/legal_templates`. El catálogo `/api/collaborator/legal-templates` exige sesión y cuenta de colaborador o superadministrador. Descargar una matriz no acredita firma, no otorga una comisión y no autoriza un pago.

La custodia, validación de evidencias y liquidación requieren integrar el proveedor y los registros reales de la operación. Este cambio de documentos no demuestra que esos componentes estén operativos; no se han encontrado en este servicio los módulos que ejecuten esa liquidación. No se deben generar pagos automáticos desde un PDF descargado ni desde campos enviados por el navegador.

Los cambios en GoHighLevel y el despliegue se verifican por separado. Este fichero no es una prueba de publicación.
