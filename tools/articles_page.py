"""Articles: docs/articles/*.md -> one designed page per article + the «المقالات» listing.

Each .md starts with a title (# …) and a header block that is for SEO only
(suggested link, Google description, search words, byline), then '---', then the article.
On WordPress each article lives at /articles/<slug>/.
"""
import re
from urllib.parse import quote
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs/articles"
# per article: cover image, tag shown on the card, publish date, the tool it leads to
EXTRA = {
    "why-we-see-what-is-missing": dict(cover="ain-sahia", tag="الامتنان", date="2026-11-25"),
    "hardship-and-gift": dict(cover="decode-acceptance", tag="التشافي", date="2026-11-25"),
}
AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def ar_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{str(d).translate(AR)} {MONTHS[m - 1]} {str(y).translate(AR)}"


def load():
    out = []
    for f in sorted(DOCS.glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        head, body = raw.split("\n---\n", 1)
        title = re.search(r"^# (.+)$", head, re.M).group(1).strip()
        field = lambda k: (re.search(r"^\*\*" + k + r":\*\*\s*(.+)$", head, re.M) or [None, ""])[1].strip()
        slug = field("الرابط المقترح").rstrip("/").split("/")[-1]
        words = len(re.findall(r"\w+", body))
        a = dict(slug=slug, title=title, desc=field("الوصف في جوجل"), keywords=field("الكلمات التي يبحث بها الناس"),
                 body=body.strip(), minutes=max(3, round(words / 180)), **EXTRA.get(slug, dict(cover="ain-sahia", tag="الوعي", date="2026-11-25")))
        out.append(a)
    return out


def inline(s, E):
    s = E(s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{link(m.group(2))}">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    return s


def link(u):
    """Absolute site links -> static page names (the WordPress build turns them into real addresses)."""
    m = re.match(r"https?://(?:www\.)?mervatsror\.com/(?:tools/)?([a-z0-9-]+)/?$", u)
    return f"{m.group(1)}.html" if m else u


def md_html(md, E):
    """The small Markdown subset the articles use: ## headings, paragraphs, - lists, ١. lists, **bold**, *em*, links, ---."""
    html, faq = [], []
    in_faq = False
    for block in re.split(r"\n\s*\n", md.strip()):
        lines = [l.rstrip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        first = lines[0]
        if first.startswith("## "):
            h = first[3:].strip()
            in_faq = h == "أسئلة شائعة"
            html.append(f'<h2 id="s{len(html)}">{inline(h, E)}</h2>')
            lines = lines[1:]
            if not lines:
                continue
            first = lines[0]
        if first == "---":
            html.append('<hr class="ar-sep">'); in_faq = False
            continue
        if in_faq and first.startswith("**") and first.endswith("**") and len(lines) > 1:
            q, a = first.strip("*"), " ".join(lines[1:])
            faq.append((q, re.sub(r"\*", "", a)))
            html.append(f'<div class="ar-q"><h3>{inline(q, E)}</h3><p>{inline(a, E)}</p></div>')
            continue
        items = [l for l in lines if l.startswith("- ")]
        nums = [l for l in lines if re.match(r"^[١-٩0-9]+[.)]\s", l)]
        if items and len(items) == len(lines) or (items and not lines[0].startswith("- ") and len(items) == len(lines) - 1):
            lead = [] if lines[0].startswith("- ") else [lines[0]]
            if lead:
                html.append(f"<p>{inline(lead[0], E)}</p>")
            html.append("<ul>" + "".join(f"<li>{inline(l[2:], E)}</li>" for l in items) + "</ul>")
            continue
        if nums and len(nums) == len(lines):
            html.append('<ol class="ar-steps">' + "".join(f"<li>{inline(re.sub(r'^[١-٩0-9]+[.)]\s*', '', l), E)}</li>" for l in nums) + "</ol>")
            continue
        if all(l.startswith("← ") for l in lines[1:]) and len(lines) > 1:
            html.append(f'<div class="ar-next"><p>{inline(lines[0], E)}</p>' + "".join(
                f'<p class="ar-go">{inline(l[2:], E)}</p>' for l in lines[1:]) + "</div>")
            continue
        if len(lines) == 1 and re.match(r"^\*[^*].*\*$", first):
            html.append(f'<p class="ar-note">{inline(first, E)}</p>')
            continue
        html.append("<p>" + "<br>".join(inline(l, E) for l in lines) + "</p>")
    # the "← link" lines become buttons
    out = "\n".join(html)
    out = re.sub(r'<p class="ar-go"><a href="([^"]+)">([^<]+)</a></p>', r'<a class="btn btn-gold ar-btn" href="\1">\2</a>', out)
    return out, faq


def build(g):
    page, E, ic, page_hero, SITE_URL, NAME = g["page"], g["E"], g["ic"], g["page_hero"], g["SITE_URL"], g["NAME"]
    arts = load()
    author = {"@type": "Person", "name": "د. مرفت سرور", "url": SITE_URL + "/about/", "jobTitle": "مدربة وعي وتشافٍ معتمدة من ICF"}
    for i, a in enumerate(arts):
        body, faq = md_html(a["body"], E)
        others = [o for o in arts if o is not a][:2]
        more = "".join(f'<a class="ar-more-i" href="{o["slug"]}.html"><img src="assets/img/covers/{o["cover"]}-sm.webp" alt="" loading="lazy" width="120" height="120"><span><small>{E(o["tag"])}</small><b>{E(o["title"])}</b></span></a>' for o in others)
        url = f'{SITE_URL}/articles/{a["slug"]}/'
        schema = [{"@context": "https://schema.org", "@type": "Article", "headline": a["title"][:110], "description": a["desc"],
                   "inLanguage": "ar", "datePublished": a["date"], "dateModified": a["date"], "author": author,
                   "publisher": {"@type": "Organization", "name": NAME, "logo": {"@type": "ImageObject", "url": SITE_URL + "/wp-content/themes/mervat/assets/brand/favicon-192.png"}},
                   "image": f'{SITE_URL}/wp-content/themes/mervat/assets/img/covers/{a["cover"]}.webp', "mainEntityOfPage": url,
                   "keywords": a["keywords"].replace("، ", ", ")},
                  {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                      {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": SITE_URL + "/"},
                      {"@type": "ListItem", "position": 2, "name": "المقالات", "item": SITE_URL + "/articles/"},
                      {"@type": "ListItem", "position": 3, "name": a["title"]}]}]
        meta = f'<div class="ar-by"><img src="assets/img/mervat-about.webp" alt="" width="56" height="56"><div><b>بقلم د. مرفت سرور</b><span>مدربة وعي وتشافٍ معتمدة من الاتحاد الدولي للتدريب ICF</span><span class="ar-meta">{ic("cal")}{ar_date(a["date"])} · {ic("clock")}{str(a["minutes"]).translate(AR)} دقائق قراءة</span></div></div>'
        page(f'{a["slug"]}.html', a["title"], a["desc"],
             page_hero(a["title"], "", ("المقالات", "articles.html"), (a["tag"], None), eyebrow=E(a["tag"])) + f'''
<section class="band-sm ar-band"><div class="wrap"><article class="ar">
  {meta}
  <figure class="ar-cover"><img src="assets/img/covers/{a["cover"]}.webp" alt="" width="1200" height="1200"></figure>
  <div class="prose ar-body">{body}</div>
  <div class="ar-share"><span>شاركي المقال مع من تحبين</span><a class="btn btn-line btn-sm" href="https://wa.me/?text={quote(a["title"] + " " + url)}" target="_blank" rel="noopener">{ic("chat", "icon icon-sm")}واتساب</a><a class="btn btn-line btn-sm" href="https://www.facebook.com/sharer/sharer.php?u={quote(url, safe="")}" target="_blank" rel="noopener">{ic("user", "icon icon-sm")}فيسبوك</a></div>
  {f'<div class="ar-more"><h2>اقرئي أيضاً</h2>{more}</div>' if more else ''}
</article></div></section>''', active="articles.html", schema=schema)

    cards = "".join(f'''<article class="scard"><a class="sc-img" href="{a["slug"]}.html" tabindex="-1" aria-hidden="true"><span class="ph has-cover"><img src="assets/img/covers/{a["cover"]}-sm.webp" alt="" loading="lazy"></span></a>
      <div class="sc-tags"><span>{E(a["tag"])}</span></div><h3><a href="{a["slug"]}.html">{E(a["title"])}</a></h3><p class="ar-ex">{E(a["desc"])}</p><span class="sc-meta">{ic("clock")}{str(a["minutes"]).translate(AR)} دقائق قراءة · {ic("cal")}{ar_date(a["date"])}</span>
      <div class="sc-act"><a class="btn btn-gold btn-sm" href="{a["slug"]}.html">اقرئي المقال</a></div></article>''' for a in sorted(arts, key=lambda a: a["date"], reverse=True))
    page("articles.html", "المقالات", "مقالات د. مرفت سرور عن الوعي الذاتي، الامتنان، التشافي، فك التعلّق، الطفل الداخلي والـ Decoding.", f'''
{page_hero("المقالات", "عن الوعي الذاتي، والامتنان، والتشافي، وفكّ التعلّق، والطفل الداخلي، والـ Decoding.")}
<section class="pg"><div class="wrap"><div class="shelf ar-shelf">{cards}</div>
  <p class="ar-soon">{ic("mail", "icon icon-sm")}مقالات جديدة قريباً. <a href="gift.html">اشتركي واستلمي هديتك</a> ليصلك الجديد أولاً.</p></div></section>''', active="articles.html")
    return arts
