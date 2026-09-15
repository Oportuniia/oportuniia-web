<?php
/**
 * Plugin Name: OPORTUNIIA Control Bridge (READ-ONLY)
 * Description: Puente REST de SOLO LECTURA para leer un unico template Elementor autorizado (HEADER 2.0, ID 1641). GET only. Sin escritura. Sin acceso a otros templates. Sin tocar el header activo. Retirable en cualquier momento.
 * Version: 1.0.0
 * Author: OPORTUNIIA Arquitectura Master
 * License: GPL-2.0-or-later
 * Requires at least: 5.6
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit; // No acceso directo.
}

/*
 * LIMITES DUROS — no configurables desde el cliente.
 * Cualquier intento de leer otro ID o post_type se rechaza.
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
 * Permiso: solo el usuario tecnico autorizado + capacidad minima edit_posts.
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
    if ( ! current_user_can( 'edit_posts' ) ) {
        return new WP_Error( 'oportuniia_forbidden', 'Minimum capability missing.', array( 'status' => 403 ) );
    }
    return true;
}

/**
 * Devuelve SOLO: id, title, status, post_type, _elementor_data del template 1641.
 * READ-ONLY. No escribe nada. No expone otros templates ni el header activo.
 */
function oportuniia_bridge_read_header( WP_REST_Request $request ) {
    $id = OPORTUNIIA_BRIDGE_ALLOWED_ID; // Fijado por codigo. El cliente no puede pedir otro ID.

    $post = get_post( $id );
    if ( ! $post || get_post_type( $post ) !== OPORTUNIIA_BRIDGE_ALLOWED_TYPE ) {
        return new WP_Error( 'oportuniia_not_found', 'Authorized template not found or wrong type.', array( 'status' => 404 ) );
    }

    $elementor_data = get_post_meta( $id, '_elementor_data', true );

    $data = array(
        'id'              => (int) $post->ID,
        'title'           => get_the_title( $post ),
        'status'          => $post->post_status,
        'post_type'       => $post->post_type,
        '_elementor_data' => $elementor_data, // JSON string tal cual se almacena.
    );

    return new WP_REST_Response( $data, 200 );
}
