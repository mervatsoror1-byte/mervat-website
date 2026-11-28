<?php
// Private page for Dr. Mervat: read «أسئلة كشف الهوية» answers and send each one a branded analysis email.
// Login is shared with voices.php (same admin session).
require dirname(__DIR__) . '/api/_lib.php';
require dirname(__DIR__) . '/api/_reply_mail.php';
if (is_file(MS_WP_LOAD)) { if (!defined('WP_USE_THEMES')) { define('WP_USE_THEMES', false); } require_once MS_WP_LOAD; }
header('X-Robots-Tag: noindex, nofollow');
header('X-Frame-Options: DENY');
header("Content-Security-Policy: default-src 'self'; img-src 'self' https://mervatsror.com data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; form-action 'self'; frame-ancestors 'none'");
start_admin_session();
if (empty($_SESSION['csrf'])) { $_SESSION['csrf'] = bin2hex(random_bytes(16)); }
if (!ms_voice_admin()) { header('Location: voices.php?next=replies'); exit; }

$h = fn($s) => htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8');
$fmtDate = fn($d) => $d ? date('Y/m/d H:i', strtotime($d) + 2 * 3600) : '';
$gifts = is_file(data_dir() . '/gift.json') ? (json_decode((string)file_get_contents(data_dir() . '/gift.json'), true) ?: []) : [];
usort($gifts, fn($a, $b) => strcmp($b['created_at'], $a['created_at']));
$byId = []; foreach ($gifts as $g) { $byId[$g['id']] = $g; }
$rpath = data_dir() . '/replies.json';

/** read-modify-write replies.json under a lock */
$withReplies = function (?callable $fn = null) use ($rpath) {
    $fh = fopen($rpath, 'c+'); flock($fh, LOCK_EX);
    $all = json_decode((string)stream_get_contents($fh), true) ?: [];
    if ($fn) { $all = $fn($all); ftruncate($fh, 0); rewind($fh); fwrite($fh, json_encode($all, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)); }
    flock($fh, LOCK_UN); fclose($fh); @chmod($rpath, 0600);
    return $all;
};
$replies = $withReplies();

