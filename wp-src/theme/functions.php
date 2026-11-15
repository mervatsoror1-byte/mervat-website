<?php
/**
 * Mervat Soror theme. Design lives in parts/*.html (generated from the static site);
 * WooCommerce handles cart, checkout and accounts; wp-bridge.js connects the two.
 */
if (!defined('ABSPATH')) { exit; }

const MS_PRODUCT_BASE = 'tools';

add_action('after_setup_theme', function () {
    add_theme_support('title-tag');
    add_theme_support('woocommerce');
    add_theme_support('html5', ['search-form', 'gallery', 'caption', 'style', 'script']);
    load_theme_textdomain('mervat');
});

function ms_meta(): array {
    static $m = null;
    if ($m === null) { $m = json_decode((string)file_get_contents(get_template_directory() . '/parts/_meta.json'), true) ?: []; }
    return $m;
}

/** Print a design part with the real addresses filled in. */
function ms_part(string $name): void {
    $file = get_template_directory() . '/parts/' . basename($name) . '.html';
    if (!is_file($file)) { return; }
    echo str_replace(['{{H}}', '{{T}}'], [untrailingslashit(home_url()), get_template_directory_uri()], (string)file_get_contents($file));
}

/** Which design part belongs to the current request (or '' for WooCommerce/other pages). */
function ms_current_part(): string {
    $meta = ms_meta();
    if (is_front_page()) { return 'front'; }
    if (function_exists('is_product') && is_product()) {
        $slug = get_post_field('post_name', get_queried_object_id());
        return (isset($meta[$slug]) && $meta[$slug]['type'] === 'product') ? $slug : '';
    }
    if (is_page()) {
        $slug = get_post_field('post_name', get_queried_object_id());
        return (isset($meta[$slug]) && $meta[$slug]['type'] === 'page') ? $slug : '';
    }
    if (is_404()) { return '404'; }
    return '';
}

add_action('wp_enqueue_scripts', function () {
    $t = get_template_directory_uri();
    $v = wp_get_theme()->get('Version') . '.' . (string)@filemtime(get_template_directory() . '/assets/css/site.css');
    wp_enqueue_style('ms-fonts', 'https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&family=Almarai:wght@400;700&family=El+Messiri:wght@500;600;700&family=Amiri:ital@0;1&family=Great+Vibes&family=Noto+Naskh+Arabic:wght@500;700&family=Cormorant+Garamond:wght@300&display=swap', [], null);
    wp_enqueue_style('ms-site', $t . '/assets/css/site.css', [], $v);
    wp_enqueue_style('ms-wp', $t . '/assets/css/wp.css', ['ms-site'], $v);

    wp_enqueue_script('ms-data', $t . '/assets/js/data.js', [], $v, true);
    wp_enqueue_script('ms-site', $t . '/assets/js/site.js', ['ms-data'], $v, true);
    wp_enqueue_script('ms-bridge', $t . '/assets/js/wp-bridge.js', ['ms-site'], $v, true);

    $ids = []; $inCart = [];
    if (function_exists('wc_get_product_id_by_sku')) {
        foreach (json_decode((string)file_get_contents(WP_PLUGIN_DIR . '/mervat-setup/products.json'), true) ?: [] as $p) {
            $id = wc_get_product_id_by_sku($p['sku']);
            if ($id) { $ids[$p['sku']] = $id; }
        }
        if (WC()->cart) {
            foreach (WC()->cart->get_cart() as $item) {
                $sku = get_post_meta($item['product_id'], '_sku', true);
                if ($sku) { $inCart[] = $sku; }
            }
        }
    }
    $cur = function_exists('get_woocommerce_currency') ? get_woocommerce_currency() : 'USD';
    $user = wp_get_current_user();
    // Data and links must be ready before site.js runs.
    wp_add_inline_script('ms-data', 'window.SITE_DATA=JSON.parse(JSON.stringify(window.SITE_DATA).split("{{T}}").join(' . wp_json_encode($t) . '));', 'after');
    wp_add_inline_script('ms-site', 'window.MS_WP=' . wp_json_encode([
        'home' => untrailingslashit(home_url()),
        'theme' => $t,
        'currency' => $cur,
        'ids' => $ids,
        'inCart' => $inCart,
        'cartCount' => (function_exists('WC') && WC()->cart) ? WC()->cart->get_cart_contents_count() : 0,
        'cart' => function_exists('wc_get_cart_url') ? wc_get_cart_url() : home_url('/cart/'),
        'checkout' => function_exists('wc_get_checkout_url') ? wc_get_checkout_url() : home_url('/checkout/'),
        'account' => function_exists('wc_get_page_permalink') ? wc_get_page_permalink('myaccount') : home_url('/my-account/'),
        'ajax' => home_url('/?wc-ajax=add_to_cart'),
        'user' => $user->ID ? ['name' => $user->display_name, 'email' => $user->user_email] : null,
    ]) . ';(function(){try{var k="ms_state_v1",s=JSON.parse(localStorage.getItem(k)||"{}");s.region=MS_WP.currency==="EGP"?"eg":"intl";s.user=MS_WP.user?Object.assign({since:new Date().toISOString()},MS_WP.user):null;s.cart=(MS_WP.inCart||[]).map(function(id){return{id:id}});localStorage.setItem(k,JSON.stringify(s));}catch(e){}})();', 'before');
}, 20);

