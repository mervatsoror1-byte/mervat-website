<?php
// WordPress/WooCommerce pages (cart, checkout, my account, anything added later) inside the site's frame.
if (!defined('ABSPATH')) { exit; }
get_header(); ?>
<section class="wp-hero"><div class="wrap"><h1 class="title"><?php echo esc_html(get_the_title()); ?></h1></div></section>
<section class="band wp-body"><div class="wrap wp-content">
<?php while (have_posts()) { the_post(); the_content(); } ?>
</div></section>
<?php get_footer();
