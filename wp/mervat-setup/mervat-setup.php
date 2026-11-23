<?php
/**
 * Plugin Name: Mervat Setup
 * Description: Sets up the shop from the site's own data: pages, products with EGP/USD prices, currencies, payments and session dates. Safe to run again; it updates instead of duplicating.
 * Version: 1.2.5
 * Author: Mervat Soror
 * Requires Plugins: woocommerce
 */
if (!defined('ABSPATH')) { exit; }

const MS_SETUP_VERSION = '1.2.5';
const MS_EGYPT_ZONE = 'egypt';

/* ---------------------------------------------------------------- run setup once per version */
add_action('init', function () {
    if (get_option('ms_setup_version') === MS_SETUP_VERSION) { return; }
    if (!function_exists('wc_get_product_id_by_sku') || !class_exists('WC_Product_Simple')) { return; }
    if (get_transient('ms_setup_lock')) { return; }
    set_transient('ms_setup_lock', 1, 300);
    @set_time_limit(240);
    ms_setup_run();
    update_option('ms_setup_version', MS_SETUP_VERSION);
    delete_transient('ms_setup_lock');
}, 50);

// Product photos are added a few at a time on later visits, so no single visit is slow.
add_action('init', function () {
    if (get_option('ms_setup_version') !== MS_SETUP_VERSION || get_option('ms_images_done') === MS_SETUP_VERSION) { return; }
    if (get_transient('ms_img_lock')) { return; }
    set_transient('ms_img_lock', 1, 120);
    $left = ms_attach_images(4);
    if ($left === 0) { update_option('ms_images_done', MS_SETUP_VERSION); }
    delete_transient('ms_img_lock');
}, 60);

function ms_data(string $file): array {
    return json_decode((string)file_get_contents(__DIR__ . '/' . $file), true) ?: [];
}

function ms_setup_run(): void {
    $staging = strpos((string)wp_parse_url(home_url(), PHP_URL_HOST), 'new.') === 0;

    // General shop settings (digital products, Arabic labels)
    $opts = [
        'woocommerce_currency' => 'USD',
        'woocommerce_default_country' => 'EG',
        'woocommerce_store_city' => 'القاهرة',
        'woocommerce_currency_pos' => 'right_space',
        'woocommerce_price_num_decimals' => '0',
        'woocommerce_price_thousand_sep' => ',',
        'woocommerce_default_customer_address' => 'base',
        'woocommerce_calc_taxes' => 'no',
        'woocommerce_enable_reviews' => 'no',
        'woocommerce_cart_redirect_after_add' => 'no',
        'woocommerce_enable_ajax_add_to_cart' => 'yes',
        'woocommerce_enable_guest_checkout' => 'no',
        'woocommerce_enable_checkout_login_reminder' => 'yes',
        'woocommerce_enable_signup_and_login_from_checkout' => 'yes',
        'woocommerce_enable_myaccount_registration' => 'yes',
        'woocommerce_registration_generate_username' => 'yes',
        'woocommerce_registration_generate_password' => 'yes',
        'woocommerce_ship_to_countries' => 'disabled',
        'woocommerce_coming_soon' => 'no',
        'woocommerce_store_pages_only' => 'no',
        'woocommerce_email_from_name' => 'د. مرفت سرور',
        'woocommerce_email_from_address' => 'info@mervatsror.com',
        'blogname' => 'د. مرفت سرور',
        'blogdescription' => 'مدربة وعي وتشافي معتمدة من ICF',
        'permalink_structure' => '/%postname%/',
        'blog_public' => $staging ? '0' : '1',
        'timezone_string' => 'Africa/Cairo',
        'date_format' => 'j F Y',
        'users_can_register' => '1',
        'default_role' => 'customer',
        'woocommerce_email_base_color' => '#1F3F7C',
        'woocommerce_email_background_color' => '#FBF8EE',
        'woocommerce_email_body_background_color' => '#FFFFFF',
        'woocommerce_email_text_color' => '#1A3670',
        'woocommerce_email_footer_text' => 'د. مرفت سرور · مدربة وعي وتشافي معتمدة من ICF · info@mervatsror.com · واتساب 01095292748',
        'woocommerce_registration_privacy_policy_text' => 'نستخدم بياناتك لإدارة حسابك وطلباتك فقط، كما هو موضّح في [privacy_policy].',
        'woocommerce_checkout_privacy_policy_text' => 'نستخدم بياناتك لإتمام طلبك وإدارة حسابك فقط، كما هو موضّح في [privacy_policy].',
    ];
    foreach ($opts as $k => $v) { update_option($k, $v); }
    $perma = (array)get_option('woocommerce_permalinks', []);
    $perma['product_base'] = MS_PRODUCT_BASE_SLUG;
    update_option('woocommerce_permalinks', $perma);

    // Egyptian pound for visitors in Egypt, US dollar for everyone else (fixed prices, no conversion)
    if (class_exists('WCPBC_Pricing_Zones')) {
        $zones = (array)get_option('wc_price_based_country_regions', []);
        if (!isset($zones[MS_EGYPT_ZONE])) {
            $zones[MS_EGYPT_ZONE] = ['enabled' => 'yes', 'name' => 'مصر', 'countries' => ['EG'], 'currency' => 'EGP',
                                    'exchange_rate' => '50', 'auto_exchange_rate' => 'no', 'disable_tax_adjustment' => 'no', 'order' => 1];
            update_option('wc_price_based_country_regions', $zones);
        }
    }

    // Pay in Egyptian pounds by transfer (InstaPay / Vodafone Cash) until the card gateway is ready
    update_option('woocommerce_bacs_settings', [
        'enabled' => 'yes',
        'title' => 'الدفع بالجنيه المصري: إنستاباي أو فودافون كاش أو تحويل بنكي',
        'description' => 'بعد إتمام الطلب تصلك طريقة الدفع على بريدك، ويمكنك إرسال صورة التحويل على واتساب 01095292748، ونفعّل طلبك فور التأكيد.',
        'instructions' => 'شكراً لطلبك. أرسلي صورة التحويل مع رقم الطلب على واتساب 01095292748، وسنفعّل طلبك فور التأكيد.',
        'account_details' => '',
    ]);

    if (class_exists('WC_Install')) { WC_Install::create_pages(); }
    ms_setup_pages();
    ms_link_policy_pages();
    ms_classic_checkout();
    ms_email_logo();
    ms_setup_subscriptions();
    ms_setup_courses();
    ms_setup_lessons();
    ms_setup_products();
    ms_name_shop_pages();
    ms_install_translations();
    update_option('ms_needs_flush', 1);
}

