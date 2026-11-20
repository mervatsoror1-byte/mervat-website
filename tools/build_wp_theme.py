#!/usr/bin/env python3
"""Turn the static site (site/) into a WordPress theme (wp/mervat) and a setup plugin (wp/mervat-setup).

The static pages stay the single source of design: each page's <main> becomes a "part" the theme prints,
links are mapped to WordPress addresses, and buy/cart buttons go to WooCommerce through wp-bridge.js.
Run: python3 tools/build_wp_theme.py   (it rebuilds site/ first)
"""
import json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_site as B  # noqa: E402

SITE = ROOT / "site"
WP = ROOT / "wp"
THEME = WP / "mervat"
PLUGIN = WP / "mervat-setup"
WPSRC = ROOT / "wp-src"          # hand-written PHP/JS/CSS for the theme and plugin

# pages that WooCommerce (or later Tutor) owns
WOO = {"cart": "cart/", "checkout": "checkout/", "account": "my-account/", "login": "my-account/", "register": "my-account/",
       "forgot": "my-account/lost-password/", "learn": "my-account/", "reader": "my-account/", "success": "my-account/orders/",
       "failed": "checkout/"}
PRODUCT_BASE = "tools"


def load_data():
    raw = (SITE / "assets/js/data.js").read_text(encoding="utf-8")
    return json.loads(raw[raw.index("=") + 1:].rstrip().rstrip(";"))


def classify(data):
    """Return (product pages by stem -> product id, plain pages set)."""
    product_pages = {}
    shared = {"vip.html", "sessions.html", "marriage.html", "bundles.html", "books.html", "library.html", "index.html"}
    for p in data["products"]:
        page = p.get("page") or ""
        if page and page.endswith(".html") and page not in shared and not page.startswith("lp-"):
            product_pages[page[:-5]] = p["id"]
    pages = set()
    for f in SITE.glob("*.html"):
        stem = f.stem
        if stem.startswith("_") or stem == "index" or stem in WOO or stem in product_pages:
            continue
        pages.add(stem)
    return product_pages, pages


def url_for(href, product_pages, pages):
    """Map a static href to a placeholder WordPress URL ({{H}} = home)."""
    if not href or href.startswith(("http:", "https:", "mailto:", "tel:", "#", "{{", "javascript:", "data:")):
        return href
    if href.startswith("assets/"):
        return "{{T}}/" + href
    m = re.match(r"^([a-z0-9-]+)\.html([?#].*)?$", href)
    if not m:
        return href
    stem, rest = m.group(1), m.group(2) or ""
    if stem == "index":
        return "{{H}}/" + rest
    if stem in product_pages:
        return "{{H}}/%s/%s/%s" % (PRODUCT_BASE, stem, rest)
    if stem in WOO:
        return "{{H}}/" + WOO[stem] + rest
    if stem in pages:
        return "{{H}}/%s/%s" % (stem, rest)
    return href


def rewrite_html(html, product_pages, pages):
    html = re.sub(r'(href|src|poster)="([^"]*)"', lambda m: '%s="%s"' % (m.group(1), url_for(m.group(2), product_pages, pages)), html)
    html = re.sub(r"url\((['\"]?)assets/", r"url(\1{{T}}/assets/", html)
    html = html.replace('srcset="assets/', 'srcset="{{T}}/assets/')
    return html


def extract(path):
    doc = path.read_text(encoding="utf-8")
    head = re.search(r"<head>(.*?)</head>", doc, re.S).group(1)
    body = re.search(r"<body>(.*)</body>", doc, re.S).group(1)
    title = re.search(r"<title>(.*?)</title>", head, re.S).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', head)
    ld = re.findall(r'<script type="application/ld\+json">.*?</script>', head, re.S)
    main = re.search(r'<main id="main">(.*)</main>', body, re.S)
    before = body[:main.start()] if main else ""
    after = body[main.end():] if main else ""
    after = re.sub(r'<script src="assets/js/[^"]+"></script>', "", after)
    return {"title": title, "desc": desc.group(1) if desc else "", "ld": "".join(ld), "main": main.group(1) if main else body,
            "before": before, "after": after, "noindex": 'name="robots" content="noindex' in head}


