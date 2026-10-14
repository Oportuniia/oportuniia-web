# OPORTUNIIA · Última milla · Evidencias del 14/10/2026

Estado de la misión integral: **PENDIENTE**. Existe una versión Preview revisable; no es una entrega de producción ni una certificación de integraciones reales.

## Versión comprobada
- Rama: `feat/ultima-milla-consolidacion-20261014`.
- Base conservada: `36f85536c4863061ef3e52b22c7a98218aea9f24`.
- Implementación: `243b733c29b9184c7e8ad137d4eba3e6d24b06e5`.
- Corrección móvil: `301d1c6b820e85e01aea6ec498c6b35f67563007`.
- Preview comprobado: https://oportuniia-jw2c39k7i-oportuniia-app.vercel.app
- Aplicación: https://oportuniia-jw2c39k7i-oportuniia-app.vercel.app/mi-oportuniia.html?demo=1
- Producción antes y después: `dpl_CRghiUg5ZFAWGM7YE251L6ydv9VN`, main `ffaa1428847f21fb7246ee19d393d402cbf74d4e`. Sin modificaciones.

## Recuperación y conservación
Se compararon árboles de main, professional-engine, favorites-saved-searches, consolidacion-segura, visual-remix, web-oportuniiapp-control, presentation-web-consumer y m2m-master. Se leyeron la arquitectura de producto y el estándar M2M. Se revisaron README de los ocho repositorios relacionados; los README de LEGAL, VISUAL, LIVING y PRESENTACIÓN LEGACY no describen sus contratos, por lo que su revisión profunda sigue pendiente.

Se preservaron contenidos corporativos, imágenes y lógica pública de la base, precios, modalidades A/B/C/D y recursos originales. Se sustituyó la implementación privada provisional por módulos separados de interfaz, catálogo y estilos. Se centralizó la cabecera pública y se añadió menú móvil a las rutas React. La ruta /mi-oportuniia converge en la misma DEMO. Se conserva el logo horizontal existente; **la implantación y validación de los nueve PNG aportados no está cerrada**.

## Inventario público comprobado
Chromium, escritorio 1440×1000 y móvil 390×844. Todas las rutas siguientes: HTTP 200, siete enlaces principales coherentes, menú móvil operativo, sin desbordamiento horizontal ni errores JavaScript detectados. Esto no demuestra envíos de formularios ni integraciones externas.

| Ruta | Botones DOM |
|---|---:|
| / | 3 |
| /nuestra-filosofia | 1 |
| /como-funciona | 1 |
| /oportunidades | 4 |
| /grupo-oportuniia | 3 |
| /tecnologia | 1 |
| /contacto | 2 |
| /servicers | 1 |
| /acceso | 3 |
| /premium | 1 |
| /inversor | 1 |
| /login | 2 |
| /registro | 2 |
| /solicitar-colaboracion | 2 |

El inventario de destinos y acciones de todos los enlaces y formularios públicos todavía requiere cierre. Los enlaces legales de footer sin destino se identifican como pendientes y no se les ha inventado contenido. No se enviaron formularios externos ni mensajes.