// Address rules are refreshed on the request after setup, once the new product base is registered.
add_action('init', function () {
    if (get_option('ms_needs_flush')) { delete_option('ms_needs_flush'); flush_rewrite_rules(false); }
}, 999);

function ms_name_shop_pages(): void {
    $names = ['cart' => 'السلة', 'checkout' => 'إتمام الطلب', 'myaccount' => 'حسابي', 'shop' => 'المتجر'];
    foreach ($names as $key => $title) {
        $id = function_exists('wc_get_page_id') ? wc_get_page_id($key) : 0;
        if ($id > 0 && get_the_title($id) !== $title) { wp_update_post(['ID' => $id, 'post_title' => $title]); }
    }
}

const MS_PRODUCT_BASE_SLUG = 'tools';

function ms_theme_meta(): array {
    $f = get_theme_root() . '/mervat/parts/_meta.json';
    return is_file($f) ? (json_decode((string)file_get_contents($f), true) ?: []) : [];
}

function ms_setup_pages(): void {
    $meta = ms_theme_meta();
    foreach (ms_data('pages.json') as $slug) {
        if ($slug === '404') { continue; } // the theme shows its own 404; WordPress cannot keep a page named "404"
        $want = $slug === 'front' ? 'home' : $slug;
        $title = $meta[$slug]['title'] ?? $want;
        if ($slug === 'front') { $title = 'الرئيسية'; }
        $page = get_page_by_path($want, OBJECT, 'page');
        if (!$page) {
            $id = wp_insert_post(['post_type' => 'page', 'post_status' => 'publish', 'post_name' => $want, 'post_title' => $title, 'post_content' => '']);
        } else {
            $id = $page->ID;
            if ($page->post_title !== $title) { wp_update_post(['ID' => $id, 'post_title' => $title]); }
        }
        if ($slug === 'front' && $id && !is_wp_error($id)) {
            update_option('show_on_front', 'page');
            update_option('page_on_front', $id);
        }
    }
    // the sample page WordPress creates is not needed
    $sample = get_page_by_path('sample-page', OBJECT, 'page');
    if ($sample) { wp_trash_post($sample->ID); }
    // clean up: duplicate "404-N" pages made by earlier setup runs, WordPress's sample post, unused duplicate shop pages
    global $wpdb;
    foreach ($wpdb->get_col("SELECT ID FROM {$wpdb->posts} WHERE post_type = 'page' AND post_status = 'publish' AND post_name REGEXP '^404(-[0-9]+)?$'") as $pid) { wp_trash_post((int)$pid); }
    $hello = get_page_by_path('hello-world', OBJECT, 'post'); if ($hello) { wp_trash_post($hello->ID); }
    $used = array_map('intval', [get_option('woocommerce_cart_page_id'), get_option('woocommerce_checkout_page_id'), get_option('woocommerce_myaccount_page_id'), get_option('woocommerce_shop_page_id')]);
    foreach (['cart-2', 'checkout-2'] as $dup) { $pg = get_page_by_path($dup, OBJECT, 'page'); if ($pg && !in_array((int)$pg->ID, $used, true)) { wp_trash_post($pg->ID); } }
}

function ms_setup_products(): void {
    foreach (ms_data('products.json') as $p) {
        if (empty($p['sku']) || $p['us'] === null) { continue; }
        $id = wc_get_product_id_by_sku($p['sku']);
        $product = $id ? wc_get_product($id) : new WC_Product_Simple();
        if (!$product) { continue; }
        $product->set_name($p['name']);
        $product->set_slug($p['slug']);
        if (!$id) { $product->set_sku($p['sku']); }
        $product->set_regular_price((string)$p['us']);
        $product->set_sale_price('');
        $product->set_virtual(true);
        $product->set_sold_individually(true);
        $product->set_tax_status('none');
        $product->set_status('publish');
        $product->set_catalog_visibility($p['redirect'] ? 'hidden' : 'visible');
        if (!empty($p['short'])) { $product->set_short_description($p['short']); }
        $id = $product->save();

        update_post_meta($id, '_ms_redirect', $p['redirect'] ?: '');
        update_post_meta($id, '_ms_kind', $p['kind'] ?? '');
        update_post_meta($id, '_ms_grants', $p['grants'] ?? '');
        update_post_meta($id, '_ms_img', $p['img'] ?? '');
        // fixed Egyptian price
        if ($p['eg'] !== null) {
            update_post_meta($id, '_' . MS_EGYPT_ZONE . '_price_method', 'manual');
            // launch price: the original stays as the struck regular price, the launch price is the sale price
            $was = !empty($p['was']) ? (string)$p['was'] : '';
            update_post_meta($id, '_' . MS_EGYPT_ZONE . '_regular_price', $was !== '' ? $was : (string)$p['eg']);
            update_post_meta($id, '_' . MS_EGYPT_ZONE . '_sale_price', $was !== '' ? (string)$p['eg'] : '');
            update_post_meta($id, '_' . MS_EGYPT_ZONE . '_price', (string)$p['eg']);
            update_post_meta($id, '_' . MS_EGYPT_ZONE . '_sale_price_dates', 'default');
        }
        wc_delete_product_transients($id);
    }
}

