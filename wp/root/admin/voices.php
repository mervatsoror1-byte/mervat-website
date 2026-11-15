<?php
// Private page for Dr. Mervat: listen to new voice reviews, publish or delete them.
require dirname(__DIR__) . '/api/_lib.php';
header('X-Robots-Tag: noindex, nofollow');
header('X-Frame-Options: DENY');
header("Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; media-src 'self'; form-action 'self'; frame-ancestors 'none'");
start_admin_session();

$cfg = require dirname(__DIR__) . '/api/_config.php';
$authFile = data_dir() . '/admin.json';
$auth = is_file($authFile) ? (json_decode((string)file_get_contents($authFile), true) ?: []) : [];
$hasPassword = !empty($auth['pass_hash']);
$msg = ''; $err = '';

if (empty($_SESSION['csrf'])) { $_SESSION['csrf'] = bin2hex(random_bytes(16)); }
$csrfOk = fn() => hash_equals($_SESSION['csrf'], (string)($_POST['csrf'] ?? ''));

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $do = $_POST['do'] ?? '';
    if (!$csrfOk()) { $err = 'انتهت صلاحية الصفحة، أعيدي المحاولة.'; }
    elseif ($do === 'setup' && !$hasPassword) {
        if (!rate_ok('login', 5, 900, false)) { $err = 'محاولات كثيرة. انتظري ربع ساعة.'; }
        elseif (!password_verify(implode('-', str_split(substr(preg_replace('/[^A-Z0-9]/', '', strtoupper((string)($_POST['code'] ?? ''))), 0, 12), 4)), $cfg['setup_code_hash'])) { rate_ok('login', 5, 900); $err = 'كود الإعداد غير صحيح.'; }
        elseif (mb_strlen((string)($_POST['pass'] ?? '')) < 10) { $err = 'كلمة السر يجب أن تكون ١٠ أحرف على الأقل.'; }
        elseif (($_POST['pass'] ?? '') !== ($_POST['pass2'] ?? '')) { $err = 'كلمتا السر غير متطابقتين.'; }
        else {
            file_put_contents($authFile, json_encode(['pass_hash' => password_hash($_POST['pass'], PASSWORD_DEFAULT), 'set_at' => gmdate('c')]), LOCK_EX);
            @chmod($authFile, 0600);
            session_regenerate_id(true);
            $_SESSION['ms_admin'] = 1; $_SESSION['ms_admin_until'] = time() + 8 * 3600;
            $hasPassword = true; $msg = 'تم حفظ كلمة السر. احتفظي بها في مكان آمن.';
        }
    } elseif ($do === 'login' && $hasPassword) {
        if (!rate_ok('login', 5, 900, false)) { $err = 'محاولات كثيرة. انتظري ربع ساعة.'; }
        elseif (password_verify((string)($_POST['pass'] ?? ''), $auth['pass_hash'])) {
            session_regenerate_id(true);
            $_SESSION['ms_admin'] = 1; $_SESSION['ms_admin_until'] = time() + 8 * 3600;
        } else { rate_ok('login', 5, 900); $err = 'كلمة السر غير صحيحة.'; }
    } elseif ($do === 'logout') {
        $_SESSION = []; session_destroy(); header('Location: voices.php'); exit;
    } elseif (in_array($do, ['approve', 'hide', 'delete'], true) && is_admin()) {
        $id = preg_replace('/[^a-f0-9]/', '', (string)($_POST['id'] ?? ''));
        $gone = null;
        with_index(function ($list) use ($id, $do, &$gone) {
            foreach ($list as $i => $v) {
                if ($v['id'] !== $id) continue;
                if ($do === 'delete') { $gone = $v['file']; unset($list[$i]); }
                else { $list[$i]['status'] = $do === 'approve' ? 'approved' : 'pending'; if ($do === 'approve') $list[$i]['approved_at'] = gmdate('c'); }
            }
            return [$list, true];
        });
        if ($gone) { @unlink(data_dir() . '/voices/' . basename($gone)); }
        header('Location: voices.php?done=' . $do); exit;
    }
}

$admin = is_admin();
$h = fn($s) => htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8');
$doneMsg = ['approve' => 'نُشر التسجيل في الموقع.', 'hide' => 'أُخفي التسجيل من الموقع.', 'delete' => 'حُذف التسجيل نهائياً.'][$_GET['done'] ?? ''] ?? '';
$list = $admin ? read_index() : [];
usort($list, fn($a, $b) => strcmp($b['created_at'], $a['created_at']));
$pending = array_filter($list, fn($v) => $v['status'] === 'pending');
$approved = array_filter($list, fn($v) => $v['status'] === 'approved');
$fmtLen = fn($s) => floor($s / 60) . ':' . str_pad((string)round(fmod($s, 60)), 2, '0', STR_PAD_LEFT);
$fmtDate = fn($d) => date('Y/m/d H:i', strtotime($d) + 2 * 3600);

