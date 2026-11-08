"""Pages rebuilt on the reference site's page layouts (structure only), with Mervat's own content and identity.
   Called at the end of build(); each call overwrites the earlier version of the page."""
import types
B = types.SimpleNamespace()
page = crumbs = ic = E = None
BY = EXERCISES = CATS = FAQ = PRODUCTS = None

def init(g):
    """Receive the builder's globals so pages share its page() and PAGES list."""
    global page, crumbs, ic, E, BY, EXERCISES, CATS, FAQ, PRODUCTS
    B.__dict__.update(g)
    page, crumbs, ic, E = g["page"], g["crumbs"], g["ic"], g["E"]
    BY, EXERCISES, CATS, FAQ, PRODUCTS = g["BY"], g["EXERCISES"], g["CATS"], g["FAQ"], g["PRODUCTS"]


def tabs_v7():
    return ('<div class="bigtabs" role="group" aria-label="تصنيف الأدوات">' +
            "".join(f'<button class="tab" type="button" data-filter="{k}" aria-pressed="{str(k=="all").lower()}">{v}</button>' for k, v in CATS) + "</div>")


def library():
    page("library.html", "الأدوات", "كل أدوات د. مرفت سرور: كورس عين صاحية، تمارين Decoding وPriming، فك التعلق، تشافي الطفل الداخلي، تنفّس الاتزان الداخلي وتأمل السكينة.", f'''
<section class="pg"><div class="wrap">
  <h1 class="pg-title">الأدوات</h1>
  {tabs_v7()}
  <div class="toolbar">
    <label class="sortbox"><span class="muted">ترتيب حسب</span><select id="sortSel" aria-label="ترتيب حسب"><option value="new">الأحدث</option><option value="low">السعر: الأقل</option><option value="high">السعر: الأعلى</option></select></label>
    <div class="search grow">{ic("search")}<label class="sr" for="q">ابحث بعنوان الأداة</label><input id="q" type="text" placeholder="ابحث بعنوان الأداة"></div>
    <span class="filter-ic" aria-hidden="true">{ic("sort")}</span>
  </div>
  <div class="shelf" data-shelf="library"></div>
</div></section>''', active="library.html")


