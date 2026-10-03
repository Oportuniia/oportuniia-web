# DIRECTRIZ MASTER · Tres perfiles, dos sistemas de identidad

**Decisión del propietario — 2026-10-03.** Separación obligatoria entre usuario inversor, colaborador y suscriptor. Esta directriz se integra como control de acceso durante el proceso de validación de WEB 5.0, sin ampliar las funciones de MI OPORTUNIIA ya congeladas.

| Perfil | Acceso e identidad | Aprobación / histórico |
| --- | --- | --- |
| **Usuario inversor** | Cuenta WEB validada y acceso exclusivo a **MI OPORTUNIIA** con sus propios documentos, agenda y Premium si procede | Registro y controles existentes de WEB |
| **Colaborador** | Alta diferenciada y circuito de colaborador propio. **No hereda acceso al archivo privado del inversor** | Requiere **aprobación expresa y específica de OPORTUNIIA**, además de verificar correo; código de colaborador distinto del inversor |
| **Suscriptor** | Se identifica mediante su **código y contraseña existentes de OPORTUNIIAPP**. Accede a las prestaciones que correspondan a su suscripción en el ecosistema, pero **NO a MI OPORTUNIIA** | Su cuenta, ficha y **historial permanecen en OPORTUNIIAPP**; WEB no crea una identidad paralela, no importa el histórico ni le exige un segundo registro |

**Matiz de interpretación:** «acceso a todo» del suscriptor significa el acceso correspondiente a su condición de suscriptor según los permisos de cada aplicación; **nunca** implica acceso al archivo privado de terceros, herramientas administrativas, LEGAL u otras áreas restringidas.

## Controles ya introducidos en sandbox WEB

- `backend/mi_role_boundaries.py` centraliza las barreras de identidad. `require_mi_investor` rechaza cualquier otro rol al intentar entrar en rutas privadas MI, incluidos documentos, ofertas, calendario, notificaciones y Premium. La comprobación es del servidor, no solo un ocultamiento de botones.
- El registro WEB existente diferencia INVERSOR y COLABORADOR; la aprobación administrativa de colaboradores depende de la validación expresa y de su código propio. El indicador `collaborator_is_approved` **no autoriza automáticamente otras herramientas ni crea una sesión de OPORTUNIIAPP**.
- `subscriber_access_contract` fija el criterio de integración sin simular SSO: autoridad de identidad, credenciales, ficha e historial quedan en OPORTUNIIAPP, con exclusión expresa de MI.

## Integración y pruebas pendientes antes de publicar

1. **ARQUITECTURA MASTER / OPORTUNIIAPP:** acordar el contrato de autenticación de suscriptores (p. ej. intercambio de sesión mediante API de confianza), permisos efectivos y enlace desde WEB sin transportar contraseñas a WEB ni copiarlas a sus bases de datos. OPORTUNIIAPP seguirá siendo la fuente de verdad de historial y perfil.
2. **OPERACIONES:** verificar quién aprueba a cada colaborador, qué evidencia y facultades quedan registradas, qué ocurre si se suspende o revoca la aprobación y qué interfaz independiente necesita. No reutilizar el panel MI.
3. **SEGURIDAD:** pruebas E2E para impedir acceso cruzado entre los tres perfiles, reutilización de sesión, escalada de privilegios, modificación de código/rol desde el navegador y lectura de datos de OPORTUNIIAPP desde WEB.
4. **FRONTEND WEB:** diferenciar accesos y explicar que un suscriptor continúa en su área habitual de OPORTUNIIAPP. Ningún botón de acceso constituye una integración autenticada hasta superar las pruebas.

**Estado:** regla aceptada; separación inversor/MI aplicada en rutas sandbox WEB. Login único real del suscriptor desde WEB, interfaz y revocación del colaborador, y autorización interaplicaciones siguen PENDIENTES de coordinación con sus responsables. No desplegar todavía.