/** Attach each product's picture from the theme; returns how many are still waiting. */
function ms_attach_images(int $max): int {
    require_once ABSPATH . 'wp-admin/includes/image.php';
    $left = 0; $done = 0;
    foreach (ms_data('products.json') as $p) {
        $id = wc_get_product_id_by_sku($p['sku'] ?? '');
        if (!$id || empty($p['img']) || get_post_thumbnail_id($id)) { continue; }
        if ($done >= $max) { $left++; continue; }
        $src = get_theme_root() . '/mervat/' . ltrim($p['img'], '/');
        if (!is_file($src)) { update_post_meta($id, '_thumbnail_id', 0); continue; }
        $up = wp_upload_bits(basename($src), null, (string)file_get_contents($src));
        if (!empty($up['error'])) { continue; }
        $type = wp_check_filetype($up['file']);
        $att = wp_insert_attachment(['post_mime_type' => $type['type'], 'post_title' => $p['name'], 'post_status' => 'inherit'], $up['file'], $id);
        if (is_wp_error($att)) { continue; }
        wp_update_attachment_metadata($att, wp_generate_attachment_metadata($att, $up['file']));
        set_post_thumbnail($id, $att);
        $done++;
    }
    return $left;
}

/* ---------------------------------------------------------------- session date on the order */
add_filter('woocommerce_add_cart_item_data', function ($data) {
    if (!empty($_REQUEST['ms_when'])) {
        $data['ms_when'] = mb_substr(sanitize_text_field(wp_unslash($_REQUEST['ms_when'])), 0, 120);
        $data['ms_unique'] = md5($data['ms_when']);
    }
    return $data;
});
add_filter('woocommerce_get_item_data', function ($items, $cart_item) {
    if (!empty($cart_item['ms_when'])) { $items[] = ['name' => 'الموعد', 'value' => esc_html($cart_item['ms_when'])]; }
    return $items;
}, 10, 2);
add_action('woocommerce_checkout_create_order_line_item', function ($item, $key, $values) {
    if (!empty($values['ms_when'])) { $item->add_meta_data('الموعد', $values['ms_when'], true); }
}, 10, 3);

/* ---------------------------------------------------------------- payment methods per currency */
add_filter('woocommerce_available_payment_gateways', function ($gateways) {
    if (is_admin() || !function_exists('get_woocommerce_currency')) { return $gateways; }
    if (get_woocommerce_currency() !== 'EGP') { unset($gateways['bacs']); }
    if (get_woocommerce_currency() === 'EGP') { foreach (array_keys($gateways) as $g) { if (strpos($g, 'ppcp') === 0) { unset($gateways[$g]); } } }
    return $gateways;
});

/* ---------------------------------------------------------------- Arabic for WooCommerce, Tutor, Amelia */
function ms_install_translations(): void {
    require_once ABSPATH . 'wp-admin/includes/admin.php';
    require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
    if (get_locale() !== 'ar') { update_option('WPLANG', 'ar'); }
    delete_site_transient('update_plugins');
    delete_site_transient('update_themes');
    wp_update_plugins();
    wp_update_themes();
    $updates = wp_get_translation_updates();
    if ($updates) {
        $skin = new Automatic_Upgrader_Skin();
        (new Language_Pack_Upgrader($skin))->bulk_upgrade($updates);
    }
}

/* ---------------------------------------------------------------- short checkout: no postal address for digital items */
add_filter('woocommerce_get_country_locale', function ($locale) {
    $hide = ['address_1', 'address_2', 'city', 'state', 'postcode', 'company'];
    foreach (array_keys($locale) as $cc) {
        foreach ($hide as $f) { $locale[$cc][$f]['required'] = false; $locale[$cc][$f]['hidden'] = true; }
    }
    return $locale;
});
add_filter('woocommerce_get_country_locale_default', function ($fields) {
    foreach (['address_1', 'address_2', 'city', 'state', 'postcode', 'company'] as $f) { $fields[$f]['required'] = false; $fields[$f]['hidden'] = true; }
    return $fields;
});
add_filter('woocommerce_billing_fields', function ($fields) {
    foreach (['billing_address_1', 'billing_address_2', 'billing_city', 'billing_state', 'billing_postcode', 'billing_company'] as $f) { unset($fields[$f]); }
    return $fields;
});

/* ---------------------------------------------------------------- privacy and terms links in checkout */
function ms_link_policy_pages(): void {
    $privacy = get_page_by_path('privacy', OBJECT, 'page');
    $terms = get_page_by_path('terms', OBJECT, 'page');
    if ($privacy) { update_option('wp_page_for_privacy_policy', $privacy->ID); }
    if ($terms) { update_option('woocommerce_terms_page_id', $terms->ID); }
    $old = get_post(3);
    if ($old && $old->post_type === 'page' && $old->post_status === 'draft' && (!$privacy || $old->ID !== $privacy->ID)) { wp_trash_post($old->ID); }
}