def product(p):
    is_course = p["kind"] == "course"
    total = sum(len(m["lessons"]) for m in p["modules"])
    secs = 0
    for m in p["modules"]:
        for l in m["lessons"]:
            mm, ss = l[1].split(":"); secs += int(mm) * 60 + int(ss)
    dur = f"{secs//3600:02d}:{(secs%3600)//60:02d}:{secs%60:02d}"
    axes = "".join(f"<li><b>{E(m['title'])}</b></li>" for m in p["modules"])
    lessons = "".join(f'<div class="lrow">{ic("play","icon icon-sm pl")}<span>{E(l[0])}</span>' + (f'<a href="learn.html#{p["id"]}">شاهد مجاناً</a>' if l[2:] else ic("lock","icon icon-sm lk")) + '</div>' for m in p["modules"] for l in m["lessons"])
    kind = "الكورس" if is_course else "التمرين"
    _ar = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    def _n(k): return str(k).translate(_ar) + " " + ("درس" if k == 1 else "درسان" if k == 2 else "دروس")
    facts = list(p.get("facts") or [["lessons", f"يحتوي على {_n(total)}"], ["clock", f"المدة: {dur.translate(_ar)}"]])
    if p.get("ctype"): facts.append(["layers", f"نوع المادة: {p['ctype']}"])
    if p.get("level"): facts.append(["award", f"المستوى: {p['level']}"])
    facts += [["cal", "مدة الوصول: ٣٦٥ يوماً من تاريخ الشراء"], ["devices", "تابع من أي لابتوب أو موبايل"]]
    facts_html = "".join(f'<li>{ic(i, "icon icon-sm")}<span>{E(t)}</span></li>' for i, t in facts)
    modules_html = "".join(f'<details {"open" if n == 0 else ""}><summary>{E(m["title"])}</summary>' + "".join(f'<div class="pd3-l">{ic("play" if l[2:] else "lock", "icon icon-sm")}<span>{E(l[0])}</span>' + (f'<a href="learn.html#{p["id"]}">استمع مجاناً</a>' if l[2:] else "") + '</div>' for l in m["lessons"]) + '</details>' for n, m in enumerate(p["modules"]))
    page(p["page"], f'{p["title"]}', p["short"] + f' {p["catLabel"]} مع د. مرفت سرور.', f'''
<section class="pg"><div class="wrap">
  {crumbs(("الأدوات","library.html"), (p["title"], None))}
  <div class="pd3">
    <a class="pd3-media{" has-cover" if p.get("cover") else ""}" href="learn.html#{p["id"]}" aria-label="استمع لمقدمة {E(p["title"])} مجاناً">
      <img src="{p.get("coverLg") or p.get("cover") or "assets/brand/logo-icon-gold.webp"}" alt="{E(p["title"])}" width="1600" height="900">
      <span class="pd3-play">{ic("play")}</span><span class="pd3-free">المقدمة مجاناً</span></a>
    <aside class="pd3-buy">
      <h1>{E(p["title"])}</h1>
      <p class="pd3-kicker">{E(p["catLabel"])}</p>
      <ul class="pd3-facts">{facts_html}</ul>
      <div class="pd3-price"><span class="sc-price" data-price="{p["id"]}">{p["eg"]} ج.م</span></div>
      <button class="btn-safia pd3-cta" type="button" data-buy="{p["id"]}"><span>ابدأ الآن</span></button>
      <button class="pd3-add2" type="button" data-add="{p["id"]}">{ic("bag","icon icon-sm")}<span>أضف إلى السلة لشراء أكثر من أداة</span></button>
      <div class="pd3-links"><button type="button" data-fav="{p["id"]}" aria-pressed="false">{ic("heart","icon icon-sm")}احفظ</button><a href="contact.html">{ic("gift","icon icon-sm")}إهداء</a><a href="contact.html">{ic("share","icon icon-sm")}مشاركة</a></div>
      {"<p class=pd3-vip>" + ic("crown","icon icon-sm") + "مشمول في برنامج استيقظ VIP</p>" if p.get("vipIncluded") else ""}
    </aside>
  </div>
  <div class="pd3-body">
    <div class="pd3-sec"><h2>عن {kind}</h2><div class="prose">{"".join(f"<p>{E(x)}</p>" for x in p["desc"])}</div></div>
    <div class="pd3-sec" id="voices"><h2>قالوا عن {"الكورس" if is_course else "التمرين"}</h2><p class="vr-hint">آراء صوتية من عميلات جرّبن {"الكورس" if is_course else "التمرين"}، تسجّلها كل عميلة بنفسها بعد الشراء.</p>
      <div class="vr-rec" data-vrrec="{p["id"]}"></div><div class="vr-list" data-vr="{p["id"]}"></div></div>
    <div class="pd3-sec"><h2>مناسب لك إذا كنت…</h2><ul class="pd3-for">{"".join(f"<li><i class=vp-dot></i>{E(x)}</li>" for x in p["forWho"])}</ul></div>
    <div class="pd3-sec"><h2>محتوى {kind}</h2><div class="vp-faq">{modules_html}</div>{"<p class=vp-small>أسماء الدروس مبدئية وتُحدَّث قريباً</p>" if p.get("facts") else ""}</div>
  </div>
  <div class="vp-head" style="margin:clamp(50px,7vw,90px) 0 30px"><span class="vp-orn" aria-hidden="true">✦</span><h2>أدوات قد تعجبك</h2></div>
  <div class="shelf" data-shelf="related" data-current="{p["id"]}"></div>
</div></section>''', active="library.html",
         schema=[{"@context": "https://schema.org", "@type": "Course", "name": p["title"], "description": p["short"], "inLanguage": "ar",
                  "provider": {"@type": "Person", "name": "مرفت سرور"},
                  "offers": [{"@type": "Offer", "price": p["eg"], "priceCurrency": "EGP"}, {"@type": "Offer", "price": p["us"], "priceCurrency": "USD"}]}])


