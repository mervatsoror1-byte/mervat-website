"""Gift page: «أسئلة كشف الهوية» — video, then the questions in short steps; answers go to Dr. Mervat by email."""
import json

GIFT_VIDEO = "https://iframe.mediadelivery.net/embed/811029/275d6897-fd8b-4a41-9e7d-aacf2a743d2b?autoplay=false&preload=true&responsive=true"

INSTRUCTIONS = ["اجلس في مكان هادئ.", "أجب عن الأسئلة بهدوء ودون ضغط.", "لا توجد إجابة صحيحة ولا خاطئة.",
                "ركّز على الجسد وما يرسله لك من مشاعر، وأين توجد هذه المشاعر."]

# grouped like the slides in the video (the repeated question on slide 6 is removed)
STEPS = [
    ["ما هي الصفة أو السلوك الذي لو اتهمك به شخص ما اليوم، سيجعلك تفقد صوابك وتدافع عن نفسك باستماتة؟",
     "إذا فُرض عليك أن تعيش بقية حياتك مع النسخة الحالية من نفسك في غرفة مغلقة، ما هو أكثر شيء سيجعلك تملّ أو تنفر من نفسك؟",
     "ما هو «السر» أو «الحدث» في ماضيك الذي تبذل طاقة هائلة يوميًا لتبدو وكأنه لم يؤثر عليك، وكيف يظهر هذا المجهود في تصرفاتك الحالية؟",
     "من هو الشخص في حياتك الحالية الذي تراقب سقطاته وأخطاءه بشغف، وما الذي يمثله هذا الشخص في الجزء غير المحقق من ذاتك؟"],
    ["لما بتيجي تاخد خطوة شجاعة أو قرار مصيري وبتتراجع في آخر لحظة... إيه الصوت الداخلي الهامس اللي بيوقفك؟ بيقولك إيه بالضبط؟ ويا ترى الصوت ده خايف عليك من إيه؟",
     "بص لجسمك في لحظات الخوف أو الارتباك... أي منطقة في جسمك بتنقبض أو بتتأثر بالشعور ده؟ ولو المنطقة دي عندها لسان وهتتكلم، إيه الشكوى أو الصرخة اللي هتقولها في الوقت ده؟",
     "إيه الدور اللي بتحاول تلعبه في علاقاتك ومنتظر عليه مكافأة صامتة؟ مثلًا: هل أنت المنقذ، الضحية، أم المضحي؟ وإيه اللي هيحصل لو بطّلت تلعب الدور ده؟"],
    ["لو جرّدناك تمامًا من اسمك، وعائلتك، ووظيفتك، وتاريخك، وإنجازاتك، وحتى الأشخاص اللي بتحبهم وبيحبوك... مين أو إيه اللي هيفضل موجود معانا دلوقتي؟",
     "لو فيه كذبة مريحة أو وهم صغير بتصبّر بيه نفسك كل يوم الصبح علشان تقدر تكمّل حياتك الحالية وما تواجهش الواقع، إيه هي الكذبة أو الوهم ده؟",
     "لو عرفت وتيقّنت إن حياتك بكل تعقيداتها وأزماتها الحالية هي اختيارك الكامل والواعي بنسبة ١٠٠٪... إيه الجزء في حياتك اللي هترفض تمامًا تحمّل مسؤوليته وهتحس بالخوف بسببه؟"],
    ["إيه المشكلة أو الأزمة اللي بقالها سنين في حياتك ومش راضية تتحل رغم محاولاتك؟ يا ترى إيه هو الأمان اللي محققاه لك الأزمة دي؟ مثلًا: هل محققالك اهتمام من الآخرين، عذر مريح للفشل، أم هروب من مسؤولية أكبر؟",
     "لو بكرة الصبح صحيت لقيت نفسك قوي، ناجح، متشافي تمامًا، ومفيش فيك أي عيب أو شكوى... إيه اللي ممكن تخسره في الوقت ده؟ ومين اللي مش هتقدر تلومه على تعاستك بعد كده؟",
     "أنت بتستمد قيمتك واستحقاقك في الدنيا من إيه؟ مثلًا: من مجرد وجودك، ولا من حجم معاناتك وتضحياتك؟ وإمتى كانت آخر مرة حسّيت فيها إنك كافي من غير ما تعمل مجهود أو تتألم؟"],
    ["عندما تشعر بهذه المشاعر الضاغطة، هل هناك جزء في جسدك يتشنج أو يتألم؟",
     "ما هو العَرَض الجسدي أو العَرَض المتكرر الذي يلازمك دائمًا في أوقات الأزمات النفسية؟",
     "لو نظرت في المرآة الآن وركّزت في تفاصيل عينيك، من هو الشخص من ماضيك أو عائلتك أو أي شخص آخر، الذي يمكن أن ترى نظرته تسكن عينيك وتتحكم في اختياراتك؟"],
    ["ما هو الحكم القاسي الذي ترده لنفسك دائمًا عندما تفشل، ومن هو صاحب الصوت الأصلي لهذا الحكم؟ هل كان في طفولتك، مدرستك، زواجك، أم عملك؟",
     "ما الذي تظن أنك كنت مضطرًا لفعله أو تقديمه للآخرين طوال الوقت حتى تضمن استمرار حبهم وقبولهم لك؟ وماذا سيحدث لو توقفت عن تقديمه فورًا؟",
     "إذا عشت حياتك كلها متمسكًا بمبدأ معين هو سبب معاناتك، فما هو الشيء الثمين الذي تحميه، أو الشيء الذي تتجنب تحمّل مسؤوليته؟"],
]
AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def questions():
    return [q for s in STEPS for q in s]


