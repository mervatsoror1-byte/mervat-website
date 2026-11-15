<?php
// Voice reviews API.
//   GET  ?action=list              -> approved voices (public)
//   GET  ?action=audio&id=ID       -> audio of an approved voice (admins can also play pending ones)
//   POST ?action=submit (multipart)-> new recording, saved as "pending" until approved
require __DIR__ . '/_lib.php';

$action = $_GET['action'] ?? '';

if ($action === 'list' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $out = [];
    foreach (read_index() as $v) { if (($v['status'] ?? '') === 'approved') $out[] = public_voice($v); }
    usort($out, fn($a, $b) => strcmp($b['date'], $a['date']));
    send_json(['ok' => true, 'voices' => $out]);
}

if ($action === 'audio' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $id = preg_replace('/[^a-f0-9]/', '', (string)($_GET['id'] ?? ''));
    if (strlen($id) !== 24) { fail(404, 'missing'); }
    $admin = false;
    if (isset($_COOKIE['ms_admin'])) { start_admin_session(); $admin = is_admin(); session_write_close(); }
    foreach (read_index() as $v) {
        if ($v['id'] === $id && (($v['status'] ?? '') === 'approved' || $admin)) { stream_audio($v); }
    }
    fail(404, 'missing');
}

if ($action === 'submit' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    // Honeypot: real people never fill this hidden field.
    if (!empty($_POST['website'])) { send_json(['ok' => true]); }
    // Only accept posts coming from our own pages.
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    $host = $_SERVER['HTTP_HOST'] ?? '';
    if ($origin !== '' && strtolower((string)parse_url($origin, PHP_URL_HOST)) !== strtolower(explode(':', $host)[0])) { fail(403, 'origin'); }

    $pid = (string)($_POST['pid'] ?? '');
    if (!isset(products()[$pid])) { fail(400, 'product'); }
    if (($_POST['consent'] ?? '') !== '1') { fail(400, 'consent'); }
    $name = clean_text((string)($_POST['name'] ?? ''), 40);
    if ($name === '') { $name = 'عميلة'; }
    $len = (float)($_POST['len'] ?? 0);
    if ($len <= 0 || $len > VOICE_MAX_SECONDS) { fail(400, 'length'); }

    $f = $_FILES['audio'] ?? null;
    if (!$f || ($f['error'] ?? 1) !== UPLOAD_ERR_OK || !is_uploaded_file($f['tmp_name'])) { fail(400, 'file'); }
    if ($f['size'] <= 1000 || $f['size'] > VOICE_MAX_BYTES) { fail(400, 'size'); }
    $type = sniff_audio($f['tmp_name']);
    if (!$type) { fail(400, 'type'); }

    if (!rate_ok('submit', SUBMITS_PER_HOUR, 3600)) { fail(429, 'limit'); }

    $id = bin2hex(random_bytes(12));
    $file = $id . '.' . $type[0];
    if (!move_uploaded_file($f['tmp_name'], data_dir() . '/voices/' . $file)) { fail(500, 'storage'); }
    @chmod(data_dir() . '/voices/' . $file, 0600);

    $saved = with_index(function ($list) use ($id, $pid, $name, $len, $file, $type) {
        $pending = count(array_filter($list, fn($v) => ($v['status'] ?? '') === 'pending'));
        if ($pending >= MAX_PENDING) { return [$list, false]; }
        $list[] = ['id' => $id, 'pid' => $pid, 'name' => $name, 'len' => round($len, 1), 'file' => $file, 'mime' => $type[1],
                   'status' => 'pending', 'created_at' => gmdate('c'), 'consent' => true];
        return [$list, true];
    });
    if (!$saved) { @unlink(data_dir() . '/voices/' . $file); fail(503, 'full'); }

    $title = products()[$pid];
    @mail(NOTIFY_EMAIL, '=?UTF-8?B?' . base64_encode('تسجيل صوتي جديد ينتظر موافقتك') . '?=',
          "وصل تسجيل صوتي جديد من «{$name}» عن «{$title}».\nللاستماع والموافقة أو الحذف: https://{$host}/admin/voices.php\n",
          "Content-Type: text/plain; charset=UTF-8\r\nFrom: " . NOTIFY_EMAIL);
    send_json(['ok' => true]);
}

fail(404, 'unknown');
