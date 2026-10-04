# MI OPORTUNIIA · Secretaría Premium contextualizada (decisión 2026-10-03)

## Directriz del propietario
Analizar la documentación privada **con autorización del titular** para proponer recordatorios personalizados en función de su situación declarada: periodicidad y día de cobro, próximas revisiones documentales y calendario fiscal/tributario pertinente. No reducir la secretaría Premium a avisos genéricos de revisión documental.

## Implementación inicial (sandbox)
- `mi_personalized_secretary.py` propone señales conservadoras de nóminas y declaraciones: fecha histórica etiquetada de abono, periodicidad expresamente indicada y residencia fiscal declarada. Conserva referencia del documento original pero no copia el texto, cuantías, identificación personal ni documentos a la cola de correo.
- La IA/OCR **no confirma** por sí sola ni situación fiscal actual ni calendario obligatorio; toda propuesta exige validación por el titular. Para recurrencias simples de nómina, solo aceptar días 1–28 para evitar errores de final de mes, pendiente de ampliar el calendario de fin de mes según confirmación del usuario.
- No calcular fechas tributarias a partir de declaraciones antiguas; serán reglas jurisdiccionales **versionadas, contrastadas con fuentes oficiales para el ejercicio concreto**, y activadas solo cuando el inversor confirme su jurisdicción, situación y preferencias. Presentar aviso informativo, no asesoramiento tributario.
- Correo `info.web@oportuniia.com`: mensaje discreto sin importes, nombres de documentos, NIF ni detalles fiscales; la explicación y tareas se consultarán tras autenticación en MI OPORTUNIIA.

## Siguiente desarrollo
1. Canalizar texto OCR limpio y autorizado del organizador al extractor; mostrar propuesta, fecha original y advertencias en UI privada, sin conservar el texto sensible.
2. Endpoint de confirmación revocable de las señales, independiente de la edición del documento original; retención mínima y consentimiento diferenciado para procesamiento analítico.
3. Convertir la situación confirmada en calendario de recordatorios (nóminas mensuales, recurrentes personalizadas, ventanas fiscales contrastadas oficialmente) con edición por usuario y sin duplicados en outbox.
4. Probar casos: nómina desactualizada, mes de 28/29/30/31 días, cambio de empleo, residencia fiscal distinta, autónomos/sociedades, renta de ejercicio antiguo, consentimiento retirado, Premium caducado, varias personas con documentos similares.
5. Los servicios R2/ClamAV/OCR, correo corporativo real, n8n/cron, suscripciones y validación LEGAL siguen siendo puertas previas de despliegue.
