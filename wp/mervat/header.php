<?php if (!defined('ABSPATH')) { exit; }
$ms_part = ms_current_part();
$ms_meta = ms_meta();
$ms_bare = $ms_part && !empty($ms_meta[$ms_part]['bare']);
?><!doctype html>
<html <?php language_attributes(); ?> dir="rtl">
<head>
<meta charset="<?php bloginfo('charset'); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<?php ms_part('_sprite'); ?>
<?php if (!$ms_bare) { ms_part($ms_part === 'front' ? '_header-hero' : '_header'); } ?>
<main id="main">