def about():
    bio = ("<p>مرفت سرور مدربة وعي وكوتش معتمد من الاتحاد الدولي للتدريب <b>ICF</b> بدرجة <b>PCC</b> "
           "<span class='en'>(Professional Certified Coach)</span>.</p>"
           "<p>بدأت مرفت مسيرتها منذ عام 2019 بدراسة علوم الوعي على يد كبار المعلمين، وعزّزت ذلك بالدراسة في عدة جامعات، "
           "منها جامعة بنسلفانيا حيث درست على يد الأب الروحي لعلم النفس الإيجابي مارتن سليجمان، "
           "كما درست اليقظة الذهنية في جامعة لايدن الهولندية على يد المدرب الكبير كريس غوتو-جونز.</p>"
           "<p>ونتيجةً لهذه الدراسات، ومع التطبيق على نفسها أولاً ثم على أكثر من 100 عميل، بدأت في تطبيق برنامجها الخاص للتشافي: "
           "برنامج <b>استيقظ VIP</b>. يتميّز البرنامج بأنه يجمع بين هذه التقنيات جميعاً، ليوفّر طريقاً للتشافي بخطوات عملية وعلمية مرتبة، "
           "ويعمل على عدة مستويات ليصل بالعميل في النهاية إلى التشافي، وتغيير نسخته القديمة، وبناء الهوية الجديدة التي طالما طمح إليها.</p>")
    page("about.html", "عن مرفت", "مرفت سرور مدربة وعي وكوتش معتمد من ICF بدرجة PCC، ومؤسسة برنامج استيقظ VIP للتشافي.", f'''
{B.page_hero("من هي مرفت سرور", "مدربة وعي وتشافي، ورفيقة رحلة العودة إلى الذات", ("عن مرفت", None))}
<section class="pg"><div class="wrap">
  <div class="ab-row ab-main"><div class="ab-ph"><img src="assets/img/mervat-about.webp" alt="مرفت سرور" width="900" height="1012"></div>
    <div class="ab-tx"><h2>مرفت سرور</h2>{bio}
      </div></div>
  <div class="center-cta"><a class="btn btn-gold" href="vip.html">ابدأ معي في برنامج استيقظ VIP</a></div>
</div></section>''', active="about.html", schema=[B.PERSON])


def contact():
    items = [("chat", "01095292748", "https://wa.me/201095292748"), ("mail", "support@mervatsoror.com", "contact.html"),
             ("play", "يوتيوب", "https://www.youtube.com/@mervatsoror"), ("heart", "إنستغرام", "https://www.instagram.com/mervatsoror111"),
             ("user", "فيسبوك", "https://www.facebook.com/mrft.srwr"), ("globe", "تيك توك", "https://www.tiktok.com/@fefesoror")]
    page("contact.html", "اتصل بنا", "تواصل مع فريق د. مرفت سرور: واتساب 01095292748، أو أرسل رسالتك من النموذج.", f'''
{B.page_hero("مساحة آمنة لاستفساراتك", "شاركني ما يدور في خاطرك، ويسعدني مرافقتك.", ("اتصل بنا", None))}
<section class="pg"><div class="wrap ct-grid">
  <div class="ct-form">
    <form class="form" data-simple="وصلتنا رسالتك، وسنرد عليك قريباً.">
      <div class="field"><label for="ctName">الاسم <i>*</i></label><input id="ctName" required placeholder="أدخل اسمك"></div>
      <div class="field"><label for="ctEmail">البريد الإلكتروني <i>*</i></label><input id="ctEmail" type="email" required placeholder="أدخل بريدك الإلكتروني"></div>
      <div class="field"><label for="ctPhone">رقم الهاتف <i>*</i></label><div class="phone"><select aria-label="كود الدولة"><option>+20</option><option>+966</option><option>+971</option><option>+965</option><option>+974</option><option>+1</option></select><input id="ctPhone" type="tel" required placeholder="أدخل رقم هاتفك"></div></div>
      <div class="field"><label for="ctMsg">رسالتك <i>*</i></label><textarea id="ctMsg" required maxlength="500" placeholder="أدخل محتوى الرسالة"></textarea></div>
      <div class="alert" hidden></div><button class="btn btn-gold btn-block" type="submit">إرسال الرسالة</button></form></div>
  <div class="ct-card"><h2>تابع رحلة الوعي اليومية عبر منصاتنا</h2><p>حيث نشارككم ومضات من النور والإلهام.</p>
    <div class="ct-list">{"".join(f'<a href="{h}" {"target=_blank rel=noopener" if h.startswith("http") else ""}><span class="gic">{ic(i,"icon icon-sm")}</span><b>{t}</b></a>' for i,t,h in items)}</div></div>
</div></section>''', active="contact.html")


