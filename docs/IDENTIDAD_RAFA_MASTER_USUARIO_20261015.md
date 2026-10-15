# OPORTUNIIA — Identidades operativas aprobadas (2026-10-15)

Estado: ESPECIFICACIÓN EN RAMA DE TRABAJO. NO IMPLANTADO NI DESPLEGADO.

## Cuentas requeridas
- username: RafaMaster; role: superadmin; recovery_email: rafa.querol77@gmail.com
- username: rafa.querol; role: user; recovery_email: rafa.querol77@gmail.com

## Requisitos obligatorios
- Autenticación y autorización locales a esta aplicación. Ninguna aplicación (incluida CORE) controla el login de otra.
- Verificar credenciales y rol en el servidor; jamás conceder rol por coincidencia del nombre de usuario.
- Cuenta rafa.querol con restricciones reales de usuario, sin bypass, datos falsos ni privilegios encubiertos.
- Formulario con nombre de usuario, contraseña, botón accesible mostrar/ocultar y recuperación de contraseña por email verificado con token temporal de un solo uso.
- Almacenamiento de contraseña mediante algoritmo de hash resistente (Argon2id o equivalente). No contraseñas ni hashes en Git, logs o variables frontend.
- No asignar contraseña desde este documento: provisionar con mecanismo administrativo seguro y verificación de titularidad del correo.
- Evitar compartir contraseñas entre aplicaciones, aunque el usuario lo ha solicitado; cualquier excepción exige aceptación explícita del riesgo.
- No modificar producción, main, datos reales ni accesos existentes hasta superar pruebas y obtener autorización.
- Tests: login correcto/incorrecto, rol normal vs superadmin, recuperación, caducidad de tokens, controles de acceso a endpoints, ausencia de escalada de privilegios.

## Estado
Pendiente auditoría del backend, implementación, provisión de cuentas, pruebas E2E y despliegue. Este archivo no crea cuentas.
