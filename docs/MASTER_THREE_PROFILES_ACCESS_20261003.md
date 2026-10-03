# DIRECTRIZ MASTER · Tres perfiles y doble espacio del suscriptor

**Corrección del propietario, 2026-10-03.** El suscriptor TAMBIÉN capta inversores como un colaborador **exclusivamente en modalidad A**, por lo que dispone de una sección privada WEB de aportación de inversores, independientes de su cuenta, trabajos, historia y permisos OPORTUNIIAPP. No se crea una segunda contraseña de suscriptor: la WEB verificará en el futuro identidad y permanencia mediante una integración segura de OPORTUNIIAPP. Esta integración aún NO está implementada.

| Perfil | Identidad y espacios | Relaciones económicas |
| --- | --- | --- |
| Inversor | Cuenta WEB personal, su MI OPORTUNIIA documental y Premium si procede | Sus operaciones y preferencias propias |
| Colaborador | Cuenta WEB propia, habilitada solo tras aprobación individual de OPORTUNIIA; área comercial separada de los documentos del inversor | Código de aportación, modelo A o B según contrato vigente |
| Suscriptor | Cuenta histórica y credenciales únicamente en OPORTUNIIAPP **más** área WEB de aportaciones (sección comercial de MI OPORTUNIIA, no MI documental del inversor) | Código propio de aportación WEB vinculado a su identidad OPORTUNIIAPP; **siempre modelo A** |

**Interpretación de dos espacios:** el suscriptor conserva sus operaciones/servicios/historia OPORTUNIIAPP en dicha aplicación y puede consultar exclusivamente los inversores que aporta, sus operaciones atribuibles y los honorarios aprobados de modelo A en su sección WEB. No se sincronizan nóminas, documentos del inversor ni historial íntegro OPORTUNIIAPP. La autorización comercial de WEB no otorga acceso a su carpeta MI de inversor ni a paneles de otros colaboradores.

## Alta común de inversores (colaborador y suscriptor)

Ambos dispondrán del botón **«Dar de alta a un inversor»** en su panel comercial, una forma de preparar alta asistida que requiere que el inversor acepte las condiciones y **confirme personalmente su email**. Nunca pueden fijar o conocer su contraseña. También tendrán un **enlace de captación reutilizable para difusión masiva**, con QR descargable/impreso en tarjeta, asociado al **código inmutable de aportador**. La URL de campaña común identifica al aportador, pero cada alta genera un **expediente individual de atribución y confirmación**, con huella de campaña, consentimiento, email verificado y revisión OPORTUNIIA. No usar un token único compartido como credencial de inversor; proteger campañas contra sustitución, phishing, suplantación y duplicidades.

Alta asistida, enlace o QR NO crean por sí solos una relación económica firme. Tras verificación del email y aceptación del inversor, OPORTUNIIA revisa los conflictos de atribución e historial preexistente y confirma la asignación, asociando el código del aportador a su ficha WEB. Capturas/reenvíos de enlaces no pueden desplazar aportadores anteriores automáticamente.

## Continuidad del suscriptor

**Regla empresarial propuesta:** si el inversor rescinde su relación directa con el suscriptor, pero el suscriptor sigue efectivamente dentro de la estructura OPORTUNIIA, subsiste su derecho pactado a recibir los honorarios modelo A derivados de los inversores aportados conforme a condiciones verificadas. NO hereda esta regla automáticamente el colaborador externo, cuya protección inicial pactada es de dos años. LEGAL tendrá que armonizar ambas condiciones en los acuerdos existentes y precisar qué ocurre ante baja/suspensión del suscriptor, vigencia, operaciones anteriores, transmisión, mala praxis e incidencias, sin pago automático.

## Estado de implementación y puertas

- **Ya disponible en sandbox:** aislamiento de rutas documentales MI a inversores; verificación de aprobación del colaborador; proyección privada de operaciones y honorarios revisados modelo A/B, sin endpoint público.
- **Nueva especificación y contratos:** código WEB del suscriptor distinto de su credencial OPORTUNIIAPP, resolución segura de identidad mediante OPORTUNIIAPP como fuente de verdad; botón de alta asistida, enlaces masivos y QR; verificación de email por el propio inversor, pruebas antiapropiación y revisión humana.
- **Pendiente de integración:** comprobar credenciales de suscriptor en OPORTUNIIAPP sin recibir/copiar su contraseña; verificar su permanencia cada vez que se autoricen derechos económicos y acceso WEB, incluyendo revocaciones; fuente transaccional y revisión contable.
- **Pendiente LEGAL:** reforzar los contratos existentes A/B y términos de suscriptores, naturaleza y duración de su derecho mientras permanezcan en estructura OPORTUNIIA y tratamiento de conflictos. Los pagos, premios y sanciones requieren revisión manual.

**Sin alta real ni SSO desplegados.** Mantener PR sandbox sin fusionar hasta pruebas de aislamiento y firma jurídica.
