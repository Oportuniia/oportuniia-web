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
- VR03 — ENTREGADO 15/09/2026, pendiente de aprobación de Rafa. Archivo: `/app/frontend/public/web2.html`.

### VR03 — Especificación implementada
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
