# CIERRE DE BLOQUEOS LEGALLAB · 2026-10-04

Fuente jurídica inicial: Oportuniia/oportuniia-legal-lab @ 9886fb120e9cd6ca9c7789e37e89f55c2384a8b6.\nCierre suscriptor/geo/TRADE: `docs/LEGAL_GATE_CLOSURE_SUBSCRIBER_GEO_TRADE_20261004.md` @ ca2a82104d77f62607770aed329be9d48897f458.

## Estado ejecutado
- Quality/Rappel: v1 retirada de la base WEB; v2 declarada única vigente.
- Contratación electrónica: control técnico implementado en OPORTUNIIAPP con contract_id, contract_version, SHA-256 content_hash, identidad, canal, evidencia precontractual, copia descargable/referenciada antes de aceptación, aceptación expresa mediante control no premarcado, copia posterior, acuse, accepted_at e histórico inmutable. Regla única para Suscriptor, Inversor, Colaborador, PREMIUM y demás contratos electrónicos OPORTUNIIA.
- Suscriptor: ledger de incidencia → alegación → decisión; efectos económicos explícitos y sin pérdida automática.
- Geolocalización: endpoint exclusivo de check-in puntual de misión; no existe ruta de tracking continuo.
- Privacidad: ledger versionado de preferencias/opt-out por finalidad.
- PBC/FT: gate transaccional explícito, separado del mero registro.
- PREMIUM: la evidencia contractual permite distinguir consumidor, obligación de pago e inicio anticipado. La UI B2C no debe abrirse hasta probar el flujo completo.
- LEGAL/abogado: sigue condicionado a identificación profesional y hoja de encargo cuando exista servicio profesional real.

## Gates que requieren validación externa/documental
- Laboralidad: PASS WITH CONDITIONS / NON-BLOCKING según cierre LEGALLAB ca2a82104d77f62607770aed329be9d48897f458; mantener coherencia entre contrato y operativa real.
- TRADE: PASS WITH CONDITIONS / NON-BLOCKING; control individual, declaración de autonomía/no exclusividad y revisión ante posible dependencia económica, sin renuncia de derechos.
- Geolocalización: PASS; exclusivamente puntual y vinculada a misión, sin tracking/background/rutas/control horario.
- EIPD: PASS WITH CONDITIONS / NON-BLOCKING; no se exige EIPD completa por la mera geolocalización puntual bajo el diseño aprobado. Mantener análisis de riesgo RGPD y reabrir ante nuevos factores de alto riesgo.
- Abogado: completar lawyer_id, colegiación, encargo, alcance y honorarios en cada asunto profesional.
- GATE FINAL CONTRACTUAL de LEGALLAB tras integrar contratos finales y evidencias de prueba.

## Regla de producción
Ningún cambio de esta rama abre por sí mismo tráfico M2M ni gates jurídicos cerrados.
