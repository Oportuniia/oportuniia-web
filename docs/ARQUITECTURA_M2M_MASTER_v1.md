# DIRECTRIZ MASTER OPORTUNIIA
## ARQUITECTURA GLOBAL DE COMUNICACIONES
## ESTÁNDAR SOBERANO M2M DIRECTO v1

**Autoridad MASTER:** Rafa  
**Ámbito:** todo el ecosistema OPORTUNIIA  
**Estado:** autorizado para diseño, desarrollo, adaptación, migración técnica, coordinación y pruebas en SANDBOX.  
**No autoriza:** producción, PII no autorizada, pagos automáticos, cambios de autoridad de negocio ni retirada de sistemas anteriores sin sustituto probado.

## 1. Decisión MASTER

M2M directo será el estándar general de comunicación interna del ecosistema:

```
SISTEMA A
   ⇅
API M2M DIRECTA
   ⇅
SISTEMA B
```

Aplica a OPORTUNIIAPP, IA OPORTUNIIA, LEGAL LAB, VISUAL ENGINE, PRESENTACIÓN, WEB, CORE y cualquier herramienta futura.

n8n deja de ser transportista general. Se mantiene únicamente cuando exista orquestación real que justifique un tercer sistema.

## 2. Garantías obligatorias

Toda relación M2M deberá ser:

- directa;
- automática;
- persistente;
- idempotente;
- trazable;
- autenticada;
- cifrada;
- versionada;
- recuperable;
- fail-closed.

Eliminar intermediarios no elimina garantías.

## 3. Soberanía

Cada herramienta conserva su propia base de datos, lógica, permisos, credenciales y autoridad sobre sus datos.

Queda prohibido el acceso directo a la base de datos de otra aplicación.

Cada sistema expondrá únicamente APIs M2M mínimas bajo principio **need to know**.

## 4. Automatización y persistencia

Antes de transmitir un evento crítico, el emisor deberá persistirlo.

La cola deberá sobrevivir a reinicios y recuperar automáticamente los eventos pendientes.

Ninguna comunicación ordinaria dependerá de una acción manual para iniciar, reanudar o comprobar el transporte.

## 5. Reintentos universales

Calendario inicial común:

- intento 1: inmediato;
- intento 2: +5 min;
- intento 3: +15 min;
- intento 4: +30 min;
- intento 5: +60 min;
- intento 6: +90 min.

Esto equivale a **1 intento inicial + 5 reintentos automáticos**.

Si se agotan, el evento NO se borra. Pasa a `REQUIRES_INTERVENTION` o equivalente y debe poder recuperarse y reenviarse posteriormente.

## 6. Idempotencia

Toda operación con efectos de negocio deberá ser idempotente.

- mismo `event_id` + mismo payload = mismo evento;
- mismo `event_id` + payload diferente = conflicto y fail-closed.

Un mismo evento enviado varias veces deberá producir un solo efecto de negocio.

## 7. Correlación

Toda operación extremo a extremo deberá usar `correlation_id` o equivalente común para relacionar entrada, proceso, salida y respuesta.

## 8. Integridad

Los contratos relevantes deberán incluir `payload_hash` o mecanismo equivalente.

### Regla de hash único

El hash deberá calcularse mediante un **método universal y determinista** de serialización y cálculo, compartido por todas las herramientas.

Mismo contenido + mismo método = mismo hash.

Un reintento no podrá modificar silenciosamente el payload original.

## 9. ACK

Una llamada HTTP realizada no implica entrega.

El receptor deberá confirmar explícitamente la recepción válida.

Solo entonces podrá marcarse `DELIVERED` / `ACCEPTED`.

El ACK de transporte nunca equivale a aprobación de negocio.

## 10. Trazabilidad mínima

Registrar como mínimo:

- event_id;
- correlation_id;
- contrato y versión;
- emisor;
- receptor;
- fecha;
- intento;
- estado;
- respuesta;
- error;
- ACK;
- estado final.

No almacenar innecesariamente PII, tokens, secretos, credenciales ni payloads sensibles.

## 11. Seguridad M2M

Obligatorio:

- HTTPS/TLS;
- credenciales M2M específicas por relación;
- secretos fuera del código y repositorios;
- permisos mínimos;
- rotación;
- validación estricta;
- protección anti-replay;
- rate limiting cuando corresponda;
- auditoría;
- deny-by-default;
- fail-closed.

Evaluar red privada entre servicios cuando la infraestructura lo permita.

