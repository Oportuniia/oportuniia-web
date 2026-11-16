# Entrega de partners y bonos - 16 noviembre 2026

## Aprobado
Norma: POLITICA_PARTNERS_REFERIDOS_20261116.md. El último criterio de Premium es canje voluntario: 1 bono por mensualidad al 50%; 3 por mensualidad gratuita. Los consumidos no vuelven a contar. No convertir automáticamente saldos.

## Implementado y probado localmente
- Motor de porcentajes y plazo de dos años desde el alta; guardas de consentimiento y modalidad A; elimina el antiguo cálculo preliminar del 15% de una operación de colaborador.
- Banco persistente con concesión idempotente por identidad canónica de inversor, reserva atómica, elección de canje, confirmación contra referencia de facturación y rechazo de doble gasto.
- Consulta privada de norma y saldo, y descarga autenticada de los cinco dosieres.
- Material de formación con respuestas por identificador para poder barajar opciones.
- Cinco dosieres de una página y manual de dos páginas con guiones de vídeo. No se han generado vídeos.
- 31 pruebas locales pasan con datos ficticios en memoria. No son pruebas de cobro ni pruebas con Mongo de producción.

## Interfaces
GET /api/account/referrals/policy
GET /api/account/referrals/bonuses
GET /api/account/referrals/dossiers/{partner|suscriptor|equipo|colaborador|inversor}
Todas requieren la sesión WEB existente. No reciben claves en URL ni permiten asignarse bonos.

## Pendiente para operación real
Rafael confirma en esta entrega que el cobro Premium todavía no se ha activado. No activar pagos ni contratar un proveedor como efecto de publicar estos documentos. El bloqueo de facturación debe mantenerse explícito.
1. Conectar el cierre y cobro verificados con la concesión del bono. La reserva Stripe existente NO prueba por sí sola el cobro de honorarios propios. No usar generated_income como base propia sin reparto verificado.
2. Conectar la elección de canje con la siguiente mensualidad y la confirmación del proveedor de facturación. Por eso la API devuelve BILLING_NOT_CONNECTED y no expone un canje público que aparente funcionar.
3. Completar registro y comprobación del reconocimiento firmado de apadrinamiento y modalidad A; el origen por cookie no basta.
4. Completar libro de liquidaciones, reversos y conciliación. El cálculo no es una transferencia bancaria.
5. Incorporar el complemento a los cursos realmente publicados; el JSON no cambia automáticamente GHL ni APP.
6. Formalizar la actualización de plantillas contractuales conservando originales firmados; la norma y los dosieres no sustituyen automáticamente un contrato.
7. Verificar el recorrido autenticado en producción y la facturación en modo de pruebas, sin cargos reales.

No declarar terminada la implantación completa hasta resolver los puntos anteriores. Los dosieres explican la norma aprobada, no certifican la disponibilidad técnica.

## Identidad visual corregida
Logo aportado expresamente por Rafael el 16 de noviembre: OPORTUNIIA SIN FONDO PNG.png, conservado sin modificación en docs/brand/oportuniia-oficial-20261116.png. Sustituye en estos dosieres al logo histórico y al emblema de OPORTUNIIAPP usados inicialmente por error. Poppins, fondo azul oscuro, cian y blanco.
