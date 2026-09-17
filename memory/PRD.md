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

## Estado — CORRECCIÓN CONCEPTUAL V11 (implementado, 2026-06)
Corrección de MODELO del switch (cambio conceptual clave):
1. RECUPERACIÓN y ACUERDOS ya NO son la misma operación: son DOS CATÁLOGOS DISTINTOS. Recuperación = 3 operaciones (Sevilla/Alicante/Zaragoza · dark). Acuerdos = 3 operaciones DIFERENTES (Marbella villa+piscina / Valencia local comercial / Bilbao adosados · light). 6 fotos, ubicaciones y datos distintos.
2. Inversión visual DARK→LIGHT scoped SOLO a #producto (se neutralizó el flip global de `body.acuerdos`; el resto del sitio no cambia). Acuerdos: fondo claro, tarjetas blancas, texto oscuro, acento cian.
3. Switch protagonista sobre las tarjetas; eliminada la microfrase "misma operación/dos lógicas". Grids alternan con `.grid-rec`/`.grid-acu` (display + animación acuIn). JS simplificado (sin mutación in-place).
4. Fotos protagonistas y a color en ambos modos (media 256px); variedad (piscina, local, adosados, nave, edificio).
5. Logo header: PNG transparente derivado del asset oficial horizontal, altura 40px, limpio e integrado. Slot preparado para sustituir por PNG/SVG oficial transparente (ASSET REQUIRED reportado al usuario).
6. Acceso profesional CTAs: Inversor "Darse de alta", Colaborador "Darse de alta", Suscriptor "Entrar con mi código" (→ #acceso, sin backend).

Estado V11: PASS — READY FOR HUMAN REVIEW. Pendiente del usuario: PNG/SVG transparente oficial del logo para el final.

## Estado — AJUSTE V12 · LOGOS + ROI (implementado, 2026-06)
Cambios mínimos (resto FREEZE):
1. ROI demo actualizados (todos ≥22%, una operación extraordinaria al 45%):
   - RECUPERACIÓN: Sevilla 27,5% / Alicante 34,0% / Zaragoza 45,0%.
   - ACUERDOS: Marbella 24,5% / Valencia 29,0% / Bilbao 37,5%.
   - "* Datos demostrativos" presente. Layout sin cambios (misma altura/alineación).
2. Logos: NO recreados.
   - HEADER LOGO = PROVISIONAL (PNG transparente derivado del asset oficial JPG). OFFICIAL ASSET REQUIRED = YES.
   - GRUPO (OPORTUNIIA/LIVING/ROBOTICS) = renders 3D sobre fondo oscuro que se integran con la sección (tratamiento aprobado). Son mockups, no logos vectoriales oficiales transparentes → ASSET REQUIRED = YES (provisional) para cada uno. Enlaces: OPORTUNIIA→oportuniia.com, LIVING slot preparado, ROBOTICS sin enlace (Próximamente).

Estado V12: PASS. Bloqueado hasta que el usuario aporte assets oficiales de logo transparentes.

## Estado — LOGO FINAL FIX V13 (implementado, 2026-06)
- HEADER LOGO sustituido por el asset oficial transparente aportado por el usuario: `logo web.webp` (RGBA real, horizontal). Copiado byte a byte a `/app/frontend/public/oportuniia-logo.webp` (SIN procesar: sin flood-fill, sin quitar blancos, sin caja/fondo). CSS: height 70px, object-fit:contain, proporción preservada. Sin caja/halo/agujero. Integración limpia en header claro (desktop + móvil).
- SCOPE = header logo únicamente. ROI FREEZE, Grupo sin tocar, resto sin cambios.
Estado V13: PASS — header logo cerrado visualmente. (SVG maestro futuro será 1:1 sin bloquear.)

## Estado — V11 FASE 1 · TAXONOMÍA + UNIVERSOS (implementado, 2026-06)
Sobre `web2.html` (base aprobada), sin rediseño:
- TAXONOMÍA: tipologías = NPL / CDR / REO únicamente. "Acuerdos" NO es tipología (0 referencias como 4º tipo).
- INTERFACES/UNIVERSOS: renombrado definitivo del selector a "Ejecuciones Judiciales" ↔ "Universo Acuerdos" (eliminado "Recuperación": 0 referencias, incl. comentarios). data-mode = judicial/acuerdos; JS/CSS actualizados. Dos catálogos distintos (dark↔light) se mantienen; cada operación sigue siendo NPL/CDR/REO.
- Bloque explicativo ANTES del selector: "Dos formas de entrar. Una diferencia importante." con definición de cada universo (copy aprobado en la orden). Tematizado dark (judicial) y light (acuerdos).
- PROPUESTA DE VALOR Universo Acuerdos (visible solo en modo acuerdos): "Más control. Menos incertidumbre." + variables (Capital/inversión, Tiempo estimado, Resultado previsto, ROI, Situación del activo, Estructura del acuerdo).
- PLACEHOLDER VIP: nota "Universo Acuerdos formará parte de la Suscripción VIP · próximamente" + CTA Solicitar acceso. SIN precio, SIN pago (PAYMENT NOT IMPLEMENTED, PRICING NOT DEFINED).
- ROI FREEZE y logo FREEZE respetados.

PENDIENTE (fases siguientes de V11): arquitectura multipágina real (rutas, catálogo `/oportunidades`, ficha `/oportunidades/[slug]`, cómo-funciona, grupo, contacto, solicitar-acceso, área-privada), data model backend, filtros, integración GoHighLevel (URLs PENDING), SEO por página. Requiere OK de arquitectura + inputs humanos.

Estado V11-Fase1: PASS.

## Estado — V11 · CIERRE DE COMPRENSIÓN HOME (implementado, 2026-06)
- Titular universos: "Dos formas de entrar" → "Dos universos. Una diferencia importante." (evita sugerir misma operación con dos vías).
- Bloque explicativo NPL/CDR/REO (SOLO 3 tipologías) añadido bajo el titular "NPL, CDR y REO.": nombre + significado + 1 línea humana c/u (NPL=Préstamo impagado, CDR=Cesión de Remate, REO=Inmueble adjudicado). Tematizado dark/light. Responsive (3→1 col). Copy = PROPUESTO (pendiente validación humana).
- HOME ya cubre: qué es/ofrece OPORTUNIIA, NPL/CDR/REO, diferencia Ejecuciones Judiciales vs Universo Acuerdos, valor diferencial de Acuerdos, perfiles (Inversor/Colaborador/Suscriptor), siguiente paso (CTAs). Sin GHL URLs, sin pago VIP, sin multipágina, sin rediseño.
Estado V11-Cierre HOME: PASS.

## Estado — V11 · MASTER UX/IA · ITEM A (HOME) implementado (2026-06)
- Universo Acuerdos: +espacio bajo el bloque de valor antes del catálogo (margin 60px).
- Grupo: copy LIVING = "La compra de Obra Nueva se convierte en experiencia." (reduce tamaño + mover a último bloque = PENDIENTE, no ejecutado por riesgo de reordenar DOM).
- Inversor: intro "Elige cómo quieres participar en cada oportunidad." + A/B/C reescritas sin yoísmo.
- Colaborador: MODELO CLIENTE CORREGIDO ("Encuentra la oportunidad adecuada para tu cliente..."); A Resultado compartido / B Mantienes a tu cliente; CTA "Agenda una videollamada" (#agenda).
- Eliminado "Dinos qué buscas" → nuevo bloque "Agenda una videollamada" (#agenda, calendario PENDING) + banda "Fondos y servicers".
- Cómo trabajamos: intro tecnológica añadida; paso 03 sin "recuperar".
- Tecnología: cierre "La tecnología al servicio de la operación." (línea propia); eco-link → /tecnologia (ruta preparada, página pendiente).
- ROI/logo FREEZE respetados. No GHL/URLs inventadas. No multipágina/catálogo/ficha/área privada (ítems B–G pendientes).
Estado V11-ItemA: PASS.

## Backlog (bloqueado hasta aprobación visual)
- P1: Portar diseño a Elementor JSON (`_elementor_data`) HOME 2.0 (ID 1630) y HEADER 2.0 (ID 1641).
- P1: Ejecutar Write Bridge (solo tras autorización explícita).
- P2: QA responsive dentro de Elementor tras escritura.
- Pendiente confirmar: URL oficial LIVING EXPERIENCE; destino público definitivo de Tecnología.

## Salud
- Roto: ninguno. Mock: ROI/plazos/ubicaciones/valor de compra son DEMO (se sustituirán por operaciones reales 1:1).
