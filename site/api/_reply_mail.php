<?php
// Branded HTML email for Dr. Mervat's personal replies (first use: the «أسئلة كشف الهوية» analysis).
// She writes plain text with a few simple marks; ms_reply_html() turns it into an email in the brand colours:
//   ## عنوان            -> section heading (gold star)
//   | أ | ب | ج |       -> table (first row = header). Consecutive lines form one table.
//   > نص                -> highlighted message box (cream, gold border)
//   - نص                -> bullet list
//   [زرار: النص | الرابط] -> gold button
//   **كلمة**           -> bold
//   empty line          -> new paragraph
if (basename($_SERVER['SCRIPT_FILENAME'] ?? '') === '_reply_mail.php') { http_response_code(404); exit; }

const MS_MAIL_ROYAL = '#1B3468';
const MS_MAIL_ROYAL2 = '#284D92';
const MS_MAIL_GOLD = '#C5A059';
const MS_MAIL_GOLD_DEEP = '#A8843F';
const MS_MAIL_CREAM = '#FBF6EA';
const MS_MAIL_TEXT = '#25304D';
const MS_MAIL_FONT = "Tahoma, 'Segoe UI', Arial, sans-serif";

function ms_mail_inline(string $s): string {
    $s = htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
    $s = preg_replace('/\*\*(.+?)\*\*/u', '<b style="color:' . MS_MAIL_ROYAL . '">$1</b>', $s) ?? $s;
    return $s;
}

/** Body markup (the simple marks above) -> email-safe HTML blocks. */
function ms_mail_blocks(string $text): string {
    $lines = preg_split("/\r?\n/", str_replace("\r", '', trim($text))) ?: [];
    $out = ''; $para = []; $table = []; $list = []; $quote = [];
    $p = 'margin:0 0 16px;font-size:16px;line-height:1.95;color:' . MS_MAIL_TEXT . ';';
    $flush = function () use (&$out, &$para, &$table, &$list, &$quote, $p) {
        if ($para) { $out .= '<p style="' . $p . '">' . implode('<br>', array_map('ms_mail_inline', $para)) . '</p>'; $para = []; }
        if ($list) {
            $out .= '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px">';
            foreach ($list as $li) {
                $out .= '<tr><td width="22" valign="top" style="color:' . MS_MAIL_GOLD . ';font-size:15px;line-height:1.95;padding-top:1px">✦</td>'
                      . '<td style="font-size:16px;line-height:1.95;color:' . MS_MAIL_TEXT . ';padding-bottom:4px">' . ms_mail_inline($li) . '</td></tr>';
            }
            $out .= '</table>'; $list = [];
        }
        if ($quote) {
            $out .= '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:6px 0 22px"><tr>'
                  . '<td style="background:' . MS_MAIL_CREAM . ';border:1px solid #E6D3A6;border-right:4px solid ' . MS_MAIL_GOLD . ';border-radius:14px;padding:18px 20px;'
                  . 'font-size:16.5px;line-height:2;color:' . MS_MAIL_ROYAL . ';font-family:' . MS_MAIL_FONT . '">'
                  . implode('<br>', array_map('ms_mail_inline', $quote)) . '</td></tr></table>';
            $quote = [];
        }
        if ($table) {
            $rows = array_map(fn($l) => array_map('trim', explode('|', trim(trim($l), '|'))), $table);
            $rows = array_values(array_filter($rows, fn($r) => !preg_match('/^[\s:\-|]*$/u', implode('', $r))));   // drop |---| rows
            $cols = max(array_map('count', $rows));
            $out .= '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:6px 0 22px;border-collapse:separate;border-spacing:0;border:1px solid #E2CFA0;border-radius:14px;overflow:hidden">';
            foreach ($rows as $i => $r) {
                $out .= $i === 0 ? '<tr class="ms-thr">' : '<tr>';
                for ($c = 0; $c < $cols; $c++) {
                    $v = ms_mail_inline($r[$c] ?? '');
                    if ($i === 0) {
                        $out .= '<th align="right" style="background:' . MS_MAIL_ROYAL . ';color:' . MS_MAIL_GOLD . ';font-size:14.5px;font-weight:bold;padding:12px 14px;'
                              . ($c ? 'border-right:1px solid #2E4E8C;' : '') . 'font-family:' . MS_MAIL_FONT . '">' . $v . '</th>';
                    } else {
                        $bg = $i % 2 ? '#FFFFFF' : MS_MAIL_CREAM;
                        $lbl = $c > 0 && isset($rows[0][$c]) && $rows[0][$c] !== '' ? '<span class="ms-lbl" style="display:none;font-size:12.5px;color:' . MS_MAIL_GOLD_DEEP . ';font-weight:bold">' . ms_mail_inline($rows[0][$c]) . '</span>' : '';
                        $out .= '<td valign="top" class="ms-tc' . ($c === 0 ? ' ms-tc0' : ' ms-tcn') . '" style="background:' . $bg . ';border-top:1px solid #EADCB8;' . ($c ? 'border-right:1px solid #EADCB8;' : '')
                              . 'padding:12px 14px;font-size:15px;line-height:1.85;color:' . ($c === 0 ? MS_MAIL_ROYAL . ';font-weight:bold' : MS_MAIL_TEXT) . ';font-family:' . MS_MAIL_FONT . '">' . $lbl . $v . '</td>';
                    }
                }
                $out .= '</tr>';
            }
            $out .= '</table>'; $table = [];
        }
    };
    foreach ($lines as $raw) {
        $l = trim($raw);
        $kind = $l === '' ? 'blank' : (str_starts_with($l, '##') ? 'h' : (str_starts_with($l, '|') ? 'table' : (str_starts_with($l, '>') ? 'quote'
              : (preg_match('/^[-•]\s+/u', $l) ? 'list' : (preg_match('/^\[زرار\s*:/u', $l) ? 'btn' : 'p')))));
        if (($kind !== 'table' && $table) || ($kind !== 'list' && $list) || ($kind !== 'quote' && $quote) || ($kind !== 'p' && $para)) { $flush(); }
        switch ($kind) {
            case 'h':
                $out .= '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:26px 0 12px"><tr>'
                      . '<td style="font-size:20px;font-weight:bold;color:' . MS_MAIL_ROYAL . ';font-family:' . MS_MAIL_FONT . ';padding-bottom:8px;border-bottom:1px solid #E6D3A6">'
                      . '<span style="color:' . MS_MAIL_GOLD . '">✦</span>&nbsp; ' . ms_mail_inline(trim(ltrim($l, '#'))) . '</td></tr></table>';
                break;
            case 'table': $table[] = $l; break;
            case 'quote': $quote[] = trim(ltrim($l, '>')); break;
            case 'list': $list[] = preg_replace('/^[-•]\s+/u', '', $l); break;
            case 'btn':
                if (preg_match('/^\[زرار\s*:\s*(.+?)\s*\|\s*(\S+?)\s*\]$/u', $l, $m)) {
                    $url = preg_match('~^https?://~', $m[2]) ? $m[2] : 'https://mervatsror.com/' . ltrim($m[2], '/');
                    $out .= '<table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin:10px auto 24px"><tr>'
                          . '<td align="center" bgcolor="' . MS_MAIL_GOLD . '" style="border-radius:999px;background:' . MS_MAIL_GOLD . ';background-image:linear-gradient(135deg,#E2C68C,#C5A059 55%,#AE8945)">'
                          . '<a href="' . htmlspecialchars($url, ENT_QUOTES) . '" style="display:inline-block;padding:13px 38px;font-size:16px;font-weight:bold;color:' . MS_MAIL_ROYAL
                          . ';text-decoration:none;border-radius:999px;font-family:' . MS_MAIL_FONT . '">' . ms_mail_inline($m[1]) . '</a></td></tr></table>';
                } else { $para[] = $l; }
                break;
            case 'p': $para[] = $l; break;
        }
    }
    $flush();
    return $out;
}