$DEF_TITLE = 'تحليلك النفسي والشعوري';
$DEF_SUBJECT = 'تحليلك الشخصي من د. مرفت سرور';
$id = preg_replace('/[^A-Z0-9-]/', '', strtoupper((string)($_GET['id'] ?? $_POST['id'] ?? '')));
$gift = $byId[$id] ?? null;
$msg = ''; $err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $gift) {
    if (!hash_equals($_SESSION['csrf'], (string)($_POST['csrf'] ?? ''))) { $err = 'انتهت صلاحية الصفحة، أعيدي المحاولة.'; }
    else {
        $do = (string)($_POST['do'] ?? 'save');
        $draft = [
            'name' => clean_text((string)($_POST['name'] ?? ''), 60),
            'email' => strtolower(trim((string)($_POST['email'] ?? ''))),
            'subject' => clean_text((string)($_POST['subject'] ?? ''), 120) ?: $DEF_SUBJECT,
            'title' => clean_text((string)($_POST['title'] ?? ''), 90) ?: $DEF_TITLE,
            'body' => mb_substr(str_replace("\r", '', (string)($_POST['body'] ?? '')), 0, 30000),
            'updated_at' => gmdate('c'),
        ];
        $withReplies(function ($all) use ($id, $draft) { $all[$id] = array_merge($all[$id] ?? [], $draft); return $all; });
        $html = ms_reply_html(['name' => $draft['name'], 'title' => $draft['title'], 'body' => $draft['body']]);
        if ($do === 'test') {
            $raw = strtolower(preg_replace('/\s+/u', '', (string)($_POST['test_to'] ?? '')) ?? '');
            $tto = $raw === '' ? NOTIFY_EMAIL : (filter_var($raw, FILTER_VALIDATE_EMAIL) ?: '');
            if ($tto === '') { $err = 'الإيميل المكتوب في خانة التجربة غير صحيح: «' . $raw . '». صحّحيه أو امسحيه.'; goto done_post; }
            $_SESSION['test_to'] = $tto === NOTIFY_EMAIL ? '' : $tto;
            $ok = ms_send_reply_html($tto, '[تجربة ' . date('H:i', time() + 2 * 3600) . '] ' . $draft['subject'], $html, $tto !== NOTIFY_EMAIL);
            if ($ok) { header('Location: replies.php?id=' . $id . '&done=test'); exit; }
            $err = 'تعذّر إرسال النسخة التجريبية.';
        } elseif ($do === 'send') {
            if (!filter_var($draft['email'], FILTER_VALIDATE_EMAIL)) { $err = 'البريد الإلكتروني غير صحيح.'; }
            elseif (trim($draft['body']) === '') { $err = 'اكتبي نص الرد أولاً.'; }
            elseif (($_POST['sure'] ?? '') !== '1') { $err = 'ضعي علامة «راجعتُ الرد وأريد إرساله» أولاً.'; }
            else {
                $ok = ms_send_reply_html($draft['email'], $draft['subject'], $html, true);
                if ($ok) {
                    ms_send_reply_html(NOTIFY_EMAIL, 'نسختك: ' . $draft['subject'] . ' — ' . $draft['name'], $html, false);
                    $withReplies(function ($all) use ($id, $draft) { $all[$id]['sent'][] = ['at' => gmdate('c'), 'to' => $draft['email']]; return $all; });
                    header('Location: replies.php?id=' . $id . '&done=sent'); exit;
                }
                $err = 'تعذّر الإرسال. حاولي مرة أخرى بعد دقيقة.';
            }
        } else { header('Location: replies.php?id=' . $id . '&done=' . ($do === 'preview' ? 'preview#preview' : 'saved')); exit; }
        done_post:
        $replies = $withReplies();
    }
}
// after every save we redirect back here (so refreshing the page never re-sends the form)
$msg = $msg ?: (['sent' => 'تم إرسال الرد ✓ ووصلتك نسخة منه على info@mervatsror.com.', 'saved' => 'تم حفظ المسودة ✓',
                 'preview' => 'تم حفظ المسودة ✓ والمعاينة تحت محدّثة.', 'test' => 'أُرسلت نسخة تجريبية إلى ' . (($_SESSION['test_to'] ?? '') ?: 'info@mervatsror.com') . ' ✓ (تصل خلال دقيقة). افتحي الإيميل الجديد، عنوانه فيه الساعة.'][$_GET['done'] ?? ''] ?? '');

