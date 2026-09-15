<?php
/**
 * Security/behaviour tests for OPORTUNIIA Control Write Bridge (PHP CLI, stubbed WP).
 * Run: php test_write_bridge.php
 */
require __DIR__ . '/wp-stubs.php';
require __DIR__ . '/../oportuniia-control-write-bridge/oportuniia-control-write-bridge.php';

$PASS = 0; $FAIL = 0; $RESULTS = array();
function check( $name, $cond ) {
    global $PASS, $FAIL, $RESULTS;
    if ( $cond ) { $PASS++; $RESULTS[] = "PASS  $name"; }
    else { $FAIL++; $RESULTS[] = "FAIL  $name"; }
}

/* Valid minimal Elementor tree */
function valid_tree() {
    return array(
        array( 'id' => 'a1', 'elType' => 'container', 'elements' => array(
            array( 'id' => 'w1', 'elType' => 'widget', 'elements' => array() ),
        ) ),
    );
}
function valid_json() { return json_encode( valid_tree() ); }

/* Seed both drafts with a known current data, return base_hash */
function seed_drafts( $data ) {
    __reset();
    __seed_post( 1630, 'page', 'draft', 'HOME 2.0', $data );
    __seed_post( 1641, 'elementor_library', 'draft', 'Elementor Cabecera #1641', $data );
    return hash( 'sha256', $data );
}

/* Do a prepare, return decoded response array */
function prepare( $slug ) {
    $r = ( 'home' === $slug ) ? oportuniia_wb_prepare_home( new WP_REST_Request() )
                              : oportuniia_wb_prepare_header( new WP_REST_Request() );
    return $r;
}
function write( $slug, $body ) {
    return ( 'home' === $slug ) ? oportuniia_wb_write_home( new WP_REST_Request( $body ) )
                                : oportuniia_wb_write_header( new WP_REST_Request( $body ) );
}
function status_of( $resp ) {
    if ( is_wp_error( $resp ) ) { return $resp->get_error_data()['status'] ?? 0; }
    return $resp->get_status();
}

/* ---------- Happy path (home) ---------- */
$cur = valid_json();
$base = seed_drafts( $cur );
$p = prepare( 'home' );
check( 'prepare returns operation_id', ! is_wp_error( $p ) && ! empty( $p->get_data()['operation_id'] ) );
check( 'prepare base_hash matches current', $p->get_data()['base_hash'] === $base );
$op = $p->get_data()['operation_id'];
$newtree = valid_tree();
$newtree[0]['elements'][] = array( 'id' => 'w2', 'elType' => 'widget', 'elements' => array() );
$newjson = json_encode( $newtree );
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => $newjson ) );
check( 'happy write 200', ! is_wp_error( $w ) && $w->get_status() === 200 );
check( 'happy write readback PASS', ! is_wp_error( $w ) && $w->get_data()['readback'] === 'PASS' );
check( 'happy write only _elementor_data mutated', $GLOBALS['__posts'][1630]->post_status === 'draft' && $GLOBALS['__posts'][1630]->post_title === 'HOME 2.0' );

/* ---------- correct user already covered; wrong user ---------- */
$base = seed_drafts( $cur );
$GLOBALS['__current']['login'] = 'admin';
check( 'wrong user -> 403', status_of( oportuniia_wb_permission( 'home' ) ) === 403 );
$GLOBALS['__current']['login'] = 'emergent_build';

/* ---------- missing auth ---------- */
$GLOBALS['__current']['logged_in'] = false;
check( 'missing auth -> 401', status_of( oportuniia_wb_permission( 'home' ) ) === 401 );
$GLOBALS['__current']['logged_in'] = true;

/* ---------- missing capability ---------- */
$GLOBALS['__caps']['edit_post'] = false;
check( 'no cap -> 403', status_of( oportuniia_wb_permission( 'home' ) ) === 403 );
$GLOBALS['__caps']['edit_post'] = true;

/* ---------- non-draft target ---------- */
$base = seed_drafts( $cur );
$GLOBALS['__posts'][1630]->post_status = 'publish';
check( 'non-draft -> 409 and no write', status_of( oportuniia_wb_load_guarded( 'home' ) ) === 409 );

/* ---------- wrong post_type ---------- */
$base = seed_drafts( $cur );
$GLOBALS['__posts'][1641]->post_type = 'page';
check( 'wrong post_type -> 404', status_of( oportuniia_wb_load_guarded( 'header' ) ) === 404 );

/* ---------- unexpected payload field ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => valid_json(), 'status' => 'publish' ) );
check( 'unexpected field status -> 422', status_of( $w ) === 422 );

/* ---------- attempted title/publish/instances/meta fields rejected (same whitelist) ---------- */
foreach ( array( 'title', 'publish', 'instances', 'meta', 'post_id', 'author', 'slug', 'featured_media', 'content' ) as $bad ) {
    $base = seed_drafts( $cur );
    $op = prepare( 'home' )->get_data()['operation_id'];
    $w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => valid_json(), $bad => 'x' ) );
    check( "reject field '$bad' -> 422", status_of( $w ) === 422 );
}

/* ---------- malformed JSON ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => '{not json' ) );
check( 'malformed JSON -> 422', status_of( $w ) === 422 );

/* ---------- invalid root (object not list) ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => json_encode( array( 'foo' => 'bar' ) ) ) );
check( 'invalid root -> 422', status_of( $w ) === 422 );

/* ---------- invalid node (bad elType) ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => json_encode( array( array( 'id' => 'x', 'elType' => 'iframe' ) ) ) ) );
check( 'invalid elType -> 422', status_of( $w ) === 422 );

/* ---------- excessive depth ---------- */
$deep = array( 'id' => 'r', 'elType' => 'container', 'elements' => array() );
$ref = &$deep;
for ( $i = 0; $i < 40; $i++ ) { $ref['elements'] = array( array( 'id' => "n$i", 'elType' => 'container', 'elements' => array() ) ); $ref = &$ref['elements'][0]; }
unset( $ref );
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => json_encode( array( $deep ) ) ) );
check( 'excessive depth -> 422', status_of( $w ) === 422 );