function card($v, $h, $fmtLen, $fmtDate, $actions) {
    $title = products()[$v['pid']] ?? $v['pid'];
    $btns = '';
    foreach ($actions as [$do, $label, $cls]) {
        $confirm = $do === 'delete' ? ' onsubmit="return confirm(\'حذف التسجيل نهائياً؟\')"' : '';
        $btns .= '<form method="post"' . $confirm . '><input type="hidden" name="csrf" value="' . $h($_SESSION['csrf']) . '"><input type="hidden" name="id" value="' . $h($v['id']) . '"><button class="' . $cls . '" name="do" value="' . $do . '">' . $label . '</button></form>';
    }
    return '<article class="v"><div class="vt"><b>' . $h($v['name']) . '</b><span>' . $h($title) . ' · ' . $fmtLen($v['len']) . ' · ' . $fmtDate($v['created_at']) . '</span></div>'
         . '<audio controls preload="none" src="/api/voice.php?action=audio&amp;id=' . $h($v['id']) . '"></audio><div class="va">' . $btns . '</div></article>';
}
?><!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>الآراء الصوتية · لوحة مرفت</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{--blue:#1F3F7C;--deep:#1A3670;--gold:#C5A059;--cream:#FBF8EE;--line:#E8DFC6;--muted:#5A6582}
*{box-sizing:border-box}body{margin:0;font-family:"Noto Naskh Arabic",serif;background:var(--cream);color:var(--deep);line-height:1.7}
header{background:radial-gradient(80% 120% at 70% 0%,#3A62A8,#1F3F7C 60%,#1A3670);color:#F5F5DC;padding:22px 16px}
header .w{display:flex;justify-content:space-between;align-items:center;gap:12px}header h1{margin:0;font-size:1.3rem;color:#E2C68C}
.w{max-width:860px;margin:0 auto;padding:0 16px}main .w{padding:22px 16px 60px}
h2{font-size:1.15rem;margin:28px 0 12px}.box{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px;max-width:440px;margin:30px auto}
label{display:block;font-weight:700;margin:12px 0 4px}input[type=password],input[type=text]{width:100%;padding:11px 14px;border:1px solid var(--line);border-radius:12px;font:inherit}
button{font:inherit;font-weight:700;border:0;border-radius:999px;padding:9px 18px;cursor:pointer}
.gold{background:linear-gradient(135deg,#E2C68C,#C5A059);color:var(--deep)}.ghost{background:#fff;border:1px solid var(--line);color:var(--deep)}.red{background:#fff;border:1px solid #e3b8b8;color:#9b2c2c}
.out{background:transparent;border:1px solid rgba(245,245,220,.5);color:#F5F5DC}
.v{background:#fff;border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin-bottom:12px;display:grid;gap:10px}
.vt{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline}.vt span{color:var(--muted);font-size:.9rem}
audio{width:100%}.va{display:flex;gap:8px;flex-wrap:wrap}.va form{margin:0}
.ok{background:#eef7ee;border:1px solid #b9dcb9;padding:10px 14px;border-radius:12px}.err{background:#fbeeee;border:1px solid #e3b8b8;padding:10px 14px;border-radius:12px}
.empty{color:var(--muted)}.count{background:var(--gold);color:var(--deep);border-radius:999px;padding:0 10px;font-size:.85rem;margin-inline-start:6px}
</style></head><body>
<header><div class="w"><h1>الآراء الصوتية</h1><?php if ($admin): ?><form method="post"><input type="hidden" name="csrf" value="<?= $h($_SESSION['csrf']) ?>"><button class="out" name="do" value="logout">خروج</button></form><?php endif; ?></div></header>
<main><div class="w">
<?php if ($msg): ?><p class="ok"><?= $h($msg) ?></p><?php endif; ?>
<?php if ($doneMsg): ?><p class="ok"><?= $h($doneMsg) ?></p><?php endif; ?>
<?php if ($err): ?><p class="err"><?= $h($err) ?></p><?php endif; ?>

<?php if (!$hasPassword): ?>
  <form class="box" method="post" autocomplete="off"><h2 style="margin-top:0">إعداد كلمة السر لأول مرة</h2>
    <input type="hidden" name="csrf" value="<?= $h($_SESSION['csrf']) ?>"><input type="hidden" name="do" value="setup">
    <label for="code">كود الإعداد</label><input id="code" name="code" type="text" required dir="ltr">
    <label for="pass">كلمة سر جديدة (١٠ أحرف على الأقل)</label><input id="pass" name="pass" type="password" required minlength="10" autocomplete="new-password">
    <label for="pass2">أعيدي كتابة كلمة السر</label><input id="pass2" name="pass2" type="password" required minlength="10" autocomplete="new-password">
    <p><button class="gold">حفظ والدخول</button></p></form>
<?php elseif (!$admin): ?>
  <form class="box" method="post"><h2 style="margin-top:0">دخول</h2>
    <input type="hidden" name="csrf" value="<?= $h($_SESSION['csrf']) ?>"><input type="hidden" name="do" value="login">
    <label for="pass">كلمة السر</label><input id="pass" name="pass" type="password" required autocomplete="current-password">
    <p><button class="gold">دخول</button></p></form>
<?php else: ?>
  <h2>في انتظار موافقتك<span class="count"><?= count($pending) ?></span></h2>
  <?php if (!$pending): ?><p class="empty">لا توجد تسجيلات جديدة.</p><?php endif; ?>
  <?php foreach ($pending as $v) echo card($v, $h, $fmtLen, $fmtDate, [['approve', 'انشري في الموقع', 'gold'], ['delete', 'احذفي', 'red']]); ?>
  <h2>منشورة في الموقع<span class="count"><?= count($approved) ?></span></h2>
  <?php if (!$approved): ?><p class="empty">لم يُنشر أي تسجيل بعد.</p><?php endif; ?>
  <?php foreach ($approved as $v) echo card($v, $h, $fmtLen, $fmtDate, [['hide', 'إخفاء من الموقع', 'ghost'], ['delete', 'احذفي نهائياً', 'red']]); ?>
<?php endif; ?>
</div></main></body></html>
