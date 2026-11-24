<?php
// Records a PayPal payment the buyer just approved and emails Dr. Mervat to deliver the order.
// The amount shown in the email is what our prices say; Mervat confirms the received amount in PayPal before delivering.
require __DIR__ . '/_lib.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { fail(404, 'unknown'); }
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$host = $_SERVER['HTTP_HOST'] ?? '';
if ($origin !== '' && strtolower((string)parse_url($origin, PHP_URL_HOST)) !== strtolower(explode(':', $host)[0])) { fail(403, 'origin'); }
if (!rate_ok('order', 10, 3600)) { fail(429, 'limit'); }

$in = json_decode((string)file_get_contents('php://input'), true);
if (!is_array($in)) { fail(400, 'body'); }

$paypalId = preg_replace('/[^A-Z0-9]/', '', strtoupper((string)($in['paypal_id'] ?? '')));
if (strlen($paypalId) < 10 || strlen($paypalId) > 40) { fail(400, 'paypal_id'); }
$paid = (string)($in['paid'] ?? '');
$prices = require __DIR__ . '/_prices.php';
$titles = products();

$items = []; $expected = 0.0;
foreach ((array)($in['items'] ?? []) as $it) {
    $id = (string)($it['id'] ?? '');
    if (!isset($prices[$id])) { fail(400, 'item'); }
    $items[] = ['id' => $id, 'title' => $prices[$id]['t'], 'us' => $prices[$id]['us'], 'when' => clean_text((string)($it['when'] ?? ''), 80)];
    $expected += $prices[$id]['us'];
    if (count($items) > 20) { fail(400, 'items'); }
}
if (!$items) { fail(400, 'items'); }

$order = [
    'no' => 'MS-' . strtoupper(substr(bin2hex(random_bytes(4)), 0, 6)),
    'paypal_id' => $paypalId,
    'paid_reported' => clean_text($paid, 20),
    'expected_usd' => round($expected, 2),
    'name' => clean_text((string)($in['name'] ?? ''), 60),
    'email' => filter_var((string)($in['email'] ?? ''), FILTER_VALIDATE_EMAIL) ?: '',
    'payer_email' => filter_var((string)($in['payer_email'] ?? ''), FILTER_VALIDATE_EMAIL) ?: '',
    'items' => $items,
    'created_at' => gmdate('c'),
];

$path = data_dir() . '/orders.json';
$fh = fopen($path, 'c+'); flock($fh, LOCK_EX);
$list = json_decode((string)stream_get_contents($fh), true) ?: [];
foreach ($list as $o) { if (($o['paypal_id'] ?? '') === $paypalId) { flock($fh, LOCK_UN); fclose($fh); send_json(['ok' => true, 'no' => $o['no']]); } }
$list[] = $order;
ftruncate($fh, 0); rewind($fh); fwrite($fh, json_encode($list, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
flock($fh, LOCK_UN); fclose($fh); @chmod($path, 0600);

if (is_file(MS_WP_LOAD)) { if (!defined('WP_USE_THEMES')) { define('WP_USE_THEMES', false); } require_once MS_WP_LOAD; }
$lines = implode("\n", array_map(fn($i) => "• {$i['title']}" . ($i['when'] ? " ({$i['when']})" : '') . " — \${$i['us']}", $items));
$body = "طلب جديد مدفوع عبر PayPal\n\nرقم الطلب: {$order['no']}\nرقم عملية PayPal: {$paypalId}\n\n{$lines}\n\nالمبلغ حسب أسعار الموقع: \${$order['expected_usd']}\n"
      . "المبلغ الذي أبلغ عنه المتصفح: {$order['paid_reported']}\n\n"
      . "العميلة: {$order['name']}\nبريدها في الموقع: {$order['email']}\nبريدها في PayPal: {$order['payer_email']}\n\n"
      . "مهم: تأكدي من وصول المبلغ كاملاً في حساب PayPal (بنفس رقم العملية) قبل تفعيل الطلب.\n";
ms_mail(NOTIFY_EMAIL, "طلب PayPal جديد {$order['no']}", $body, $order['email'], 'موقع د. مرفت سرور');

send_json(['ok' => true, 'no' => $order['no']]);