### Protección anti-replay

Cuando el contrato lo requiera, utilizar timestamp, nonce y ventana temporal además de `event_id`.

## 12. Contratos versionados

Cada relación deberá definir un contrato explícito, por ejemplo `OPORTUNIIA_M2M_v1`, incluyendo:

- emisor;
- receptor;
- schema_version;
- campos permitidos;
- campos obligatorios;
- autenticación;
- event_id;
- correlation_id;
- payload_hash;
- respuestas;
- errores;
- ACK;
- reglas de idempotencia.

Cambios incompatibles requieren nueva versión.

## 13. Patrón universal OUTBOX / INBOX

### Emisor
Cada sistema deberá mantener una **M2M_OUTBOX persistente** o mecanismo equivalente para registrar el evento antes de enviarlo.

### Receptor
Cada sistema deberá mantener una **M2M_INBOX / registro de idempotencia** o mecanismo equivalente para reconocer eventos ya recibidos y evitar duplicar efectos.

### Inmutabilidad
Una vez iniciado el primer intento, el payload del evento queda inmutable.

Si cambia contenido relevante, deberá generarse un nuevo `event_id`.

## 14. Estados universales recomendados

Las herramientas deberán converger, cuando sea técnicamente viable, en una máquina de estados equivalente a:

```
PENDING
→ SENDING
→ ACKNOWLEDGED
→ DELIVERED
```

En fallo:

```
RETRY_SCHEDULED
→ REQUIRES_INTERVENTION
```

Podrán existir estados internos adicionales, pero su equivalencia deberá documentarse.

## 15. Papel de n8n

No usar n8n únicamente para:

- persistencia;
- reintentos;
- idempotencia;
- trazabilidad;
- ACK;
- correlación;
- transporte A → B.

Estas garantías pertenecen al estándar M2M propio.

n8n podrá mantenerse cuando exista orquestación real: esperas, bifurcaciones, coordinación de múltiples sistemas, acciones encadenadas o lógica multi-etapa.

## 16. Migración

Orden obligatorio:

1. construir M2M;
2. añadir persistencia;
3. automatización;
4. reintentos;
5. idempotencia;
6. correlación;
7. integridad;
8. ACK;
9. trazabilidad;
10. seguridad;
11. probar;
12. comparar con sistema anterior;
13. retirar intermediario solo con equivalencia o mejora demostrada.

## 17. Pruebas obligatorias

Cada conexión deberá probar al menos:

- entrega normal;
- receptor caído;
- emisor reiniciado;
- receptor reiniciado;
- timeout;
- pérdida y recuperación de conexión;
- reintentos;
- evento duplicado;
- ACK perdido;
- evento procesado + respuesta perdida;
- mismo ID + payload diferente;
- hash incorrecto;
- credencial incorrecta;
- replay;
- agotamiento de reintentos;
- recuperación posterior.

Las pruebas deberán demostrar:

**NO SE PIERDE EL EVENTO.**  
**NO SE DUPLICA EL EFECTO DE NEGOCIO.**

## 18. WEB / “Vendido por mí”

WEB queda incluida en el mismo estándar.

OPORTUNIIAPP persiste y transporta automáticamente. WEB recibe de forma idempotente y mantiene autoridad sobre duplicados, atribución, verificación, códigos oficiales y estados comerciales.

PII real permanece bloqueada hasta autorización LEGAL.

## 19. Ejecución por herramienta

Cada herramienta deberá:

1. asumir esta directriz;
2. auditar conexiones entrantes y salientes;
3. clasificarlas como M2M DIRECTA / n8n / OTRA / NO IMPLEMENTADA;
4. identificar desviaciones;
5. adaptar contratos al estándar;
6. implementar las garantías que le correspondan;
7. coordinar cada contrato con su contraparte;
8. probar en SANDBOX;
9. documentar evidencias y bloqueos;
10. no declarar una conexión operativa hasta superar pruebas E2E.

## Principio MASTER

**M2M DIRECTO  
+ AUTOMATIZACIÓN TOTAL  
+ PERSISTENCIA  
+ 5 REINTENTOS TRAS EL INTENTO INICIAL  
+ IDEMPOTENCIA  
+ CORRELACIÓN  
+ INTEGRIDAD  
+ ACK  
+ TRAZABILIDAD  
+ SEGURIDAD  
+ RECUPERACIÓN.**

Menos intermediarios.  
Mismas o mayores garantías.  
Una arquitectura común para todo OPORTUNIIA.
