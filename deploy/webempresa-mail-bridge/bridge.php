<?php
/* Dedicated HTTPS mail bridge for the existing Webempresa hosting.
 * Deploy only after review. Config and replay records MUST be outside public_html.
 * No access tokens/passwords/recipients/message bodies are written to logs.
 */
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
function stop_request(int $status, string $code): never {
    http_response_code($status); echo json_encode(['code' => $code]); exit;
}
if (empty($_SERVER['HTTPS']) || $_SERVER['HTTPS'] === 'off') stop_request(403, 'https_required');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') stop_request(405, 'method_not_allowed');
$configPath = dirname(__DIR__, 2) . '/private/oportuniia-mail.php';
if (!is_file($configPath)) stop_request(503, 'not_configured');
$config = require $configPath;
if (!is_array($config) || empty($config['enabled']) || strlen($config['key'] ?? '') < 40) stop_request(503, 'not_configured');
$timestamp = $_SERVER['HTTP_X_OPP_MAIL_TIMESTAMP'] ?? '';
$nonce = $_SERVER['HTTP_X_OPP_MAIL_NONCE'] ?? '';
$signature = $_SERVER['HTTP_X_OPP_MAIL_SIGNATURE'] ?? '';
if (!ctype_digit($timestamp) || abs(time() - (int)$timestamp) > 300 || !preg_match('/^[a-f0-9]{32}$/D', $nonce)) stop_request(401, 'unauthorized');
$input = fopen('php://input', 'rb');
$raw = stream_get_contents($input, 65537); fclose($input);
if (strlen($raw) > 65536) stop_request(413, 'too_large');
$expected = hash_hmac('sha256', $timestamp . '.' . $nonce . '.' . $raw, $config['key']);
if (!hash_equals($expected, $signature)) stop_request(401, 'unauthorized');
try { $message = json_decode($raw, true, 8, JSON_THROW_ON_ERROR); } catch (JsonException $e) { stop_request(422, 'invalid_json'); }
if (!is_array($message)) stop_request(422, 'invalid_json');
$to = $message['to'] ?? ''; $subject = $message['subject'] ?? ''; $body = $message['body'] ?? '';
if (!is_string($to) || !filter_var($to, FILTER_VALIDATE_EMAIL) || strlen($to) > 180 || preg_match('/[\r\n]/', $to)) stop_request(422, 'invalid_recipient');
if (!is_string($subject) || strlen($subject) > 300 || preg_match('/[\r\n]/', $subject) || !is_string($body) || strlen($body) > 50000) stop_request(422, 'invalid_message');
$from = $config['from'] ?? '';
if (!filter_var($from, FILTER_VALIDATE_EMAIL) || preg_match('/[\r\n]/', $from)) stop_request(503, 'invalid_sender_configuration');
$directory = $config['nonce_directory'] ?? '';
if (!is_dir($directory) || !is_writable($directory)) stop_request(503, 'replay_store_unavailable');
// Atomic nonce reservation prevents replay, even across concurrent PHP workers.
$noncePath = $directory . '/' . hash('sha256', $nonce) . '.nonce';
$handle = @fopen($noncePath, 'x');
if ($handle === false) stop_request(409, 'already_processed');
fwrite($handle, $timestamp); fclose($handle); chmod($noncePath, 0600);
// Fixed local sender. The hosting MTA handles delivery; no SMTP credentials in code.
$headers = ['From' => 'OPORTUNIIA <' . $from . '>', 'Reply-To' => $from, 'Content-Type' => 'text/plain; charset=UTF-8', 'MIME-Version' => '1.0'];
$encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
$accepted = mail($to, $encodedSubject, $body, $headers);
if (!$accepted) stop_request(503, 'hosting_mail_unavailable');
// Only acceptance by the MTA, not a delivery receipt.
echo json_encode(['accepted' => true]);
foreach (array_slice(glob($directory . '/*.nonce') ?: [], 0, 100) as $old) {
    if (filemtime($old) < time() - 900) @unlink($old);
}
