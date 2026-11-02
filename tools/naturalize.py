"""Photographic finishing for generated portraits: deeper lens blur on background,
gentle de-gloss, warm grade, film grain, soft vignette. Usage: naturalize.py in.webp out.webp"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB'); w, h = im.size
mask = remove(im, session=new_session('birefnet-portrait'), only_mask=True).convert('L')
mask = mask.filter(ImageFilter.GaussianBlur(3))
bg = im.filter(ImageFilter.GaussianBlur(max(w, h) / 180))
out = Image.composite(im, bg, mask)
a = np.asarray(out).astype(np.float32) / 255
# de-gloss: soften highlights, lift shadows slightly
a = np.where(a > 0.8, 0.8 + (a - 0.8) * 0.75, a)
a = a * 0.97 + 0.015
# reduce saturation 8%, warm the image a touch
g = a.mean(axis=2, keepdims=True); a = g + (a - g) * 0.92
a[..., 0] *= 1.015; a[..., 2] *= 0.985
# vignette
yy, xx = np.mgrid[0:h, 0:w]; r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
a *= (1 - 0.10 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None]
# luminance film grain
rng = np.random.default_rng(7); n = rng.normal(0, 0.022, (h, w, 1)).astype(np.float32)
n = np.asarray(Image.fromarray(((n[..., 0] + .5) * 255).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32)[..., None] / 255 - .5
a = np.clip(a + n, 0, 1)
Image.fromarray((a * 255).astype(np.uint8)).save(dst, 'WEBP', quality=88, method=6)
print('ok', dst)