def build(g):
    page, ic, E, OUT = g["page"], g["ic"], g["E"], g["OUT"]
    total = len(STEPS)
    steps_html, n = "", 0
    for si, qs in enumerate(STEPS, 1):
        items = ""
        for q in qs:
            n += 1
            items += (f'<div class="gf-q"><label for="gq{n}"><span class="gf-n">{str(n).translate(AR)}</span>{E(q)}</label>'
                      f'<textarea id="gq{n}" data-q="{n}" rows="4" maxlength="4000" placeholder="اكتب إجابتك هنا بحرية…"></textarea></div>')
        last = si == total
        steps_html += (f'<div class="gf-step" data-step="{si + 1}" hidden>'
                       f'<div class="gf-bar"><span>الخطوة {str(si).translate(AR)} من {str(total).translate(AR)}</span><i><b style="width:{round(si / total * 100)}%"></b></i></div>'
                       f'<p class="gf-hint">{ic("award", "icon icon-sm")}<span>كل الأسئلة اختيارية، لكن <b>كلما أجبت عن أسئلة أكثر وبتفاصيل أصدق، كان تحليلك أدق</b>. د. مرفت تقرأ إجاباتك وتكتب تحليلك بنفسها.</span></p>'
                       f'{items}<div class="gf-nav"><button type="button" class="btn btn-line" data-gf-back>السابق</button>'
                       + (f'<button type="button" class="btn btn-gold" data-gf-send>{ic("mail", "icon icon-sm")}أرسل إجاباتي لد. مرفت</button>' if last
                          else '<button type="button" class="btn btn-gold" data-gf-next>التالي</button>')
                       + '</div><p class="gf-saved">تُحفظ إجاباتك على جهازك وأنت تكتب، فيمكنك الإكمال لاحقاً.</p></div>')

    body = f'''
<section class="gf-hero"><canvas class="sparkle" data-density="1700" aria-hidden="true"></canvas><div class="wrap gf-hero-in">
  <figure class="gf-img"><img src="assets/img/gift-mask.webp" alt="قناع ذهبي: أسئلة كشف الهوية" width="1040" height="584" fetchpriority="high"></figure>
  <div class="gf-copy"><span class="vs-eyebrow">هدية مجانية من د. مرفت</span>
    <h1>اكتشف الأقنعة التي <em>تعيش بها</em></h1>
    <p>كلنا نلبس أقنعة دون أن ننتبه: قناع القوي، أو المنقذ، أو المضحّي، أو الذي لا يتأثر. في هذه الهدية تشاهد فيديو قصيراً، وتجيب عن <b>أسئلة كشف الهوية</b> بقلبك، ثم يصلك <b>تحليل شخصي</b> لهويتك والأقنعة التي تعيش بها.</p>
    <ul class="gf-facts"><li>{ic("play", "icon icon-sm")}فيديو دقيقتين</li><li>{ic("user", "icon icon-sm")}تحليل تكتبه د. مرفت بنفسها</li><li>{ic("mail", "icon icon-sm")}يصلك على بريدك خلال ٣ أيام</li><li>{ic("shield", "icon icon-sm")}إجاباتك سرية تماماً</li></ul>
    <a class="btn-safia" href="#giftApp">ابدأ الهدية</a></div></div></section>
<section class="vp-sec vp-ivory" id="giftApp"><div class="vp-wrap gf-wrap" data-gift-app>
  <div class="gf-step" data-step="0">
    <header class="vp-head"><span class="vp-orn" aria-hidden="true">✦</span><h2>لمن نرسل تحليلك؟</h2><p>اكتب اسمك وبريدك، وسنرسل التحليل عليه.</p></header>
    <div class="gf-card form"><div class="field"><label for="gName">الاسم</label><input id="gName" autocomplete="name" placeholder="اسمك كما تحب أن نناديك"></div>
      <div class="field"><label for="gEmail">البريد الإلكتروني</label><input id="gEmail" type="email" autocomplete="email" dir="ltr" placeholder="you@example.com"></div>
      <input type="text" name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
      <label class="check"><input type="checkbox" id="gConsent"><span>أوافق على أن تطّلع د. مرفت على إجاباتي لإعداد تحليلي الشخصي فقط، كما في <a href="privacy.html" target="_blank">سياسة الخصوصية</a>.</span></label>
      <label class="check"><input type="checkbox" id="gNews" checked><span>أرسلوا لي جديد د. مرفت على بريدي.</span></label>
      <div class="alert" hidden></div><button type="button" class="btn btn-gold btn-block" data-gf-start>{ic("gift", "icon icon-sm")}ابدأ الهدية</button></div></div>
  <div class="gf-step" data-step="1" hidden>
    <header class="vp-head"><span class="vp-orn" aria-hidden="true">✦</span><h2>شاهد الفيديو أولاً</h2><p>خذ نفساً عميقاً، وشاهد الفيديو بهدوء قبل أن تبدأ الإجابة.</p></header>
    <div class="gf-video"><iframe src="{GIFT_VIDEO}" loading="lazy" title="أسئلة كشف الهوية" allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture" allowfullscreen></iframe></div>
    <div class="gf-card"><h3>تعليمات مهمة</h3><ol class="gf-ins">{"".join(f"<li>{E(x)}</li>" for x in INSTRUCTIONS)}</ol></div>
    <div class="gf-nav"><button type="button" class="btn btn-line" data-gf-back>السابق</button><button type="button" class="btn btn-gold" data-gf-next>ابدأ الإجابة</button></div></div>
  {steps_html}
  <div class="gf-step gf-done" data-step="{total + 2}" hidden>
    <span class="gf-done-ico">{ic("check")}</span><h2>وصلتنا إجاباتك</h2>
    <p>شكراً لصدقك وشجاعتك. د. مرفت ستقرأ إجاباتك بنفسها، ويصلك <b>تحليلك الشخصي على بريدك خلال ٣ أيام</b>. إن لم تجده، انظر في مجلد الرسائل غير المرغوب فيها.</p>
    <p class="gf-closing">أنوي لك التشافي بكل حب</p>
    <div class="ctas" style="justify-content:center"><a class="btn btn-gold" href="library.html">تصفّح أدوات د. مرفت</a><a class="btn btn-line" href="sessions.html">احجز جلسة فردية</a></div></div>
  <p class="gf-note">هذا التحليل للتطوير الذاتي والوعي، وليس تشخيصاً أو علاجاً طبياً أو نفسياً.</p>
</div></section>'''
    page("gift.html", "هدية: أسئلة كشف الهوية", "هدية مجانية من د. مرفت سرور: شاهد فيديو أسئلة كشف الهوية، أجب بقلبك، ويصلك تحليل شخصي لهويتك والأقنعة التي تعيش بها تكتبه د. مرفت بنفسها.",
         body, og="og-gift.jpg")
    qs = questions()
    (OUT / "api/_gift_questions.php").write_text("<?php\nreturn " + "[\n" + "".join("  " + json.dumps(q, ensure_ascii=False) + ",\n" for q in qs) + "];\n", encoding="utf-8")
