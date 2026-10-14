# Perfil · Países, ubicación y direcciones · 14/10/2026

- Selectores de país de nacionalidad y residencia fiscal: 249 códigos ISO 3166-1 (pycountry 24.6.1), nombres españoles de Unicode/Intl, España primero y resto alfabético. Nacionalidad admite además Apátrida. No se asigna una nacionalidad automáticamente.
- La lista incluye países y territorios ISO; no es una lista de gentilicios ni una comprobación de ciudadanía.
- Catálogo local existente: 19 comunidades/ciudades autónomas, 52 provincias y 8.132 municipios. Selección dependiente comunidad -> provincia -> población/municipio. Los municipios no equivalen al inventario de todas las entidades menores de población.
- Cambiar comunidad borra provincia y municipio; cambiar provincia borra municipio. Se conservan los demás datos del borrador. Para domicilios fuera de España se habilita entrada manual territorial.
- Domicilios fiscal, personal (inversor) y social (jurídica): calle, número/s/n, piso/puerta opcional y código postal. Botón para copiar explícitamente domicilio fiscal a otro domicilio. No se asume que coincidan.
- Búsqueda de calles a petición explícita, con el servicio oficial CartoCiudad IGN/CNIG. Solo consulta el texto del campo calle y municipio/provincia elegidos; no consulta identidad, email, número, piso o puerta. Petición sin credenciales ni referrer. No es descarga de todos los callejeros ni garantiza cobertura exhaustiva.
- API fija HTTPS, resultados callejero del municipio solicitado, máximo 12, texto escapado por textContent, límite de 10 segundos y cancelación de búsquedas antiguas. El usuario selecciona y confirma número; el código postal se sugiere cuando está disponible.
- Si el servicio no responde o no encuentra la calle, se mantiene entrada manual. No se marca una dirección como verificada por elegir sugerencia. Premium y reservas conservan la revisión de servidor obligatoria.
- Provincia y números/s/n se incluyen en completitud y esquema de borrador y snapshot de oferta; campos opcionales de piso/puerta y código postal se reutilizan. Los perfiles previos sin datos nuevos necesitan completarse y revisarse antes de contratar.

## Fuentes
- Catálogo ya versionado: frontend/public/private/geography.js (backend/data/geo_es.json).
- https://github.com/IDEESpain/Cartociudad (contrato candidates, filtros municipio/provincia y límites).
- https://www.cartociudad.es/web/portal/directorio-de-servicios/geoprocesamiento
- https://www.cartociudad.es/geocoder/api/geocoder/candidates

## Comprobaciones
- tests/profile-location.cjs: países y orden, encadenado y reinicio, consulta REAL desde navegador a CartoCiudad (Marina, Viladecans, Barcelona), selección, número independiente y copia del domicilio, recarga, fallo de servicio y entrada manual, domicilio extranjero y móviles 390/768.
- tests/onboarding-journey.cjs: cuatro perfiles PF/PJ inversor/colaborador, completos con la nueva ubicación y documentos ficticios; continúan pendientes de revisión y contratación bloqueada.
- backend/tests/test_investor_access.py: 20 casos, con provincia y números de dirección en los snapshots sintéticos; sin cobros ni envíos.

Solo rama/Preview. No se modifica producción ni se activa custodia de documentos o identidad real.