/* ---------------------------------------------------------------- quiet cart: the header count is enough */
add_filter('wc_add_to_cart_message_html', '__return_empty_string');
add_filter('woocommerce_add_success', function ($message) { return trim(wp_strip_all_tags((string)$message)) === '' ? '' : $message; });

/* ---------------------------------------------------------------- email look */
function ms_email_logo(): void {
    $logo = get_theme_root_uri() . '/mervat/assets/brand/logo-gold-transparent.png';
    update_option('woocommerce_email_header_image', $logo);
}

/* ---------------------------------------------------------------- VIP as renewing subscriptions (Flexible Subscriptions) */
function ms_setup_subscriptions(): void {
    if (!taxonomy_exists('product_type')) { return; }
    $plans = ['vip-m' => [1, 'M'], 'vip-q' => [3, 'M'], 'vip-y' => [1, 'Y']];   // periods: D, W, M, Y
    foreach ($plans as $sku => [$interval, $period]) {
        $id = wc_get_product_id_by_sku($sku);
        if (!$id) { continue; }
        wp_set_object_terms($id, 'fsb-subscription', 'product_type');
        update_post_meta($id, '_fsb_subscription_interval', (string)$interval);
        update_post_meta($id, '_fsb_subscription_period', $period);
        update_post_meta($id, '_fsb_total_billing_cycles', '0');
        update_post_meta($id, '_fsb_subscription_trial_length', '0');
        update_post_meta($id, '_fsb_subscription_sign_up_fee', '');
        update_post_meta($id, '_fsb_subscription_one_time_shipping', 'no');
        wc_delete_product_transients($id);
    }
}

/* ---------------------------------------------------------------- one Tutor course per tool, opened after payment */
function ms_course_for(string $sku): int {
    $q = get_posts(['post_type' => 'courses', 'post_status' => 'any', 'meta_key' => '_ms_sku', 'meta_value' => $sku, 'numberposts' => 1, 'fields' => 'ids']);
    return $q ? (int)$q[0] : 0;
}

function ms_setup_courses(): void {
    if (!post_type_exists('courses')) { return; }
    $opt = (array)get_option('tutor_option', []);
    $opt['monetize_by'] = 'wc';
    update_option('tutor_option', $opt);
    foreach (ms_data('products.json') as $p) {
        if (!in_array($p['kind'] ?? '', ['course', 'exercise', 'book'], true)) { continue; }
        $pid = wc_get_product_id_by_sku($p['sku']);
        if (!$pid) { continue; }
        $cid = ms_course_for($p['sku']);
        $post = ['post_type' => 'courses', 'post_status' => 'publish', 'post_title' => $p['name'],
                 'post_name' => 'learn-' . $p['sku'], 'post_excerpt' => $p['short'] ?? ''];
        if ($cid) { $post['ID'] = $cid; wp_update_post($post); }
        else { $cid = wp_insert_post($post); }
        if (!$cid || is_wp_error($cid)) { continue; }
        update_post_meta($cid, '_ms_sku', $p['sku']);
        update_post_meta($cid, '_tutor_course_price_type', 'paid');
        $cs = (array)get_post_meta($cid, '_tutor_course_settings', true);
        $cs['enrollment_expiry'] = 0;   // access length is managed by ms_access (90 days, or while VIP is active)
        update_post_meta($cid, '_tutor_course_settings', $cs);
        update_post_meta($cid, '_tutor_course_product_id', $pid);
        update_post_meta($pid, '_tutor_product', 'yes');
        update_post_meta($pid, '_ms_course', $cid);
        $thumb = get_post_thumbnail_id($pid);
        if ($thumb) { set_post_thumbnail($cid, $thumb); }
    }
}

/** Courses a purchased product opens: itself, an offer's tool, a bundle's tools, or every VIP tool. */
function ms_courses_for_product(int $product_id): array {
    $sku = (string)get_post_meta($product_id, '_sku', true);
    $all = ms_data('products.json');
    $by = [];
    foreach ($all as $p) { $by[$p['sku']] = $p; }
    $p = $by[$sku] ?? null;
    if (!$p) { return []; }
    $skus = [];
    if (in_array($p['kind'], ['course', 'exercise', 'book'], true)) { $skus[] = $sku; }
    if ($p['kind'] === 'offer' && !empty($p['grants'])) { $skus[] = $p['grants']; }
    if ($p['kind'] === 'bundle') { $skus = array_merge($skus, (array)($p['items'] ?? [])); }
    if ($p['kind'] === 'vip') { foreach ($all as $q) { if (!empty($q['vip'])) { $skus[] = $q['sku']; } } }
    $ids = [];
    foreach (array_unique($skus) as $s) { $c = ms_course_for($s); if ($c) { $ids[] = $c; } }
    return $ids;
}

/* Digital orders finish on payment, so access opens at once. */
function ms_order_is_digital($order): bool {
    foreach ($order->get_items() as $item) {
        $prod = $item->get_product();
        if ($prod && !$prod->is_virtual()) { return false; }
    }
    return true;
}
add_filter('woocommerce_payment_complete_order_status', function ($status, $order_id, $order) {
    return ($order && ms_order_is_digital($order)) ? 'completed' : $status;
}, 10, 3);
add_action('woocommerce_order_status_processing', function ($order_id) {
    $order = wc_get_order($order_id);
    if ($order && ms_order_is_digital($order)) { $order->update_status('completed', 'تم تفعيل الطلب تلقائياً لأنه منتج رقمي.'); }
}, 20);

