# OPORTUNIIA · MATRIZ DE CORRESPONDENCIA FINAL · 2026-10-05
Estado: IMPLEMENTACIÓN EN RAMA · PRODUCCIÓN CERRADA

| Decisión aprobada | Implementación soberana | Consumidores | Verificación / contrato |
|---|---|---|---|
| Inversor A/B/C/D por operación | APP /operations/service-modality | WEB, CORE, IA, UI | operation_id + investor_id; nunca perfil permanente |
| Colaborador A/B separado | namespace contractual separado | CORE/IA/UI | no reutilizar campo modality de operación |
| Expediente vigente universal | APP /pbc/document-profile + checklist | WEB vía readiness | mandatory_documents_current |
| PBC universal | APP /pbc | WEB vía readiness | CURRENT + CLEARED |
| PBC propio OPORTUNIIA si obligado | APP PbcGate oportuniia_is_obliged_entity / own_status | WEB | tercero no sustituye own CLEARED |
| Gate territorial C/D | APP /territorial-compliance | WEB vía readiness | C/D bloqueado sin CLEARED |
| Secretaría PF/PJ adaptativa | APP /pbc/document-checklist | Secretaría/UI/IA | PF/PJ + legal_structure |
| Aprendizaje Secretaría | APP experience/pattern | Secretaría/IA | ADVISORY ONLY; preferir anonimizado/agregado |
| Legal externo B/D | APP /operations/legal-partner-matter | WEB/operaciones | cliente-despacho; conflicto+encargo+alcance+fees |
| Comercialización C/D | APP modality flags + territorial gate | operaciones | servicio OPORTUNIIA, no despacho externo |
| GEO puntual | APP /missions/check-in | OPORTUNIIAPP | misión real/activa/asignada; 100m; fuera=review |
| Foto visita | APP /missions/visit-evidence | OPORTUNIIAPP | IN_APP_CAMERA + hash + server timestamp |
| Retención por categoría | APP /retention-policies | todos los archivos/evidencias | PBC no extiende automáticamente GEO/foto |
| Quality/Rappel v2 | APP quality_rappel.py | CORE/IA/reporting | 3.75; 15/06,15/12; 3=.25,4=.33,5=.42,6=.50; floor5 cap10 |
| Premium | WEB /premium | contratación/pagos futuro | 1000 mensual; 10000 anual; 12 meses activación |
| Privacidad | APP operational-only preference | WEB/CORE/IA | sin marketing/commercial purpose |
| Contratación electrónica | APP contracts publish/accept | WEB/APP | version+hash+preinfo+copies+ack+explicit acceptance |
| B2C obligación pago | APP accept gate + WEB checkout UX | WEB | consumer_applicable exige payment_obligation_confirmed |
| Readiness único | APP /pbc/operation-readiness | WEB /operations/readiness-sync | fail closed; WEB no fabrica CLEARED |

## Regla de prevalencia
LEGALLAB Final Gate + CONTRACTUAL_MASTER_FINAL_GATE_20261005 prevalecen sobre documentación legacy. CORE/IA/Presentación/Visual no pueden redefinir estados soberanos.

## Condición antes de contratos definitivos
1. P0 APP verde en head con cambios finales.
2. WEB conserva fail-closed y sincronización autoritativa.
3. Contratos reflejan esta matriz sin prometer reglas internas.
4. Validación de correspondencia posterior a generación.
5. Sin merge/deploy/producción hasta autorización expresa de RAFA.