def faq():
    allq = [q for k in FAQ for q in FAQ[k]]
    page("faq.html", "الأسئلة الشائعة", "إجابات عن الدفع والأسعار داخل مصر وخارجها، برنامج استيقظ VIP، الجلسات والكتب.", f'''
{B.page_hero("الأسئلة الشائعة", "إجابات عن الدفع والأسعار، وبرنامج استيقظ VIP، والجلسات والكتب.")}
<section class="pg"><div class="wrap narrow"><div class="faq2 vp-faq">{"".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q,a in allq)}</div></div></section>''',
         schema=[{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in allq]}])


ARTICLES = [("كيف أتصالح مع نفسي؟ خطوات عملية للبداية", "التشافي", "٦ دقائق قراءة"),
            ("ما هو الـ Decoding ولماذا نحتاجه؟", "Decoding", "٥ دقائق قراءة"),
            ("علامات التعلّق المؤذي وكيف تبدأ في فكّه", "فك التعلّق", "٧ دقائق قراءة"),
            ("الطفل الداخلي: لماذا يتكلم في المواقف الصعبة؟", "التشافي", "٦ دقائق قراءة"),
            ("تنفّس الاتزان الداخلي: دقائق تغيّر يومك", "تنفّس وتأمل", "٤ دقائق قراءة"),
            ("Priming الصباح: كيف تبدأ يومك من مكان هادئ", "Priming", "٤ دقائق قراءة")]


def articles():
    cards = "".join(f'''<article class="scard"><div class="sc-img"><span class="ph has-cover"><img src="assets/img/covers/{cv}-sm.webp" alt="" loading="lazy"></span><button class="sc-fav" type="button" aria-label="احفظ">{ic("heart")}</button></div>
      <div class="sc-tags"><span>{c}</span></div><h3>{E(t)}</h3><span class="sc-meta">{ic("clock")}{r} · {ic("cal")}قريباً</span>
      <div class="sc-act"><a class="btn btn-gold btn-sm" href="articles.html">اقرأ المزيد</a></div></article>''' for (t, c, r), cv in zip(ARTICLES, ["decode-acceptance","decode-original","attach","inner-child","breath","morning-priming"]))
    page("articles.html", "المقالات", "مقالات د. مرفت سرور عن الوعي الذاتي، التشافي، فك التعلّق، الطفل الداخلي والـ Decoding.", f'''
{B.page_hero("المقالات", "عن الوعي الذاتي، والتشافي، وفكّ التعلّق، والطفل الداخلي، والـ Decoding.")}
<section class="pg"><div class="wrap"><div class="pg-row">
  <div class="toolbar" style="margin:0;flex:1;max-width:640px"><div class="search grow">{ic("search")}<label class="sr" for="aq">ابحث بعنوان المقالة</label><input id="aq" type="text" placeholder="ابحث بعنوان المقالة"></div><label class="sortbox"><span class="muted">ترتيب حسب</span><select aria-label="ترتيب"><option>الأحدث</option></select></label></div></div>
  <p class="muted" style="margin-bottom:22px"><span class="demo">عناوين مقترحة حسب كلمات البحث المستهدفة، تُكتب لاحقاً</span></p>
  <div class="shelf">{cards}</div></div></section>''')


