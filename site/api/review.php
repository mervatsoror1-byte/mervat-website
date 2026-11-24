<?php
// Written reviews.
//   GET  ?action=list    -> approved reviews (public)
//   POST ?action=submit  -> new review (JSON), saved as "pending" until Dr. Mervat approves it
require __DIR__ . '/_lib.php';

const REVIEWS_FILE = 'reviews.json';
function reviews_read(): array {
    $p = data_dir() . '/' . REVIEWS_FILE;
    return is_file($p) ? (json_decode((string)file_get_contents($p), true) ?: []) : [];
}

$action = $_GET['action'] ?? '';

if ($action === 'list' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $out = [];
    foreach (reviews_read() as $r) {
        if (($r['status'] ?? '') !== 'approved') continue;
        $out[] = ['id' => $r['id'], 'pid' => $r['pid'], 'name' => $r['name'], 'stars' => $r['stars'], 'text' => $r['text'], 'date' => $r['approved_at'] ?? $r['created_at']];
    }
    usort($out, fn($a, $b) => strcmp($b['date'], $a['date']));
    header('Cache-Control: no-store');
    send_json(['ok' => true, 'reviews' => $out]);
}

if ($action === 'submit' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $origin = $_SERVER['HTTP_ORIGIN'] ?? ''; $host = $_SERVER['HTTP_HOST'] ?? '';
    if ($origin !== '' && strtolower((string)parse_url($origin, PHP_URL_HOST)) !== strtolower(explode(':', $host)[0])) { fail(403, 'origin'); }
    $in = json_decode((string)file_get_contents('php://input'), true);
    if (!is_array($in)) { fail(400, 'body'); }
    if (!empty($in['website'])) { send_json(['ok' => true]); }
    if (!rate_ok('review', 5, 3600)) { fail(429, 'limit'); }
    $pid = (string)($in['pid'] ?? 'general');
    if ($pid !== 'general' && !isset(products()[$pid])) { fail(400, 'product'); }
    if (empty($in['consent'])) { fail(400, 'consent'); }
    $text = preg_replace('/[\x00-\x09\x0B-\x1F\x7F<>]/u', '', (string)($in['text'] ?? '')) ?? '';
    $text = trim(preg_replace("/\n{3,}/", "\n\n", str_replace("\r", '', $text)) ?? '');
    if (mb_strlen($text) < 10) { fail(400, 'text'); }
    $text = mb_substr($text, 0, 2000);
    $name = clean_text((string)($in['name'] ?? ''), 40); if ($name === '') { $name = 'عميلة'; }
    $stars = max(1, min(5, (int)($in['stars'] ?? 5)));
    $email = filter_var(trim((string)($in['email'] ?? '')), FILTER_VALIDATE_EMAIL) ?: '';
    $rec = ['id' => bin2hex(random_bytes(8)), 'pid' => $pid, 'name' => $name, 'stars' => $stars, 'text' => $text, 'email' => $email,
            'status' => 'pending', 'created_at' => gmdate('c'), 'consent' => true];
    $path = data_dir() . '/' . REVIEWS_FILE;
    $fh = fopen($path, 'c+'); flock($fh, LOCK_EX);
    $list = json_decode((string)stream_get_contents($fh), true) ?: [];
    if (count(array_filter($list, fn($r) => ($r['status'] ?? '') === 'pending')) >= 300) { flock($fh, LOCK_UN); fclose($fh); fail(503, 'full'); }
    $list[] = $rec;
    ftruncate($fh, 0); rewind($fh); fwrite($fh, json_encode($list, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    flock($fh, LOCK_UN); fclose($fh); @chmod($path, 0600);

    $about = $pid === 'general' ? 'تجربة عامة مع د. مرفت' : products()[$pid];
    if (is_file(MS_WP_LOAD)) { if (!defined('WP_USE_THEMES')) { define('WP_USE_THEMES', false); } require_once MS_WP_LOAD; }
    ms_mail(NOTIFY_EMAIL, 'رأي مكتوب جديد ينتظر موافقتك', "وصل رأي مكتوب جديد من «{$name}» عن «{$about}» (" . str_repeat('★', $stars) . ").\n\n{$text}\n\nللموافقة أو الحذف: https://{$host}/admin/voices.php\n", $email, 'موقع د. مرفت سرور');
    send_json(['ok' => true]);
}

fail(404, 'unknown');
