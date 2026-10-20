# WEB · Acceso anticipado

La WEB reciente utiliza `WEB_EARLY_ACCESS` en el servicio de identidad de Render. Activo por defecto; `false`, `off` o `0` lo desactivan. Guardar la variable y reiniciar/desplegar el servicio actualiza el modo sin reconstruir el frontend. No cambia suscripciones, cobros, permisos ni canales M2M.

`GET /api/account/config` devuelve el modo y únicamente el estado agregado `catalog_state`: `empty`, `available` o `error`. Solo se considera producto publicado si existe una vinculación aprobada y segura y una publicación `PUBLISHED` correspondiente. Un error de consulta no se transforma en ausencia de catálogo. El área privada diferencia catálogo vacío de ausencia de oportunidades para el perfil/universo seleccionado.

La portada omite las tarjetas ilustrativas; desactivar el modo no debe volver a presentarlas como producto real. El botón lleva al catálogo real en el área privada. El registro gratuito avisa del acceso anticipado y no implica suscripción ni cargos.

Reversión: restaurar el despliegue anterior de Vercel y el commit anterior del servicio Render. La variable permite desactivar únicamente la comunicación de prelanzamiento. No hay migraciones ni modificaciones de registros de usuarios.

Importante: al revisar el 20/10/2026, el dominio oportuniia.com servía otra WEB en WordPress; el proyecto Vercel oportuniia-web no tenía ese dominio asignado. Publicar esta rama en Vercel no modifica por sí solo WordPress ni su DNS.