/* ---------------------------------------------------------------- who can open what, and until when
   User meta _ms_access = [course_id => ['own_until' => timestamp, 'vip' => bool]]
   - a tool bought on its own or in a bundle stays open 365 days; a landing-page offer 90 days
   - VIP tools stay open while the VIP subscription is active
   A daily check closes anything that is neither. */
const MS_OWN_DAYS = 365;      // regular purchase
const MS_OFFER_DAYS = 90;     // discounted landing-page offer

function ms_access_get(int $user): array { $v = get_user_meta($user, '_ms_access', true); return is_array($v) ? $v : []; }
function ms_access_set(int $user, array $a): void { $a ? update_user_meta($user, '_ms_access', $a) : delete_user_meta($user, '_ms_access'); }

function ms_enroll(int $cid, int $user, int $order_id = 0): void {
    if (!function_exists('tutor_utils') || tutor_utils()->is_enrolled($cid, $user)) { return; }
    $enrol = tutor_utils()->do_enroll($cid, $order_id, $user);
    if ($enrol) { tutor_utils()->course_enrol_status_change($enrol, 'completed'); }
}

function ms_unenroll(int $cid, int $user): void {
    // Close the enrollment record directly (Tutor's own cancel relies on a per-request cache).
    global $wpdb;
    $ids = $wpdb->get_col($wpdb->prepare("SELECT ID FROM {$wpdb->posts} WHERE post_type = 'tutor_enrolled' AND post_parent = %d AND post_author = %d AND post_status = 'completed'", $cid, $user));
    foreach ($ids as $id) {
        $wpdb->update($wpdb->posts, ['post_status' => 'cancel'], ['ID' => (int)$id]);
        clean_post_cache((int)$id);
    }
    clean_post_cache($cid);
    wp_cache_flush_group('tutor');
    do_action('tutor_enrollment/after/cancel', $cid, $user);
}

/** Close whatever this person no longer has a reason to open. */
function ms_access_sweep(int $user): void {
    $a = ms_access_get($user); $now = time();
    foreach ($a as $cid => $r) {
        $open = !empty($r['vip']) || (int)($r['own_until'] ?? 0) > $now;
        if (!$open) { ms_unenroll((int)$cid, $user); unset($a[$cid]); }
    }
    ms_access_set($user, $a);
}

function ms_is_vip_product(int $product_id): bool {
    return get_post_meta($product_id, '_ms_kind', true) === 'vip';
}

add_action('woocommerce_order_status_completed', function ($order_id) {
    $order = wc_get_order($order_id);
    $user = $order ? (int)$order->get_user_id() : 0;
    if (!$user) { return; }
    $a = ms_access_get($user);
    foreach ($order->get_items() as $item) {
        $pid = (int)$item->get_product_id();
        $vip = ms_is_vip_product($pid);
        foreach (ms_courses_for_product($pid) as $cid) {
            $r = $a[$cid] ?? ['own_until' => 0, 'vip' => false];
            if ($vip) { $r['vip'] = true; }
            else { $days = get_post_meta($pid, '_ms_kind', true) === 'offer' ? MS_OFFER_DAYS : MS_OWN_DAYS; $r['own_until'] = max((int)$r['own_until'], time() + $days * DAY_IN_SECONDS); }
            $a[$cid] = $r;
            ms_enroll($cid, $user, (int)$order_id);
        }
    }
    ms_access_set($user, $a);
}, 30);

/** Does this person still have another active VIP subscription? */
function ms_user_has_active_vip(int $user, int $except = 0): bool {
    if (!function_exists('wc_get_orders')) { return false; }
    $subs = wc_get_orders(['type' => 'fsb_subscription', 'customer_id' => $user, 'status' => ['wc-active', 'wc-pending-cancel', 'active', 'pending-cancel'], 'limit' => -1]);
    foreach ($subs as $sub) {
        if ((int)$sub->get_id() === $except) { continue; }
        if (!is_object($sub) || $sub->get_type() !== 'fsb_subscription' || !$sub->has_status(['active', 'pending-cancel'])) { continue; }
        foreach ($sub->get_items() as $it) { if (ms_is_vip_product((int)$it->get_product_id())) { return true; } }
    }
    return false;
}

/* VIP subscription changes: renewed/reactivated -> open; ended/on hold -> close VIP tools (own purchases stay). */
add_action('fsub/subscription/status/updated', 'ms_on_sub_status', 20, 3);
function ms_on_sub_status($subscription, $new_status = '', $previous = null): void {
    if (!is_object($subscription) || !method_exists($subscription, 'get_customer_id')) { return; }
    $user = (int)$subscription->get_customer_id();
    if (!$user) { return; }
    $is_vip = false;
    foreach ($subscription->get_items() as $it) { if (ms_is_vip_product((int)$it->get_product_id())) { $is_vip = true; break; } }
    if (!$is_vip) { return; }
    $a = ms_access_get($user);
    if (in_array($new_status, ['active', 'pending-cancel'], true)) {
        foreach (ms_courses_for_product((int)wc_get_product_id_by_sku('vip-m')) as $cid) {
            $r = $a[$cid] ?? ['own_until' => 0, 'vip' => false];
            $r['vip'] = true; $a[$cid] = $r;
            ms_enroll($cid, $user);
        }
        ms_access_set($user, $a);
        return;
    }
    if (in_array($new_status, ['cancelled', 'expired', 'on-hold'], true) && !ms_user_has_active_vip($user, (int)$subscription->get_id())) {
        foreach ($a as $cid => $r) { $a[$cid]['vip'] = false; }
        ms_access_set($user, $a);
        ms_access_sweep($user);
    }
}

