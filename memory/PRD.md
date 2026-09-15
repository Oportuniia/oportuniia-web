# OPORTUNIIA · WEB 2.0 — PRD / Control Environment

## Problema original
Proyecto "Full App Execution" (no web nueva): entorno de control FastAPI/React para
conectarse de forma segura al WordPress de producción (`oportuniia.com`) vía REST API,
y editar EXCLUSIVAMENTE dos borradores Elementor autorizados: HOME 2.0 (ID 1630) y
HEADER 2.0 (ID 1641), bajo modelo estricto de "cero mutaciones sin autorización".
Objetivo creativo: experiencia visual extremadamente premium, sobria e institucional
(nivel Blackstone/Apollo/KKR) para la firma de deuda OPORTUNIIA. Presentar prototipo
("Visual Review") y, tras aprobación, portar estructura nativa Elementor (`_elementor_data`).

## Idioma
ESPAÑOL. Responder siempre en español.

## Reglas duras
- ZERO MUTATIONS a WordPress producción sin autorización explícita.
- Secretos WP solo en runtime desplegado (no en `.env` local). curl contra URL externa.
- No portar a WordPress hasta aprobación del Visual Review.
- Estética institucional: NO SaaS/startup/fintech/crypto/agencia.

## Estado del diseño (Visual Reviews)
- VR01 — RECHAZADO.
- VR02 — RECHAZADO (navy oscuro + Fraunces + interruptor pequeño + vacío lateral).
- VR03 — "Mejora clara" pero no cerrado.
- VR04 — "Mejora clara" pero con exceso de contenido / copy formal.
- VR05 — base sólida; brief llegó cortado en §9.
- VR05.1 — base válida; errores de producto/terminología.
- VR05.2 — ENTREGADO (producto real + negocio real), pendiente de aprobación. Archivo: `/app/frontend/public/web2.html`.