def auth():
    quotes = '<div class="au-quote"><span class="au-orn" aria-hidden="true">✦</span><p>كل خطوة<br>نحو ذاتك<br>خطوة<br>نحو <em>النور</em></p></div>'
    art = f'<div class="au-art"><a class="au-logo" href="index.html"><img src="assets/brand/logo-gold-transparent.webp" alt="د. مرفت سرور" width="120" height="90"></a><img class="au-photo" src="assets/img/auth-white.webp" alt="د. مرفت سرور" width="1122" height="1402"><img class="au-photo au-cut" src="assets/img/auth-white-cut.webp" alt="" aria-hidden="true" width="1122" height="1402">{quotes}</div>'
    spark = '<canvas class="sparkle" data-density="1600" aria-hidden="true"></canvas>'
    social = '<div class="au-social">' + "".join(f'<a href="{h}" target="_blank" rel="noopener" aria-label="{n}">{ic(i,"icon icon-sm")}</a>' for i, n, h in [("chat", "واتساب", "https://wa.me/201095292748"), ("play", "يوتيوب", "https://www.youtube.com/@mervatsoror"), ("heart", "إنستغرام", "https://www.instagram.com/mervatsoror111"), ("user", "فيسبوك", "https://www.facebook.com/mrft.srwr")]) + '</div>'
    back = f'<a class="au-back" href="index.html">عودة {ic("fwd","icon icon-sm")}</a>'
    page("login.html", "تسجيل الدخول", "سجّل الدخول لمتابعة رحلتك مع د. مرفت سرور.", f'''<div class="au">{spark}{art}<div class="au-panel">{back}<div class="au-in">
  <h1>أهلاً بك مجدداً</h1><p>سجّل الدخول لمتابعة رحلة التشافي الخاصة بك</p>
  <form class="form" id="loginForm" novalidate><div class="field"><label for="email">البريد الإلكتروني <i>*</i></label><input id="email" type="email" autocomplete="email" placeholder="أدخل بريدك الإلكتروني" required></div>
    <div class="field"><label for="password">كلمة المرور <i>*</i></label><input id="password" type="password" autocomplete="current-password" placeholder="أدخل كلمة المرور" required></div>
    <div class="au-row"><label class="check"><input type="checkbox"><span>تذكرني</span></label><a href="forgot.html">نسيت كلمة المرور؟</a></div>
    <div class="alert" hidden></div><button class="btn btn-gold btn-block" type="submit">تسجيل الدخول</button></form>
  <div class="or">أو المتابعة باستخدام</div><div class="social-login"><button class="btn au-sso" type="button" onclick="this.textContent='يُفعّل في الموقع الفعلي'">Google</button><button class="btn au-sso dark" type="button" onclick="this.textContent='يُفعّل في الموقع الفعلي'">Apple</button></div>
  <button class="btn btn-line btn-sm js-demo-login au-demo" type="button">جرّب حساباً تجريبياً جاهزاً</button>
  <p class="au-alt">ليس لديك حساب؟ <a href="register.html">انضم إلينا الآن</a></p>{social}</div></div></div>''', bare=True, noindex=True)
    page("register.html", "إنشاء حساب", "أنشئ حسابك المجاني واحصل على هدية.", f'''<div class="au">{spark}{art}<div class="au-panel">{back}<div class="au-in">
  <h1>ابدأ رحلتك</h1><p>حساب مجاني، ومعه هدية تُفتح فوراً</p>
  <form class="form" id="registerForm" novalidate><div class="field"><label for="name">الاسم <i>*</i></label><input id="name" autocomplete="name" placeholder="أدخل اسمك" required></div>
    <div class="field"><label for="email">البريد الإلكتروني <i>*</i></label><input id="email" type="email" autocomplete="email" placeholder="أدخل بريدك الإلكتروني" required></div>
    <div class="field"><label for="password">كلمة المرور <i>*</i></label><input id="password" type="password" autocomplete="new-password" placeholder="٦ أحرف على الأقل" minlength="6" required></div>
    <label class="check"><input type="checkbox" id="gift" checked><span>أرسل لي الهدية وجديد د. مرفت على بريدي</span></label>
    <label class="check"><input type="checkbox" required checked><span>أوافق على <a href="terms.html">الشروط</a> و<a href="privacy.html">الخصوصية</a></span></label>
    <div class="alert" hidden></div><button class="btn btn-gold btn-block" type="submit">إنشاء حسابي</button></form>
  <p class="au-alt">لديك حساب؟ <a href="login.html">سجّل الدخول</a></p>{social}</div></div></div>''', bare=True, noindex=True)
    page("forgot.html", "استعادة كلمة المرور", "استعادة كلمة المرور.", f'''<div class="au">{spark}{art}<div class="au-panel">{back}<div class="au-in">
  <h1>نسيت كلمة المرور؟</h1><p>اكتب بريدك وسنرسل لك رابطاً لتعيينها</p>
  <form class="form" id="forgotForm"><div class="field"><label for="fEmail">البريد الإلكتروني <i>*</i></label><input id="fEmail" type="email" required></div><div class="alert" hidden></div><button class="btn btn-gold btn-block" type="submit">أرسل الرابط</button></form>
  <p class="au-alt"><a href="login.html">العودة لتسجيل الدخول</a></p></div></div></div>''', bare=True, noindex=True)