// Keep the page lean: WordPress block styles are not used by this design.
add_action('wp_enqueue_scripts', function () {
    if (ms_current_part()) {
        wp_dequeue_style('wp-block-library');
        wp_dequeue_style('wp-block-library-theme');
        wp_dequeue_style('global-styles');
        wp_dequeue_style('classic-theme-styles');
    }
}, 100);
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');

add_action('wp_head', function () {
    $meta = ms_meta(); $part = ms_current_part();
    echo '<meta name="theme-color" content="#FDFAF5">' . "\n";
    echo '<link rel="icon" href="' . esc_url(get_template_directory_uri() . '/assets/brand/favicon-32.png') . '" sizes="32x32">' . "\n";
    echo '<link rel="apple-touch-icon" href="' . esc_url(get_template_directory_uri() . '/assets/brand/favicon-192.png') . '">' . "\n";
    if ($part && isset($meta[$part])) {
        $m = $meta[$part];
        if ($m['desc']) { echo '<meta name="description" content="' . esc_attr($m['desc']) . '">' . "\n"; }
        echo '<meta property="og:title" content="' . esc_attr(wp_get_document_title()) . '"><meta property="og:description" content="' . esc_attr($m['desc']) . '">';
        echo '<meta property="og:image" content="' . esc_url(get_template_directory_uri() . '/assets/img/og-share.jpg') . '"><meta property="og:locale" content="ar_AR"><meta name="twitter:card" content="summary_large_image">' . "\n";
        if (!empty($m['noindex'])) { echo '<meta name="robots" content="noindex,nofollow">' . "\n"; }
        if (!empty($m['ld'])) { echo str_replace('{{H}}', untrailingslashit(home_url()), $m['ld']) . "\n"; }
    }
}, 1);

// Titles come from the design's own page titles.
add_filter('pre_get_document_title', function ($title) {
    $meta = ms_meta(); $part = ms_current_part();
    if ($part === 'front') { return 'د. مرفت سرور | مدربة وعي وتشافي معتمدة من ICF'; }
    if ($part && !empty($meta[$part]['title'])) { return $meta[$part]['title'] . ' | د. مرفت سرور'; }
    return $title;
});

// Design pages use their own template; everything else (cart, checkout, account) uses page.php.
add_filter('template_include', function ($template) {
    $part = ms_current_part();
    if ($part) { return get_template_directory() . '/design-page.php'; }
    return $template;
}, 99);

// Products that live on a shared page (VIP plans, sessions, bundles, offers) open that page instead.
add_action('template_redirect', function () {
    if (function_exists('is_product') && is_product()) {
        $to = get_post_meta(get_queried_object_id(), '_ms_redirect', true);
        if ($to) { wp_safe_redirect(str_replace('{{H}}', untrailingslashit(home_url()), $to), 302); exit; }
    }
    if (function_exists('is_shop') && is_shop()) { wp_safe_redirect(home_url('/library/'), 302); exit; }
});

// Arabic currency labels.
add_filter('woocommerce_currency_symbol', function ($symbol, $currency) {
    return $currency === 'EGP' ? 'ج.م' : ($currency === 'USD' ? '$' : $symbol);
}, 10, 2);

// Cart count in the header updates after AJAX adds.
add_filter('woocommerce_add_to_cart_fragments', function ($f) {
    $n = WC()->cart ? WC()->cart->get_cart_contents_count() : 0;
    $f['ms_count'] = $n;
    return $f;
});
