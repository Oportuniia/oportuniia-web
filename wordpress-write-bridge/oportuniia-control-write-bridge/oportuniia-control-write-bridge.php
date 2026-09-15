<?php
/**
 * Plugin Name: OPORTUNIIA Control Write Bridge
 * Description: PRE-RELEASE. Escritura controlada de SOLO el campo _elementor_data en dos borradores fijos (HOME 2.0 #1630 page, HEADER 2.0 #1641 elementor_library). Rutas fijas por objeto, sin IDs de cliente. Prepare+nonce (single-use, TTL 5m), precondition hash (anti stale-write), whitelist estricta de payload, validacion Elementor, size cap, readback. Sin publicar, sin tocar status/title/otros campos, sin purgas globales. Instalable/retirable de forma independiente al Read Bridge v1.0.1.
 * Version: 0.1.0-rc1
 * Author: OPORTUNIIA Arquitectura Master
 * License: GPL-2.0-or-later
 * Requires at least: 5.6
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit; // No acceso directo.
}

/* ------------------------------------------------------------------ *
 * LIMITES DUROS — no configurables por cliente.
 * ------------------------------------------------------------------ */
if ( ! defined( 'OPORTUNIIA_WB_USER' ) ) {
    define( 'OPORTUNIIA_WB_USER', 'emergent_build' );
}
if ( ! defined( 'OPORTUNIIA_WB_STATUS' ) ) {
    define( 'OPORTUNIIA_WB_STATUS', 'draft' );
}
if ( ! defined( 'OPORTUNIIA_WB_NS' ) ) {
    define( 'OPORTUNIIA_WB_NS', 'oportuniia-control-write/v1' );
}
if ( ! defined( 'OPORTUNIIA_WB_MAX_BYTES' ) ) {
    // Provisional (1.5 MiB). HEADER real ~11 KB. Ajustar tras medir HOME.
    define( 'OPORTUNIIA_WB_MAX_BYTES', 1572864 );
}
if ( ! defined( 'OPORTUNIIA_WB_MAX_DEPTH' ) ) {
    define( 'OPORTUNIIA_WB_MAX_DEPTH', 32 );
}
if ( ! defined( 'OPORTUNIIA_WB_TTL' ) ) {
    define( 'OPORTUNIIA_WB_TTL', 300 ); // 5 min.
}

/**
 * Targets fijos. El ID nunca viaja en el request; se resuelve por la ruta.
 */
function oportuniia_wb_targets() {
    return array(
        'home'   => array( 'id' => 1630, 'type' => 'page' ),
        'header' => array( 'id' => 1641, 'type' => 'elementor_library' ),
    );
}

/* ------------------------------------------------------------------ *
 * RUTAS — separadas por objeto. GET prepare + POST write.
 * ------------------------------------------------------------------ */
add_action( 'rest_api_init', function () {
    foreach ( array( 'home', 'header' ) as $slug ) {
        register_rest_route(
            OPORTUNIIA_WB_NS,
            '/' . $slug . '/prepare',
            array(
                'methods'             => 'GET',
                'permission_callback' => 'oportuniia_wb_perm_' . $slug,
                'callback'            => 'oportuniia_wb_prepare_' . $slug,
            )
        );
        register_rest_route(
            OPORTUNIIA_WB_NS,
            '/' . $slug,
            array(
                'methods'             => 'POST',
                'permission_callback' => 'oportuniia_wb_perm_' . $slug,
                'callback'            => 'oportuniia_wb_write_' . $slug,
            )
        );
    }
} );

/* Wrappers fijos (evitan target dinamico desde cliente). */
function oportuniia_wb_perm_home()   { return oportuniia_wb_permission( 'home' ); }
function oportuniia_wb_perm_header() { return oportuniia_wb_permission( 'header' ); }
function oportuniia_wb_prepare_home( $r )   { return oportuniia_wb_do_prepare( 'home', $r ); }
function oportuniia_wb_prepare_header( $r ) { return oportuniia_wb_do_prepare( 'header', $r ); }
function oportuniia_wb_write_home( $r )     { return oportuniia_wb_do_write( 'home', $r ); }
function oportuniia_wb_write_header( $r )   { return oportuniia_wb_do_write( 'header', $r ); }

