<?php
// Fallback for anything without its own template (archives, search, WooCommerce lists).
if (!defined('ABSPATH')) { exit; }
get_header(); ?>
<section class="wp-hero"><div class="wrap"><h1 class="title"><?php echo esc_html(wp_get_document_title()); ?></h1></div></section>
<section class="band wp-body"><div class="wrap wp-content">
<?php
if (function_exists('is_woocommerce') && is_woocommerce()) {
    woocommerce_content();
} elseif (have_posts()) {
    while (have_posts()) { the_post(); echo '<article><h2><a href="' . esc_url(get_permalink()) . '">' . esc_html(get_the_title()) . '</a></h2>'; the_excerpt(); echo '</article>'; }
} else {
    echo '<p>لا يوجد محتوى هنا.</p>';
}
?>
</div></section>
<?php get_footer();