def build_v7():
    library(); about(); contact(); faq(); articles(); auth(); landings()
    for p in PRODUCTS:
        if p["kind"] in ("course", "exercise"):
            product(p)


LANDINGS = [
  dict(file="lp-serenity.html", offer="lp-serenity", base="serenity", cover="serenity", pos="82% 50%",
       title="تأمل السكينة والتنظيف", desc="تأمل موجّه بصوت د. مرفت سرور لتنظيف المشاعر السلبية في ثلاث مراحل: التنفّس، التحرّر، الحماية.",
       h1=("نظّف ما تراكم داخلك", "وعُد إلى سكينتك"), lead="تأمل السكينة والتنظيف يحرّرك من المشاعر السلبية في ثلاث مراحل.",
       cta="ابدأ التأمل الآن", pains_h="هذا التأمل لك إذا كنت…",
       pains=["تحمل ثقلاً عاطفياً متراكماً لا تعرف مصدره", "تتأثر بطاقات من حولك بسهولة", "تشعر بمشاعر سلبية لا تعرف كيف تتخلص منها", "تحتاج إلى هدوء حقيقي وحماية داخلية"],
       steps_h="ثلاث مراحل في تأمل واحد",
       steps=[("التنفّس", "تهدأ أنفاسك وتعود إلى جسدك."), ("التحرّر", "تتخلّص من مشاعرك السلبية."), ("الحماية", "حماية في نهاية التمرين من أي طاقات سلبية.")],
       gets=[("play", "تأمل موجّه بصوت د. مرفت سرور"), ("layers", "ثلاث مراحل: التنفّس، التحرّر، الحماية"), ("lessons", "مقدمة مجانية تشرح التأمل"), ("cal", "وصول لمدة ٣٦٥ يوماً"), ("devices", "على الهاتف أو الكمبيوتر")],
       faqs=[("هل يناسبني إن لم أجرّب التأمل من قبل؟", "التأمل موجّه خطوة بخطوة بصوت د. مرفت، ومعه مقدمة تشرح طريقته قبل أن تبدأ."),
             ("متى أمارسه؟", "عند الشعور بالثقل، أو بعد يوم مرهق، أو بشكل منتظم ضمن روتينك اليومي."),
             ("متى أحصل عليه بعد الدفع؟", "يُفتح فوراً في حسابك بعد تأكيد الدفع، وتستمع إليه من أي جهاز.")],
       final="امنح نفسك دقائق من السكينة اليوم"),
  dict(file="lp-attach.html", offer="lp-attach", base="attach", cover="attach", pos="50% 50%",
       title="تمرين فك التعلّق", desc="تأمل موجّه بصوت د. مرفت سرور مدته ١٠ دقائق، يساعدك على تحرير التعلّق بشخص أو موقف أو نتيجة.",
       h1=("حرّر قلبك مما يُثقله", "وعُد إلى مركزك"), lead="تأمل موجّه مدته ١٠ دقائق يساعدك على تحرير التعلّق بشخص أو موقف أو نتيجة.",
       cta="ابدأ التمرين الآن", pains_h="هذا التمرين لك إذا كنت…",
       pains=["متعلّقاً بعلاقة انتهت أو لم تبدأ", "تعيش قلقاً دائماً من فقدان شخص أو شيء", "تجد صعوبة في ترك النتائج لله", "لا يتوقف تفكيرك في نفس الشخص أو الموقف"],
       steps_h="ماذا يحدث في التمرين",
       steps=[("تلاحظ", "ترى تعلّقك بوضوح دون أن تحكم على نفسك."), ("تفهم", "تعرف ما الذي يحاول هذا التعلّق أن يحميه فيك."), ("تتحرّر", "تحرّره بهدوء، وتعود إلى سلامك الداخلي.")],
       gets=[("play", "تأمل موجّه مدته ١٠ دقائق بصوت د. مرفت سرور"), ("award", "مستوى مبتدئ، مناسب لأول تجربة"), ("lessons", "مقدمة مجانية تشرح التمرين"), ("cal", "وصول لمدة ٣٦٥ يوماً"), ("devices", "على الهاتف أو الكمبيوتر")],
       faqs=[("هل يناسبني إن لم أجرّب التأمل من قبل؟", "نعم، مستواه مبتدئ، وهو موجّه خطوة بخطوة، ومعه مقدمة تشرح طريقته."),
             ("كم مرة أمارسه؟", "يمكنك تكراره كلما شعرت بالتعلّق أو القلق، ومع التكرار يصبح التحرّر أسهل."),
             ("متى أحصل عليه بعد الدفع؟", "يُفتح فوراً في حسابك بعد تأكيد الدفع، وتستمع إليه من أي جهاز.")],
       final="امنح نفسك عشر دقائق من الحرية اليوم"),
]


