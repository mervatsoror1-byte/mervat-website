<?php
// Shared helpers for voice reviews. Data lives OUTSIDE public_html so site deploys never touch it.
if (basename($_SERVER['SCRIPT_FILENAME'] ?? '') === '_lib.php') { http_response_code(404); exit; }

const VOICE_MAX_BYTES = 4 * 1024 * 1024;   // 4 MB (about 2 minutes)
const VOICE_MAX_SECONDS = 130;
const SUBMITS_PER_HOUR = 5;                 // per visitor
const MAX_PENDING = 300;
const NOTIFY_EMAIL = 'info@mervatsror.com';

function data_dir(): string {
    $base = getenv('MS_DATA_DIR') ?: dirname(__DIR__, 2) . '/ms_data';
    foreach (['', '/voices', '/limits'] as $sub) {
        $d = $base . $sub;
        if (!is_dir($d) && !@mkdir($d, 0700, true)) { fail(500, 'storage'); }
    }
    return $base;
}

function fail(int $code, string $msg): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => $msg], JSON_UNESCAPED_UNICODE);
    exit;
}

function send_json(array $data): void {
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

// Read-modify-write the voices index under an exclusive lock.
function with_index(callable $fn) {
    $path = data_dir() . '/voices.json';
    $fh = fopen($path, 'c+');
    if (!$fh) { fail(500, 'storage'); }
    flock($fh, LOCK_EX);
    $raw = stream_get_contents($fh);
    $list = $raw ? (json_decode($raw, true) ?: []) : [];
    $result = $fn($list);
    if ($result !== null) {
        [$list, $out] = $result;
        ftruncate($fh, 0); rewind($fh);
        fwrite($fh, json_encode(array_values($list), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }
    flock($fh, LOCK_UN); fclose($fh);
    return $result === null ? $list : $out;
}

function read_index(): array {
    return with_index(fn($list) => null);
}

function visitor_key(): string {
    $ip = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '0';
    $ip = trim(explode(',', $ip)[0]);
    return hash('sha256', 'ms-voice|' . $ip);   // never store raw IPs
}

// Simple sliding-window limiter; returns false when over the limit.
function rate_ok(string $bucket, int $max, int $window, bool $record = true): bool {
    $f = data_dir() . '/limits/' . $bucket . '-' . substr(visitor_key(), 0, 32) . '.json';
    $now = time();
    $hits = is_file($f) ? (json_decode((string)file_get_contents($f), true) ?: []) : [];
    $hits = array_values(array_filter($hits, fn($t) => $t > $now - $window));
    if (count($hits) >= $max) { return false; }
    if (!$record) { return true; }
    $hits[] = $now;
    file_put_contents($f, json_encode($hits), LOCK_EX);
    return true;
}

// Identify audio by its first bytes, not by what the browser claims.
function sniff_audio(string $path): ?array {
    $h = (string)file_get_contents($path, false, null, 0, 16);
    if (strncmp($h, "\x1A\x45\xDF\xA3", 4) === 0) return ['webm', 'audio/webm'];
    if (strncmp($h, 'OggS', 4) === 0) return ['ogg', 'audio/ogg'];
    if (substr($h, 4, 4) === 'ftyp') return ['m4a', 'audio/mp4'];
    if (strncmp($h, 'ID3', 3) === 0 || (ord($h[0] ?? "\0") === 0xFF && (ord($h[1] ?? "\0") & 0xE0) === 0xE0)) return ['mp3', 'audio/mpeg'];
    if (strncmp($h, 'RIFF', 4) === 0 && substr($h, 8, 4) === 'WAVE') return ['wav', 'audio/wav'];
    return null;
}

function products(): array {
    static $p = null;
    if ($p === null) { $p = require __DIR__ . '/_products.php'; }
    return $p;
}

function clean_text(string $s, int $max): string {
    $s = preg_replace('/[\x00-\x1F\x7F<>]/u', '', $s) ?? '';
    $s = trim(preg_replace('/\s+/u', ' ', $s) ?? '');
    return mb_substr($s, 0, $max);
}

function public_voice(array $v): array {
    return ['id' => $v['id'], 'pid' => $v['pid'], 'name' => $v['name'], 'len' => $v['len'], 'date' => $v['approved_at'] ?? $v['created_at']];
}

function stream_audio(array $v): void {
    $file = data_dir() . '/voices/' . basename($v['file']);
    if (!is_file($file)) { fail(404, 'missing'); }
    $size = filesize($file); $start = 0; $end = $size - 1;
    header('Content-Type: ' . $v['mime']);
    header('Accept-Ranges: bytes');
    header('Cache-Control: private, max-age=3600');
    header('X-Content-Type-Options: nosniff');
    if (isset($_SERVER['HTTP_RANGE']) && preg_match('/bytes=(\d*)-(\d*)/', $_SERVER['HTTP_RANGE'], $m)) {
        if ($m[1] !== '') { $start = (int)$m[1]; if ($m[2] !== '') $end = min((int)$m[2], $end); }
        elseif ($m[2] !== '') { $start = max(0, $size - (int)$m[2]); }
        if ($start > $end) { header("Content-Range: bytes */$size"); http_response_code(416); exit; }
        http_response_code(206);
        header("Content-Range: bytes $start-$end/$size");
    }
    header('Content-Length: ' . ($end - $start + 1));
    $fh = fopen($file, 'rb'); fseek($fh, $start);
    $left = $end - $start + 1;
    while ($left > 0 && !feof($fh)) { $chunk = fread($fh, min(65536, $left)); echo $chunk; $left -= strlen($chunk); }
    fclose($fh);
    exit;
}

function start_admin_session(): void {
    session_name('ms_admin');
    session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => !empty($_SERVER['HTTPS']) || ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https', 'httponly' => true, 'samesite' => 'Strict']);
    session_start();
}

function is_admin(): bool {
    return !empty($_SESSION['ms_admin']) && ($_SESSION['ms_admin_until'] ?? 0) > time();
}
