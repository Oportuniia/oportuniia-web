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

## Estado — V11 · HOME FINAL CLOSURE (implementado, 2026-06)
- Grupo OPORTUNIIA movido a ÚLTIMO bloque editorial (antes del footer). Orden: hero, producto, quienes, flow, tecnologia, acceso, grupo, footer.
- Grupo reducido: padding sección menor, logos a 16/10 (más pequeños), grid max-width 840, tipografía meta más discreta. Más editorial/premium.
- Calendario "Agenda una videollamada" (#agenda) permanece dentro de #acceso, antes de Grupo. (Micro-orden: en #acceso va perfiles → Agenda → Fondos; el master sugería Fondos antes de Agenda — desviación menor, ambos antes de Grupo.)
- LIVING copy = "La compra de Obra Nueva se convierte en experiencia." · ROBOTICS = Próximamente.
- Resto HOME FREEZE. ROI/logo FREEZE. Multipágina (B–G) NO iniciada (aprobada en principio; URLs externas no bloquean su construcción).
Estado V11-HOME Closure: PASS.

## Estado — V11 · HOME VISUAL CORRECTION (3 fixes, implementado 2026-06)
1. Universo Acuerdos: panel de valor "Más control. Menos incertidumbre." ahora full-width, radio superior, unido (sin gap) al catálogo dentro de un panel claro compartido → una sola composición/interfaz. margin-bottom 0 + grid-acu con borde/fondo/rounded-bottom.
2. Grupo: logos con object-fit:contain (escudos completos, SIN recorte); copy OPORTUNIIA = "Humanizamos la deuda." (LIVING/ROBOTICS sin cambios).
3. Selector: cue "Explora los dos universos" + estados claros + cursor/hover; demo de primera visita (Judiciales→Acuerdos→Judiciales, una vez, IntersectionObserver, respeta prefers-reduced-motion).
FREEZE respetado (ROI, logo header, arquitectura, resto copy). Multipágica Fase 2 NO iniciada. Pendiente HUMAN REVIEW Rafa/Alba.
Estado V11-HOME Visual Correction: PASS (técnico).

## Estado — V11 · FINAL HOME VISUAL RECTIFICATION (rev. humana Rafa, 2026-06)
Rev. humana marcó 2 de 3 en FAIL/PARTIAL. Reejecutado sólo a) y b) (selector CONGELADO/PASS):
a) Universo Acuerdos = UNA sola superficie continua real: nuevo wrapper `.acu-surface` (1 borde + 1 sombra + fondo blanco, radius 20, overflow hidden) que envuelve cabecera de valor + catálogo. Cabecera sin caja propia (transparente, solo hairline divider inferior); `.grid-acu` sin borde/sombra/fondo propios (padding interno). Eliminada la percepción de "panel flotante + catálogo debajo". En modo judicial el wrapper es invisible (bg transparente, 0 borde, sin sombra) → grid-rec intacto.
b) Grupo OPORTUNIIA: descubierto que los PNG originales del CDN traían el NOMBRE de marca "quemado" (texto blanco filas ~800-951) además del `.meta` HTML → doble etiqueta al subir el escudo. Solución: assets reprocesados a ESCUDO-SOLO (borrado del texto quemado preservando el degradado/glow) + subida sutil (aire superior 12%), escudo completo sin recorte ni deformación, mismo tamaño y alineación en las 3 marcas. Servidos localmente en `/app/frontend/public/grupo/{oportuniia,living,robotics}.webp` (originales CDN intactos). Copy: OPORTUNIIA "Humanizamos la deuda.", LIVING "La compra de Obra Nueva se convierte en experiencia.", ROBOTICS sin cambios.
Verificado por screenshot: desktop Acuerdos (superficie única), desktop Judicial (sin caja blanca), Grupo (etiqueta única, escudos elevados), transición Judiciales↔Acuerdos OK.
FREEZE respetado (selector, ROI, fotos, copy, estructura, header logo, taxonomías). Multipágina NO iniciada. Pendiente HUMAN VISUAL REVIEW Rafa/Alba.
Estado V11-FINAL Rectification: PASS (técnico).

