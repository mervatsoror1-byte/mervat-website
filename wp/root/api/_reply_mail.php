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
                      . '<td style="font-size:16px;line-height:1.95;color:' . MS_MAIL_TEXT . ';padding-bottom:4px;text-align:right">' . ms_mail_inline($li) . '</td></tr>';
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
            // Shown as stacked cards (one per row) on every screen: Gmail on phones has no reliable way to fit side-by-side columns.
            $rows = array_map(fn($l) => array_map('trim', explode('|', trim(trim($l), '|'))), $table);
            $rows = array_values(array_filter($rows, fn($r) => !preg_match('/^[\s:\-|]*$/u', implode('', $r))));   // drop |---| rows
            $head = count($rows) > 1 ? array_shift($rows) : [];
            foreach ($rows as $r) {
                $out .= '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="width:100%;margin:0 0 12px;border:1px solid #E2CFA0;border-right:4px solid ' . MS_MAIL_GOLD . ';background:' . MS_MAIL_CREAM . '">'
                      . '<tr><td style="padding:12px 14px 4px;font-family:' . MS_MAIL_FONT . ';font-size:16px;font-weight:bold;line-height:1.7;color:' . MS_MAIL_ROYAL . ';text-align:right">' . ms_mail_inline($r[0] ?? '') . '</td></tr>';
                for ($c = 1; $c < count($r); $c++) {
                    if (($r[$c] ?? '') === '') continue;
                    $lbl = ($head[$c] ?? '') !== '' ? '<span style="display:block;font-size:13px;font-weight:bold;color:' . MS_MAIL_GOLD_DEEP . '">' . ms_mail_inline($head[$c]) . '</span>' : '';
                    $out .= '<tr><td style="padding:4px 14px ' . ($c === count($r) - 1 ? '12px' : '6px') . ';font-family:' . MS_MAIL_FONT . ';font-size:15px;line-height:1.85;color:' . MS_MAIL_TEXT . ';text-align:right">' . $lbl . ms_mail_inline($r[$c]) . '</td></tr>';
                }
                $out .= '</table>';
            }
            $out .= '<div style="height:10px;line-height:10px;font-size:0">&nbsp;</div>'; $table = [];
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
                      . '<td style="font-size:18px;font-weight:bold;color:' . MS_MAIL_ROYAL . ';font-family:' . MS_MAIL_FONT . ';padding-bottom:8px;border-bottom:1px solid #E6D3A6">'
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
                          . '<a href="' . htmlspecialchars($url, ENT_QUOTES) . '" style="display:inline-block;padding:12px 28px;font-size:15.5px;font-weight:bold;color:' . MS_MAIL_ROYAL
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
    // Outer layout comes from tools/email/reply.mjml (compiled with MJML, which is built for Gmail/Outlook/phones).
    $e = fn($s) => htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8');
    $social = '';
    foreach ([['فيسبوك', 'https://facebook.com/mrft.srwr'], ['إنستجرام', 'https://instagram.com/mervatsoror111'], ['يوتيوب', 'https://youtube.com/@mervatsoror'],
              ['تيك توك', 'https://tiktok.com/@fefesoror'], ['لينكدإن', 'https://www.linkedin.com/in/mervatsoror']] as $i => [$t, $u]) {
        $social .= ($i ? '<span style="color:#5C77B0">&nbsp;·&nbsp;</span>' : '') . '<a href="' . $u . '" style="color:' . MS_MAIL_GOLD . ';text-decoration:none">' . $t . '</a>';
    }
    $uniq = '<span style="display:none;font-size:0;line-height:0;max-height:0;overflow:hidden;opacity:0">' . bin2hex(random_bytes(6)) . date('His') . '</span>';
    return strtr((string)file_get_contents(__DIR__ . '/_reply_shell.html'), [
        '%%TITLE%%' => $e($r['title'] ?? 'رسالة من د. مرفت سرور'),
        '%%PRE%%' => $e($r['preheader'] ?? 'تحليلك الشخصي من د. مرفت سرور'),
        '%%NAME%%' => $e($r['name'] ?? ''),
        '%%BODY%%' => '<div dir="rtl" style="direction:rtl;text-align:right">' . ms_mail_blocks((string)($r['body'] ?? '')) . '</div>',
        '%%SOCIAL%%' => $social,
        '%%UNIQ%%' => $uniq,
    ]);
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