/* Daily: close tools whose 90 days have passed. */
add_action('init', function () {
    if (!wp_next_scheduled('ms_access_daily')) { wp_schedule_event(time() + HOUR_IN_SECONDS, 'daily', 'ms_access_daily'); }
});
add_action('ms_access_daily', function () {
    foreach (get_users(['meta_key' => '_ms_access', 'fields' => 'ID', 'number' => -1]) as $uid) { ms_access_sweep((int)$uid); }
});

/* A course page opens only for people who bought it; everyone else sees the tool's own page. */
add_action('template_redirect', function () {
    if (!is_singular('courses') || current_user_can('edit_posts')) { return; }
    $cid = get_queried_object_id();
    $uid = get_current_user_id();
    if ($uid && function_exists('tutor_utils') && tutor_utils()->is_enrolled($cid, $uid)) { return; }
    $pid = (int)get_post_meta($cid, '_tutor_course_product_id', true);
    if ($pid) { wp_safe_redirect(get_permalink($pid), 302); exit; }
});

/* ---------------------------------------------------------------- fixed EGP prices for VIP subscriptions too */
add_filter('wc_price_based_country_product_types_overriden', function ($types) { $types[] = 'fsb-subscription'; return $types; });
add_filter('wc_price_based_country_third_party_product_types', function ($types) { $types['fsb-subscription'] = 'Flexible Subscriptions'; return $types; });

/* ---------------------------------------------------------------- admin-only status check: /wp-admin/?ms_diag=1 */
add_action('admin_init', function () {
    if (empty($_GET['ms_diag']) || !current_user_can('manage_options')) { return; }
    $out = ['setup' => get_option('ms_setup_version'), 'gateways' => []];
    foreach (WC()->payment_gateways()->payment_gateways() as $id => $g) {
        $out['gateways'][$id] = ['enabled' => $g->enabled, 'subscriptions' => $g->supports('subscriptions'), 'title' => $g->get_title()];
    }
    $out['courses'] = count(get_posts(['post_type' => 'courses', 'numberposts' => -1, 'fields' => 'ids']));
    $out['monetize_by'] = (get_option('tutor_option') ?: [])['monetize_by'] ?? null;
    $out['email_preview'] = wp_nonce_url(admin_url('?preview_woocommerce_mail=true'), 'preview-mail');
    wp_send_json($out);
});

/* ---------------------------------------------------------------- admin-only self-test of access rules: /wp-admin/?ms_access_test=1 */
function ms_test_cleanup(): array {
    require_once ABSPATH . 'wp-admin/includes/user.php';
    $n = 0;
    foreach (get_users(['search' => 'ms_test_*', 'search_columns' => ['user_login'], 'fields' => 'ID']) as $uid) {
        foreach (wc_get_orders(['customer_id' => (int)$uid, 'limit' => -1, 'type' => 'shop_order']) as $o) { $o->delete(true); }
        if (function_exists('wc_get_orders')) { foreach (wc_get_orders(['customer_id' => (int)$uid, 'limit' => -1, 'type' => 'fsb_subscription']) as $o) { $o->delete(true); } }
        foreach (get_posts(['post_type' => 'tutor_enrolled', 'author' => (int)$uid, 'post_status' => 'any', 'numberposts' => -1, 'fields' => 'ids']) as $e) { wp_delete_post($e, true); }
        wp_delete_user((int)$uid); $n++;
    }
    return ['removed test users' => $n];
}
add_action('admin_init', function () {
    if (empty($_GET['ms_access_test']) || !current_user_can('manage_options')) { return; }
    $log = [ms_test_cleanup()];
    if ($_GET['ms_access_test'] === 'clean') { wp_send_json($log); }
    try {
        $uid = wp_create_user('ms_test_' . wp_generate_password(6, false), wp_generate_password(20), 'ms-test-' . time() . '@example.invalid');
        if (is_wp_error($uid)) { throw new Exception($uid->get_error_message()); }
        $mk = function (string $sku) use ($uid) {
            $o = wc_create_order(['customer_id' => $uid]);
            $o->add_product(wc_get_product(wc_get_product_id_by_sku($sku)), 1);
            $o->calculate_totals(); $o->save();
            $o->update_status('completed');
            return $o;
        };
        $open = function () use ($uid) { global $wpdb; return array_map('intval', $wpdb->get_col($wpdb->prepare("SELECT DISTINCT post_parent FROM {$wpdb->posts} WHERE post_type='tutor_enrolled' AND post_author=%d AND post_status='completed'", $uid))); };
        $count = function () use ($open) { return count($open()); };
        $has = function ($cid) use ($open) { return in_array($cid, $open(), true) ? 'yes' : 'no'; };
        $attach = ms_course_for('attach'); $course = ms_course_for('ain-sahia');
        $mk('attach');
        $log[] = 'after buying attach: enrolled=' . $count() . ' attach=' . $has($attach);
        $o2 = $mk('vip-m');
        $log[] = 'after VIP: enrolled=' . $count() . ' (course not in VIP enrolled: ' . $has($course) . ')';
        $log[] = 'other active VIP found: ' . (ms_user_has_active_vip($uid, (int)$o2->get_id()) ? 'yes' : 'no');
        ms_on_sub_status($o2, 'cancelled', 'active');
        $log[] = 'after VIP cancelled: enrolled=' . $count() . ' attach kept=' . $has($attach);
        $a = ms_access_get($uid); foreach ($a as $c => $r) { $a[$c]['own_until'] = time() - 10; } ms_access_set($uid, $a); ms_access_sweep($uid);
        $log[] = 'after access period passed: enrolled=' . $count();
        $mk('vip-m');
        $log[] = 'after new VIP: enrolled=' . $count();
    } catch (\Throwable $e) {
        $log[] = 'ERROR ' . $e->getMessage() . ' @ ' . basename($e->getFile()) . ':' . $e->getLine();
    }
    $log[] = ms_test_cleanup();
    wp_send_json($log);
});

