# Cuentas reales y seguridad · preparación aislada · 14/10/2026

## Estado exacto

Implementación en `feat/ultima-milla-consolidacion-20261014`. Main, producción, DNS, web antigua, buzones y otros módulos no se han modificado. La interfaz DEMO se conserva mediante `?demo=1`. El acceso oficial `/mi-oportuniia` requiere sesión del servidor; `/cuenta` contiene el acceso real. No se afirma que las altas estén activadas.

Servicio aislado Render (Free, Frankfurt): `oportuniia-web-private-staging`, `srv-db7q9ffavr4c7396bc3g`. Se añadió porque los servicios existentes WEB siguen main/producción o son adaptadores públicos sin cuentas. Se reutilizan cuenta Render, repositorio WEB, FastAPI/MongoDB, el gateway de inversores, las fichas autorizadas, el perfil PF/PJ, geografía, OCR de Secretaría y el modelo de sesiones opacas de OPORTUNIIAPP. No se mezclan identidades administrativas de CORE con inversores ni se replican datos de producción.

## Implementación

- Registro de inversor/colaborador; nombre/email no habilitan operaciones. Confirmación del email mediante token aleatorio de un solo uso y 30 minutos, almacenado por hash y enviado en fragmento de URL; no se confunde con verificación de identidad.
- Contraseña bcrypt con mínimo de 12 caracteres y rechazo explícito del límite de 72 bytes. Sin contraseñas iniciales conocidas, registro admin ni autoaprobación.
- Sesión opaca en cookie `__Host-opp_session`, Secure/HttpOnly/SameSite, hash en base de datos, caducidad absoluta 12 horas e inactividad 30 minutos. Revocación por cierre, desactivación, cambio de contraseña y versión de sesión. Sin tokens ni perfiles reales en localStorage.
- CSRF por origen HTTPS fijo, cookie/token vinculado a la sesión y cabecera en todas las escrituras privadas. Registro/login/recuperación exigen origen y JSON. Límites atómicos compartidos en Mongo y límites del cuerpo, incluidos envíos por fragmentos.
- Doble factor TOTP con secreto cifrado, contador antirrepetición, retos cortos de cinco intentos y códigos de recuperación guardados por hash y de un solo uso. Activar MFA revoca sesiones anteriores; el gateway real lo exige por defecto.
- Recuperación de contraseña de un solo uso, ligada a la versión de cuenta; invalida todas las sesiones. No elimina el segundo factor.
- Persistencia de perfil, fotografía normalizada, preferencias, mensajes, notificaciones y operaciones, siempre por el sujeto obtenido de la sesión. Roles del navegador y IDs arbitrarios no dan acceso.
- Archivos propios: límite 20 MB, comprobación de firma/tipo, clave elegida por servidor y S3 privado con KMS. En cuarentena hasta escáner; errores/infecciones impiden lectura. Descarga propia y de revisor autorizada en cada solicitud, con hash, no-store y auditoría.
- Cola interna de revisión con allowlist de sujetos configurada exclusivamente en servidor y MFA, sin autoaprobación. Requiere expediente completo y documentos propios limpios. Snapshot y decisión inmutables; sin permisos de operación automáticos. Revisión vigente 90 días. Cambiar el perfil o la revisión invalida los permisos anteriores, también frente a carreras mediante revisión de versión.
- PC/RE/IC/RF/LEGAL siguen el gateway PRESENTACIÓN/LEGAL ya creado: permiso por usuario/OP, propietario, integridad y autorización. Premium no sustituye identidad, expediente ni PBC/FT.
- Conector Stripe preparado, cerrado por defecto y sin claves ni cargos reales. Precios/condiciones aprobados solo desde servidor. Checkout idempotente; webhook con firma, entorno y estado fresco del proveedor; ninguna URL del navegador activa Premium. Plan anual cancela renovación al final del periodo. Reserva pagada queda pendiente de revisión de la operación. Su devolución/cancelación comercial y los textos deben validarse antes de activar cobros.
- Avisos operativos: respuesta privada y notificación sin leer; cola de copia de aviso por email, preferencia propia, sin documentos judiciales en correo. Aceptación SMTP/MTA no equivale a entrega. Claims ambiguos tras caída se revisan manualmente en lugar de reenvío ciego.
- Mantenimiento reutilizable desde el orquestador existente: `/api/m2m/maintenance/run`, clave dedicada privada; procesa un aviso y un archivo por llamada. No hay cron/chatbot nuevo ni tareas reales activadas.

## Correo y hosting acordados

