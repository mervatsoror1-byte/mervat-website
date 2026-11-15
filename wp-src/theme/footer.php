<?php if (!defined('ABSPATH')) { exit; }
$ms_part = ms_current_part();
$ms_meta = ms_meta();
$ms_bare = $ms_part && !empty($ms_meta[$ms_part]['bare']);
?>
</main>
<?php if (!$ms_bare) { ms_part('_footer'); } ?>
<?php wp_footer(); ?>
</body>
</html>