/* ---------- empty payload ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => '[]' ) );
check( 'empty array -> 422', status_of( $w ) === 422 );

/* ---------- oversized payload ---------- */
$big = array();
$blob = str_repeat( 'x', 2000000 );
$big[] = array( 'id' => 'big', 'elType' => 'widget', 'settings' => array( 'text' => $blob ), 'elements' => array() );
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => json_encode( $big ) ) );
check( 'oversized -> 413', status_of( $w ) === 413 );

/* ---------- expired operation ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$GLOBALS['__transients'][ 'oportuniia_wb_' . $op ]['expires_at'] = time() - 1;
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => valid_json() ) );
check( 'expired operation -> 403', status_of( $w ) === 403 );

/* ---------- reused operation (single-use) ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$w1 = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => valid_json() ) );
$w2 = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => valid_json() ) );
check( 'first use ok', ! is_wp_error( $w1 ) && $w1->get_status() === 200 );
check( 'reuse -> 403 (unknown/consumed)', status_of( $w2 ) === 403 );

/* ---------- unknown operation ---------- */
$base = seed_drafts( $cur );
$w = write( 'home', array( 'operation_id' => 'does-not-exist', 'base_hash' => $base, '_elementor_data' => valid_json() ) );
check( 'unknown operation -> 403', status_of( $w ) === 403 );

/* ---------- wrong base_hash ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => 'deadbeef', '_elementor_data' => valid_json() ) );
check( 'wrong base_hash -> 409', status_of( $w ) === 409 );

/* ---------- stale base (human edit after prepare) ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$GLOBALS['__meta'][1630]['_elementor_data'] = json_encode( valid_tree() ) . ' '; // changed
$w = write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => valid_json() ) );
check( 'stale base -> 409 conflict', status_of( $w ) === 409 );
check( 'stale conflict invalidates nonce', get_transient( 'oportuniia_wb_' . $op ) === false );

/* ---------- operation bound to target (cannot reuse home op on header) ---------- */
$base = seed_drafts( $cur );
$op_home = prepare( 'home' )->get_data()['operation_id'];
$w = write( 'header', array( 'operation_id' => $op_home, 'base_hash' => $base, '_elementor_data' => valid_json() ) );
check( 'cross-target op reuse -> 403', status_of( $w ) === 403 );

/* ---------- no arbitrary ID: routes are fixed (structural) ---------- */
$routes = array_keys( $GLOBALS['__routes'] );
$has_dynamic = false;
foreach ( $routes as $rt ) { if ( strpos( $rt, '(?P<' ) !== false || strpos( $rt, '{' ) !== false ) { $has_dynamic = true; } }
check( 'no dynamic ID route params', ! $has_dynamic );
check( 'exactly 4 routes (home/header prepare+write)', count( $routes ) === 4 );

/* ---------- write only touched _elementor_data + allowed flags ---------- */
$base = seed_drafts( $cur );
$op = prepare( 'home' )->get_data()['operation_id'];
$GLOBALS['__meta_calls'] = array();
write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => valid_json() ) );
$touched_keys = array_unique( array_map( function( $c ) { return $c[1]; }, $GLOBALS['__meta_calls'] ) );
$allowed_meta = array( '_elementor_data', '_elementor_edit_mode', '_elementor_version' );
$only_allowed = ! array_diff( $touched_keys, $allowed_meta );
check( 'only elementor meta keys written', $only_allowed );
$only_1630 = true;
foreach ( $GLOBALS['__meta_calls'] as $c ) { if ( (int) $c[0] !== 1630 ) { $only_1630 = false; } }
check( 'only target object 1630 written', $only_1630 );

/* ---------- ROLLBACK model: restore previous via same guarded write ---------- */
// snapshot previous, write new, then rollback to previous.
$prev = valid_json();
$base = seed_drafts( $prev );
$snapshot_prev = $GLOBALS['__meta'][1630]['_elementor_data'];
$op = prepare( 'home' )->get_data()['operation_id'];
$newtree = valid_tree(); $newtree[0]['id'] = 'changed';
write( 'home', array( 'operation_id' => $op, 'base_hash' => $base, '_elementor_data' => json_encode( $newtree ) ) );
$cur_after = hash( 'sha256', $GLOBALS['__meta'][1630]['_elementor_data'] );
// rollback: fresh prepare (new base = current), write snapshot_prev
$op2 = prepare( 'home' )->get_data()['operation_id'];
$base2 = hash( 'sha256', $GLOBALS['__meta'][1630]['_elementor_data'] );
$wr = write( 'home', array( 'operation_id' => $op2, 'base_hash' => $base2, '_elementor_data' => $snapshot_prev ) );
check( 'rollback write 200', ! is_wp_error( $wr ) && $wr->get_status() === 200 );
check( 'rollback restored previous data', hash( 'sha256', $GLOBALS['__meta'][1630]['_elementor_data'] ) === hash( 'sha256', wp_json_encode( json_decode( $snapshot_prev, true ) ) ) );

echo implode( "\n", $RESULTS ) . "\n";
echo "----\nTOTAL PASS=$PASS FAIL=$FAIL\n";
exit( $FAIL === 0 ? 0 : 1 );
