# MI OPORTUNIIA · ARQUITECTURA DE PRODUCTO v1.0
**Ámbito:** web pública, aplicación privada, búsqueda y fichas, servicios Premium e integración con Presentación y OPORTUNIIAPP.
**Autoridad de aprobación:** Rafa. **Estado:** propuesta de ejecución en rama de pruebas; no autorización de producción.
**Fuentes contrastadas:** `frontend/src/App.js` en `feat/web-consolidacion-segura-20261012` (incluye ruta `/mi-oportuniia`, componentes `DealCard` y fichas privadas); `feat/mi-oportuniia-professional-engine-20261009` (12 prestaciones Premium y modalidades A/B/C/D); `feat/mi-oportuniia-favorites-saved-searches-20261010`; `oportuniia-presentacion/README.md` (motor documental PC/RE/IC/RF y API); `docs/ARQUITECTURA_M2M_MASTER_v1.md`. La interfaz histórica del vídeo del propietario es referencia visual de aceptación, no evidencia de que su código esté localizado.
## 1. Decisión de producto
MI OPORTUNIIA es **aplicación privada de inversión**, no duplicado de la web pública ni back office de administración. Se comparte **design system** (logo oficial, Poppins, paleta, botones y tarjetas), pero se separan navegación, composición y contenido. La web pública conserva filosofía, captación y servicios; la privada ofrece resumen, exploración, análisis y gestión. Nunca incrustar `web2.html` en un iframe privado.
## 2. Interfaz y navegación
Shell privado: barra lateral azul noche; cabecera contextual con búsqueda, avisos, identidad/perfil y etiqueta DEMO cuando proceda; superficie blanca/gris clara, tipografía Poppins; responsive. Inicio/resumen con KPIs de usuario y actividad. Menú: Resumen; Oportunidades; Favoritos; Búsquedas guardadas; Mis reservas; Mis operaciones; Documentación; Comunicaciones; Premium; Peticiones a la carta; Perímetros; Secretaría; Recordatorios; IA; Apoyo LEGAL; Visitas; Mi perfil; Notificaciones. Mostrar u ocultar entradas según rol y permisos, sin eliminar acceso a información ya autorizada.
## 3. Buscador y catálogo
Selector visible de universos **Ejecuciones Judiciales / Universo Acuerdos**. Su cambio altera la identidad cromática contextual **verde/blanco** aprobada y el universo de resultados, sin alterar la navegación. Filtros: texto libre; NPL/CDR/REO; CCAA/provincia/municipio; ubicación; rango precio/capital; ROI; plazo; tipo activo; procedimiento; fase; hito procesal; situación judicial; ocupación; orden y favoritos. Estado de filtros serializable en URL, chips activos, limpiar, guardar búsqueda y contador. Tarjetas **compactas** con fotografía, código, ubicación, precio/capital, ROI, plazo, estado, favoritos y acceso a ficha. Diseño inspirado en fichas públicas, sin textos corporativos ni enlaces públicos.
## 4. Ficha privada
Cabecera y galería; resumen ejecutivo; estrategia/ROI/plazo/capital con hipótesis; procedimiento/fase/hitos/ocupación; reportaje y comprobaciones; documentación por permiso; actividad/trazabilidad; favoritos; reservar; solicitar información/visita; generar o consultar presentaciones. Cada acción tiene estado: solicitado, en curso, completado, rechazado y evidencia, si existe soporte real. Nunca representar botones sin destino o sin explicar que la acción es DEMO.
## 5. Responsabilidad por sistema
| Dominio | Propietario soberano | WEB |
|---|---|---|
| Identidad, navegación, buscador y favoritos de usuario | WEB para experiencia y preferencias; backend autorizado para persistencia | Renderiza y controla acceso |
| Inventario de oportunidades, estados de operación y reservas | OPORTUNIIAPP / backend operativo que corresponda | Consulta proyecciones autorizadas, solicita acciones |
| Documentos PC/RE/IC/RF y PDF | PRESENTACIÓN | Solicita/consulta y muestra artefactos autorizados |
| Criterio jurídico y decisiones legales | LEGAL | Muestra estados recibidos; no los calcula |
| PBC/Compliance y clearance | Sistema responsable de Compliance | Muestra requisitos y estado, nunca concede clearance |
| Enriquecimiento territorial | CORE | Consume datos ya enriquecidos |
| IA | IA OPORTUNIIA | Interfaz de consulta con permisos y advertencias |
| Secretaría | Servicio operativo responsable | Bandeja documental y seguimiento; no sustituye Compliance |
## 6. Contratos de integración
La UI no consulta bases de datos ajenas. Definir APIs versionadas de lectura de catálogo/ficha, perfil/permisos, favoritos, búsquedas, reservas, solicitudes, documentos y notificaciones. Para intercambios entre sistemas aplicar `ARQUITECTURA_M2M_MASTER_v1`: HTTPS, credenciales por relación, deny-by-default, `event_id`, `correlation_id`, `payload_hash`, ACK, idempotencia, outbox/inbox, reintentos y auditoría. Las acciones financieras, jurídicas y de compliance requieren autoridad del servicio soberano y nunca se completan desde el navegador.
## 7. DEMO realista, no engañosa
Dataset sintético de al menos 24 oportunidades con identificadores estables, geografía y datos consistentes; NPL/CDR/REO y ambos universos. Entidades relacionadas sintéticas: 4 roles (Normal/Premium/Colaborador/Canal profesional), usuarios, favoritos, búsquedas guardadas, reservas, operaciones, documentos, tareas, solicitudes y notificaciones. Persistencia de prueba en backend sandbox o almacenamiento local claramente etiquetado como DEMO; botones ejecutan transiciones visibles y reversibles, no alertas sin estado. Los PDF DEMO deben generarse realmente o deshabilitarse con motivo visible. Ninguna operación ficticia se publica como real.
## 8. Seguridad
Autenticación real de backend antes de producción; el parámetro `?demo=1` solo puede existir en despliegues de demostración aislados sin datos reales. RBAC en servidor y filtrado de documentos según perfil. No basta ocultar botones ni usar `sessionStorage`. Auditoría de accesos y acciones; secretos nunca en frontend.
## 9. Plan de reconstrucción (orden obligatorio)
**F0 — Recuperación:** inventariar archivos, commits y ramas WEB 5/6 y Arquitectura 3/4, comparar diseño histórico, componentes y contratos; determinar origen exacto del vídeo. Registrar qué existe, qué es mock y qué falta.
**F1 — Design system y shell:** reconstruir sidebar/cabecera, responsive, navegación y estados; retirar iframe de web pública.
**F2 — Catálogo:** tarjetas compactas, selector visual verde/blanco, filtros combinables, favoritos y búsquedas guardadas.
**F3 — Ficha y flujos:** detalles, reservas, operaciones, solicitudes, documentación y notificaciones DEMO con persistencia coherente.
**F4 — Servicios Premium:** módulos y restricciones por rol, 12 prestaciones y estados.
**F5 — Integraciones:** contratos WEB↔OPORTUNIIAPP y WEB↔PRESENTACIÓN, verificación de permisos, trazabilidad y errores.
**F6 — QA:** pruebas E2E de navegación, filtrado, guardado, ficha, acciones, PDF, permisos, móvil y accesibilidad. Validar captura por captura contra vídeo histórico.
## 10. Gates de aceptación
G1: cero contenido corporativo dentro de la experiencia privada, cero iframe público.
G2: cada filtro afecta resultados y es combinable; el selector cambia universo y color; tarjetas compactas.
G3: cada botón visible funciona o indica de manera explícita por qué no está habilitado.
G4: las acciones DEMO dejan estado persistente coherente en los módulos correspondientes.
G5: Presentación y Compliance mantienen soberanía; no se finge conexión real.
G6: no se toca producción sin autorización y pruebas documentadas.
**Estado de ejecución:** arquitectura documentada; implementación integral y QA pendientes. No declarar terminado sin pruebas.
