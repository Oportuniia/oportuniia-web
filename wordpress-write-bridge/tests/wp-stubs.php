<?php
/**
 * Minimal WordPress stubs to unit-test the Write Bridge plugin logic in PHP CLI.
 * NOT part of the plugin artifact. Test-only.
 */

if ( ! defined( 'ABSPATH' ) ) {
    define( 'ABSPATH', '/tmp/wp/' );
}

$GLOBALS['__posts']      = array();   // id => (object){ID,post_type,post_status,post_title}
$GLOBALS['__meta']       = array();   // id => [key => value]
$GLOBALS['__transients'] = array();   // key => ['value'=>..,'expires_at'=>ts]
$GLOBALS['__routes']     = array();
$GLOBALS['__current']    = array( 'login' => 'emergent_build', 'logged_in' => true );
$GLOBALS['__caps']       = array( 'edit_post' => true ); // per-cap boolean

class WP_Error {
    public $code; public $message; public $data;
    public function __construct( $code = '', $message = '', $data = array() ) {
        $this->code = $code; $this->message = $message; $this->data = $data;
    }
    public function get_error_data() { return $this->data; }
    public function get_error_code() { return $this->code; }
}
function is_wp_error( $x ) { return ( $x instanceof WP_Error ); }

class WP_REST_Response {
    public $data; public $status;
    public function __construct( $data = null, $status = 200 ) { $this->data = $data; $this->status = $status; }
    public function get_data() { return $this->data; }
    public function get_status() { return $this->status; }
}

class WP_REST_Request {
    private $json;
    public function __construct( $json = array() ) { $this->json = $json; }
    public function get_json_params() { return $this->json; }
}

function add_action( $hook, $cb ) { if ( 'rest_api_init' === $hook ) { $cb(); } }
function register_rest_route( $ns, $route, $args ) {
    $GLOBALS['__routes'][ $ns . $route ] = $args;
}

function is_user_logged_in() { return (bool) $GLOBALS['__current']['logged_in']; }
function wp_get_current_user() { return (object) array( 'user_login' => $GLOBALS['__current']['login'] ); }
function current_user_can( $cap, $id = null ) { return ! empty( $GLOBALS['__caps'][ $cap ] ); }

function get_post( $id ) { return isset( $GLOBALS['__posts'][ $id ] ) ? $GLOBALS['__posts'][ $id ] : null; }
function get_post_type( $post ) { return is_object( $post ) ? $post->post_type : null; }
function get_post_meta( $id, $key, $single = false ) {
    return isset( $GLOBALS['__meta'][ $id ][ $key ] ) ? $GLOBALS['__meta'][ $id ][ $key ] : '';
}
function update_post_meta( $id, $key, $val ) {
    $GLOBALS['__meta'][ $id ][ $key ] = $val;
    $GLOBALS['__meta_calls'][] = array( $id, $key );
    return true;
}
function wp_slash( $v ) { return $v; }
function wp_json_encode( $v ) { return json_encode( $v ); }
function wp_generate_uuid4() { return sprintf( '%04x%04x-%04x-%04x-%04x-%04x%04x%04x', mt_rand(0,0xffff), mt_rand(0,0xffff), mt_rand(0,0xffff), mt_rand(0,0x0fff)|0x4000, mt_rand(0,0x3fff)|0x8000, mt_rand(0,0xffff), mt_rand(0,0xffff), mt_rand(0,0xffff) ); }

function set_transient( $key, $val, $ttl ) {
    $GLOBALS['__transients'][ $key ] = array( 'value' => $val, 'expires_at' => time() + $ttl );
    return true;
}
function get_transient( $key ) {
    if ( ! isset( $GLOBALS['__transients'][ $key ] ) ) { return false; }
    $t = $GLOBALS['__transients'][ $key ];
    if ( time() > $t['expires_at'] ) { unset( $GLOBALS['__transients'][ $key ] ); return false; }
    return $t['value'];
}
function delete_transient( $key ) { unset( $GLOBALS['__transients'][ $key ] ); return true; }

/* Helpers for tests */
function __seed_post( $id, $type, $status, $title, $elementor_data ) {
    $GLOBALS['__posts'][ $id ] = (object) array( 'ID' => $id, 'post_type' => $type, 'post_status' => $status, 'post_title' => $title );
    $GLOBALS['__meta'][ $id ]['_elementor_data'] = $elementor_data;
}
function __reset() {
    $GLOBALS['__posts'] = array(); $GLOBALS['__meta'] = array(); $GLOBALS['__transients'] = array();
    $GLOBALS['__current'] = array( 'login' => 'emergent_build', 'logged_in' => true );
    $GLOBALS['__caps'] = array( 'edit_post' => true );
    $GLOBALS['__meta_calls'] = array();
}