/* ---------------------------------------------------------------- lessons from lessons.json (Bunny Stream videos)
   {"_library": 811029, "<tool sku>": [{"title": "...", "video": "<bunny guid>", "length": "m:ss"}]} */
function ms_setup_lessons(): void {
    if (!post_type_exists('lesson') || !post_type_exists('topics')) { return; }
    $all = ms_data('lessons.json');
    $lib = (int)($all['_library'] ?? 0);
    foreach ($all as $sku => $list) {
        if ($sku === '_library' || !is_array($list)) { continue; }
        $cid = ms_course_for($sku);
        if (!$cid) { continue; }
        $topic = get_posts(['post_type' => 'topics', 'post_parent' => $cid, 'post_status' => 'any', 'numberposts' => 1, 'fields' => 'ids']);
        $tid = $topic ? (int)$topic[0] : wp_insert_post(['post_type' => 'topics', 'post_parent' => $cid, 'post_status' => 'publish', 'post_title' => 'المحتوى', 'menu_order' => 1]);
        foreach (array_values($list) as $i => $l) {
            $found = get_posts(['post_type' => 'lesson', 'post_status' => 'any', 'meta_key' => '_ms_video', 'meta_value' => $l['video'], 'numberposts' => 1, 'fields' => 'ids']);
            $post = ['post_type' => 'lesson', 'post_parent' => $tid, 'post_status' => 'publish', 'post_title' => $l['title'], 'menu_order' => $i + 1];
            if ($found) { $post['ID'] = (int)$found[0]; $lid = wp_update_post($post); } else { $lid = wp_insert_post($post); }
            if (!$lid || is_wp_error($lid)) { continue; }
            [$m, $s] = array_pad(explode(':', $l['length'] ?? '0:00'), 2, '0');
            update_post_meta($lid, '_ms_video', $l['video']);
            update_post_meta($lid, '_tutor_course_id_for_lesson', $cid);
            update_post_meta($lid, '_video', [
                'source' => 'bunnynet',
                'source_bunnynet' => "https://iframe.mediadelivery.net/embed/{$lib}/{$l['video']}",
                'runtime' => ['hours' => '00', 'minutes' => str_pad((string)(int)$m, 2, '0', STR_PAD_LEFT), 'seconds' => str_pad((string)(int)$s, 2, '0', STR_PAD_LEFT)],
            ]);
        }
    }
}

/* ---------------------------------------------------------------- "coming soon" tools can't be bought */
function ms_soon_skus(): array {
    static $s = null;
    if ($s === null) { $s = []; foreach (ms_data('products.json') as $p) { if (!empty($p['soon'])) { $s[] = $p['sku']; } } }
    return $s;
}
add_filter('woocommerce_is_purchasable', function ($ok, $product) {
    $sku = $product ? $product->get_sku() : '';
    return ($sku && in_array($sku, ms_soon_skus(), true)) ? false : $ok;
}, 20, 2);

/* ---------------------------------------------------------------- checkout with a required "I agree" checkbox (Paymob: refund policy accepted before paying) */
function ms_classic_checkout(): void {
    foreach (['checkout' => '[woocommerce_checkout]', 'cart' => '[woocommerce_cart]'] as $key => $code) {
        $id = wc_get_page_id($key);
        if ($id > 0) { wp_update_post(['ID' => $id, 'post_content' => '<!-- wp:shortcode -->' . $code . '<!-- /wp:shortcode -->']); }
    }
}
add_filter('woocommerce_get_terms_and_conditions_checkbox_text', function () {
    $t = get_permalink((int)get_option('woocommerce_terms_page_id'));
    $r = home_url('/refund/');
    return 'قرأت وأوافق على <a href="' . esc_url($t) . '" target="_blank">الشروط والأحكام</a> و<a href="' . esc_url($r) . '" target="_blank">سياسة الاسترداد والإلغاء</a>';
});
add_filter('woocommerce_checkout_required_field_notice', function ($n) { return $n; });
add_filter('woocommerce_get_privacy_policy_text', function ($text, $type) { return $type === 'checkout' ? '' : $text; }, 10, 2);

/* New sign-up -> short email to info@ (same as the old site's sign-up notice). */
add_action('woocommerce_created_customer', function ($customer_id) {
    $u = get_userdata($customer_id); if (!$u) { return; }
    $count = count_users()['avail_roles']['customer'] ?? 0;
    $body = "تسجيل جديد في الموقع\n\nالبريد: {$u->user_email}\nالاسم: " . trim($u->first_name . ' ' . $u->last_name) . "\nإجمالي العملاء المسجلين: {$count}\n";
    wp_mail('info@mervatsror.com', 'تسجيل جديد: ' . $u->user_email, $body, ['Reply-To: ' . $u->user_email]);
});

