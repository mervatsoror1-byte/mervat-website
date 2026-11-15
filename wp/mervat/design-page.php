<?php
// A page whose design comes from parts/<slug>.html (home, VIP, sessions, product pages, policies…).
if (!defined('ABSPATH')) { exit; }
get_header();
ms_part(ms_current_part());
get_footer();
