<?php
// Gift «أسئلة كشف الهوية»: saves the answers privately and emails them to Dr. Mervat; the visitor gets a confirmation email.
require __DIR__ . '/_lib.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { fail(404, 'unknown'); }
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$host = $_SERVER['HTTP_HOST'] ?? '';
if ($origin !== '' && strtolower((string)parse_url($origin, PHP_URL_HOST)) !== strtolower(explode(':', $host)[0])) { fail(403, 'origin'); }

$in = json_decode((string)file_get_contents('php://input'), true);
if (!is_array($in)) { fail(400, 'body'); }
if (!empty($in['website'])) { send_json(['ok' => true]); }   // honeypot
if (!rate_ok('gift', 5, 3600)) { fail(429, 'limit'); }

$name = clean_text((string)($in['name'] ?? ''), 60);
$email = filter_var(trim((string)($in['email'] ?? '')), FILTER_VALIDATE_EMAIL) ?: '';
if ($name === '' || $email === '' || empty($in['consent'])) { fail(400, 'fields'); }

$questions = require __DIR__ . '/_gift_questions.php';
$keep = function (string $s): string {           // keep line breaks, drop control characters and tags
    $s = preg_replace('/[\x00-\x09\x0B-\x1F\x7F<>]/u', '', $s) ?? '';
    $s = preg_replace("/\n{3,}/", "\n\n", str_replace("\r", '', $s)) ?? '';
    return mb_substr(trim($s), 0, 4000);
};
$answers = [];
foreach ((array)($in['answers'] ?? []) as $k => $v) {
    $i = (int)$k;
    if ($i >= 1 && $i <= count($questions)) { $t = $keep((string)$v); if ($t !== '') { $answers[$i] = $t; } }
}

$rec = ['id' => 'G-' . strtoupper(substr(bin2hex(random_bytes(4)), 0, 6)), 'name' => $name, 'email' => strtolower($email),
        'news' => !empty($in['news']), 'answers' => $answers, 'answered' => count($answers), 'created_at' => gmdate('c')];
$path = data_dir() . '/gift.json';
$fh = fopen($path, 'c+'); flock($fh, LOCK_EX);
$list = json_decode((string)stream_get_contents($fh), true) ?: [];
$list[] = $rec;
ftruncate($fh, 0); rewind($fh); fwrite($fh, json_encode($list, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
flock($fh, LOCK_UN); fclose($fh); @chmod($path, 0600);

if (is_file(MS_WP_LOAD)) { if (!defined('WP_USE_THEMES')) { define('WP_USE_THEMES', false); } require_once MS_WP_LOAD; }
$enc = fn($s) => '=?UTF-8?B?' . base64_encode($s) . '?=';
$lines = '';
foreach ($questions as $i => $q) {
    $n = $i + 1;
    $lines .= "{$n}) {$q}\n" . ($answers[$n] ?? '— لم يُجب —') . "\n\n";
}
$body = "إجابات «أسئلة كشف الهوية»\n\nرقم الطلب: {$rec['id']}\nالاسم: {$name}\nالبريد: {$rec['email']}\nأجاب عن " . count($answers) . " من " . count($questions) . " سؤالاً\n"
      . "يريد جديد د. مرفت: " . ($rec['news'] ? 'نعم' : 'لا') . "\n\n────────────\n\n{$lines}"
      . "للرد بالتحليل: اضغطي «رد» على هذه الرسالة، فيذهب الرد إلى بريده مباشرة.\n";
ms_mail(NOTIFY_EMAIL, "كشف الهوية: {$name}", $body, $rec['email'], 'موقع د. مرفت سرور');

$thanks = "أهلاً {$name}،\n\nوصلتنا إجاباتك على «أسئلة كشف الهوية». شكراً لصدقك وشجاعتك.\n\n"
        . "د. مرفت ستقرأ إجاباتك بنفسها، ويصلك تحليلك الشخصي على هذا البريد خلال ٣ أيام.\n\n"
        . "أنوي لك التشافي بكل حب\nد. مرفت سرور\nhttps://mervatsror.com\n";
ms_mail($rec['email'], 'وصلتنا إجاباتك: أسئلة كشف الهوية', $thanks, NOTIFY_EMAIL);

send_json(['ok' => true, 'id' => $rec['id']]);
