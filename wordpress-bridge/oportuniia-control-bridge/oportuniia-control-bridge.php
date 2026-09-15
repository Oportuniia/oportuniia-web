<?php
/**
 * Plugin Name: OPORTUNIIA Control Bridge (READ-ONLY)
 * Description: Puente REST de SOLO LECTURA para leer un unico template Elementor autorizado (HEADER 2.0, ID 1641) mientras siga en estado draft. GET only. Sin escritura. Sin acceso a otros templates. Sin tocar el header activo. Retirable en cualquier momento.
 * Version: 1.0.1
 * Author: OPORTUNIIA Arquitectura Master
 * License: GPL-2.0-or-later
 * Requires at least: 5.6
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit; // No acceso directo.
}

/*
 * LIMITES DUROS — no configurables desde el cliente.
 * Cualquier intento de leer otro ID, post_type o estado se rechaza.
 */
if ( ! defined( 'OPORTUNIIA_BRIDGE_ALLOWED_ID' ) ) {
    define( 'OPORTUNIIA_BRIDGE_ALLOWED_ID', 1641 );
}
if ( ! defined( 'OPORTUNIIA_BRIDGE_ALLOWED_TYPE' ) ) {
    define( 'OPORTUNIIA_BRIDGE_ALLOWED_TYPE', 'elementor_library' );
}
if ( ! defined( 'OPORTUNIIA_BRIDGE_ALLOWED_USER' ) ) {
    define( 'OPORTUNIIA_BRIDGE_ALLOWED_USER', 'emergent_build' );
}
if ( ! defined( 'OPORTUNIIA_BRIDGE_ALLOWED_STATUS' ) ) {
    define( 'OPORTUNIIA_BRIDGE_ALLOWED_STATUS', 'draft' );
}
if ( ! defined( 'OPORTUNIIA_BRIDGE_NS' ) ) {
    define( 'OPORTUNIIA_BRIDGE_NS', 'oportuniia-control/v1' );
}

add_action( 'rest_api_init', function () {
    // Ruta unica, sin parametro de ID: el ID esta fijado por codigo.
    register_rest_route(
        OPORTUNIIA_BRIDGE_NS,
        '/header',
        array(
            'methods'             => 'GET', // GET ONLY. Sin POST/PUT/PATCH/DELETE.
            'permission_callback' => 'oportuniia_bridge_permission',
            'callback'            => 'oportuniia_bridge_read_header',
        )
    );
} );

/**
 * Permiso (doble barrera independiente):
 *   1) user_login === emergent_build
 *   2) current_user_can( 'edit_post', 1641 )  -> capability sobre el objeto concreto
 * No exige manage_options ni edit_theme_options.
 */
function oportuniia_bridge_permission() {
    if ( ! is_user_logged_in() ) {
        return new WP_Error( 'oportuniia_forbidden', 'Authentication required.', array( 'status' => 401 ) );
    }
    $user = wp_get_current_user();
    if ( ! $user || $user->user_login !== OPORTUNIIA_BRIDGE_ALLOWED_USER ) {
        return new WP_Error( 'oportuniia_forbidden', 'User not authorized for this bridge.', array( 'status' => 403 ) );
    }
    if ( ! current_user_can( 'edit_post', OPORTUNIIA_BRIDGE_ALLOWED_ID ) ) {
        return new WP_Error( 'oportuniia_forbidden', 'Minimum capability missing for this object.', array( 'status' => 403 ) );
    }
    return true;
}

/**
 * Devuelve SOLO: id, title, status, post_type, _elementor_data del template 1641,
 * y UNICAMENTE si sigue en estado draft. READ-ONLY. No escribe nada.
 */
function oportuniia_bridge_read_header( WP_REST_Request $request ) {
    $id = OPORTUNIIA_BRIDGE_ALLOWED_ID; // Fijado por codigo. El cliente no puede pedir otro ID.

    $post = get_post( $id );
    if ( ! $post || get_post_type( $post ) !== OPORTUNIIA_BRIDGE_ALLOWED_TYPE ) {
        return new WP_Error( 'oportuniia_not_found', 'Authorized template not found or wrong type.', array( 'status' => 404 ) );
    }

    // DRAFT OBLIGATORIO: si 1641 deja de ser borrador, no se devuelve nada.
    if ( $post->post_status !== OPORTUNIIA_BRIDGE_ALLOWED_STATUS ) {
        return new WP_Error( 'oportuniia_forbidden', 'Template is no longer a draft. Access denied.', array( 'status' => 403 ) );
    }

    $elementor_data = get_post_meta( $id, '_elementor_data', true );

    // READ-ONLY payload. Titulo RAW (sin filtros de presentacion) para respuesta determinista.
    $data = array(
        'id'              => (int) $post->ID,
        'title'           => $post->post_title,
        'status'          => $post->post_status,
        'post_type'       => $post->post_type,
        '_elementor_data' => $elementor_data, // JSON string tal cual se almacena.
    );

    return new WP_REST_Response( $data, 200 );
}
