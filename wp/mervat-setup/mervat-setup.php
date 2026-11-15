<?php
/**
 * Plugin Name: Mervat Setup
 * Description: Sets up the shop from the site's own data: pages, products with EGP/USD prices, currencies, payments and session dates. Safe to run again; it updates instead of duplicating.
 * Version: 1.0.2
 * Author: Mervat Soror
 * Requires Plugins: woocommerce
 */
if (!defined('ABSPATH')) { exit; }

const MS_SETUP_VERSION = '1.0.2';
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
            update_post_meta($id, '_' . MS_EGYPT_ZONE . '_regular_price', (string)$p['eg']);
            update_post_meta($id, '_' . MS_EGYPT_ZONE . '_sale_price', '');
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