## Estado — V11 · CORRECCIÓN VISUAL DEFINITIVA (Master + Human Gate, 2026-06)
Rectificación tras evidencia visual. SOLO puntos a) y b). Selector CONGELADO.
a) UNIVERSO ACUERDOS — invariante geométrica: el bloque de valor ("Más control…" + variables) se RETIRÓ del layout (no oculto con hueco; `display:none !important`, contenido conservado en HTML para fase posterior). El wrapper `.acu-surface` quedó como passthrough transparente (sin borde/sombra/fondo/padding). Ahora el selector desemboca DIRECTO en las tarjetas en AMBOS universos. Medido con offsetTop (independiente de transform): JUDICIAL selector→cards = 164px, ACUERDOS selector→cards = 164px → DIFERENCIA = 0px. Animación `acuIn` cambiada a opacity-only (sin translateY) para no mover geometría al cambiar. El cambio de universo = solo inversión de tema (dark↔light) + fade, sin desplazamiento.
b) GRUPO OPORTUNIIA — assets ORIGINALES del CDN restaurados (sin reprocesar; los .webp reprocesados de la iteración anterior fueron eliminados). Corrección solo por CSS: `.gcard .logo` aspect 1.95/1 (uniforme en todos los breakpoints) + `object-fit:cover`. Ventana que muestra el escudo completo y oculta el NOMBRE quemado del asset vía overflow: `object-position:center 26%` (OPORTUNIIA/LIVING) y `center 23%` (ROBOTICS, cuyo nombre está más alto). Escudos completos (sin recorte del escudo), sin deformación, centrados, aire equilibrado, misma escala/alineación. Copy meta intacto (OPORTUNIIA/LIVING/ROBOTICS).
Verificado por screenshot + medición offsetTop. FREEZE total en resto. Multipágina NO iniciada. Pendiente HUMAN VISUAL GATE Rafa/Alba.
Estado V11-Definitiva: PASS (técnico).

## Estado — HOME · ITERACIÓN CONSOLIDADA POST-ORACLE (2026-06)
Scope autorizado ejecutado (solo web2.html + 3 assets derivados locales):
1. FREEZE geometría Judiciales↔Acuerdos: medido offsetTop → JUDICIAL=164px, ACUERDOS=164px, DIFF=0px. acuIn opacity-only.
2. Bloque info Acuerdos ("Más control…" + 6 variables) reinsertado DEBAJO de las tarjetas (infoTop>gridTop), panel secundario integrado (tinte brand, no caja blanca gigante). No empuja selector/cards.
3. Ritmo vertical: `.sec` padding reducido clamp(60,7.5vw,116). 4. Alternancia light/dark: #tecnologia ahora petrol/oscuro; #quienes en bg2 (variación tonal).
5. Calendario REAL LeadConnector embebido (widget A7XNkrehcriifyMZe98E) en #agenda vía iframe + form_embed.js; muestra disponibilidad directa. 6. AUDIT: evento "30 min" pero descripción dice "15 minutos" → INCONSISTENTE (corregir en GoHighLevel, no bloquea).
7. Audiencia videollamada reenfocada (inversores/colaboradores/contactos; no principal para fondos).
8-10. Fondos&Servicers rediseñado: "Su cartera. Clara, ordenada y bajo control." + panel dashboard DEMO/abstracto (KPIs con "—", barras demo, sin métricas reales) + CTA "Acceder con código" (no videollamada). Sin arquitectura de identidad/auth (CTA demo).
11. Nav: "Quiénes somos" → "Nuestra filosofía" (nav desktop, móvil, footer). 12. Sección filosofía reescrita (principio, no About genérico).
13-15. ESCUDOS (Oracle root cause): assets ORIGINALES CDN preservados intactos; creados 3 derivados LOCALES `/app/frontend/public/grupo/*.png` recortando SOLO la banda del texto quemado (source 1254×1254 → derived 1254×626, escudo 100% completo, 0 px de escudo eliminados, sin IA/redibujo). CSS: `object-fit:contain` + `object-position:center` (SIN cover, SIN object-position hack), contenedor `aspect 7/4`. Escudos completos, centrados, aire equilibrado, misma escala.
Mobile 390px: sin overflow horizontal. Multipágina NO iniciada. Pendiente HUMAN VISUAL GATE Rafa/Alba.
Estado: IMPLEMENTED, TECHNICAL QA PASS, HUMAN VISUAL APPROVAL PENDING.