/* ------------------------------------------------------------------ *
 * PERMISOS — doble barrera + capability sobre el objeto concreto.
 * ------------------------------------------------------------------ */
function oportuniia_wb_permission( $slug ) {
    $targets = oportuniia_wb_targets();
    if ( ! isset( $targets[ $slug ] ) ) {
        return new WP_Error( 'oportuniia_forbidden', 'Unknown target.', array( 'status' => 403 ) );
    }
    if ( ! is_user_logged_in() ) {
        return new WP_Error( 'oportuniia_forbidden', 'Authentication required.', array( 'status' => 401 ) );
    }
    $user = wp_get_current_user();
    if ( ! $user || $user->user_login !== OPORTUNIIA_WB_USER ) {
        return new WP_Error( 'oportuniia_forbidden', 'User not authorized.', array( 'status' => 403 ) );
    }
    if ( ! current_user_can( 'edit_post', $targets[ $slug ]['id'] ) ) {
        return new WP_Error( 'oportuniia_forbidden', 'Capability missing for object.', array( 'status' => 403 ) );
    }
    return true;
}

/* ------------------------------------------------------------------ *
 * GUARDA COMUN — valida objeto/tipo/estado. Fail-closed.
 * ------------------------------------------------------------------ */
function oportuniia_wb_load_guarded( $slug ) {
    $targets = oportuniia_wb_targets();
    $cfg     = $targets[ $slug ];
    $post    = get_post( $cfg['id'] );
    if ( ! $post || get_post_type( $post ) !== $cfg['type'] ) {
        return new WP_Error( 'oportuniia_not_found', 'Target not found or wrong type.', array( 'status' => 404 ) );
    }
    if ( $post->post_status !== OPORTUNIIA_WB_STATUS ) {
        return new WP_Error( 'oportuniia_forbidden', 'Target is not a draft. Denied.', array( 'status' => 409 ) );
    }
    return array( 'cfg' => $cfg, 'post' => $post );
}

function oportuniia_wb_current_data_hash( $id ) {
    $raw = get_post_meta( $id, '_elementor_data', true );
    if ( ! is_string( $raw ) ) {
        $raw = is_array( $raw ) ? wp_json_encode( $raw ) : '';
    }
    return array( 'raw' => $raw, 'hash' => hash( 'sha256', $raw ), 'bytes' => strlen( $raw ) );
}

/* ------------------------------------------------------------------ *
 * PREPARE — emite operation_id (single-use, TTL) ligado a target+base_hash.
 * ------------------------------------------------------------------ */
function oportuniia_wb_do_prepare( $slug, $request ) {
    $guard = oportuniia_wb_load_guarded( $slug );
    if ( is_wp_error( $guard ) ) {
        return $guard;
    }
    $cfg  = $guard['cfg'];
    $cur  = oportuniia_wb_current_data_hash( $cfg['id'] );

    $operation_id = wp_generate_uuid4();
    $record = array(
        'slug'      => $slug,
        'target_id' => $cfg['id'],
        'type'      => $cfg['type'],
        'base_hash' => $cur['hash'],
        'created'   => time(),
        'used'      => 0,
    );
    set_transient( 'oportuniia_wb_' . $operation_id, $record, OPORTUNIIA_WB_TTL );

    return new WP_REST_Response(
        array(
            'operation_id' => $operation_id,
            'target_id'    => $cfg['id'],
            'post_type'    => $cfg['type'],
            'status'       => OPORTUNIIA_WB_STATUS,
            'base_hash'    => $cur['hash'],
            'current_bytes'=> $cur['bytes'],
            'ttl'          => OPORTUNIIA_WB_TTL,
            'max_bytes'    => OPORTUNIIA_WB_MAX_BYTES,
        ),
        200
    );
}

/* ------------------------------------------------------------------ *
 * VALIDACION ELEMENTOR — estructura nativa, no autocorrige.
 * ------------------------------------------------------------------ */
