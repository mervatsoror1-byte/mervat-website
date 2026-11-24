<?php
// Free sign-up from the site (name + email, no password): saved privately and emailed to Dr. Mervat.
require __DIR__ . '/_lib.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { fail(404, 'unknown'); }
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$host = $_SERVER['HTTP_HOST'] ?? '';
if ($origin !== '' && strtolower((string)parse_url($origin, PHP_URL_HOST)) !== strtolower(explode(':', $host)[0])) { fail(403, 'origin'); }

$in = json_decode((string)file_get_contents('php://input'), true);
if (!is_array($in)) { fail(400, 'body'); }
if (!empty($in['website'])) { send_json(['ok' => true]); }   // honeypot
if (!rate_ok('lead', 8, 3600)) { fail(429, 'limit'); }

$name = clean_text((string)($in['name'] ?? ''), 60);
$email = filter_var(trim((string)($in['email'] ?? '')), FILTER_VALIDATE_EMAIL) ?: '';
if ($name === '' || $email === '') { fail(400, 'fields'); }
$lead = ['name' => $name, 'email' => strtolower($email), 'news' => !empty($in['news']), 'source' => clean_text((string)($in['source'] ?? ''), 80), 'created_at' => gmdate('c')];

$path = data_dir() . '/leads.json';
$fh = fopen($path, 'c+'); flock($fh, LOCK_EX);
$list = json_decode((string)stream_get_contents($fh), true) ?: [];
$new = true;
foreach ($list as $l) { if (($l['email'] ?? '') === $lead['email']) { $new = false; break; } }
if ($new) { $list[] = $lead; ftruncate($fh, 0); rewind($fh); fwrite($fh, json_encode($list, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)); }
flock($fh, LOCK_UN); fclose($fh); @chmod($path, 0600);

if (is_file(MS_WP_LOAD)) { if (!defined('WP_USE_THEMES')) { define('WP_USE_THEMES', false); } require_once MS_WP_LOAD; }
if ($new) {
    $body = "تسجيل جديد في الموقع\n\nالاسم: {$lead['name']}\nالبريد: {$lead['email']}\nيريد الهدية وجديد د. مرفت على بريده: " . ($lead['news'] ? 'نعم' : 'لا') . "\nمن صفحة: {$lead['source']}\n\nإجمالي المسجلين حتى الآن: " . count($list) . "\n";
    ms_mail(NOTIFY_EMAIL, 'تسجيل جديد: ' . $lead['name'], $body, $lead['email'], 'موقع د. مرفت سرور');
}
send_json(['ok' => true]);
