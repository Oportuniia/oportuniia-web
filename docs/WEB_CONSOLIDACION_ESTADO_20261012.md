# OPORTUNIIA · Consolidación web · 12/10/2026

## Alcance
Rama de trabajo aislada: `feat/web-consolidacion-segura-20261012`. Sin merge a rama principal ni despliegue manual a producción.

## Implementado en esta rama
- WEB-02: rutas React de login, registro de inversor y solicitud de colaboración; formularios de demostración sin backend, sin envío ni almacenamiento.
- Rewrites Vercel para estas rutas y para tecnología, inversor y Premium.
- WEB-03: filtrado local en catálogo privado de demostración por texto, producto, situación, ubicación y universo.
- Identificación expresa de datos de demostración; eliminado nombre personal hardcodeado de la cabecera privada.

## Límites y bloqueos de lanzamiento
- NO hay autenticación real, registro real, envío de formularios ni recuperación de contraseñas.
- NO hay cobros reales; checkout Premium es sandbox. Las tarifas mostradas en el código no constituyen aprobación comercial.
- El catálogo privado contiene datos de muestra, no 24 operaciones reales. Favoritos, guardar búsqueda, añadir operación y otros botones todavía no están conectados a backend.
- MI OPORTUNIIA no puede declararse área privada segura: falta control de acceso del servidor y permisos por rol.
- No se ha acreditado QA en navegador, despliegue de vista previa ni prueba de extremo a extremo.
- Pendientes auditoría legal y de protección de datos, responsive, accesibilidad, enlaces y conexiones M2M.

## Condición de publicación
No fusionar ni publicar hasta contar con autenticación y autorización reales, integración backend validada, pruebas funcionales y revisión expresa del responsable del proyecto.