/**
 * Whole email. $r = [name, title, body, preheader?]
 * Images come from the live site (email clients load them by URL).
 */
function ms_reply_html(array $r): string {
    $base = 'https://mervatsror.com';
    $name = htmlspecialchars($r['name'] ?? '', ENT_QUOTES, 'UTF-8');
    $title = htmlspecialchars($r['title'] ?? 'رسالة من د. مرفت سرور', ENT_QUOTES, 'UTF-8');
    $pre = htmlspecialchars($r['preheader'] ?? ('تحليلك الشخصي من د. مرفت سرور'), ENT_QUOTES, 'UTF-8');
    $body = ms_mail_blocks((string)($r['body'] ?? ''));
    $uniq = '<span style="display:none;font-size:0;line-height:0;max-height:0;overflow:hidden;opacity:0">' . bin2hex(random_bytes(6)) . date('His') . '</span>';
    $f = MS_MAIL_FONT; $royal = MS_MAIL_ROYAL; $gold = MS_MAIL_GOLD; $text = MS_MAIL_TEXT;
    $social = '';
    foreach ([['فيسبوك', 'https://facebook.com/mrft.srwr'], ['إنستجرام', 'https://instagram.com/mervatsoror111'], ['يوتيوب', 'https://youtube.com/@mervatsoror'],
              ['تيك توك', 'https://tiktok.com/@fefesoror'], ['لينكدإن', 'https://www.linkedin.com/in/mervatsoror']] as $i => [$t, $u]) {
        $social .= ($i ? '<span style="color:#5C77B0">&nbsp;·&nbsp;</span>' : '') . '<a href="' . $u . '" style="color:' . $gold . ';text-decoration:none">' . $t . '</a>';
    }
    return <<<HTML
<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light">
<title>{$title}</title>
<style>
@media only screen and (max-width:620px){
  .ms-outer{padding:0!important}
  .ms-card{border-radius:0!important;box-shadow:none!important}
  .ms-px{padding-left:18px!important;padding-right:18px!important}
  .ms-thr{display:none!important}
  .ms-tc{display:block!important;width:auto!important;border-right:0!important;padding:4px 14px 10px!important;font-size:15.5px!important}
  .ms-tc0{padding-top:12px!important;font-size:16px!important}
  .ms-tcn{border-top:0!important}
  .ms-lbl{display:block!important}
  .ms-title{font-size:20px!important}
}
</style></head>
<body style="margin:0;padding:0;background:#EEF0F6;direction:rtl">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{$pre}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF0F6"><tr><td align="center" class="ms-outer" style="padding:28px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" class="ms-card" style="width:100%;max-width:600px;background:#FFFFFF;border-radius:22px;overflow:hidden;box-shadow:0 18px 40px -24px rgba(27,52,104,.45)" dir="rtl">
  <tr><td align="center" bgcolor="{$royal}" style="background:{$royal};background-image:radial-gradient(120% 140% at 50% 0%,#2E5AA6 0%,#1B3468 62%);padding:34px 24px 28px">
    <img src="{$base}/assets/email/logo-gold.png" width="150" alt="د. مرفت سرور" style="display:block;width:150px;max-width:150px;height:auto;border:0;margin:0 auto 14px">
    <div style="font-family:{$f};font-size:13px;letter-spacing:2px;color:#E2C68C">✦ &nbsp;✦ &nbsp;✦</div>
    <div class="ms-title" style="font-family:{$f};font-size:22px;font-weight:bold;color:#FFFFFF;margin-top:10px;line-height:1.6">{$title}</div>
  </td></tr>
  <tr><td style="height:4px;line-height:4px;font-size:0;background:{$gold};background-image:linear-gradient(90deg,#A8843F,#E6BE57,#FFF1B5,#E6BE57,#A8843F)">&nbsp;</td></tr>
  <tr><td class="ms-px" style="padding:34px 34px 10px;font-family:{$f};text-align:right" dir="rtl">
    <p style="margin:0 0 18px;font-size:19px;font-weight:bold;color:{$royal}">عزيزتي {$name}،</p>
    {$body}
  </td></tr>
  <tr><td class="ms-px" style="padding:6px 34px 30px;font-family:{$f}" dir="rtl">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #E6D3A6"><tr>
      <td width="84" valign="middle" style="padding-top:22px"><img src="{$base}/assets/email/mervat.jpg" width="72" height="72" alt="د. مرفت سرور" style="display:block;width:72px;height:72px;border-radius:50%;border:2px solid {$gold}"></td>
      <td valign="middle" style="padding-top:22px;font-family:{$f};text-align:right">
        <div style="font-size:15px;color:{$gold};font-weight:bold">أنوي لكِ التشافي بكل حب</div>
        <div style="font-size:18px;color:{$royal};font-weight:bold;margin-top:2px">د. مرفت سرور</div>
        <div style="font-size:13px;color:#6B7390;margin-top:2px">مدربة وعي معتمدة من الاتحاد الدولي للتدريب ICF{$uniq}</div>
      </td></tr></table>
  </td></tr>
  <tr><td align="center" bgcolor="{$royal}" style="background:{$royal};padding:24px 24px 26px;font-family:{$f}">
    <div style="font-size:14px;line-height:2">{$social}</div>
    <div style="font-size:13px;color:#C9D3EC;margin-top:8px"><a href="{$base}" style="color:#FFFFFF;text-decoration:none;font-weight:bold">mervatsror.com</a> &nbsp;·&nbsp; <a href="mailto:info@mervatsror.com" style="color:#C9D3EC;text-decoration:none">info@mervatsror.com</a></div>
    <div style="font-size:11.5px;color:#9FB0D6;line-height:1.9;margin-top:12px">هذه الرسالة شخصية ومُرسلة إليكِ وحدكِ ردّاً على إجاباتك.<br>المحتوى للتطوير الذاتي والوعي، وليس بديلاً عن التشخيص أو العلاج الطبي أو النفسي.{$uniq}</div>
  </td></tr>
</table>
</td></tr></table>
</body></html>
HTML;
}

/** Send the branded HTML email. Customer copy comes From info@ (Reply-To info@); Mervat's copy uses WordPress's own sender so it reaches her Gmail. */
function ms_send_reply_html(string $to, string $subject, string $html, bool $to_customer): bool {
    if (!function_exists('wp_mail')) {
        $enc = fn($s) => '=?UTF-8?B?' . base64_encode($s) . '?=';
        return @mail($to, $enc($subject), $html, "MIME-Version: 1.0\r\nContent-Type: text/html; charset=UTF-8\r\nFrom: " . $enc('د. مرفت سرور') . ' <' . NOTIFY_EMAIL . ">\r\nReply-To: " . NOTIFY_EMAIL);
    }
    $h = ['Content-Type: text/html; charset=UTF-8'];
    if ($to_customer) { $h[] = 'From: د. مرفت سرور <' . NOTIFY_EMAIL . '>'; $h[] = 'Reply-To: ' . NOTIFY_EMAIL; }
    return (bool)wp_mail($to, $subject, $html, $h);
}