Webempresa aloja la web antigua y el correo. La nueva WEB está en Vercel y su API aislada en Render. Cambiar posteriormente la web de `oportuniia.com` no exige mover el correo: se conservan MX, DKIM, SPF y demás registros necesarios. Buzón previsto WEB: `info.web@oportuniia.com`; APP/CORE y demás módulos tendrán buzones separados. Que se consulten desde Gmail no convierte a Google en su alojamiento.

Render Free bloquea SMTP 25/465/587. `deploy/webempresa-mail-bridge/` prepara un puente HTTPS firmado para usar el MTA del hosting existente; configuración y nonces fuera de public_html, clave privada, límite de tamaño, firma HMAC, ventana temporal y rechazo de replay. NO se ha instalado en Webempresa ni se ha enviado correo. Alternativamente, SMTP directo solo en un entorno que permita esos puertos; no se ha contratado plan de pago.

## Configuración pendiente para abrir cuentas

1. MongoDB Atlas existente: crear o identificar base de staging y usuario restringido a ella; establecer `MONGO_URL`/`DB_NAME`. No se ha podido leer ni reutilizar una credencial de producción desde el conector. No se usa una base simulada en el servicio desplegado.
2. Crear y comprobar el buzón de Webempresa. Instalar/probar el puente revisado y configurar `WEB_MAIL_BRIDGE_URL`. Las claves de cifrado MFA y firma de puente están generadas y guardadas en Render; no están en el repositorio, frontend ni chat. El hosting necesita la clave en su fichero privado.
3. Publicar las versiones jurídicas definitivas y sus identificadores (`WEB_PRIVACY_VERSION`, `WEB_TERMS_VERSION`); las versiones QA no sirven para activar altas reales.
4. Activar explícitamente `WEB_IDENTITY_MODE=web_sessions` y registro solo tras comprobar correo/base/HTTPS. Mantener `WEB_REQUIRE_MFA=true`.
5. Para documentación: bucket privado/KMS con permisos mínimos, bloqueo de acceso público, almacenamiento/región y retención aprobados, escáner privado y revisión humana. No se han contratado estos recursos ni abierto subidas.
6. Configurar sujetos revisores con MFA; conectar autoridades M2M de PRESENTACIÓN/LEGAL y readiness, sin copiar claves a navegador. Asignación por OP y pruebas con documentos autorizados aún pendientes.
7. Para cobros: cuenta/pasarela y claves de prueba, precios autorizados, fiscalidad, condiciones/versiones, firma, importe de reserva por operación, devolución/cancelación y pruebas con webhook. Nunca activar claves reales por quitar un rótulo DEMO.

## Validación

55 pruebas backend superadas, incluidas 37 de identidad/gateway/servicios, con dependencias actuales fijadas en requirements-private.txt. Incluyen falsificación de roles, CSRF, caducidad, revocación, aislamiento, enlace de un solo uso, MFA/recovery, cuarentena, revisión, versión de perfil, precio de servidor, webhook/firma/replay, cola operativa y límites de cuerpo. Mongo simulado (mongomock) se usa solo en tests; no sustituye Atlas en el despliegue.

Recorrido Playwright sobre HTTPS local y datos sintéticos: alta → email simulado → MFA/autenticador y recuperación → sesión servidor → perfil guardar/recargar → consulta guardar/recargar → móvil 390/768 → logout. Sin correos reales, cobros ni documentos personales reales.

No es certificación externa, auditoría de penetración ni prueba de entrega SMTP/Atlas/S3/Stripe reales. La recepción/escaneo real, la matriz operativa final, las políticas definitivas y la puesta en producción permanecen pendientes de configuración y validación.


Verificación de regresión final: 55 tests backend locales seleccionados (las suites HTTP externas backend_test.py y test_filter_contract_v1.py necesitan su endpoint/configuración y no se incluyen). Las plantillas legacy se adaptaron a la API actual de Starlette; tz_aware se habilitó para las fechas de sesiones. En Preview se probaron de nuevo 16 rutas públicas, nueve assets originales por SHA-256 y las cuatro variantes de perfil DEMO. El flujo real con MFA también pasó con las dependencias actuales.

Puente PHP validado con php -l y ocho comprobaciones HTTP locales: solicitud válida, replay, firma falsa, expiración, JSON inválido, tamaño y dos inyecciones de cabecera/destinatario. El MTA se sustituyó por /bin/true; no se envió correo. Falta su prueba de entrega en Webempresa.

Handshake del despliegue: Render staging LIVE y Preview READY; /api/account/config devuelve identity_enabled=false y registration_enabled=false con no-store y require_mfa=true. Sin base configurada, las rutas privadas devuelven 503. Esta respuesta cerrada es intencional; no acredita una cuenta real activada.