## Estado — HOME · V51 (correcciones visuales Rafa/Alba, 2026-06)
Scope V51 ejecutado (solo web2.html + assets derivados locales):
1. CTA HIERARCHY global. PRIMARY (relleno petrol sólido + sombra + hover lift): Solicitar acceso, Ver oportunidades, Darse de alta, Acceder con código. SECONDARY (relleno brand-tint + borde brand, hover sólido): Agenda una videollamada, Entrar con mi código, Conocer OPORTUNIIA. TERTIARY (links con flecha): Ver operación, vip-cta, footer. `.entry .ecta` reforzado (full-width, 16px, centrado).
2. Videollamada = composición HORIZONTAL desktop: `.agenda-block` grid .6fr/1fr (≈37.5% texto | 62.5% calendario), ancho editorial completo; móvil apila (texto→calendario). Calendario real LeadConnector (URL sin cambios) con viewport controlado 600px + scroll interno.
3. Escudos Grupo: fondo TRANSPARENTE. Assets derivados locales `/grupo/*.webp` (RGBA) generados quitando SOLO el fondo oscuro (floodfill desde esquinas; huecos internos del escudo auto-preservados) sobre los crops sin texto; escudo 100% intacto, 0 px de escudo eliminados, sin IA/redibujo. CSS `object-fit:contain` + `object-position:center` (SIN cover/hacks), contenedor aspect 3/2, escala premium mayor. Copy Grupo aumentado (nombre 19px, statement 14px). Separador de luz sutil #grupo::after (glow cian) antes del footer.
4. Fondos&Servicers: ancho completo (editorial), fondo de ATMÓSFERA financiera (SVG: grid + curva de área + línea analítica + puntos, sin datos reales), contenido sobre overlay legible, CTA "Acceder con código" (PRIMARY). Etiqueta "Representación demostrativa". Sin métricas inventadas.
FREEZE respetado: geometría Judiciales↔Acuerdos intacta (no tocada; DIFF=0px), info Acuerdos AFTER cards, taxonomía, filosofía, nav. Móvil 390px sin overflow. AUDIT calendario: evento 30 min vs descripción "15 minutos" = INCONSISTENTE (corregir en GoHighLevel).
Multipágina NO iniciada. Pendiente HUMAN VISUAL GATE Rafa/Alba.
Estado V51: IMPLEMENTED, TECHNICAL QA PASS, HUMAN VISUAL APPROVAL PENDING.

