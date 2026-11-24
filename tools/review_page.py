"""«شاركينا تجربتك»: one page where a client writes a review, records one by voice, or both."""


def options(BY, PRODUCTS, E):
    o = ['<option value="general">تجربة عامة مع د. مرفت</option>']
    grp = [("البرامج والجلسات", [("vip-m", "برنامج استيقظ VIP"), ("s-single", "الجلسات الفردية"), ("m-single", "الاستشارات الزوجية")])]
    tools = [(p["id"], p["title"]) for p in PRODUCTS if p.get("kind") in ("course", "exercise", "book")]
    bundles = [(p["id"], p["title"]) for p in PRODUCTS if p.get("kind") == "bundle"]
    grp += [("الأدوات", tools), ("الباقات", bundles)]
    for label, items in grp:
        if items:
            o.append(f'<optgroup label="{E(label)}">' + "".join(f'<option value="{k}">{E(t)}</option>' for k, t in items) + '</optgroup>')
    return "".join(o)


def build(g):
    page, ic, E, BY, PRODUCTS, page_hero = g["page"], g["ic"], g["E"], g["BY"], g["PRODUCTS"], g["page_hero"]
    stars = "".join(f'<button type="button" class="rw-star" data-star="{i}" aria-label="{i} من ٥" aria-pressed="true">★</button>' for i in range(1, 6))
    body = page_hero("شاركينا تجربتك", "كلماتك قد تكون الخطوة الأولى لإنسانة أخرى. اكتبي تجربتك أو سجّليها بصوتك، وتُنشر بعد مراجعة د. مرفت.") + f'''
<section class="band-sm"><div class="wrap narrow rw-wrap" data-review-app>
  <div class="rw-card rw-top">
    <label for="rwAbout"><b>عن أي شيء تحكين؟</b></label>
    <select id="rwAbout">{options(BY, PRODUCTS, E)}</select>
    <div class="rw-stars-row"><b>تقييمك</b><div class="rw-stars" role="group" aria-label="التقييم">{stars}</div></div>
  </div>
  <div class="rw-grid">
    <div class="rw-card"><h2>{ic("mail", "icon icon-sm")}اكتبي تجربتك</h2>
      <textarea id="rwText" rows="7" maxlength="2000" placeholder="ماذا تغيّر فيكِ؟ كيف كنتِ قبل وكيف أصبحتِ؟ اكتبي بكلماتك…"></textarea>
      <div class="rw-name"><label><input type="radio" name="rwN" value="first" checked> باسمي الأول</label><input id="rwFirst" type="text" maxlength="30" placeholder="اسمك الأول">
        <label><input type="radio" name="rwN" value="city"> «عميلة من…»</label><input id="rwCity" type="text" maxlength="30" placeholder="المدينة أو البلد"></div>
      <input id="rwEmail" type="email" dir="ltr" placeholder="بريدك (اختياري، لا يظهر في الموقع)">
      <input type="text" name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
      <label class="check"><input type="checkbox" id="rwOk"><span>أوافق على نشر رأيي في الموقع بعد مراجعته</span></label>
      <button type="button" class="btn btn-gold btn-block" data-rw-send>أرسلي رأيي</button>
      <div class="rw-done" hidden>{ic("check")}<span>وصل رأيك، شكراً لك من القلب. سيظهر في الموقع بعد مراجعة د. مرفت.</span></div></div>
    <div class="rw-card rw-voice"><h2>{ic("chat", "icon icon-sm")}أو سجّليها بصوتك</h2>
      <p>صوتك يصل أعمق من أي كتابة. اضغطي وسجّلي حتى دقيقتين، واسمعي التسجيل قبل الإرسال.</p>
      <div class="vr-rec" data-vrrec="general"></div></div>
  </div>
  <p class="rw-note">تقرأ د. مرفت كل رأي بنفسها قبل نشره. لا ننشر البريد الإلكتروني أبداً.</p>
</div></section>'''
    page("review.html", "شاركينا تجربتك", "شاركي تجربتك مع د. مرفت سرور، كتابة أو بصوتك، في التمارين أو الجلسات أو برنامج استيقظ VIP أو الاستشارات الزوجية.", body, noindex=True)