function oportuniia_wb_validate_elementor( $value, &$reason ) {
    // Acepta string JSON o array ya decodificado.
    if ( is_string( $value ) ) {
        $decoded = json_decode( $value, true );
        if ( json_last_error() !== JSON_ERROR_NONE ) {
            $reason = 'invalid_json';
            return null;
        }
    } elseif ( is_array( $value ) ) {
        $decoded = $value;
    } else {
        $reason = 'unsupported_type';
        return null;
    }

    if ( ! is_array( $decoded ) || array() === $decoded ) {
        $reason = 'root_not_nonempty_array';
        return null;
    }
    // Raiz debe ser lista (array de nodos), no objeto asociativo.
    if ( array_keys( $decoded ) !== range( 0, count( $decoded ) - 1 ) ) {
        $reason = 'root_not_list';
        return null;
    }
    $allowed = array( 'section', 'column', 'container', 'widget' );
    $ok = oportuniia_wb_walk_nodes( $decoded, $allowed, 1, $reason );
    if ( ! $ok ) {
        return null;
    }
    return $decoded;
}

function oportuniia_wb_walk_nodes( $nodes, $allowed, $depth, &$reason ) {
    if ( $depth > OPORTUNIIA_WB_MAX_DEPTH ) {
        $reason = 'max_depth_exceeded';
        return false;
    }
    foreach ( $nodes as $node ) {
        if ( ! is_array( $node ) ) {
            $reason = 'node_not_object';
            return false;
        }
        if ( ! isset( $node['elType'] ) || ! in_array( $node['elType'], $allowed, true ) ) {
            $reason = 'invalid_elType';
            return false;
        }
        if ( ! empty( $node['elements'] ) ) {
            if ( ! is_array( $node['elements'] ) ) {
                $reason = 'elements_not_array';
                return false;
            }
            if ( ! oportuniia_wb_walk_nodes( $node['elements'], $allowed, $depth + 1, $reason ) ) {
                return false;
            }
        }
    }
    return true;
}

/* ------------------------------------------------------------------ *
 * WRITE — whitelist estricta, nonce, precondition hash, write, readback.
 * ------------------------------------------------------------------ */