/* Customers choose any password they like: no strength meter, no "weak password" block. */
add_filter('woocommerce_min_password_strength', function () { return 0; });
add_action('wp_enqueue_scripts', function () {
    if (!is_admin()) { wp_dequeue_script('wc-password-strength-meter'); wp_deregister_script('wc-password-strength-meter'); }
}, 100);
add_action('login_enqueue_scripts', function () {
    wp_dequeue_script('user-profile'); wp_dequeue_script('password-strength-meter');
    echo '<style>.pw-weak{display:none!important}#pass-strength-result{display:none!important}</style>';
});
add_action('login_footer', function () {
    echo '<script>(function(){var c=document.getElementById("pw-weak");if(c){c.checked=true;}var b=document.getElementById("wp-submit");if(b){b.disabled=false;}})();</script>';
});

/* VIP subscriptions: allow PayPal (USD) and transfer (EGP). Renewals are paid by the customer from the renewal email/link
   until PayPal vaulting (automatic renewals) is approved on the PayPal account. */
add_filter('fsub/payment/manual_renewal/enabled', '__return_true');

/* PayPal Payments asks WooCommerce Subscriptions whether manual renewals are accepted (WCS_Manual_Renewal_Manager).
   Flexible Subscriptions does not provide that class, so PayPal hid itself for VIP. Provide it, so a VIP checkout is
   charged as a normal PayPal payment and each renewal is paid from the renewal email/link. */
add_action('plugins_loaded', function () {
    if (class_exists('WCS_Manual_Renewal_Manager', false)) { return; }
    if (!function_exists('is_plugin_active')) { require_once ABSPATH . 'wp-admin/includes/plugin.php'; }
    if (is_plugin_active('woocommerce-subscriptions/woocommerce-subscriptions.php')) { return; }
    if (!class_exists('WCS_Manual_Renewal_Manager', false)) {
        eval('class WCS_Manual_Renewal_Manager { public static function is_manual_renewal_enabled() { return true; } public static function is_manual_renewal_required() { return false; } }');
    }
}, 1);

/* Arabic wording for the subscription plugin's checkout texts. */
add_filter('gettext', function ($t, $text, $domain) {
    if ($domain !== 'flexible-subscriptions' && $domain !== 'woocommerce-paypal-payments') { return $t; }
    static $ar = [
        'Sign up now' => 'اشترك الآن', 'Total due today' => 'المطلوب اليوم', 'Details' => 'التفاصيل',
        'Recurring total every month' => 'يتجدد كل شهر', 'Recurring total every year' => 'يتجدد كل سنة',
        'Recurring total' => 'قيمة التجديد', 'Recurring totals' => 'قيمة التجديد', 'every month' => 'كل شهر', 'every year' => 'كل سنة',
        'month' => 'شهر', 'months' => 'أشهر', 'year' => 'سنة', 'years' => 'سنوات', 'Starting: %s' => 'يبدأ: %s', 'Starting' => 'يبدأ',
        'Pay via PayPal.' => 'ادفع عبر PayPal.', 'Pay via PayPal' => 'ادفع عبر PayPal',
    ];
    return $ar[$text] ?? $t;
}, 20, 3);
add_filter('ngettext', function ($t, $single, $plural, $n, $domain) {
    if ($domain !== 'flexible-subscriptions') { return $t; }
    $map = ['every %s month' => 'كل %s شهر', 'every %s months' => 'كل %s أشهر', 'every %s year' => 'كل %s سنة', 'every %s years' => 'كل %s سنوات',
            'every month' => 'كل شهر', 'every %d months' => 'كل %d أشهر', 'every year' => 'كل سنة', 'every %d years' => 'كل %d سنوات'];
    $key = $n == 1 ? $single : $plural;
    return $map[$key] ?? $t;
}, 20, 5);
add_filter('gettext', function ($t, $text, $domain) {
    if ($domain !== 'flexible-subscriptions') { return $t; }
    $m = ['%1$s every %2$s' => '%1$s كل %2$s', 'From %1$s every %2$s' => 'من %1$s كل %2$s', 'Recurring total every %s' => 'يتجدد كل %s',
          'Recurring total (every %s)' => 'قيمة التجديد (كل %s)', '%s due today' => '%s المطلوب اليوم', 'day' => 'يوم', 'week' => 'أسبوع'];
    return $m[$text] ?? $t;
}, 21, 3);
add_filter('ngettext', function ($t, $single, $plural, $n, $domain) {
    if ($domain !== 'flexible-subscriptions') { return $t; }
    $m = ['%d month' => ['%d شهر', '%d أشهر'], '%d year' => ['%d سنة', '%d سنوات'], '%d week' => ['%d أسبوع', '%d أسابيع'], '%d day' => ['%d يوم', '%d أيام']];
    return isset($m[$single]) ? ($n == 1 ? $m[$single][0] : $m[$single][1]) : $t;
}, 21, 5);
add_filter('ngettext_with_context', function ($t, $single, $plural, $n, $ctx, $domain) {
    if ($domain !== 'flexible-subscriptions') { return $t; }
    $m = ['month' => ['شهر', '%s أشهر'], 'year' => ['سنة', '%s سنوات'], 'week' => ['أسبوع', '%s أسابيع'], 'day' => ['يوم', '%s أيام']];
    return isset($m[$single]) ? ($n == 1 ? $m[$single][0] : $m[$single][1]) : $t;
}, 21, 6);
