<?php
// Private page for Dr. Mervat: listen to new voice reviews, publish or delete them.
require dirname(__DIR__) . '/api/_lib.php';
header('X-Robots-Tag: noindex, nofollow');
header('X-Frame-Options: DENY');
header("Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; media-src 'self' blob:; form-action 'self'; frame-ancestors 'none'");
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
    elseif ($do === 'setup' && (!$hasPassword || ($_POST['reset'] ?? '') === '1')) {
        if (!rate_ok('login', 5, 900, false)) { $err = 'محاولات كثيرة. انتظري ربع ساعة.'; }
        elseif (!password_verify(implode('-', str_split(substr(preg_replace('/[^A-Z0-9]/', '', strtoupper((string)($_POST['code'] ?? ''))), 0, 12), 4)), $cfg['setup_code_hash'])) { rate_ok('login', 5, 900); $err = 'كود الإعداد غير صحيح.'; }
        elseif (trim((string)($_POST['pass'] ?? '')) === '') { $err = 'اكتبي كلمة السر.'; }
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
            if (($_GET['next'] ?? '') === 'replies') { header('Location: replies.php'); exit; }
        } else { rate_ok('login', 5, 900); $err = 'كلمة السر غير صحيحة.'; }
    } elseif ($do === 'logout') {
        $_SESSION = []; session_destroy(); header('Location: voices.php'); exit;
    } elseif ($do === 'upload' && ms_voice_admin()) {
        // Mervat adds a review she received elsewhere (e.g. WhatsApp) after editing it; it is published right away.
        $pid = (string)($_POST['pid'] ?? '');
        $name = clean_text((string)($_POST['name'] ?? ''), 40);
        $len = min((float)($_POST['len'] ?? 0), ADMIN_VOICE_MAX_SECONDS);
        $f = $_FILES['audio'] ?? null;
        if ($pid !== 'general' && !isset(products()[$pid])) { $err = 'اختاري التمرين أو البرنامج.'; }
        elseif ($name === '') { $err = 'اكتبي اسم صاحبة التجربة كما سيظهر في الموقع.'; }
        elseif (($_POST['consent'] ?? '') !== '1') { $err = 'لازم تأكيد موافقة صاحبة التجربة على النشر.'; }
        elseif (!$f || ($f['error'] ?? 1) !== UPLOAD_ERR_OK || !is_uploaded_file($f['tmp_name'])) { $err = ($f && in_array($f['error'] ?? 0, [UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE], true)) ? 'الملف أكبر من المسموح. صدّريه كصوت فقط (MP3 أو M4A).' : 'لم يصل الملف، أعيدي المحاولة.'; }
        elseif ($f['size'] > ADMIN_VOICE_MAX_BYTES) { $err = 'الملف أكبر من ٢٥ ميجا. صدّريه كصوت فقط (MP3 أو M4A).'; }
        elseif ((float)($_POST['len'] ?? 0) > ADMIN_VOICE_MAX_SECONDS) { $err = 'التسجيل أطول من ٥ دقائق. قصّريه ثم ارفعيه.'; }
        elseif (!($type = sniff_audio($f['tmp_name']))) { $err = 'نوع الملف غير مدعوم. المسموح: MP3 أو M4A أو WAV أو MP4.'; }
        else {
            $id = bin2hex(random_bytes(12));
            $file = $id . '.' . $type[0];
            if (!move_uploaded_file($f['tmp_name'], data_dir() . '/voices/' . $file)) { $err = 'تعذّر حفظ الملف.'; }
            else {
                @chmod(data_dir() . '/voices/' . $file, 0600);
                with_index(function ($list) use ($id, $pid, $name, $len, $file, $type) {
                    $now = gmdate('c');
                    $list[] = ['id' => $id, 'pid' => $pid, 'name' => $name, 'len' => round(max(0, $len), 1), 'file' => $file, 'mime' => $type[1],
                               'status' => 'approved', 'created_at' => $now, 'approved_at' => $now, 'consent' => true, 'source' => 'admin'];
                    return [$list, true];
                });
                header('Location: voices.php?done=upload'); exit;
            }
        }
    } elseif ($do === 'edit' && ms_voice_admin()) {
        $id = preg_replace('/[^a-f0-9]/', '', (string)($_POST['id'] ?? ''));
        $pid = (string)($_POST['pid'] ?? '');
        $name = clean_text((string)($_POST['name'] ?? ''), 40);
        if (($pid === 'general' || isset(products()[$pid])) && $name !== '') {
            with_index(function ($list) use ($id, $pid, $name) {
                foreach ($list as $i => $v) { if ($v['id'] === $id) { $list[$i]['pid'] = $pid; $list[$i]['name'] = $name; } }
                return [$list, true];
            });
            header('Location: voices.php?done=edit'); exit;
        }
        $err = 'اكتبي الاسم واختاري التمرين أو البرنامج.';
    } elseif (in_array($do, ['rapprove', 'rhide', 'rdelete'], true) && ms_voice_admin()) {
        // written reviews
        $id = preg_replace('/[^a-f0-9]/', '', (string)($_POST['id'] ?? ''));
        $path = data_dir() . '/reviews.json';
        $fh = fopen($path, 'c+'); flock($fh, LOCK_EX);
        $rl = json_decode((string)stream_get_contents($fh), true) ?: [];
        foreach ($rl as $i => $r) {
            if (($r['id'] ?? '') !== $id) continue;
            if ($do === 'rdelete') { unset($rl[$i]); }
            else { $rl[$i]['status'] = $do === 'rapprove' ? 'approved' : 'pending'; if ($do === 'rapprove') { $rl[$i]['approved_at'] = gmdate('c'); } }
        }
        ftruncate($fh, 0); rewind($fh); fwrite($fh, json_encode(array_values($rl), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        flock($fh, LOCK_UN); fclose($fh); @chmod($path, 0600);
        header('Location: voices.php?done=' . $do . '#written'); exit;
    } elseif (in_array($do, ['approve', 'hide', 'delete'], true) && ms_voice_admin()) {
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

$admin = ms_voice_admin();
$h = fn($s) => htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8');
$doneMsg = ['rapprove' => 'نُشر الرأي المكتوب في الموقع.', 'rhide' => 'أُخفي الرأي المكتوب من الموقع.', 'rdelete' => 'حُذف الرأي المكتوب نهائياً.', 'edit' => 'تم حفظ التعديل.', 'upload' => 'تم رفع التسجيل ونشره في الموقع.', 'approve' => 'نُشر التسجيل في الموقع.', 'hide' => 'أُخفي التسجيل من الموقع.', 'delete' => 'حُذف التسجيل نهائياً.'][$_GET['done'] ?? ''] ?? '';
$list = $admin ? read_index() : [];
usort($list, fn($a, $b) => strcmp($b['created_at'], $a['created_at']));
$pending = array_filter($list, fn($v) => $v['status'] === 'pending');
$approved = array_filter($list, fn($v) => $v['status'] === 'approved');
$fmtLen = fn($s) => floor($s / 60) . ':' . str_pad((string)round(fmod($s, 60)), 2, '0', STR_PAD_LEFT);
$fmtDate = fn($d) => date('Y/m/d H:i', strtotime($d) + 2 * 3600);

function card($v, $h, $fmtLen, $fmtDate, $actions) {
    $title = $v['pid'] === 'general' ? 'تجربة عامة' : (products()[$v['pid']] ?? $v['pid']);
    $btns = '';
    foreach ($actions as [$do, $label, $cls]) {
        $confirm = $do === 'delete' ? ' onsubmit="return confirm(\'حذف التسجيل نهائياً؟\')"' : '';
        $btns .= '<form method="post"' . $confirm . '><input type="hidden" name="csrf" value="' . $h($_SESSION['csrf']) . '"><input type="hidden" name="id" value="' . $h($v['id']) . '"><button class="' . $cls . '" name="do" value="' . $do . '">' . $label . '</button></form>';
    }
    return '<article class="v"><div class="vt"><b>' . $h($v['name']) . '</b><span>' . $h($title) . ' · ' . $fmtLen($v['len']) . ' · ' . $fmtDate($v['created_at']) . '</span></div>'
         . '<audio controls preload="none" src="/api/voice.php?action=audio&amp;id=' . $h($v['id']) . '"></audio><div class="va">' . $btns . '</div>'
         . '<details><summary>تعديل الاسم أو التمرين</summary><form method="post" class="ed"><input type="hidden" name="csrf" value="' . $h($_SESSION['csrf']) . '"><input type="hidden" name="id" value="' . $h($v['id']) . '">'
         . '<input type="text" name="name" maxlength="40" required value="' . $h($v['name']) . '"><select name="pid">' . pid_options($v['pid'], $h) . '</select><button class="gold" name="do" value="edit">حفظ التعديل</button></form></details></article>';
}
function pid_options($sel, $h) {
    $o = '<option value="general"' . ($sel === 'general' ? ' selected' : '') . '>تجربة عامة مع د. مرفت</option>';
    foreach (products() as $k => $t) { $o .= '<option value="' . $h($k) . '"' . ($sel === $k ? ' selected' : '') . '>' . $h($t) . '</option>'; }
    return $o;
}
?><!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>آراء العملاء · لوحة مرفت</title>
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
.empty{color:var(--muted)}summary{cursor:pointer;color:var(--blue);font-weight:700}.ed{display:grid;gap:8px;margin-top:10px}.pw{position:relative}.pw input{padding-inline-end:48px}.eye{position:absolute;inset-inline-end:6px;top:50%;transform:translateY(-50%);background:none;padding:6px 8px;font-size:1.1rem;line-height:1;color:var(--muted)}a{color:var(--blue)}select{width:100%;padding:11px 14px;border:1px solid var(--line);border-radius:12px;font:inherit;background:#fff}.ck{display:flex;gap:8px;align-items:center;font-weight:700}.up label{margin-top:0}.count{background:var(--gold);color:var(--deep);border-radius:999px;padding:0 10px;font-size:.85rem;margin-inline-start:6px}
</style></head><body>
<header><div class="w"><h1>آراء العملاء</h1><?php if (ms_voice_admin()): ?><a href="replies.php" style="color:#E2C68C;font-weight:700">ردود كشف الهوية ←</a><?php endif; ?><?php if ($admin): ?><form method="post"><input type="hidden" name="csrf" value="<?= $h($_SESSION['csrf']) ?>"><button class="out" name="do" value="logout">خروج</button></form><?php endif; ?></div></header>
<main><div class="w">
<?php if ($msg): ?><p class="ok"><?= $h($msg) ?></p><?php endif; ?>
<?php if ($doneMsg): ?><p class="ok"><?= $h($doneMsg) ?></p><?php endif; ?>
<?php if ($err): ?><p class="err"><?= $h($err) ?></p><?php endif; ?>

<?php $reset = $hasPassword && !$admin && isset($_GET['reset']); if (!$hasPassword || $reset): ?>
  <form class="box" method="post" autocomplete="off"><h2 style="margin-top:0"><?= $reset ? 'تعيين كلمة سر جديدة' : 'إعداد كلمة السر لأول مرة' ?></h2>
    <?php if ($reset): ?><p class="empty" style="margin:0">اكتبي كود الإعداد الذي أرسله لك Claude، ثم اختاري كلمة سر جديدة.</p><input type="hidden" name="reset" value="1"><?php endif; ?>
    <input type="hidden" name="csrf" value="<?= $h($_SESSION['csrf']) ?>"><input type="hidden" name="do" value="setup">
    <label for="code">كود الإعداد</label><input id="code" name="code" type="text" required dir="ltr">
    <label for="pass">كلمة سر جديدة</label><input id="pass" name="pass" type="password" required autocomplete="new-password">
    <p><button class="gold">حفظ والدخول</button></p></form>
<?php elseif (!$admin): ?>
  <form class="box" method="post"><h2 style="margin-top:0">دخول</h2>
    <input type="hidden" name="csrf" value="<?= $h($_SESSION['csrf']) ?>"><input type="hidden" name="do" value="login">
    <label for="pass">كلمة السر</label><input id="pass" name="pass" type="password" required autocomplete="current-password">
    <p><button class="gold">دخول</button></p><p style="margin:0"><a href="voices.php?reset=1">نسيت كلمة السر؟</a></p></form>
<?php else: ?>
  <form class="v up" method="post" enctype="multipart/form-data"><h2 style="margin:0">رفع تسجيل وصلك (واتساب مثلاً)</h2>
    <input type="hidden" name="csrf" value="<?= $h($_SESSION['csrf']) ?>"><input type="hidden" name="do" value="upload"><input type="hidden" name="len" id="len" value="0">
    <div><label for="audio">ملف الصوت (MP3 أو M4A، حتى ٥ دقائق)</label><input id="audio" name="audio" type="file" accept="audio/*,.mp3,.m4a,.wav,.mp4" required><small id="dur" class="empty"></small></div>
    <div><label for="vname">الاسم كما يظهر في الموقع</label><input id="vname" name="name" type="text" maxlength="40" required placeholder="مثلاً: هبة، أو أم يوسف"></div>
    <div><label for="pid">عن أي تمرين أو برنامج؟</label><select id="pid" name="pid" required><?= pid_options('general', $h) ?></select></div>
    <label class="ck"><input type="checkbox" name="consent" value="1" required> صاحبة التجربة وافقت على نشر صوتها في الموقع</label>
    <p style="margin:0"><button class="gold">ارفعي وانشري</button></p></form>
  <h2>في انتظار موافقتك<span class="count"><?= count($pending) ?></span></h2>
  <?php if (!$pending): ?><p class="empty">لا توجد تسجيلات جديدة.</p><?php endif; ?>
  <?php foreach ($pending as $v) echo card($v, $h, $fmtLen, $fmtDate, [['approve', 'انشري في الموقع', 'gold'], ['delete', 'احذفي', 'red']]); ?>
  <h2>منشورة في الموقع<span class="count"><?= count($approved) ?></span></h2>
  <?php if (!$approved): ?><p class="empty">لم يُنشر أي تسجيل بعد.</p><?php endif; ?>
  <?php foreach ($approved as $v) echo card($v, $h, $fmtLen, $fmtDate, [['hide', 'إخفاء من الموقع', 'ghost'], ['delete', 'احذفي نهائياً', 'red']]); ?>
  <?php
    $rpath = data_dir() . '/reviews.json';
    $rl = is_file($rpath) ? (json_decode((string)file_get_contents($rpath), true) ?: []) : [];
    usort($rl, fn($a, $b) => strcmp($b['created_at'], $a['created_at']));
    $rcard = function ($r, $actions) use ($h, $fmtDate) {
        $about = $r['pid'] === 'general' ? 'تجربة عامة' : (products()[$r['pid']] ?? $r['pid']);
        $b = '';
        foreach ($actions as [$do, $label, $cls]) {
            $c = $do === 'rdelete' ? ' onsubmit="return confirm(\'حذف الرأي نهائياً؟\')"' : '';
            $b .= '<form method="post"' . $c . '><input type="hidden" name="csrf" value="' . $h($_SESSION['csrf']) . '"><input type="hidden" name="id" value="' . $h($r['id']) . '"><button class="' . $cls . '" name="do" value="' . $do . '">' . $label . '</button></form>';
        }
        return '<article class="v"><div class="vt"><b>' . $h($r['name']) . '</b><span>' . $h($about) . ' · <span style="color:#C5A059">' . str_repeat('★', (int)$r['stars']) . '</span> · ' . $fmtDate($r['created_at']) . ($r['email'] ? ' · ' . $h($r['email']) : '') . '</span></div>'
             . '<p style="margin:0;white-space:pre-line">' . $h($r['text']) . '</p><div class="va">' . $b . '</div></article>';
    };
    $rp = array_filter($rl, fn($r) => $r['status'] === 'pending'); $ra = array_filter($rl, fn($r) => $r['status'] === 'approved');
  ?>
  <h2 id="written" style="margin-top:44px;border-top:1px solid var(--line);padding-top:24px">آراء مكتوبة في انتظار موافقتك<span class="count"><?= count($rp) ?></span></h2>
  <?php if (!$rp): ?><p class="empty">لا توجد آراء مكتوبة جديدة.</p><?php endif; ?>
  <?php foreach ($rp as $r) echo $rcard($r, [['rapprove', 'انشري في الموقع', 'gold'], ['rdelete', 'احذفي', 'red']]); ?>
  <h2>آراء مكتوبة منشورة<span class="count"><?= count($ra) ?></span></h2>
  <?php if (!$ra): ?><p class="empty">لم يُنشر أي رأي مكتوب بعد.</p><?php endif; ?>
  <?php foreach ($ra as $r) echo $rcard($r, [['rhide', 'إخفاء من الموقع', 'ghost'], ['rdelete', 'احذفي نهائياً', 'red']]); ?>

<?php endif; ?>
</div></main><script src="voices.js"></script></body></html>