## Estado — HOME · V52 (correcciones puntuales Rafa, 2026-06)
Solo web2.html + regeneración 3 emblemas locales:
1. Tecnología (sección oscura): al hacer hover una tarjeta pasa a clara (#F4F1E9) e invierte tipografía a tono oscuro (h3 #0A1622, p #3A5262, nº/icono petrol). Regla `#tecnologia .tcap:hover` alta especificidad. Estado oscuro por defecto legible (texto blanco). Sin blanco-sobre-blanco.
2. Acceso profesional: los 3 CTA (Darse de alta / Agenda una videollamada / Entrar con mi código) ahora IDÉNTICOS PRIMARY (fondo #1F6588 sólido, texto blanco, mismo alto/ancho/sombra/hover). `.entry .ecta` base = primary sólido.
3. Escudos Grupo: regenerados normalizando por CUERPO del escudo (aislando silueta vs flare/glow con filtrado de columnas altas), altura común 560px, centrados en canvas común 620×720. Render: los 3 logos 327×379, top 494 → misma escala aparente, mismo centro, misma baseline. `.gcard .logo` aspect 31/36 + object-fit:contain. Escudo intacto (0 px alterados, sin recorte del escudo, sin IA). Fondo transparente.
4. PRÓXIMAMENTE (Robotics): badge overlay top-right, no afecta el centrado del escudo.
5. Grupo→footer: separador limpio (línea 1px a ancho editorial 1160px) en #grupo::after (glow anterior eliminado). Footer bg = #1F6588; sistema tipográfico invertido a blanco/alto contraste (h4 .78, links .82, hover blanco+subrayado, bottom .72). Grupo permanece oscuro.
FREEZE: Judiciales↔Acuerdos (164/164), cards, info Acuerdos, calendario, funds, filosofía, nav, taxonomía — no tocados. Móvil 390px sin overflow.
Multipágina NO iniciada. Pendiente HUMAN VISUAL GATE Rafa/Alba. Estado V52: IMPLEMENTED, TECHNICAL QA PASS, HUMAN VISUAL APPROVAL PENDING.

## Estado — HOME · V53 (correcciones consolidadas Rafa/Alba, 2026-06)
Solo web2.html. Verificado por testing_agent (iteration_1.json, 100% PASS):
1. P0 BUG RESUELTO: eliminado el auto-demo (IntersectionObserver que hacía setMode true→false). Estado inicial forzado a Judiciales (`setMode(false)`). testing_agent: AUTO_SWITCH_COUNT=0 en ~20s de polling (load+scroll+idle sin clicks). Cambio de universo SOLO manual. Geometría intacta (diff 0px).
2-7. GRUPO compacto: orden LIVING | OPORTUNIIA (centro) | ROBOTICS; escudos reducidos (logo max-width 148px, render 148×172, mismos tamaño/top/baseline); hover premium scale(1.15) sin reflow; copy mayor (nombre 18px, statement 14.5px); PRÓXIMAMENTE conservado sin distorsionar. Sección ~mitad de altura.
8. Calendario más compacto: agenda-block cols .8fr/1fr (~44/56), cal-embed max-width 640 + height 540. Widget real LeadConnector intacto (URL sin cambios).
9-10. Tarjetas acceso: todas fondo BLANCO (quitado gradiente Inversor); `.entry` flex-column + `.ecta` margin-top:auto → tops idénticos (5613) y CTA al fondo; 3 CTA primary iguales.
11. Diferenciación secciones: #quienes (Filosofía) con tinte petrol pálido (gradiente #E6EFF4→#EDF4F7, texto oscuro); #flow (Cómo trabajamos) off-white. Separación clara al hacer scroll.
12-16. VIP CTA: módulo fuerte `.vip-cta-mod` tras el bloque de valor Acuerdos (solo en modo Acuerdos): "Suscripción VIP · Próximamente / Accede al Universo Acuerdos" + botón sólido con pulso sutil (respeta prefers-reduced-motion) "Solicitar acceso VIP" → #acceso (destino existente, sin URL inventada) + microcopy "Acceso sujeto a validación profesional". 2º punto: link VIP secundario en tarjeta Suscriptor. Sin precios/escasez/ROI garantizado.
FREEZE: taxonomía, Judiciales↔Acuerdos, info Acuerdos, funds, footer #1F6588, calendario URL, nav — intactos. Móvil 390px sin overflow.
Multipágina NO iniciada. Pendiente HUMAN VISUAL GATE Rafa/Alba. Estado V53: IMPLEMENTED, TECHNICAL QA PASS (testing_agent 100%), HUMAN VISUAL APPROVAL PENDING.

## Estado — HOME · V54 (corrección visual consolidada Rafa + Alba, 2026-06)
Solo web2.html (CSS bloque V54 + reestructura HTML VIP/Fondos). Verificado por screenshots + medición programática:
1. HERO OSCURO: fondo petrol #0A1622 (ref. #producto), texto blanco, "deuda." cyan #57C6E4, halo radial sutil. Animación de entrada escalonada (h1 reveal + lead/CTA/strip fade-up con delays; respeta prefers-reduced-motion; 0 CLS). Header legible sobre hero oscuro: en estado top (no-scroll) logo a blanco (filter brightness(0) invert(1)), nav/ghost/burger blancos; al hacer scroll (.sc) vuelve a logo original + nav oscuro.
2. CTA VIP = BANNER a todo el ancho editorial (max-width:none, grid 1.5fr/auto, texto izq + CTA dcha), petrol sólido con halo cyan, botón con pulso sutil. Copy intacto.
3. Target VIP corregido: eliminado "¿Aún sin acceso? Solicitar acceso VIP →" de tarjeta Suscriptor (queda solo "Entrar con mi código"). Sin VIP en Colaborador.
4. Tarjetas profesionales: aire vertical garantizado (opts flex:0 + margin-bottom:26px, ecta margin-top:auto) → Colaborador ya no pega el texto al botón; 3 CTA alineados en la misma línea inferior, fondos blancos, mismo top.
5. Fondos & Servicers: eliminado "Representación demostrativa". Sección compacta (min-height auto) en 2 columnas: copy+CTA izq | dashboard realista dcha (Panel de cartera, EN VIVO, KPIs 128/34/46, gráfico de barras, filas de operaciones con estados, caption "Vista ilustrativa de la interfaz · datos no reales"). Sin ROI/€/claims reales.
6A. Selector: activo = bloque OPORTUNIIA sólido #1F6588 texto blanco (fuera cyan). uni-card destacada (uni-hi) = bloque oscuro sólido #0B2C3D (fuera degradado pastel), ambos modos.
6B. "Más control. Menos incertidumbre." (acu-value) = bloque OSCURO sólido #0A1622, textos blancos, chips con acento cyan. Copy intacto.
7. Diferenciación FILOSOFÍA vs CÓMO TRABAJAMOS (alto contraste, pensado para daltonismo Rafa): #quienes (Filosofía) = petrol oscuro sólido #0F3A52 + divisor cyan superior, texto blanco; #flow (Cómo trabajamos) = claro cálido #F4F1E9. Diferencia inequívoca al hacer scroll.
8. AGENDA VIDEOLLAMADA = bloque OSCURO OPORTUNIIA #0A1622, "¿HABLAMOS?" en cyan, iconos cyan, calendario LeadConnector intacto (misma URL/widget, compacto V53).
9. Ritmo global oscuro↔claro reforzado; fuera degradados pastel azulados en zonas autorizadas.
QA: AUTO_SWITCH tras 22s (load+scroll+idle, sin clics) = 0/False. GEOMETRÍA surface→card judicial=0px, acuerdos=0px → DIFF=0px exacto. Móvil 390px sin overflow horizontal. Taxonomía/URLs/GHL/footer #1F6588/Grupo/nav/multipágina intactos.
MULTIPAGE STARTED = NO. Estado V54: IMPLEMENTED, TECHNICAL QA PASS, HUMAN VISUAL APPROVAL PENDING (Rafa/Alba). NO FINAL / NO CLOSED.

## Estado — FASE 2 · OPPORTUNITY ENGINE (implementado, 2026-06)
Multipágina SSR sobre HOME V54 (aprobada/freeze). Verificado por testing_agent (iteration_2.json: backend 27/27 = 100%, frontend 100%).

**Arquitectura de servido:** Backend FastAPI + Jinja2 + MongoDB renderiza SSR; el frontend CRA (`frontend/src/setupProxy.js`) reenvía `/`, `/oportunidades*` y `/api*` a `http://localhost:8001` (changeOrigin:false → Host público para canonical). URLs limpias reales con SEO. Assets de `/public` (logo, /grupo) y hot-reload siguen servidos por CRA.

**Rutas:** `/` = HOME V54 (servida desde web2.html, freeze; nav "Oportunidades" + CTA "Ver oportunidades" cableados a /oportunidades). `/oportunidades` = catálogo/buscador SSR. `/oportunidades/{slug}` = detalle estilo presentación.

**Implementado FUNCIONAL:**
- Catálogo Judiciales↔Acuerdos, selector manual (default Judiciales), 0 auto-switch.
- Filtros: producto NPL/CDR/REO, ubicación en cascada CCAA→provincia→municipio (JS + `/api/locations/*`), tipo de activo, inversión mín/máx, "Más filtros", Aplicar/Limpiar. Estado en URL (shareable). Orden neutro (recientes/precio/plazo).
- Tarjetas (imagen, badge producto, ubicación, activo, inversión, ROI, plazo, situación, favorito, comparar, Ver operación → detalle).
- Detalle: resumen ejecutivo, activo, situación/estructura, recorrido, documentación (placeholder), panel de acción sticky con ROI/inversión/valor compra (blur)/plazo, CTAs Reservar y Comprar (acciones DISTINTAS), Favorito, Comparar, señal de interés veraz.
- Favoritos DEMO: cookie `opp_sid` + MongoDB (`demo_favorites`), no autoritativo.
- Comparar: selección cliente (hasta 3) + `/api/opportunities/compare` (excluye inventario acuerdos protegido), modal de campos objetivos.
- VIP locked: `_vip_active()` server-side = INACTIVE en esta fase → Universo Acuerdos SIEMPRE bloqueado (pantalla de conversión VIP mensual/anual sin precios; inventario NO entregado; detalle acuerdos → 302 al gate).
- CTA Reservar/Comprar: DEMO/no transaccional (`/api/operations/intent` → status demo, transactional false; modal etiquetado DEMO; conectado a futuro flujo actor_id→operación→Mi OPORTUNIIA→documentación).

**PREPARED (contratos, sin acciones reales):** búsquedas guardadas (`/api/saved-searches`→prepared), match/afinidad (`/api/match/preview`, explicable, sin score inventado), señales de interés (`/api/interest-signals/{slug}`, agregado veraz, umbral 3, sin urgencia falsa), notificaciones email/WhatsApp/Telegram (futuras, no activas, sin proveedor), operación/histórico, documentación (2 direcciones, sin deadline hardcodeado, sin upload), Mi OPORTUNIIA, PRESENTACIÓN outputs, VIP entitlement (OPORTUNIIA_VIP, ACTIVE/INACTIVE/EXPIRED, MONTHLY/ANNUAL, sin precio/proveedor/pago real), identidad (solo punto de integración actor_id). Ver `/api/readiness`.

**NO implementado (por diseño):** pagos reales, proveedor de pago, precios VIP, checkout/webhooks, identidad soberana/paralela, Mi OPORTUNIIA completo, CRM, reserva/compra reales, cobros, reglas contractuales/deadlines inventados, upload de documentos, envíos, algoritmo match opaco, %afinidad inventado, actividad/urgencia/viewers falsos, dashboard Fondos real, página Tecnología, integración real PRESENTACIÓN, deploy producción/DNS.

**Dataset:** DEMO. Judiciales (10, catálogo público): Sevilla/Alicante/Zaragoza + Madrid/Barcelona/Málaga/Murcia/Alcalá/Torrevieja/Hospitalet. Acuerdos (3, protegido): Marbella/Valencia/Bilbao. `backend/catalog_data.py`.

**QA:** HOME V54 preservada; AUTO UNIVERSE SWITCH=0; geometría intacta; catálogo 200 (10 cards judicial); filtros+cascada+URL+orden OK; favoritos/comparar OK; detalle 200 / acuerdos 302 / inexistente 404; APIs OK; móvil 390px sin overflow. Bug 422 (precio vacío) corregido con `_to_int_or_none`.

MULTIPAGE STARTED = SÍ. Estado Fase 2: IMPLEMENTED, TECHNICAL QA PASS (testing_agent 100%). HUMAN REVIEW PENDING Rafa/Alba. NO FINAL / NO CLOSED / NO Fase 3.

## Estado — FASE 2 · CORRECCIÓN VISUAL UNIVERSOS (persistencia cromática, 2026-06)
Feedback Rafa: los universos no cambiaban de atmósfera completa (Judicial quedaba claro; Acuerdos mostraba bloque oscuro dentro de claro; ficha judicial = cabecera oscura + cuerpo blanco). CORREGIDO con sistema de temas por universo en `base.html` (body.theme-judicial / body.theme-acuerdos con set completo de tokens CSS + transición fade + logo blanco en oscuro):
- **EJECUCIONES JUDICIALES = OSCURO COMPLETO** (catálogo + ficha): header, hero, filtros, buscador, cards, toolbar, panel económico, ROI, CTAs, secciones, footer contextual — todo dark (#0A1622). La foto del activo conserva su color.
- **UNIVERSO ACUERDOS = BLANCO COMPLETO** (catálogo + ficha): toda la interfaz clara.
- **Persistencia:** la ficha hereda el tema del universo de la operación (deep-link incluido); no vuelve a interfaz neutra.
- **NON-VIP Acuerdos** (catálogo y ficha, deep-link): se renderiza la estructura BLANCA con contenido DEMO + capa granular (blur/obscuration) + popup VIP existente (mensual/anual, "Activar VIP" → /#acceso). Antes redirigía (302); ahora la ficha acuerdos devuelve 200 bloqueada in-place. `_vip_active()` sigue server-side = INACTIVE (entitlement no expone datos vía API; el blur es solo experiencia visual, no seguridad; en prototipo se usa contenido DEMO).
- **VIP activo** (futuro): mismo código muestra Acuerdos blanco + contenido visible sin granular/popup.
Verificado por screenshots (los 5 estados A–G del pedido) + comprobación server-side de body class/locked. HOME V54 y logo = FREEZE (sin tocar). Estado: IMPLEMENTED, HUMAN PREVIEW PENDING Rafa/Alba. STOP.

## Estado — FILTER CONTRACT v1 · Catálogo faceted search (2026-06)
Iteración 1 del buscador profesional. Geografía OFICIAL (INE/codeforspain) en `backend/data/geo_es.json`: 19 CCAA · 52 provincias · 8132 municipios, cargada en `catalog_data.py`. Taxonomía geográfica ESTRUCTURAL (ubicaciones aparecen aunque tengan 0 activos; p.ej. Viladecans). `catalog_data.py` reescrito: multiselect (products/assets), cascada geo, rangos capital/ROI/plazo, `facet_counts()`, orden extendido. `catalogo.html` reescrito como faceted search (panel desktop sticky + drawer móvil): búsqueda libre, ubicación jerárquica CCAA→provincia→municipio (municipios vía `/api/locations/*` con búsqueda), producto y activo (agrupado) con checkboxes + counts, capital min/max + rangos rápidos, "Más filtros" (ROI/plazo + placeholders procedimiento/fase/posesión), chips activos con quitar-uno y limpiar-todos, orden, contadores. Estado en URL (multiselect por params repetidos, shareable). Temas por universo preservados (Judicial oscuro / Acuerdos blanco + granular + popup VIP). Backend: `/oportunidades` y `/api/opportunities` con Query lists + counts; `/api/locations/municipios?q=`.
FINDING: sin acceso a fuente soberana/HEADER_MAP en este repo → taxonomías jurídicas avanzadas (fases NPL, concursal, posesión, económicas, documentación) DIFERIDAS a auditoría (no inventadas). Datos de operaciones = DEMO/fixture.
Verificado: multiselect, filtros ccaa/precio, chips, counts (NPL3/CDR2/REO5), cascada provincias/municipios, búsqueda municipio, Viladecans (0 resultados) presente, acuerdos locked, móvil. Estado: IMPLEMENTED iteración 1, HUMAN REVIEW PENDING. STOP.

## Backlog (bloqueado hasta aprobación visual)
- (2026-06) Micro-iteración modal VIP: "Activar VIP" reubicado ARRIBA como acción principal (ancho ~340px equivalente al bloque de planes, pulse suave tipo anillo 2.6s, hover scale 1.05); Mensual/Anual debajo como secundarios con hover scale. Aplicado en catálogo (`.vip-lock`) y ficha (`.det-lock`). Sin cambios en título/copy/fondo/granular/lógica. Respeta prefers-reduced-motion.
- P1: Portar diseño a Elementor JSON (`_elementor_data`) HOME 2.0 (ID 1630) y HEADER 2.0 (ID 1641).
- P1: Ejecutar Write Bridge (solo tras autorización explícita).
- P2: QA responsive dentro de Elementor tras escritura.
- Pendiente confirmar: URL oficial LIVING EXPERIENCE; destino público definitivo de Tecnología.

## Salud
- Roto: ninguno. Mock: ROI/plazos/ubicaciones/valor de compra son DEMO (se sustituirán por operaciones reales 1:1).
