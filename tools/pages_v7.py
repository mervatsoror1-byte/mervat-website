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
    page("library.html", "الأدوات", "كل أدوات د. مرفت سرور: كورس عين صاحية، تمارين Decoding وPriming، فك التعلق، تشافي الطفل الداخلي، تنفّس الاتساق القلبي وتأمل السكينة.", f'''
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
    page(p["page"], f'{p["title"]}', p["short"] + f' {p["catLabel"]} مع د. مرفت سرور.', f'''
<section class="pg"><div class="wrap">
  {crumbs(("الأدوات","library.html"), (p["title"], None))}
  <div class="pd2">
    <div class="pd2-main">
      <h1 class="pg-title">{E(p["title"])}</h1>
      <p class="pd2-kicker">{E(p["catLabel"])}</p>
      <div class="prose">{"".join(f"<p>{E(x)}</p>" for x in p["desc"])}</div>
      <h2 class="pd2-h">محتوى {kind}</h2><ul class="axes">{axes}</ul>
      <h2 class="pd2-h">مناسب لك إذا كنت…</h2><ul class="axes">{"".join(f"<li>{E(x)}</li>" for x in p["forWho"])}</ul>
      <div class="sc-tags" style="padding:0;margin:14px 0"><span>{"كورس" if is_course else "تمرين"}</span><span>{E(p["catLabel"])}</span><span>Online</span></div>
      <details class="lbox" open><summary>محتوى {kind}</summary>{lessons}</details>
    </div>
    <aside class="pd2-side"><div class="buy2">
      <div class="sc-img"><span class="ph"><img src="assets/brand/logo-icon-gold.webp" alt=""></span></div>
      <div class="buy2-head"><h3>{E(p["title"])}</h3><span class="ctas"><button class="sq-ic" type="button" data-fav="{p["id"]}" aria-pressed="false" aria-label="احفظ">{ic("heart","icon icon-sm")}</button><a class="sq-ic" href="contact.html" aria-label="مشاركة">{ic("share","icon icon-sm")}</a></span></div>
      <span class="sc-price" style="padding:0" data-price="{p["id"]}">{p["eg"]} ج.م</span>
      <small class="muted">وصول مدى الحياة</small>
      <div class="buy2-meta"><span>{ic("lessons","icon icon-sm")}{total} {"دروس" if total > 2 else "درس"}</span><span>{ic("clock","icon icon-sm")}{dur}</span></div>
      <button class="btn btn-gold btn-block" type="button" data-buy="{p["id"]}"><span>اشترك الآن</span></button>
      <button class="btn btn-line btn-block" type="button" data-add="{p["id"]}">{ic("bag")}<span>إضافة إلى السلة</span></button>
      <a class="gift-link" href="contact.html">{ic("gift","icon icon-sm")}إهداء هذه الأداة</a>
      <div class="incl"><b>هذه الأداة تشمل:</b><span>{total} {"دروس صوتية ومرئية" if total > 2 else "درس"} عالية الجودة</span><span>وصول كامل مدى الحياة</span><span>مشمولة في برنامج استيقظ VIP</span></div>
    </div></aside>
  </div>
  <hr class="sep">
  <h2 class="pg-title" style="font-size:clamp(1.8rem,3.4vw,2.6rem)">أدوات قد تعجبك</h2>
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
<section class="pg"><div class="wrap">
  <h2 class="gold-h">من هي مرفت سرور</h2>
  <div class="ab-row ab-main"><div class="ab-ph"><img src="assets/img/mervat-about.webp" alt="مرفت سرور" width="900" height="1012"></div>
    <div class="ab-tx"><h2>مرفت سرور</h2>{bio}
      </div></div>
  <div class="center-cta"><a class="btn btn-gold" href="vip.html">ابدأ معي في برنامج استيقظ VIP</a></div>
</div></section>''', active="about.html", schema=[B.PERSON])


def contact():
    items = [("chat", "01095292748", "https://wa.me/201095292748"), ("mail", "support@mervatsoror.com", "contact.html"),
             ("play", "mervatsoror", "#"), ("user", "mervatsoror", "#"), ("globe", "mervatsoror", "#"), ("heart", "mervatsoror", "#")]
    page("contact.html", "اتصل بنا", "تواصل مع فريق د. مرفت سرور: واتساب 01095292748، أو أرسل رسالتك من النموذج.", f'''
<section class="pg"><div class="wrap ct-grid">
  <div class="ct-form"><h1 class="pg-title">مساحة آمنة لاستفساراتك</h1><p class="muted">شاركني ما يدور في خاطرك، ويسعدني مرافقتك.</p>
    <form class="form" data-simple="وصلتنا رسالتك، وسنرد عليك قريباً.">
      <div class="field"><label for="ctName">الاسم <i>*</i></label><input id="ctName" required placeholder="أدخل اسمك"></div>
      <div class="field"><label for="ctEmail">البريد الإلكتروني <i>*</i></label><input id="ctEmail" type="email" required placeholder="أدخل بريدك الإلكتروني"></div>
      <div class="field"><label for="ctPhone">رقم الهاتف <i>*</i></label><div class="phone"><select aria-label="كود الدولة"><option>+20</option><option>+966</option><option>+971</option><option>+965</option><option>+974</option><option>+1</option></select><input id="ctPhone" type="tel" required placeholder="أدخل رقم هاتفك"></div></div>
      <div class="field"><label for="ctMsg">رسالتك <i>*</i></label><textarea id="ctMsg" required maxlength="500" placeholder="أدخل محتوى الرسالة"></textarea></div>
      <div class="alert" hidden></div><button class="btn btn-gold btn-block" type="submit">إرسال الرسالة</button></form></div>
  <div class="ct-card"><h2>تابع رحلة الوعي اليومية عبر منصاتنا</h2><p>حيث نشارككم ومضات من النور والإلهام.</p>
    <div class="ct-list">{"".join(f'<a href="{h}" {"target=_blank rel=noopener" if h.startswith("http") else ""}><span class="gic">{ic(i,"icon icon-sm")}</span><b>{t}</b></a>' for i,t,h in items)}</div>
    <span class="demo" style="color:#C9D3EA;border-color:#C9D3EA">أسماء الحسابات مؤقتة</span></div>
</div></section>''', active="contact.html")


def faq():
    allq = [q for k in FAQ for q in FAQ[k]]
    page("faq.html", "الأسئلة الشائعة", "إجابات عن الدفع والأسعار داخل مصر وخارجها، برنامج استيقظ VIP، الجلسات والكتب.", f'''
<section class="pg"><div class="wrap"><h1 class="pg-title">الأسئلة الشائعة</h1><div class="faq2">{"".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q,a in allq)}</div></div></section>''',
         schema=[{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in allq]}])


ARTICLES = [("كيف أتصالح مع نفسي؟ خطوات عملية للبداية", "التشافي", "٦ دقائق قراءة"),
            ("ما هو الـ Decoding ولماذا نحتاجه؟", "Decoding", "٥ دقائق قراءة"),
            ("علامات التعلّق المؤذي وكيف تبدأ في فكّه", "فك التعلّق", "٧ دقائق قراءة"),
            ("الطفل الداخلي: لماذا يتكلم في المواقف الصعبة؟", "التشافي", "٦ دقائق قراءة"),
            ("تنفّس الاتساق القلبي: ٥ دقائق تغيّر يومك", "تنفّس وتأمل", "٤ دقائق قراءة"),
            ("Priming الصباح: كيف تبدأ يومك من مكان هادئ", "Priming", "٤ دقائق قراءة")]


def articles():
    cards = "".join(f'''<article class="scard"><div class="sc-img"><span class="ph"><img src="assets/brand/logo-icon-gold.webp" alt=""></span><button class="sc-fav" type="button" aria-label="احفظ">{ic("heart")}</button></div>
      <div class="sc-tags"><span>{c}</span></div><h3>{E(t)}</h3><span class="sc-meta">{ic("clock")}{r} · {ic("cal")}قريباً</span>
      <div class="sc-act"><a class="btn btn-gold btn-sm" href="articles.html">اقرأ المزيد</a></div></article>''' for t, c, r in ARTICLES)
    page("articles.html", "المقالات", "مقالات د. مرفت سرور عن الوعي الذاتي، التشافي، فك التعلّق، الطفل الداخلي والـ Decoding.", f'''