function oportuniia_wb_do_write( $slug, $request ) {
    $guard = oportuniia_wb_load_guarded( $slug );
    if ( is_wp_error( $guard ) ) {
        return $guard;
    }
    $cfg   = $guard['cfg'];
    $post  = $guard['post'];

    // --- Payload: whitelist EXACTA de 3 claves ---
    $body = $request->get_json_params();
    if ( ! is_array( $body ) ) {
        return new WP_Error( 'oportuniia_bad_payload', 'Body must be JSON object.', array( 'status' => 422 ) );
    }
    $allowed_keys = array( 'operation_id', 'base_hash', '_elementor_data' );
    foreach ( array_keys( $body ) as $k ) {
        if ( ! in_array( $k, $allowed_keys, true ) ) {
            return new WP_Error( 'oportuniia_bad_payload', 'Unexpected field: ' . $k, array( 'status' => 422 ) );
        }
    }
    foreach ( $allowed_keys as $k ) {
        if ( ! array_key_exists( $k, $body ) ) {
            return new WP_Error( 'oportuniia_bad_payload', 'Missing field: ' . $k, array( 'status' => 422 ) );
        }
    }

    $operation_id = (string) $body['operation_id'];
    $client_base  = (string) $body['base_hash'];

    // --- Nonce: existe, ligado al target, no usado, no expirado ---
    $tkey = 'oportuniia_wb_' . $operation_id;
    $rec  = get_transient( $tkey );
    if ( ! is_array( $rec ) ) {
        return new WP_Error( 'oportuniia_operation', 'Unknown or expired operation.', array( 'status' => 403 ) );
    }
    if ( ! empty( $rec['used'] ) ) {
        return new WP_Error( 'oportuniia_operation', 'Operation already consumed.', array( 'status' => 409 ) );
    }
    if ( $rec['slug'] !== $slug || (int) $rec['target_id'] !== (int) $cfg['id'] || $rec['type'] !== $cfg['type'] ) {
        return new WP_Error( 'oportuniia_operation', 'Operation target mismatch.', array( 'status' => 403 ) );
    }
    if ( ! hash_equals( (string) $rec['base_hash'], $client_base ) ) {
        return new WP_Error( 'oportuniia_operation', 'base_hash does not match prepared operation.', array( 'status' => 409 ) );
    }

    // --- Precondition: re-lectura inmediata + comparacion (anti stale) ---
    $cur = oportuniia_wb_current_data_hash( $cfg['id'] );
    if ( ! hash_equals( $cur['hash'], $client_base ) ) {
        // Estado humano posterior es autoritativo. Invalidamos nonce.
        delete_transient( $tkey );
        return new WP_Error( 'oportuniia_conflict', 'Stale base: content changed since prepare.', array( 'status' => 409 ) );
    }

    // --- Validacion Elementor ---
    $reason  = '';
    $decoded = oportuniia_wb_validate_elementor( $body['_elementor_data'], $reason );
    if ( null === $decoded ) {
        return new WP_Error( 'oportuniia_invalid_elementor', 'Invalid Elementor data: ' . $reason, array( 'status' => 422 ) );
    }

    // Serializacion canonica para almacenar y hashear.
    $json_string = wp_json_encode( $decoded );
    if ( ! is_string( $json_string ) ) {
        return new WP_Error( 'oportuniia_invalid_elementor', 'Re-encode failed.', array( 'status' => 422 ) );
    }

    // --- Size cap ---
    if ( strlen( $json_string ) > OPORTUNIIA_WB_MAX_BYTES ) {
        return new WP_Error( 'oportuniia_too_large', 'Payload exceeds max bytes.', array( 'status' => 413 ) );
    }

    $title_before  = $post->post_title;
    $status_before = $post->post_status;
    $after_hash    = hash( 'sha256', $json_string );

    // --- Escritura: SOLO _elementor_data. Nada mas. ---
    update_post_meta( $cfg['id'], '_elementor_data', wp_slash( $json_string ) );

    // Preservar flags SOLO si faltan (no reescribir innecesariamente).
    if ( 'builder' !== get_post_meta( $cfg['id'], '_elementor_edit_mode', true ) ) {
        update_post_meta( $cfg['id'], '_elementor_edit_mode', 'builder' );
    }
    if ( '' === (string) get_post_meta( $cfg['id'], '_elementor_version', true ) && defined( 'ELEMENTOR_VERSION' ) ) {
        update_post_meta( $cfg['id'], '_elementor_version', ELEMENTOR_VERSION );
    }

    // Consumir nonce (single-use).
    delete_transient( $tkey );

    // --- Invalidacion de CSS SOLO del objeto afectado (sin purga global) ---
    oportuniia_wb_clear_object_css( $cfg['id'] );

    // --- Readback ---
    $post2 = get_post( $cfg['id'] );
    $cur2  = oportuniia_wb_current_data_hash( $cfg['id'] );
    $readback_ok = (
        $post2 &&
        (int) $post2->ID === (int) $cfg['id'] &&
        get_post_type( $post2 ) === $cfg['type'] &&
        $post2->post_status === OPORTUNIIA_WB_STATUS &&
        $post2->post_status === $status_before &&
        $post2->post_title === $title_before &&
        hash_equals( $after_hash, $cur2['hash'] )
    );

    return new WP_REST_Response(
        array(
            'operation_id'  => $operation_id,
            'target_id'     => (int) $cfg['id'],
            'post_type'     => $cfg['type'],
            'status'        => $post2 ? $post2->post_status : null,
            'before_hash'   => $client_base,
            'after_hash'    => $after_hash,
            'title_unchanged' => $post2 ? ( $post2->post_title === $title_before ) : false,
            'readback'      => $readback_ok ? 'PASS' : 'FAIL',
            'bytes_written' => strlen( $json_string ),
        ),
        $readback_ok ? 200 : 500
    );
}

/**
 * Invalidacion de CSS ACOTADA al objeto. Sin purga global / site-wide.
 * Usa la clase de Elementor solo si existe; si no, no hace nada global.
 */
function oportuniia_wb_clear_object_css( $id ) {
    if ( class_exists( '\\Elementor\\Core\\Files\\CSS\\Post' ) ) {
        try {
            $css = new \Elementor\Core\Files\CSS\Post( (int) $id );
            $css->delete(); // Solo el CSS de ESTE post.
        } catch ( \Throwable $e ) {
            // Silencioso y acotado: nunca escalar a purga global.
            unset( $e );
        }
    }
}
