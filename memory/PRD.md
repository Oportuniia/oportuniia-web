# OPORTUNIIA · WEB 2.0 — PRD

## Contexto
"Full App Execution Project": entorno de control (FastAPI/React) para editar borradores de Elementor en un WordPress de producción bajo modelo estricto de "CERO MUTACIONES". Fase actual: diseño visual premium/institucional en prototipo local `/app/frontend/public/web2.html`. NO tocar WordPress hasta orden explícita "VISUAL REVIEW APPROVED, PROCEDE AL PORT".

## Reglas duras
- CERO mutaciones a WordPress / Write Bridge / Elementor / producción.
- Terminología: CDR = CESIÓN DE REMATE. ROI = ROI (nunca "ROI objetivo/potencial"). Prohibidos: Deal flow, Acceso controlado, Modalidad 01/02/03, etc.
- Switch Oportunidades: MISMAS 3 operaciones, in-place (nada de duplicar/ocultar tarjetas).
- Screenshots del prototipo: usar query `?v=N` para saltar caché.

## Archivo único de trabajo
`/app/frontend/public/web2.html` (HTML+CSS+JS vanilla, tipografía Poppins).

## Estado — CREATIVE REBUILD V9 (implementado, 2026-06)
Refinamiento quirúrgico sobre base V2 (aceptada). Verificado en desktop/tablet/móvil vía screenshot_tool:
1. Logo header +presencia (46px→60px) sin subir altura header (84px).
2. "Cómo trabajamos": titular 2 líneas desktop ("Una forma de trabajar." / "Cada operación, una estrategia.") + copy lateral nuevo. Sec-head a ancho completo para forzar 2 líneas sin reducir tipografía.
3. "Acceso profesional": titular 2 líneas ("Elige cómo quieres trabajar" / "con OPORTUNIIA.") + copy lateral nuevo.
4. Nuevo bloque "Oportunidades a tu medida" dentro de Acceso (beneficio de cuenta, no SaaS; claim "Dinos qué buscas. Nosotros acotamos el terreno."; chips NPL/CDR/REO/tipo/importe/ubicación/situación/estrategia; nota "próximamente").
5. Switch Recuperación↔Acuerdos INEQUÍVOCO: en Acuerdos la foto se repliega a franja oscura (identidad preservada por tag+ubicación), ROI protagonista (60px), OCUPACIÓN en caja destacada, + Tiempo/Acuerdo. Mutación in-place vía data-rec/data-acu en JS.
6. Fotografía: fachadas/edificios reconocibles (sin aéreas). Ubicaciones variadas: Sevilla (NPL), Alicante (CDR), Zaragoza (REO).
7. ROI mayor jerarquía en tarjetas.
8. Tecnología: CTA "Conoce nuestra tecnología →" ahora enlaza a bloque real de CAPACIDADES (Analizar/Estructurar/Contrastar/Presentar), no a Acceso.
9. Grupo OPORTUNIIA: intacto (oscuro, logos protagonistas). OPORTUNIIA→oportuniia.com; LIVING sin URL confirmada (href="#" preparado); ROBOTICS sin enlace (Próximamente).

Estado V9: PASS.

## Estado — CORRECCIÓN VISUAL V10 (implementado, 2026-06)
Sobre feedback de Human Visual Review:
1. Logo header: nuevo asset con TRANSPARENCIA real generado desde `LOGO PARA DOCUMENTACION.jpg` (flood-fill de fondo blanco preservando interior del escudo, recorte a bbox) → `/app/frontend/public/oportuniia-logo.png`. Sin caja blanca, integrado nativo. Altura 46px.
2. Oportunidades: ELIMINADA la fotografía de fondo ambiental de la sección (prod-bg). Fondo oscuro limpio premium.
3. Switch Recuperación/Acuerdos convertido en pieza protagonista (`.modeswitch`/`.ms-pill`): ancho, centrado, contundente, JUSTO encima de las 3 tarjetas + microayuda discreta. Copy "Ver desde Recuperación / Ver desde Acuerdos".
4. Fotografía de operaciones con más variedad y presencia (media 256px en Recuperación): edificio residencial ornamentado (Sevilla), apartamentos turísticos con piscina (Alicante), nave logística con muelles (Zaragoza).
5. Acuerdos: foto reducida a 128px pero RECONOCIBLE (grayscale .5/brightness .62, tag+ubicación intactos); ROI 66px, OCUPACIÓN en caja protagonista, Plazo + Acuerdo. Transformación inequívoca, misma operación.
6. Nota demo reducida a "* Datos demostrativos." (11px, discreta, al final).
7. Eliminada la explicación diff-line bajo las tarjetas.
8. Footer: eliminada "La misma oportunidad, dos maneras de abordarla." (solo "Humanizamos la deuda.").

Estado V10: PASS — READY FOR HUMAN REVIEW.

## Backlog (bloqueado hasta aprobación visual)
- P1: Portar diseño a Elementor JSON (`_elementor_data`) HOME 2.0 (ID 1630) y HEADER 2.0 (ID 1641).
- P1: Ejecutar Write Bridge (solo tras autorización explícita).
- P2: QA responsive dentro de Elementor tras escritura.
- Pendiente confirmar: URL oficial LIVING EXPERIENCE; destino público definitivo de Tecnología.

## Salud
- Roto: ninguno. Mock: ROI/plazos/ubicaciones/valor de compra son DEMO (se sustituirán por operaciones reales 1:1).
