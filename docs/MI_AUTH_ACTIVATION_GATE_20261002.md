# MI OPORTUNIIA · Activación de identidad soberana

Estado: código y pruebas unitarias en rama sandbox. Prohibido habilitar en producción sin completar estas condiciones.

El alta pública y los códigos definitivos de inversores/colaboradores son responsabilidad exclusiva de WEB. GHL queda dedicado al embudo de suscriptores, sin intervenir en códigos ni archivo documental. LEGAL no participa.

## Lo preparado
- `backend/mi_auth.py`: endpoints de registro, confirmación de correo, login/logout, sesión privada, consulta de perfil y aprobación inicial, TODOS denegados hasta activar `MI_AUTH_ENABLED=1`.
- `backend/personal_user_registry.py`: secuencias separadas de códigos para INVERSOR/COLABORADOR e índice de unicidad; contraseña/código de correo nunca son el código de identificación.
- `backend/personal_document_storage.py`: adaptador R2 aislado sin rutas ni acceso anónimo; requiere integración con sesión real, metadatos Mongo, antivirus/verificación real y un bucket privado separado.

## Condiciones de activación
1. Aprobación del propietario para habilitar WEB pública y sustituir expresamente enlaces antiguos de registro.
2. Crear DB o colecciones aisladas con política de permisos, backups, conservación, borrado y auditoría; confirmar que no hay cuentas anteriores y reserva de secuencias/códigos históricos. En la primera versión los correos serán únicos por cuenta.
3. Configurar remitente SMTP profesional, SPF/DKIM/DMARC, `MI_PUBLIC_ORIGIN` exacto HTTPS y dominio de correo. Configurar `MI_TERMS_VERSION` únicamente tras aprobar legalmente la versión vigente; el servidor deniega registros sin dicha versión y rechaza formularios obsoletos. No publicar secretos.
4. Establecer verificación de personas/representantes proporcional a las operaciones; configurar personal administrativo identificado, autorización por rol/MFA, revisión auditada. El token de bootstrap es solo provisional y debe sustituirse por consola administrativa segura antes de uso público.
5. Controles antiabuso distribuidos con `mi_rate_limits` (Mongo, TTL) y clave `MI_RATE_SECRET` de 32+ caracteres incorporados en sandbox para registro, verificación, acceso y recuperación; verificar comportamiento real de IP/proxy en Render. Recuperación por token, cierre global de sesiones y su interfaz añadidos. **Pendiente:** reenvío de verificación, pruebas integradas SMTP/Mongo, auditoría de respuestas y pruebas con proxy real. Hasta entonces, NO habilitar.
6. Endpoints documentales solo después de conexión a sesión real y prueba de acceso cruzado; R2 privado nuevo con límites y validación de contenidos.
7. Validación jurídica de textos de privacidad, condiciones de tratamiento, documentación requerida y minimización.
8. Tests integrados con Mongo efímera y SMTP ficticio: registro/duplicados, caducidad, simultaneidad de códigos, sesiones/CSRF, bloqueo de abusos, denegación de documentos ajenos. Prueba aislada de carga antes de 750 usuarios. No enviar pruebas a producción.

## Operativa
- Mantener `MI_AUTH_ENABLED` AUSENTE o `0` en producción hasta terminar el gate.
- PR abierto solo para revisión de código. La existencia de clases/rutas no implica sistema comercial activado.

## Avance de implementación en sandbox (2026-10-02)
- Interfaz /mi-oportuniia.html servida por /mi-oportuniia: perfil, documento privado, carga y PDF Premium con revisión manual.
- Endpoints /api/mi/private/profile, /documents, /documents/upload-intent, /documents/{file_id}/confirm y /premium/pdf/{file_id}/inspect|confirm.
- Almacenamiento documental separado y antivirus ClamAV (configurar `MI_PRIVATE_FILES_ENABLED=1` solo después de provisionar R2 privado + ClamAV y pruebas integradas).
- Organizador por texto embebido en PDF (no OCR de escaneos/fotos); requiere `MI_ORGANIZER_ENABLED=1`, verificación de suscripción de fuente confiable y originales escaneados. Derivados quedan en QUARANTINED hasta escaneo de salida; descarga no implementada.
- `MI_AUTH_ENABLED` debe permanecer 0 hasta tener SMTP, antiabuso validado, consola administrativa MFA, contratos y pruebas E2E.
- Documentos privados requieren nuevas colecciones, políticas de cuotas, concurrencia, restauración, borrado RGPD y rendimiento verificado. No afirmar que el servicio está listo para usuarios reales.