$questions = (function () { $f = dirname(__DIR__) . '/api/_gift_questions.php'; return is_file($f) ? require $f : []; })();
$status = function ($gid) use ($replies) {
    $r = $replies[$gid] ?? null;
    if (!empty($r['sent'])) { return ['sent', 'أُرسل الرد']; }
    if (!empty($r['body'])) { return ['draft', 'مسودة']; }
    return ['new', 'لم يُرد بعد'];
};
$help = "## عنوان        ← عنوان قسم بنجمة ذهبية\n| عمود | عمود |   ← جدول (أول سطر = رأس الجدول)\n> نص            ← صندوق كريمي بإطار ذهبي\n- نص            ← نقطة بنجمة ذهبية\n**كلمة**        ← خط عريض\n[زرار: النص | vip/]   ← زرار ذهبي يفتح صفحة في الموقع\nسطر فاضي        ← فقرة جديدة";
?><!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>ردود كشف الهوية · لوحة مرفت</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{--blue:#1F3F7C;--deep:#1A3670;--gold:#C5A059;--cream:#FBF8EE;--line:#E8DFC6;--muted:#5A6582}
*{box-sizing:border-box}body{margin:0;font-family:"Noto Naskh Arabic",serif;background:var(--cream);color:var(--deep);line-height:1.7}
header{background:radial-gradient(80% 120% at 70% 0%,#3A62A8,#1F3F7C 60%,#1A3670);color:#F5F5DC;padding:22px 16px}
header .w{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}header h1{margin:0;font-size:1.3rem;color:#E2C68C}header a{color:#F5F5DC}
.w{max-width:1180px;margin:0 auto;padding:0 16px}main .w{padding:22px 16px 60px}
h2{font-size:1.15rem;margin:22px 0 12px}
button,.btn{font:inherit;font-weight:700;border:0;border-radius:999px;padding:9px 18px;cursor:pointer;text-decoration:none;display:inline-block}
.gold{background:linear-gradient(135deg,#E2C68C,#C5A059);color:var(--deep)}.ghost{background:#fff;border:1px solid var(--line);color:var(--deep)}.blue{background:var(--blue);color:#F5F5DC}
.ok{background:#eef7ee;border:1px solid #b9dcb9;padding:10px 14px;border-radius:12px}.err{background:#fbeeee;border:1px solid #e3b8b8;padding:10px 14px;border-radius:12px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.card span{color:var(--muted);font-size:.9rem}.tag{font-size:.8rem;font-weight:700;border-radius:999px;padding:2px 10px;margin-inline-start:8px}
.tag.new{background:#FFF4DA;color:#8A6416}.tag.draft{background:#E8EEFA;color:var(--blue)}.tag.sent{background:#E7F5EC;color:#22764A}
.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);gap:22px;align-items:start}
@media (max-width:900px){.grid{grid-template-columns:1fr}}
.panel{background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px}
.qa{border-top:1px dashed var(--line);padding:10px 0}.qa:first-child{border-top:0}.qa b{display:block;font-size:.92rem;color:var(--blue)}.qa p{margin:4px 0 0;white-space:pre-line}.qa.no p{color:var(--muted)}
label{display:block;font-weight:700;margin:10px 0 4px}input[type=text],input[type=email],textarea{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:12px;font:inherit;background:#fff;color:var(--deep)}
textarea{min-height:520px;line-height:1.9;font-size:1rem}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}@media (max-width:600px){.row{grid-template-columns:1fr}}
.help{background:var(--cream);border:1px solid var(--line);border-radius:12px;padding:10px 12px;font-size:.85rem;white-space:pre;overflow:auto;direction:rtl;margin:8px 0 0}
.acts{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:14px}.ck{display:flex;gap:8px;align-items:center;font-weight:700;margin-top:12px}
iframe{width:100%;height:1200px;border:1px solid var(--line);border-radius:18px;background:#EEF0F6}
.sent-log{color:#22764A;font-size:.9rem}.empty{color:var(--muted)}
</style></head><body>
<header><div class="w"><h1>ردود «أسئلة كشف الهوية»</h1><nav><a href="replies.php">كل الإجابات</a> · <a href="voices.php">آراء العملاء</a></nav></div></header>
<main><div class="w">
<?php if ($msg): ?><p class="ok"><?= $h($msg) ?></p><?php endif; ?>
<?php if ($err): ?><p class="err"><?= $h($err) ?></p><?php endif; ?>

<?php if (!$gift): ?>
  <?php if ($id): ?><p class="err">لم أجد هذا الطلب.</p><?php endif; ?>
  <h2>كل الإجابات (<?= count($gifts) ?>)</h2>
  <?php if (!$gifts): ?><p class="empty">لم تصل إجابات بعد.</p><?php endif; ?>
  <?php foreach ($gifts as $g): [$st, $label] = $status($g['id']); ?>
    <div class="card"><div><b><?= $h($g['name']) ?></b><span class="tag <?= $st ?>"><?= $label ?></span><br>
      <span><?= $h($g['email']) ?> · <?= $fmtDate($g['created_at']) ?> · أجابت عن <?= (int)$g['answered'] ?> سؤالاً · <?= $h($g['id']) ?></span></div>
      <a class="btn gold" href="replies.php?id=<?= $h($g['id']) ?>"><?= $st === 'new' ? 'اكتبي الرد' : 'افتحي' ?></a></div>
  <?php endforeach; ?>
<?php else:
  $r = $replies[$id] ?? [];
  // Replies Claude prepared for Mervat: uploaded straight to the server (never in the public code), used until she saves her own draft.
  if (empty($r['body']) && is_file(__DIR__ . '/_seed_drafts.php')) {
      foreach ((array)(require __DIR__ . '/_seed_drafts.php') as $sd) {
          if (!empty($sd['match']) && mb_stripos($gift['name'] . ' ' . $gift['email'], $sd['match']) !== false) { $r = array_merge($sd, $r); $seeded = true; break; }
      }
  }
  $first = trim(explode(' ', trim($gift['name']))[0] ?? '');
  $v = ['name' => $r['name'] ?? $first, 'email' => $r['email'] ?? $gift['email'], 'subject' => $r['subject'] ?? $DEF_SUBJECT, 'title' => $r['title'] ?? $DEF_TITLE, 'body' => $r['body'] ?? ''];
  $preview = ms_reply_html(['name' => $v['name'], 'title' => $v['title'], 'body' => $v['body']]);
?>
  <p><a href="replies.php">← كل الإجابات</a></p>
  <div class="grid">
    <section>
      <div class="panel">
        <h2 style="margin-top:0">إجابات <?= $h($gift['name']) ?></h2>
        <p class="empty" style="margin:0 0 8px"><?= $h($gift['email']) ?> · <?= $fmtDate($gift['created_at']) ?> · <?= $h($gift['id']) ?></p>
        <?php foreach ($questions as $i => $q): $a = $gift['answers'][$i + 1] ?? ''; ?>
          <div class="qa<?= $a === '' ? ' no' : '' ?>"><b><?= $i + 1 ?>) <?= $h($q) ?></b><p><?= $a === '' ? '— لم تُجب —' : $h($a) ?></p></div>
        <?php endforeach; ?>
      </div>
    </section>
    <section>
      <form class="panel" id="form" method="post" novalidate action="replies.php?id=<?= $h($id) ?>">
        <h2 style="margin-top:0">الرد</h2>
        <?php if (!empty($seeded)): ?><p class="ok" style="margin:0 0 8px">هذا الرد جهّزه لكِ Claude بالتنسيق. راجعيه، ثم دوسي «احفظي المسودة» أو أرسليه.</p><?php endif; ?>
        <?php foreach (($r['sent'] ?? []) as $s): ?><p class="sent-log">✓ أُرسل إلى <?= $h($s['to']) ?> في <?= $fmtDate($s['at']) ?></p><?php endforeach; ?>
        <input type="hidden" name="csrf" value="<?= $h($_SESSION['csrf']) ?>"><input type="hidden" name="id" value="<?= $h($id) ?>">
        <div class="row">
          <div><label for="name">الاسم بعد «عزيزتي»</label><input id="name" name="name" type="text" maxlength="60" required value="<?= $h($v['name']) ?>"></div>
          <div><label for="email">بريدها</label><input id="email" name="email" type="email" dir="ltr" required value="<?= $h($v['email']) ?>"></div>
        </div>
        <div class="row">
          <div><label for="subject">موضوع الإيميل (يظهر في صندوق الوارد)</label><input id="subject" name="subject" type="text" maxlength="120" value="<?= $h($v['subject']) ?>"></div>
          <div><label for="title">العنوان داخل الإيميل (في الرأس الأزرق)</label><input id="title" name="title" type="text" maxlength="90" value="<?= $h($v['title']) ?>"></div>
        </div>
        <label for="body">نص الرد</label>
        <textarea id="body" name="body" placeholder="اكتبي التحليل هنا…"><?= $h($v['body']) ?></textarea>
        <details><summary>علامات التنسيق</summary><div class="help"><?= $h($help) ?></div></details>
        <div class="acts">
          <button class="ghost" name="do" value="save">احفظي المسودة</button>
          <button class="blue" name="do" value="preview">حدّثي المعاينة</button>
          <button class="ghost" name="do" value="test">جرّبي على إيميلي</button>
          <input name="test_to" type="text" inputmode="email" autocomplete="email" dir="ltr" placeholder="إيميل آخر للتجربة (اختياري)" value="<?= $h($_SESSION['test_to'] ?? '') ?>" style="flex:1;min-width:200px">
        </div>
        <label class="ck"><input type="checkbox" name="sure" value="1"> راجعتُ الرد وأريد إرساله</label>
        <div class="acts"><button class="gold" name="do" value="send" id="sendBtn">أرسلي الرد لـ<?= $h($v['name'] ?: 'العميلة') ?></button></div>
      </form>
      <h2 id="preview">المعاينة (هكذا يظهر لها)</h2>
      <iframe title="معاينة الإيميل" srcdoc="<?= $h($preview) ?>"></iframe>
    </section>
  </div>
<?php endif; ?>
</div></main><script src="replies.js"></script></body></html>