### VR05.2 — correcciones aplicadas
- CDR = **CESIÓN DE REMATE** en toda la experiencia (ya NO "créditos dudosos corporativos"). Imagen CDR ahora residencial (vivienda).
- Tarjetas con lógica real: NPL (Madrid, préstamo hipotecario impagado), CDR (Valencia, cesión de remate — vivienda), REO (Málaga, activo adjudicado). Campos: Valor de compra (masked), ROI objetivo (visible), Plazo estimado (visible), Estrategia/Fase/Estado. "Horizonte" → "Plazo estimado". Ciudades concretas (demo).
- Mutación acuerdo enriquecida: cambian ROI, plazo, estrategia/posesión/ocupación, estado, imagen (duotono), atmósfera.
- Header: logo REAL (asset zukoexsi_LOGO PARA DOCUMENTACION.jpg), eliminado el mark provisional.
- Grupo: eliminada explicación superior/lateral; solo "Grupo OPORTUNIIA" + 3 marcas como enlaces directos (OPORTUNIIA→oportuniia.com, LIVING→#, ROBOTICS sin enlace/Próximamente); cards más pequeñas.
- Inversor: 3 sub-modalidades A/B/C (Compra y adiós · Compra + apoyo jurídico · Servicio integral). Colaborador: 2 A/B (Modelo 50/50 · Cobras a tu cliente). Suscriptor: código.
- Cómo funciona: 5 pasos (Analizamos → Estructuramos → Definimos la mejor vía → Presentamos → Ejecutamos). Ecosistema ligero.
- Copy humanizado. Footer wordmark texto (sin icono inventado).

### VR05.1 — histórico
- Suscriptor REDEFINIDO: usuario ya vinculado al ecosistema, con código de acceso a su entorno autorizado. CTA "Entrar con mi código" (icono llave). Ya NO es newsletter/follower.
- Inversor: busca invertir → "Solicitar acceso". Colaborador: aporta operaciones → "Proponer colaboración".
- Ecosistema REDUCIDO drásticamente: bloque ligero "Tecnología e inteligencia propias..." + tags discretos (CORE·IA·LEGAL·APP·VISUAL·PRESENTACIÓN·WEB sin explicar) + link "Conoce nuestra tecnología". Sin gran grid de 7 cajas.
- Cómo funciona SIMPLIFICADO a 5 pasos humanos: Analizamos → Estructuramos → Definimos la vía → Presentamos → Ejecutamos.
- Grupo: cards/logos más pequeños en móvil (aspect 16/9→2/1, grid acotado y centrado).
- Header móvil: logo + hamburguesa (menú premium), sin texto comprimido.
- Copy general humanizado (tú a tú, directo, sin jerga jurídica).

### VR05 — base (histórico)
- Eliminado el panel/caja duplicada de deal-flow del hero (§7). Hero full-width editorial, headline gigante.
- Botón "Entrar en el Universo Acuerdos" PEGADO justo debajo de las 3 tarjetas (§2). Bloque diferencial compacto: titular + A (vía judicial/recuperación) + B (vía acuerdo/resolución) en una línea cada uno (§3).
- Tarjetas simplificadas (§4/§5): Valor de compra (masked), ROI objetivo VISIBLE (20/28/18%), Horizonte VISIBLE, Estrategia, estado en badge. Sin chips. Nota de valores demostrativos.
- Mutación al activar (§6): ROI (12/16/24%), plazos, estrategia, status, foto (duotono teal) y atmósfera cambian → "la misma operación, dos formas de resolverse".
- Acceso (§8/§9): Inversor / Colaborador / Suscriptor; copy más natural; Suscriptor corregido ("sigue el deal flow, recibe cada oportunidad antes que el mercado").
- NOTA: el brief V05 llegó cortado en §9 (definición de modalidades). Aplicadas definiciones profesionales; ajustar si Rafa envía el texto completo.

### VR04 — cambios (histórico)
- Tarjetas NPL/CDR/REO: firma grande sobre imagen (duotono) con foto elegante por modalidad (residencial / corporativo / costa); estructura lista para sustituir por operaciones reales.
- Momento diferencial integrado JUSTO debajo de las 3 tarjetas; copy simplificado a "Dos maneras de entenderlo" (vía judicial/recuperación vs vía acuerdo/resolución) + CTA grande.
- Al activar Universo Acuerdos: las MISMAS 3 tarjetas mutan (foto→duotono teal, datos ROI/timing/framing, status y chips) + auto-scroll a las tarjetas para percibir la mutación.
- Acceso rehecho: "¿Cómo vas a entrar?" → Inversor (destacado) / Colaborador / Suscriptor con microcopy.
- Grupo: cards más pequeñas y refinadas (4:3, centradas, más aire).
- Hero: radar sustituido por panel funcional "deal flow" (previsualiza producto, masked).
- Header logo: marca limar limpia (anillo "O") + wordmark; comentario para swap 1:1 con logo definitivo.
- Dropdown Quiénes somos: mini-logos (thumbnails), mejor espaciado y separación texto/icono.

### VR03 — Especificación base (conservada)
- MAIN MODE: Light Premium / editorial (marfil #FCFBF8, gris claro, ink navy #0B1A28,
  acento corporativo #1F6588). Poppins ÚNICA (sin Fraunces).
- Hero: "HUMANIZAMOS LA DEUDA." grande, sin stock, emblema editorial CSS + reveal.
- Producto NPL/CDR/REO como ventanas de private deal flow con masking (3•%, € •••.•••).
  Cero métricas inventadas.
- Momento diferencial protagonista: "Descubre nuestras oportunidades / Entra en el
  Universo Acuerdos" + explicación (2 lecturas de la MISMA oportunidad, no 4ª categoría)
  + CTA/switch GIGANTE que activa la transformación.
- SECOND MODE (Universo Acuerdos): transformación radical (~0.62s) a modo inmersivo
  oscuro/grafito con #1F6588 (→#2E9AC6) protagonista. Re-framing de las ventanas
  (Inversión ↔ Resolución/Acuerdo).
- Orden: PRIMERO Ecosistema ("La maquinaria que sostiene cada decisión": CORE·IA·LEGAL·
  APP·VISUAL·PRESENTACIÓN·WEB, explicados + "una sola máquina"), DESPUÉS Cómo funciona
  ("De la cartera al resultado").
- Nav "Quiénes somos" → dropdown Grupo. Sección GRUPO OPORTUNIIA con banda oscura y los
  3 logos reales suministrados: OPORTUNIIA / LIVING EXPERIENCE / ROBOTICS (label
  "Próximamente"). Grupo ≠ Ecosistema.
- Footer corporativo (sin URLs/textos legales inventados).
- Responsive independiente: breakpoints 1180 / 900 (hamburguesa + menú móvil) / 640.
  Verificado desktop 1920, tablet ≤900, móvil 390 (ambos modos).

### Logos reales (assets del usuario)
- OPORTUNIIA: https://customer-assets-4nw71qhi.emergentagent.net/job_master-deploy-2/artifacts/jjknh2bb_OPORTUNIIA.png
- LIVING: https://customer-assets-4nw71qhi.emergentagent.net/job_master-deploy-2/artifacts/6f5o2w4o_LIVING.png
- ROBOTICS: https://customer-assets-4nw71qhi.emergentagent.net/job_master-deploy-2/artifacts/6tt8feid_ROBOTICS.png

## Arquitectura
- backend/: server.py, wp_precheck.py (endpoints Read-Only WP), .env
- frontend/public/web2.html: prototipo Visual Review (actual = VR03)
- wordpress-bridge/: Read Bridge v1.0.1 (instalado y validado)
- wordpress-write-bridge/: Write Bridge v0.1.0-rc1 (empaquetado, pendiente instalación por usuario)

## Endpoints clave
- GET /api/wp-precheck/run?authorize=RAFA
- GET /api/wp-precheck/item?authorize=RAFA&id=...
- GET /api/wp-precheck/bridge?authorize=RAFA

## Backlog / próximo
- P0: Iterar VR03 según feedback de Rafa.
- P1 (BLOQUEADO por aprobación): Portar VR03 a Elementor JSON (`_elementor_data`) nativo,
  editable, para HOME 1630 y HEADER 1641 vía Write Bridge (snapshot + rollback).
- P2: QA responsive dentro de WordPress/Elementor tras escritura.