## Funciones privadas
| Función | Estado | Evidencia o límite |
|---|---|---|
| Dashboard y navegación diferenciada | FUNCIONAL DEMO | Sin iframe público |
| Perfil, nombre, correo, empresa y preferencias | FUNCIONAL DEMO | Persiste tras recargar; texto de usuario escapado |
| Subir, cambiar y eliminar fotografía | FUNCIONAL DEMO | Archivo raster limitado y convertido a JPEG local; iniciales de respaldo |
| 24 oportunidades, ambos universos | FUNCIONAL DEMO | Identificadores sintéticos estables y fotografías ilustrativas |
| Filtros combinados y ordenación | FUNCIONAL DEMO | Filtro REO + Barcelona devuelve dos operaciones; estado serializable en URL |
| Favoritos | FUNCIONAL DEMO | Alta/baja y módulo relacionado persistente |
| Búsquedas guardadas | FUNCIONAL DEMO | Recuperación de criterios y eliminación con confirmación |
| Reservas A/B/C/D | FUNCIONAL DEMO | Vinculación a oportunidad, prevención de duplicados y cancelación |
| Operaciones | FUNCIONAL DEMO | Expediente sintético; una reserva pendiente no se convierte en operación aceptada |
| Solicitudes, visitas y cancelación | FUNCIONAL DEMO | Estado y actividad persistentes, sin envío real |
| Documentos | FUNCIONAL DEMO | Descarga de muestra TXT explícita; no es PDF oficial |
| Recordatorios | FUNCIONAL DEMO | Crear/completar/reabrir/eliminar; sin envío de avisos externos |
| Notificaciones | FUNCIONAL DEMO | Registro, lectura y acceso contextual |
| Servicios Premium | FUNCIONAL DEMO | Doce prestaciones y condiciones conservadas; sin pagos |
| Permisos | FUNCIONAL DEMO | Roles de demostración; no concede derechos ni permisos reales |
| IA, LEGAL y Secretaría | PENDIENTE | Formularios DEMO de solicitud; no simulan respuestas soberanas |
| Autenticación y persistencia real de usuario | PENDIENTE | No se conectaron cuentas, datos ni APIs de producción |
| PRESENTACIÓN PC/RE/IC/RF | PENDIENTE | Se revisó propietario/contrato; no se genera un motor alternativo |
| CORE / OPORTUNIIAPP / M2M | PENDIENTE | Sin cambios en los sistemas ni pruebas de transporte real |
| LIVING, vídeo y fullscreen con sonido | PENDIENTE | Se conservó el enlace existente; no se validó su reproductor |
| Páginas legales y todos los formularios externos | PENDIENTE | Requieren revisión completa y destinos autorizados |

## Pruebas privadas ejecutadas
Dieciséis comprobaciones pasan en Chromium contra el Preview de código 301d1c6, además de la prueba previa en sandbox:
1. Dashboard.
2. Perfil persistente y texto escapado.
3. Subida de fotografía persistente.
4. Eliminación e iniciales.
5. Cambio real de resultados por universo.
6. Filtros combinados.
7. Guardado y recuperación exacta de búsqueda.
8. Favoritos relacionados y persistentes.
9. Reserva vinculada y persistente.
10. Prevención de reserva duplicada.
11. Solicitud de visita visible en su módulo.
12. Cancelación persistente.
13. Descarga efectiva de archivo DEMO.
14. Recordatorio creado y completado.
15. Perfil normal DEMO no obtiene Universo Acuerdos mediante el selector.
16. Navegación privada a 390 y 768 px sin desbordamiento.

Cero errores JavaScript en esa suite. Se corrigió un fallo real de cierre del menú móvil al volver a pulsar la sección activa. Capturas producidas de dashboard, perfil y vistas móviles; la captura de escritorio se inspeccionó visualmente frente a la referencia. No se han certificado Safari/iOS ni dispositivos físicos.

## Reproducción
Instalar Playwright en un entorno de pruebas y ejecutar `node tests/private-e2e.cjs` con BASE_URL del Preview. SHARE_URL, cuando sea necesario, es temporal y se proporciona por entorno; nunca se guarda en código. PHOTO_PATH permite utilizar una imagen de prueba local. El resultado se escribe en /tmp/opp-private-e2e.json.

## Pendientes para cerrar la misión
Validar e implantar todos los logos aportados; cerrar inventario interactivo público, formularios y páginas legales; revisar contratos profundos de los sistemas cuyo README es genérico; comprobar LIVING; conectar y probar las APIs sandbox autorizadas con autenticación, permisos, trazabilidad y fallos; completar verificación visual móvil y Safari/iOS. No promover ni fusionar a main sin autorización expresa.