def main():
    B.build()
    data = load_data()
    product_pages, pages = classify(data)
    if THEME.exists():
        shutil.rmtree(THEME)
    if PLUGIN.exists():
        shutil.rmtree(PLUGIN)
    (THEME / "parts").mkdir(parents=True)

    # assets (images, css, js) — same files as the static site
    shutil.copytree(SITE / "assets", THEME / "assets")
    rw = lambda s: rewrite_html(s, product_pages, pages)

    # header variants + footer, taken from real pages
    plain = extract(SITE / "about.html")
    hero = extract(SITE / "index.html")
    sprite_end = plain["before"].index("</svg>") + len("</svg>")
    (THEME / "parts/_sprite.html").write_text(plain["before"][:sprite_end], encoding="utf-8")
    nocur = lambda h: re.sub(r'\s*aria-current=page', '', h).replace(' data-current=1', '')
    (THEME / "parts/_header.html").write_text(nocur(rw(plain["before"][sprite_end:])), encoding="utf-8")
    (THEME / "parts/_header-hero.html").write_text(rw(hero["before"][hero["before"].index("</svg>") + 6:]), encoding="utf-8")
    (THEME / "parts/_footer.html").write_text(rw(plain["after"]), encoding="utf-8")

    meta = {}
    for f in sorted(SITE.glob("*.html")):
        stem = f.stem
        if stem.startswith("_") or stem in WOO:
            continue
        info = extract(f)
        name = "front" if stem == "index" else stem
        (THEME / "parts" / (name + ".html")).write_text(rw(info["main"]), encoding="utf-8")
        bare = "<header class=\"site-header" not in info["before"]
        meta[name] = {"title": re.sub(r"\s*\|.*$", "", info["title"]), "desc": info["desc"], "ld": info["ld"],
                      "noindex": info["noindex"], "bare": bare,
                      "type": "front" if stem == "index" else ("product" if stem in product_pages else "page"),
                      "sku": product_pages.get(stem, "")}
    (THEME / "parts/_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    # data.js with WordPress links
    for p in data["products"]:
        for k in ("page", "learn"):
            if p.get(k):
                p[k] = url_for(p[k], product_pages, pages)
        for k in ("img", "cover", "coverLg"):
            if isinstance(p.get(k), str) and p[k].startswith("assets/"):
                p[k] = "{{T}}/" + p[k]
    js = "window.SITE_DATA=" + json.dumps(data, ensure_ascii=False).replace('"assets/', '"{{T}}/assets/') + ";\n"
    (THEME / "assets/js/data.js").write_text(js, encoding="utf-8")

    # site.js: hard-coded page jumps -> WordPress addresses
    sj = (THEME / "assets/js/site.js").read_text(encoding="utf-8")
    sj = re.sub(r'"([a-z0-9-]+\.html(?:#[a-z-]*)?)"', lambda m: '"%s"' % url_for(m.group(1), product_pages, pages), sj)
    a = '"assets/brand/logo-icon-gold.webp"'
    assert a in sj
    sj = sj.replace(a, '(window.MS_WP ? MS_WP.theme + "/" : "") + "assets/brand/logo-icon-gold.webp"')
    # buying is WooCommerce's job in WordPress: hand these over to wp-bridge.js
    for fn in ("function startBuy(id, extra){", "function addToCart(id, extra){"):
        assert fn in sj, fn
        name = fn.split()[1].split("(")[0]
        sj = sj.replace(fn, fn + " if (window.MS_WP && window.%s && window.%s !== %s) return window.%s(id, extra);" % (name, name, name, name), 1)
    # voice reviews API lives at the site root
    sj = sj.replace('const VAPI = "api/voice.php";', 'const VAPI = (window.MS_WP ? MS_WP.home + "/" : "") + "api/voice.php";')
    sj = sj.replace('fetch("api/order.php"', 'fetch((window.MS_WP ? MS_WP.home + "/" : "") + "api/order.php"')
    (THEME / "assets/js/site.js").write_text(sj, encoding="utf-8")

    # hand-written theme + plugin files
    shutil.copytree(WPSRC / "theme", THEME, dirs_exist_ok=True)
    shutil.copytree(WPSRC / "plugin", PLUGIN)

    # products for the setup plugin
    prods = []
    page_of = {v: k for k, v in product_pages.items()}
    for p in data["products"]:
        own = page_of.get(p["id"])
        target = None
        if not own:
            pg = (p.get("page") or "")
            target = url_for(pg, product_pages, pages) if pg else None
        prods.append({"sku": p["id"], "name": p["title"], "slug": own or ("ms-" + p["id"]), "eg": p.get("eg"), "us": p.get("us"),
                      "kind": p.get("kind"), "short": p.get("short", ""), "img": (p.get("img") or "").replace("{{T}}/", ""),
                      "redirect": target, "grants": p.get("grants"), "vip": bool(p.get("vipIncluded")), "soon": bool(p.get("soon")),
                      "items": next((bd["items"] for bd in data.get("bundles", []) if bd["id"] == p["id"]), [])})
    (PLUGIN / "products.json").write_text(json.dumps(prods, ensure_ascii=False, indent=1), encoding="utf-8")
    (PLUGIN / "pages.json").write_text(json.dumps(sorted(pages | {"front"}), ensure_ascii=False), encoding="utf-8")

    # voice/order PHP API, shared with the static site
    shutil.copytree(SITE / "api", WP / "root/api", dirs_exist_ok=True)
    shutil.copytree(SITE / "admin", WP / "root/admin", dirs_exist_ok=True)
    print("theme:", sum(1 for _ in THEME.rglob("*") if _.is_file()), "files;", len(meta), "parts;", len(prods), "products")


if __name__ == "__main__":
    main()