<section class="pg"><div class="wrap"><div class="pg-row"><h1 class="pg-title">المقالات</h1>
  <div class="toolbar" style="margin:0;flex:1;max-width:640px"><div class="search grow">{ic("search")}<label class="sr" for="aq">ابحث بعنوان المقالة</label><input id="aq" type="text" placeholder="ابحث بعنوان المقالة"></div><label class="sortbox"><span class="muted">ترتيب حسب</span><select aria-label="ترتيب"><option>الأحدث</option></select></label></div></div>
  <p class="muted" style="margin-bottom:22px"><span class="demo">عناوين مقترحة حسب كلمات البحث المستهدفة، تُكتب لاحقاً</span></p>
  <div class="shelf">{cards}</div></div></section>''')


def auth():
    quotes = '<div class="au-quote"><span class="au-orn" aria-hidden="true">✦</span><p>كل خطوة<br>نحو ذاتك<br>خطوة نحو <em>النور</em></p></div>'
    art = f'<div class="au-art"><a class="au-logo" href="index.html"><img src="assets/brand/logo-gold-transparent.webp" alt="د. مرفت سرور" width="120" height="90"></a><img class="au-photo" src="assets/img/auth-white.webp" alt="د. مرفت سرور" width="1122" height="1402">{quotes}</div>'
    spark = '<canvas class="sparkle" data-density="1600" aria-hidden="true"></canvas>'
    social = '<div class="au-social">' + "".join(f'<a href="#" aria-label="{n}">{ic(i,"icon icon-sm")}</a>' for i, n in [("chat", "واتساب"), ("mail", "بريد"), ("play", "يوتيوب"), ("heart", "إنستغرام")]) + '</div>'
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
    library(); about(); contact(); faq(); articles(); auth()
    for p in PRODUCTS:
        if p["kind"] in ("course", "exercise"):
            product(p)