def landing(L):
    off, base = B.BY[L["offer"]], B.BY[L["base"]]
    pid = L["offer"]
    pr = f'<span class="price" data-price="{pid}">{off["eg"]} ج.م</span>'
    was = f'<s class="lp-was" data-was="{base["eg"]}|{base["us"]}">{base["eg"]} ج.م</s>'
    buy = (f'<div class="lp-buy"><div class="lp-price">{pr}{was}<em class="lp-tag">سعر خاص لفترة محدودة</em></div>'
           f'<button class="btn-safia" type="button" data-buy="{pid}"><span>{L["cta"]}</span></button>'
           f'<div class="lp-links"><a class="lp-free" href="learn.html#{base["id"]}">{ic("play","icon icon-sm")}استمع للمقدمة مجاناً</a>'
           f'<a class="lp-all" href="library.html">تعرّف على كل الأدوات ←</a></div></div>')
    nums = "١٢٣"
    page(L["file"], L["title"], L["desc"], f"""
<header class="lp-top"><a href="index.html" aria-label="مرفت سرور"><img src="assets/brand/logo-gold-transparent.webp" alt="مرفت سرور" width="120" height="90"></a><a class="lp-site" href="library.html">كل الأدوات</a></header>
<section class="lp-hero"><canvas class="sparkle" data-density="1500" aria-hidden="true"></canvas>
  <figure class="lp-ph"><img src="assets/img/covers/{L["cover"]}.webp" alt="" width="1600" height="900" fetchpriority="high" style="object-position:{L["pos"]}"></figure>
  <div class="lp-copy"><span class="vs-eyebrow">تأمل موجّه بصوت د. مرفت سرور</span>
    <h1>{L["h1"][0]} <span>{L["h1"][1]}</span></h1>
    <p>{L["lead"]}</p>
    {buy}</div></section>
<section class="vp-sec vp-ivory"><div class="vp-wrap vp-narrow"><header class="vp-head"><span class="vp-orn" aria-hidden="true">✦</span><h2>{L["pains_h"]}</h2></header>
  <ul class="lp-pains">{"".join(f"<li><i class=vp-dot></i>{E(x)}</li>" for x in L["pains"])}</ul></div></section>
<section class="vp-sec vp-royal"><canvas class="sparkle" data-density="2200" aria-hidden="true"></canvas><div class="vp-wrap">
  <header class="vp-head on-dark"><span class="vp-orn" aria-hidden="true">✦</span><h2>{L["steps_h"]}</h2></header>
  <div class="lp-steps">{"".join(f'<div class="lp-step"><b>{nums[k]}</b><h3>{t}</h3><p>{d}</p></div>' for k, (t, d) in enumerate(L["steps"]))}</div></div></section>
<section class="vp-sec vp-ivory"><div class="vp-wrap lp-two">
  <div><header class="vp-head" style="justify-items:start;text-align:start"><h2>ماذا تحصل عليه</h2></header>
    <ul class="pd3-facts lp-gets">{"".join(f"<li>{ic(i,'icon icon-sm')}<span>{E(t)}</span></li>" for i, t in L["gets"])}</ul></div>
  <div class="lp-me"><img src="assets/img/mervat-about.webp" alt="د. مرفت سرور" width="900" height="1012" loading="lazy">
    <div><b>د. مرفت سرور</b><span>مدربة وعي وتشافي معتمدة من ICF بدرجة PCC · أكثر من ١٨ ألف ساعة تدريبية</span></div></div></div></section>
<section class="vp-sec vp-ivory" style="padding-top:0"><div class="vp-wrap vp-narrow"><header class="vp-head"><span class="vp-orn" aria-hidden="true">✦</span><h2>أسئلة سريعة</h2></header>
  <div class="vp-faq">{"".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in L["faqs"])}</div></div></section>
<section class="vp-final"><canvas class="sparkle" data-density="2600" aria-hidden="true"></canvas><div class="vp-wrap"><h2>{L["final"]}</h2>{buy}</div></section>
<section class="lp-more"><div class="vp-wrap"><h2>اكتشف باقي أدوات د. مرفت</h2><p>تمارين Decoding، وتأملات للتشافي، وتوكيدات، وباقات بنظام يومي متكامل.</p><a class="vp-btn" href="library.html">تعرّف على كل الأدوات</a></div></section>
<footer class="lp-foot"><a href="index.html">الموقع الرئيسي</a> · <a href="terms.html">الشروط</a> · <a href="privacy.html">الخصوصية</a> · <a href="refund.html">الاسترداد</a> · <a href="contact.html">تواصل معنا</a><span>© ٢٠٢٦ د. مرفت سرور</span></footer>
<div class="lp-sticky"><div class="lp-price">{pr}{was}</div><button class="btn-safia" type="button" data-buy="{pid}"><span>ابدأ الآن</span></button></div>
""", bare=True)


def landings():
    for L in LANDINGS:
        landing(L)
