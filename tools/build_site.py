#!/usr/bin/env python3
"""Builds the static, fully clickable prototype of the site into ./site
   Content lives in DATA below; templates are plain Python f-strings.
   Usage: python3 tools/build_site.py
"""
import json, os, shutil, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "src", ROOT / "site"
SITE_URL = "https://mervatsoror.com"   # TODO: replace with the real domain
NAME = "د. مرفت سرور"
E = html.escape

# ------------------------------------------------------------------ data
def lessons_ex(main_title, dur):
    return [{"title": "التمرين", "lessons": [["مقدمة وإرشادات قبل البدء", "3:10", True], [main_title, dur], ["خطة التطبيق اليومي (٢١ يوماً)", "4:30"]]}]

PRODUCTS = [
  dict(id="vip-m", kind="vip", title="استيقظ VIP · شهري", catLabel="برنامج تدريبي", img="assets/img/thumb-vip.webp", eg=2999, us=149, page="vip.html"),
  dict(id="vip-q", kind="vip", title="استيقظ VIP · ٣ أشهر", catLabel="برنامج تدريبي", img="assets/img/thumb-vip.webp", eg=7999, us=399, page="vip.html"),
  dict(id="vip-y", kind="vip", title="استيقظ VIP · سنوي", catLabel="برنامج تدريبي", img="assets/img/thumb-vip.webp", eg=29999, us=1499, page="vip.html"),
  dict(id="ain-sahia", kind="course", slug="course-ain-sahia", title="عين صاحية", cat="course", catLabel="كورس صوتي", img="assets/img/covers/ain-sahia-sm.webp", cover="assets/img/covers/ain-sahia-sm.webp", coverLg="assets/img/covers/ain-sahia.webp", eg=1499, us=75,
       level="متقدم", ctype="تطوير ذات", cardMeta="كورس صوتي · متقدم",
       facts=[["headphones","كورس صوتي في الامتنان"],["path","تطبيق يومي قصير مع كل درس"],["lessons","عدد الدروس يُعلن قريباً"]],
       meta="كورس صوتي في الامتنان · تطبيق يومي", vipIncluded=False,
       short="كورس الامتنان: كيف تقول «الحمد لله رب العالمين» من قلبك، وتشكر الله بالشكل الصحيح، وترى ما يتغيّر في حياتك حين تمتنّ كل يوم.",
       desc=["«عين صاحية» كورس صوتي في الامتنان. يعلّمك كيف ترى النِّعم التي اعتدت عليها حتى لم تعد تراها، وكيف تقول «الحمد لله» بقلب حاضر لا بلسان معتاد.",
             "تتعلّم معنى الشكر الحقيقي وطريقته الصحيحة، وتبني عادة امتنان يومية بسيطة، وتلاحظ بنفسك كيف يتغيّر إحساسك ونظرتك وعلاقاتك حين تمتنّ كل يوم.",
             "تسمعه في وقتك وبالترتيب، ومع كل درس تطبيق قصير. الموقع يحفظ تقدّمك وتكمل من حيث توقفت."],
       forWho=["تشعر أنك تملك الكثير لكنك لا تشعر بالرضا", "تقول الحمد لله كثيراً وتريد أن تشعر بها فعلاً", "يغلب عليك التركيز على ما ينقصك", "تريد عادة يومية بسيطة تغيّر إحساسك بحياتك"],
       modules=[{"title":"المقدمة","lessons":[["لماذا الامتنان؟","8:00",True],["كيف تستفيد من الكورس","5:00"]]},
                {"title":"الوحدة الأولى: معنى الحمد الحقيقي","lessons":[["الحمد لله رب العالمين بقلب حاضر","12:00"],["النِّعم التي لم نعد نراها","12:00"],["الشكر بالشكل الصحيح","12:00"]]},
                {"title":"الوحدة الثانية: الامتنان كل يوم","lessons":[["تمرين الامتنان الصباحي","10:00"],["الامتنان في الأوقات الصعبة","12:00"],["الامتنان في العلاقات","12:00"]]},
                {"title":"الوحدة الثالثة: ما يتغيّر في حياتك","lessons":[["كيف يغيّر الامتنان نظرتك","12:00"],["خطة ٣٠ يوماً","9:00"],["الختام","6:00"]]}]),
  dict(id="attach", kind="exercise", slug="exercise-detachment", title="تمرين فك التعلّق", cat="free", catLabel="فك التعلّق", img="assets/img/covers/attach-sm.webp", cover="assets/img/covers/attach-sm.webp", coverLg="assets/img/covers/attach.webp", eg=349, us=19, isNew=True, vipIncluded=True,
       meta="تأمل · ١٠ دقائق", level="مبتدئ", ctype="تأمل", cardMeta="تأمل · ١٠ دقائق",
       facts=[["play","تأمل موجّه مدته ١٠ دقائق"],["lessons","مع مقدمة قصيرة تشرح التمرين"]],
       short="تأمل موجّه مدته ١٠ دقائق يساعدك على تحرير التعلّق بشخص أو موقف أو نتيجة، والعودة إلى مركزك.",
       desc=["التعلّق يجعل سلامك الداخلي مرهوناً بشيء خارجك. في هذا التأمل الموجّه مع د. مرفت تلاحظ التعلّق، وتفهم ما يحاول أن يحميه، ثم تحرّره بهدوء.","يبدأ بمقدمة قصيرة تشرح التمرين وطريقته، ثم التأمل نفسه في ١٠ دقائق، ويمكنك تكراره كلما احتجت إليه."],
       forWho=["تعلّق بعلاقة انتهت أو لم تبدأ","قلق دائم من فقدان شخص أو شيء","صعوبة في ترك النتائج لله","تفكير متكرر لا يتوقف"],
       modules=[{"title":"التمرين","lessons":[["مقدمة: شرح التمرين وطريقته","3:00",True],["تأمل فك التعلّق","10:00"]]}]),
  dict(id="decode-original", kind="exercise", slug="decoding-original-version", title="Decoding النسخة الأصلية", cat="decode", catLabel="Decoding", img="assets/img/covers/decode-original-sm.webp", cover="assets/img/covers/decode-original-sm.webp", coverLg="assets/img/covers/decode-original.webp", level="متقدم", eg=649, us=35, isNew=True, vipIncluded=True,
       meta="تمرين تشريحي للعقل اللاواعي · ١٠ دقائق", ctype="Decoding · تمرين تشريحي للعقل اللاواعي", cardMeta="تمرين تشريحي · ١٠ دقائق",
       facts=[["play","تمرين تشريحي للعقل اللاواعي مدته ١٠ دقائق"],["lessons","مع مقدمة قصيرة تشرح التمرين"]],
       short="تمرين تشريحي للعقل اللاواعي، فريد من نوعه: صور مركّبة بطريقة خاصة تخترق طبقات العقل اللاواعي، وتعمل على كشف نسختك الأصلية وإيصالك إليها.",
       desc=["«Decoding النسخة الأصلية» ليس تأملاً، بل تمرين تشريحي للعقل اللاواعي، فريد من نوعه صمّمته د. مرفت. يعتمد على صور معيّنة مركّبة مع بعضها بطريقة خاصة، تخترق طبقات العقل اللاواعي مباشرة.",
             "تبدأ هذه الصور في العمل على كشف ما غطّى نسختك الأصلية من برمجة وقناعات ليست لك، لتصل تدريجياً إلى نسختك الأصلية الحرة.",
             "يبدأ بمقدمة قصيرة تشرح التمرين وطريقة مشاهدته، ثم التمرين نفسه في ١٠ دقائق، ويمكنك تكراره لتعميق أثره."],
       forWho=["تشعر أنك لا تعيش حياتك أنت","تحمل قناعات قاسية عن نفسك","تريد أن تعرف ماذا تريد فعلاً","تبحث عن هوية أهدأ وأصدق"],
       modules=[{"title":"التمرين","lessons":[["مقدمة: شرح التمرين وطريقة مشاهدته","3:00",True],["تمرين Decoding النسخة الأصلية","10:00"]]}]),
  dict(id="decode-acceptance", kind="exercise", slug="decoding-light-of-acceptance", title="Decoding نور القبول", cat="decode", catLabel="Decoding", img="assets/img/covers/decode-acceptance-sm.webp", cover="assets/img/covers/decode-acceptance-sm.webp", coverLg="assets/img/covers/decode-acceptance.webp", level="متقدم", eg=649, us=35, vipIncluded=True,
       meta="تمرين تشريحي للعقل اللاواعي · ١٠ دقائق", ctype="Decoding · تمرين تشريحي للعقل اللاواعي", cardMeta="تمرين تشريحي · ١٠ دقائق",
       facts=[["play","تمرين تشريحي للعقل اللاواعي مدته ١٠ دقائق"],["lessons","مع مقدمة قصيرة تشرح التمرين"],["path","أسئلة تفتح مساحة للاوعي ليكتشف جذور الرفض"]],
       short="تمرين تشريحي للعقل اللاواعي لقبول الذات: يساعدك على الخروج من جرح الرفض والهجر، وأن تقبل نفسك أولاً حتى يبدأ الناس في الخارج بقبولك.",
       desc=["«نور القبول» تمرين Decoding تشريحي للعقل اللاواعي، مدته ١٠ دقائق، يتحدث عن قبول الذات، وكيف تتخلّى عن جرح الرفض والهجر الذي حملته طويلاً.",
             "الأسئلة داخل التمرين تفتح مساحة للعقل اللاواعي ليبدأ في اكتشاف: من أول شخص رفضك؟ وما الأحداث التي جعلتك تشعر بالرفض؟",
             "حين ترى الجذور بوضوح، تستطيع أن تخرج من جرح الرفض، وأن تقبل نفسك أولاً، فيبدأ الناس في الخارج بقبولك."],
       forWho=["تشعر بالرفض أو الهجر في علاقاتك","تبحث دائماً عن قبول الآخرين","تخاف أن يتركك من تحب","تجد صعوبة في قبول نفسك كما أنت"],
       modules=[{"title":"التمرين","lessons":[["مقدمة: شرح التمرين","3:00",True],["تمرين Decoding نور القبول","10:00"]]}]),
  dict(id="decode-stagnation", kind="exercise", slug="decoding-energy-stagnation", title="Decoding الركود والخمول", cat="decode", catLabel="Decoding", img="assets/img/covers/decode-stagnation-sm.webp", cover="assets/img/covers/decode-stagnation-sm.webp", coverLg="assets/img/covers/decode-stagnation.webp", eg=649, us=35, isNew=True, vipIncluded=True,
       meta="تمرين تشريحي للعقل اللاواعي · ١٠ دقائق", ctype="Decoding · تمرين تشريحي للعقل اللاواعي", level="متقدم", cardMeta="تمرين تشريحي · ١٠ دقائق",
       facts=[["play","تمرين تشريحي للعقل اللاواعي مدته ١٠ دقائق"],["lessons","مع مقدمة قصيرة تشرح التمرين"]],
       short="تمرين تشريحي للعقل اللاواعي يفكّ الركود والخمول: الكسل والتجمّد الذي يمنعك من التحرك نحو أهدافك.",
       desc=["«Decoding الركود والخمول» تمرين تشريحي للعقل اللاواعي، مدته ١٠ دقائق، يتعامل مع حالة يعرفها كثيرون: الكسل والخمول، وعدم القدرة على التحرك نحو أهدافك رغم أنك تعرف ما تريد.",
             "في حالة الركود والخمول تبقى متجمّداً في مكانك: تقضي الوقت في التمرير على الموبايل، أو تُلهي نفسك بأي شيء، وتؤجّل الخطوة التي تعرف أنها مهمة.",
             "التمرين يعمل على فكّ هذا الركود من جذوره في العقل اللاواعي، لتعود الطاقة للتدفق، وتستطيع أن تتحرك فعلاً نحو أهدافك."],
       forWho=["تشعر بكسل وخمول دون سبب واضح","تقضي وقتاً طويلاً في التمرير على الموبايل","تعرف أهدافك لكنك لا تتحرك نحوها","تبدأ ثم تتوقف، وتؤجّل باستمرار"],
       modules=[{"title":"التمرين","lessons":[["مقدمة: شرح التمرين","3:00",True],["تمرين Decoding الركود والخمول","10:00"]]}]),
  dict(id="inner-child", kind="exercise", slug="inner-child-healing", title="تمرين تشافي الطفل الداخلي", cat="heal", catLabel="التشافي", img="assets/img/covers/inner-child-sm.webp", cover="assets/img/covers/inner-child-sm.webp", coverLg="assets/img/covers/inner-child.webp", eg=449, us=25, vipIncluded=True,
       meta="تمرين عميق · ١٠ دقائق", level="متوسط", ctype="تشافي الطفل الداخلي", cardMeta="تمرين عميق · ١٠ دقائق",
       facts=[["play","تمرين عميق مدته ١٠ دقائق"],["lessons","مع مقدمة قصيرة تشرح التمرين"]],
       short="تمرين عميق لتشافي الطفل الداخلي: تدخل في مساحة آمنة معه، تكتشفه، وتتعرّف على ما مرّ به في طفولتك.",
       desc=["«تشافي الطفل الداخلي» تمرين عميق مدته ١٠ دقائق، يأخذك إلى مساحة آمنة تلتقي فيها بطفلك الداخلي، الطفل الذي كنته وما زال يعيش داخلك.",
             "من خلال التمرين تكتشف طفلك الداخلي، وتكتشف أشياء كثيرة جداً: هل تعرّضت لصدمة؟ هل مررت بمشكلة في طفولتك ما زالت تؤثر فيك حتى اليوم؟",
             "حين ترى ما عاشه هذا الطفل، تبدأ رحلة تشافيه، وتمنحه الأمان الذي احتاجه."],
       forWho=["ردود فعل عاطفية قوية ومفاجئة","ذكريات طفولة مؤلمة أو غير واضحة","احتياج دائم للأمان والقبول","تشعر أن جرحاً قديماً ما زال يؤثر فيك"],
       modules=[{"title":"التمرين","lessons":[["مقدمة: شرح التمرين","3:00",True],["تمرين تشافي الطفل الداخلي","10:00"]]}]),
  dict(id="heart-coherence", kind="exercise", slug="heart-coherence-breathing", title="تنفّس الاتزان الداخلي", cat="breath", catLabel="تنفّس", img="assets/img/covers/breath-sm.webp", cover="assets/img/covers/breath-sm.webp", coverLg="assets/img/covers/breath.webp", eg=249, us=12, vipIncluded=True,
       meta="تمرين تنفّس · ١٠ دقائق", level="متوسط", ctype="تنفّس · تقنية الاتساق القلبي", cardMeta="تمرين تنفّس · ١٠ دقائق",
       facts=[["play","تمرين تنفّس بتقنية الاتساق القلبي مدته ١٠ دقائق"],["heart","يعطي إشارة أمان للعصب الحائر والمخ والقلب"],["lessons","مع مقدمة قصيرة تشرح التمرين"]],
       short="تمرين تنفّس بتقنية الاتساق القلبي، يخلق توازناً بين موجات الدماغ وإيقاع القلب، وينقلك من الانقباض إلى حالة من التشافي والاتصال.",
       desc=["«تنفّس الاتزان الداخلي» تمرين تنفّس قائم على تقنية الاتساق القلبي، أساسها خلق توازن هرموني وعصبي بين موجات الدماغ ومعدل التغيّر في ضربات القلب.",
             "هذه الطريقة هي اليُسر الفعلي للعبور من الترددات المنخفضة والانقباض على سلّم هوكينز للوعي، إلى المستويات المرتفعة من الوعي.",
             "التنفّس يمكن أن يحرّرك من البقاء محبوساً في حالة استنفار بيولوجي ودفاع مستمر. فعن طريق الاتساق القلبي تعطي إشارة أمان للعصب الحائر وللمخ والقلب، فتنتقل إلى حالة من التشافي والاتصال."],
       forWho=["توتر وقلق مستمر وشعور بالاستنفار","إحساس بالانقباض وثقل الطاقة","صعوبة في الاسترخاء أو النوم","رغبة في رفع مستوى وعيك وطاقتك"],
       modules=[{"title":"التمرين","lessons":[["مقدمة: شرح التمرين","3:00",True],["تنفّس الاتزان الداخلي","10:00"]]}]),
  dict(id="morning-priming", kind="exercise", slug="morning-priming", title="تمرين Priming الصباح", cat="priming", catLabel="Priming", img="assets/img/covers/morning-priming-sm.webp", cover="assets/img/covers/morning-priming-sm.webp", coverLg="assets/img/covers/morning-priming.webp", eg=249, us=12, vipIncluded=True,
       meta="توكيدات صباحية · ١٠ دقائق", level="مبتدئ", ctype="توكيدات صباحية · تشافٍ جسدي", cardMeta="توكيدات صباحية · ١٠ دقائق",
       facts=[["play","توكيدات صباحية يومية مدتها ١٠ دقائق"],["heart","معظمها يتحدث مع الجسد ويدعم شفاءه"],["lessons","مع مقدمة قصيرة تشرح التمرين"]],
       short="توكيدات صباحية يومية تساعدك على استقبال يومك بشكل جميل، وتدعم تشافي جسدك.",
       desc=["«Priming الصباح» تمرين توكيدات يومية تسمعه مع بداية يومك، يساعدك على استقبال الصباح بشكل جميل، ويهيّئك ليوم جديد وسعيد.",
             "معظم التوكيدات تتحدث مع الجسد وتدعم الشفاء الجسدي، فتبدأ يومك وأنت في سلام مع جسدك وممتن له.",
             "مع التكرار كل صباح، يصبح عادة تضبط حالتك الداخلية قبل أن يبدأ اليوم."],
       forWho=["تبدأ يومك بقلق أو ثقل","تمرّ بتعب أو ألم جسدي وتريد دعم شفائك","تريد روتيناً صباحياً قصيراً وثابتاً","تحب أن تستقبل يومك بطاقة هادئة وجميلة"],
       modules=[{"title":"التمرين","lessons":[["مقدمة: شرح التمرين","3:00",True],["توكيدات Priming الصباح","10:00"]]}]),
  dict(id="peace-affirmations", kind="exercise", slug="peace-affirmations", title="توكيدات السلام للتشافي العميق", cat="heal", catLabel="التشافي", img="assets/img/covers/peace-sm.webp", cover="assets/img/covers/peace-sm.webp", coverLg="assets/img/covers/peace.webp", level="مبتدئ", eg=249, us=12, vipIncluded=True,
       meta="توكيدات يومية · ساعة ودقيقة", ctype="توكيدات · برمجة العقل اللاواعي", cardMeta="توكيدات يومية · ساعة ودقيقة",
       facts=[["play","توكيدات عن السلام والطمأنينة مدتها ساعة ودقيقة"],["path","للتطبيق اليومي لبرمجة العقل اللاواعي"],["lessons","مع مقدمة قصيرة تشرح التمرين"]],
       short="تمرين للتطبيق اليومي: توكيدات عن السلام والطمأنينة لبرمجة العقل اللاواعي.",
       desc=["«توكيدات السلام للتشافي العميق» تمرين للتطبيق اليومي، يعمل على برمجة العقل اللاواعي من خلال توكيدات عن السلام والطمأنينة.",
             "مدته ساعة ودقيقة، تستمع إليه بهدوء كل يوم، فتترسّخ معاني السلام والطمأنينة في عقلك اللاواعي يوماً بعد يوم، ويحلّ الهدوء مكان القلق.",
             "يمكنك الاستماع إليه وأنت مسترخٍ أو قبل النوم."],
       forWho=["قلق وتوتر مستمر","حديث داخلي قاسٍ أو مقلق","صعوبة في الهدوء قبل النوم","رغبة في برمجة يومية للسلام والطمأنينة"],
       modules=[{"title":"التمرين","lessons":[["مقدمة: شرح التمرين","3:00",True],["توكيدات السلام والطمأنينة","61:00"]]}]),
  dict(id="serenity", kind="exercise", slug="serenity-cleansing-meditation", title="تأمل السكينة والتنظيف", cat="breath", catLabel="تأمل", img="assets/img/covers/serenity-sm.webp", cover="assets/img/covers/serenity-sm.webp", coverLg="assets/img/covers/serenity.webp", level="متقدم", ctype="تأمل للتنظيف والتحرر", eg=449, us=25, vipIncluded=True,
       meta="تأمل للتنظيف · ٣ أقسام", cardMeta="تأمل للتنظيف · ٣ أقسام",
       facts=[["play","تأمل موجّه للتنظيف من المشاعر السلبية"],["layers","٣ أقسام: التنفس، التحرر، الحماية"],["lessons","مع مقدمة قصيرة تشرح التأمل"]],
       short="تأمل موجّه للتنظيف في ثلاثة أقسام: التنفس، ثم التحرر من المشاعر السلبية، ثم الحماية بنور يغلّف جسدك بالكامل.",
       desc=["«السكينة والتنظيف» تأمل موجّه بصوت د. مرفت للتحرر من المشاعر السلبية والابتعاد عنها، والعودة إلى السكينة.",
             "التأمل مقسّم إلى ثلاثة أقسام. القسم الأول هو التنفس، تهدأ فيه وتعود إلى جسدك.",
             "القسم الثاني هو التحرر: تتخيّل دخاناً يمثّل المشاعر السلبية، وتلاحظ أين يوجد هذا الدخان في جسدك بالضبط، ثم تبدأ في تحرير مشاعرك من خلاله.",
             "القسم الأخير هو الحماية: تتخيّل نوراً ينزل من السماء ويغلّف جسدك بالكامل، ليحميك من أي طاقات سلبية."],
       forWho=["ثقل عاطفي متراكم","مشاعر سلبية لا تعرف كيف تتخلص منها","تتأثر بطاقات من حولك بسهولة","حاجة إلى هدوء وحماية داخلية"],
       modules=[{"title":"التأمل","lessons":[["مقدمة: شرح التأمل","3:00",True],["القسم الأول: التنفس","5:00"],["القسم الثاني: التحرر","8:00"],["القسم الثالث: الحماية","5:00"]]}]),
  dict(id="book-ghosts", kind="book", slug="book-ghosts", title="عندما تولد في عائلة من الأشباح", cat="book", catLabel="كتاب إلكتروني", img="assets/art/book.webp", eg=349, us=14, vipIncluded=False,
       meta="كتاب · يُقرأ داخل الموقع", short="عن الموروث العائلي الذي نحمله دون أن نراه، وكيف نتحرر منه بوعي ورحمة.", learn="reader.html"),
  dict(id="lp-serenity", kind="offer", grants="serenity", title="تأمل السكينة والتنظيف · عرض خاص", catLabel="عرض خاص", img="assets/img/covers/serenity-sm.webp", eg=299, us=15, page="lp-serenity.html"),
  dict(id="lp-attach", kind="offer", grants="attach", title="تمرين فك التعلّق · عرض خاص", catLabel="عرض خاص", img="assets/img/covers/attach-sm.webp", eg=249, us=14, page="lp-attach.html"),
  dict(id="b-original", kind="bundle", title="باقة النسخة الأصلية", catLabel="باقة", img="assets/img/covers/decode-original-sm.webp", eg=1199, us=65, page="bundles.html"),
  dict(id="b-acceptance", kind="bundle", title="باقة نور القبول", catLabel="باقة", img="assets/img/covers/decode-acceptance-sm.webp", eg=1199, us=65, page="bundles.html"),
  dict(id="b-stagnation", kind="bundle", title="باقة فكّ الركود والخمول", catLabel="باقة", img="assets/img/covers/decode-stagnation-sm.webp", eg=1199, us=65, page="bundles.html"),
  dict(id="b-peace", kind="bundle", title="باقة السلام والطمأنينة", catLabel="باقة", img="assets/img/covers/peace-sm.webp", eg=879, us=45, page="bundles.html"),
  dict(id="b-child", kind="bundle", title="باقة تشافي الطفل الداخلي", catLabel="باقة", img="assets/img/covers/inner-child-sm.webp", eg=1039, us=55, page="bundles.html"),
  dict(id="b-attach", kind="bundle", title="باقة فكّ التعلّق", catLabel="باقة", img="assets/img/covers/attach-sm.webp", eg=959, us=49, page="bundles.html"),
  dict(id="s-intro", kind="session", title="جلسة تعارف · ٣٠ دقيقة", catLabel="جلسة فردية", img="assets/img/thumb-session.webp", eg=399, us=25, page="sessions.html"),
  dict(id="s-single", kind="session", title="جلسة استشارة فردية · ٦٠ دقيقة", catLabel="جلسة فردية", img="assets/img/thumb-session.webp", eg=599, us=59, page="sessions.html"),
  dict(id="s-pack", kind="session", title="باقة ٤ جلسات", catLabel="جلسات فردية", img="assets/img/thumb-session.webp", eg=1999, us=149, page="sessions.html"),
  dict(id="s-coach", kind="session", title="جلسة كوتشينج · ٦٠ دقيقة", catLabel="جلسة فردية", img="assets/img/thumb-session.webp", eg=750, us=69, page="sessions.html"),
  dict(id="serenity-gift", kind="gift", title="هدية: مقدمة تأمل السكينة", catLabel="هدية", img="assets/art/calm.webp", eg=0, us=0, page="index.html", learn="learn.html#serenity"),
]
for p in PRODUCTS:
    if p.get("slug"): p["page"] = p["slug"] + ".html"
    if p.get("modules"):
        p["learn"] = "learn.html#" + p["id"]
        p["lessonsCount"] = sum(len(m["lessons"]) for m in p["modules"])
BUNDLES = [
  dict(id="b-original", items=["heart-coherence","morning-priming","serenity","decode-original"], flow=["تنفّس الاتزان الداخلي","Priming الصباح","تأمل السكينة والتنظيف","Decoding النسخة الأصلية"], fan=["assets/img/covers/breath-sm.webp","assets/img/covers/decode-original-sm.webp","assets/img/covers/serenity-sm.webp"]),
  dict(id="b-acceptance", items=["heart-coherence","morning-priming","serenity","decode-acceptance"], flow=["تنفّس الاتزان الداخلي","Priming الصباح","تأمل السكينة والتنظيف","Decoding نور القبول"], fan=["assets/img/covers/breath-sm.webp","assets/img/covers/decode-acceptance-sm.webp","assets/img/covers/serenity-sm.webp"]),
  dict(id="b-stagnation", items=["heart-coherence","morning-priming","serenity","decode-stagnation"], flow=["تنفّس الاتزان الداخلي","Priming الصباح","تأمل السكينة والتنظيف","Decoding الركود والخمول"], fan=["assets/img/covers/breath-sm.webp","assets/img/covers/decode-stagnation-sm.webp","assets/img/covers/serenity-sm.webp"]),
  dict(id="b-peace", items=["heart-coherence","morning-priming","serenity","peace-affirmations"], flow=["تنفّس الاتزان الداخلي","Priming الصباح","تأمل السكينة والتنظيف","توكيدات السلام للتشافي العميق"], fan=["assets/img/covers/breath-sm.webp","assets/img/covers/peace-sm.webp","assets/img/covers/serenity-sm.webp"]),
  dict(id="b-child", items=["heart-coherence","morning-priming","serenity","inner-child"], flow=["تنفّس الاتزان الداخلي","Priming الصباح","تأمل السكينة والتنظيف","تشافي الطفل الداخلي"], fan=["assets/img/covers/breath-sm.webp","assets/img/covers/inner-child-sm.webp","assets/img/covers/serenity-sm.webp"]),
  dict(id="b-attach", items=["heart-coherence","morning-priming","serenity","attach"], flow=["تنفّس الاتزان الداخلي","Priming الصباح","تأمل السكينة والتنظيف","فكّ التعلّق"], fan=["assets/img/covers/breath-sm.webp","assets/img/covers/attach-sm.webp","assets/img/covers/serenity-sm.webp"]),
]
BY = {p["id"]: p for p in PRODUCTS}
EXERCISES = [p for p in PRODUCTS if p["kind"] == "exercise"]
CATS = [("all","الكل"),("course","الكورسات"),("decode","Decoding"),("priming","Priming"),("free","فك التعلّق"),("heal","التشافي"),("breath","تنفّس وتأمل")]
COUNTRIES = [("EG","مصر"),("SA","السعودية"),("AE","الإمارات"),("KW","الكويت"),("QA","قطر"),("BH","البحرين"),("OM","عُمان"),("JO","الأردن"),("LB","لبنان"),("MA","المغرب"),("DZ","الجزائر"),("TN","تونس"),("US","الولايات المتحدة"),("GB","المملكة المتحدة"),("CA","كندا"),("DE","ألمانيا"),("XX","دولة أخرى")]
BOOK_PAGES = [
  "<h2>المقدمة</h2><p>هذه صفحة نموذجية لقارئ الكتاب. في الموقع الفعلي تظهر هنا صفحات كتاب «عندما تولد في عائلة من الأشباح» من ملف PDF، صفحةً بعد صفحة، دون أي إمكانية للتحميل.</p><p>لاحظ العلامة المائية الخفيفة باسم حسابك على الصفحة: هي ما يحمي الكتاب من النسخ والمشاركة.</p>",
  "<h2>الفصل الأول</h2><p>نص تجريبي للفصل الأول. يستطيع الزائر قراءة الفصل الأول مجاناً بعد إنشاء حساب، ثم يُطلب منه شراء الكتاب لإكمال القراءة.</p><p>الموقع يتذكّر آخر صفحة وصلت إليها، فتكمل من نفس المكان على أي جهاز.</p>",
  "<h2>الفصل الأول (تابع)</h2><p>نص تجريبي. هذه آخر صفحة في المعاينة المجانية.</p>",
  "<h2>الفصل الثاني</h2><p>نص تجريبي متاح بعد الشراء فقط.</p>",
  "<h2>الفصل الثالث</h2><p>نص تجريبي متاح بعد الشراء فقط.</p>",
]
DATA = {"products": PRODUCTS, "bundles": BUNDLES, "countries": COUNTRIES, "bookPages": BOOK_PAGES, "freePages": 3,
        "slots": ["١٠:٠٠ ص","١٢:٠٠ م","٢:٠٠ م","٥:٠٠ م","٧:٠٠ م","٩:٠٠ م"], "defaultLearn": "ain-sahia"}

# ------------------------------------------------------------------ icons
ICONS = {
 "bag":'<circle cx="9" cy="20" r="1.4"/><circle cx="17" cy="20" r="1.4"/><path d="M2.5 4h2.4l2.4 11h10.6L20.5 7.5H6.2"/>',
 "share":'<circle cx="17.5" cy="5.5" r="2.3"/><circle cx="6.5" cy="12" r="2.3"/><circle cx="17.5" cy="18.5" r="2.3"/><path d="M8.6 10.9l6.8-4.1M8.6 13.1l6.8 4.1"/>',
 "sort":'<path d="M4 7h16M7 12h10M10 17h4"/>',
 "lessons":'<rect x="4" y="4" width="13" height="16" rx="2"/><path d="M8 9h5M8 13h5M20 7v12"/>',
 "plus":'<path d="M12 5v14M5 12h14"/>', "check":'<path d="M5 12.5l4.2 4.2L19 7"/>',
 "heart":'<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
 "user":'<circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20c1.4-3.6 4.2-5.2 7.5-5.2s6.1 1.6 7.5 5.2"/>',
 "play":'<path d="M8 5.5v13l10.5-6.5z"/>', "pause":'<path d="M8 5v14M16 5v14"/>',
 "back":'<path d="M11 7l-5 5 5 5M18 7l-5 5 5 5"/>', "fwd":'<path d="M13 7l5 5-5 5M6 7l5 5-5 5"/>',
 "live":'<rect x="3" y="6" width="13" height="12" rx="3"/><path d="M16 10.5l5-3v9l-5-3"/>',
 "lib":'<path d="M4 5h4v14H4zM10 5h4v14h-4zM16.5 5.5l3.5 1-3.5 13-3.5-1"/>',
 "path":'<path d="M4 19c5 0 4-6 8-6s3-6 8-6"/><circle cx="4" cy="19" r="1.5"/><circle cx="20" cy="7" r="1.5"/>',
 "crown":'<path d="M4 17l-1-9 5 4 4-7 4 7 5-4-1 9z"/><path d="M5 20h14"/>',
 "book":'<path d="M12 6.5C9.5 5 6.5 4.6 3.5 5.2v13c3-.6 6-.2 8.5 1.3 2.5-1.5 5.5-1.9 8.5-1.3v-13c-3-.6-6-.2-8.5 1.3zM12 6.5v13"/>',
 "lock":'<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
 "mark":'<path d="M7 4h10v16l-5-4-5 4z"/>', "cal":'<rect x="4" y="5.5" width="16" height="15" rx="3"/><path d="M4 10h16M9 3v4M15 3v4"/>',
 "bell":'<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
 "globe":'<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.6 2.5 14.4 0 17M12 3.5c-2.5 2.6-2.5 14.4 0 17"/>',
 "award":'<circle cx="12" cy="9" r="5.5"/><path d="M8.5 13.5L7 21l5-2.5 5 2.5-1.5-7.5"/>',
 "clock":'<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
 "layers":'<path d="M12 4l8.5 4.5L12 13 3.5 8.5z"/><path d="M3.5 12.5L12 17l8.5-4.5"/>',
 "mail":'<rect x="3.5" y="5.5" width="17" height="13" rx="2.5"/><path d="M4 7l8 6 8-6"/>',
 "phone":'<path d="M6 3.5h3l1.5 4-2 1.5a11 11 0 0 0 6.5 6.5l1.5-2 4 1.5v3a2 2 0 0 1-2 2A16 16 0 0 1 4 5.5a2 2 0 0 1 2-2z"/>',
 "pin":'<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
 "chat":'<path d="M4 18.5l1.3-3.6A7.5 7.5 0 1 1 8.6 18z"/>', "search":'<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
 "gift":'<rect x="3.5" y="8" width="17" height="4" rx="1"/><path d="M5 12v8h14v-8M12 8v12M12 8c-2-4-6-3.5-5.5-1S12 8 12 8zm0 0c2-4 6-3.5 5.5-1S12 8 12 8z"/>',
 "shield":'<path d="M12 3.5l7 3v5c0 4.5-3 8-7 9-4-1-7-4.5-7-9v-5z"/><path d="M9 12l2 2 4-4"/>',
 "home":'<path d="M4 11l8-6.5 8 6.5V20h-5v-5H9v5H4z"/>', "receipt":'<path d="M6 3.5h12v17l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>',
 "logout":'<path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4M10 16l-4-4 4-4M6 12h10"/>', "x":'<path d="M6 6l12 12M18 6L6 18"/>',
 "headphones":'<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4.5" height="6" rx="1.5"/><rect x="16.5" y="14" width="4.5" height="6" rx="1.5"/>',
 "devices":'<rect x="3" y="5" width="13" height="10" rx="1.5"/><path d="M1.5 18h16"/><rect x="17.5" y="9" width="5" height="10" rx="1.2"/>',
 "infinity":'<path d="M7.5 9a3 3 0 1 0 0 6c3 0 6-6 9-6a3 3 0 1 1 0 6c-3 0-6-6-9-6z"/>',
}
SPRITE = '<svg width="0" height="0" style="position:absolute" aria-hidden="true">' + "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items()) + "</svg>"
def ic(n, cls="icon"): return f'<svg class="{cls}"><use href="#i-{n}"/></svg>'

# ------------------------------------------------------------------ layout
NAV = [("vip.html","استيقظ VIP","vip"),("sessions.html","الجلسات",""),("books.html","الكتب",""),("about.html","عن د. مرفت",""),("contact.html","تواصل",""),("policies.html","السياسات","")]
MEGA_PAGES = {"library.html","course-ain-sahia.html","bundles.html"}

def mega():
    col = lambda title, links: f'<div class="mcol"><b>{title}</b>' + "".join(f'<a href="{h}"><span>{E(t)}</span><small>{E(m)}</small></a>' for h,t,m in links) + '</div>'
    ex = lambda cat: [(p["page"], p["title"], p["meta"]) for p in EXERCISES if p["cat"] in cat]
    return f'''<div class="mega" id="mega"><div class="mega-in">
      {col("البرامج", [("vip.html","استيقظ VIP","البرنامج التدريبي · اشتراك"),("course-ain-sahia.html","عين صاحية","كورس الامتنان · صوتي"),("bundles.html","الباقات","مسارات بسعر أقل")])}
      {col("Decoding وتحرّر", ex(("decode","free")))}
      {col("تشافٍ وسكينة و Priming", ex(("heal","breath","priming")))}
      <div class="mcol mfeat"><a class="mcard" href="library.html"><img src="assets/art/decode.webp" alt="" loading="lazy"><span><b>كل الأدوات</b><small>تصفّح الأدوات كاملة</small></span></a>
        <a class="mlink" href="book-ghosts.html">{ic("book","icon icon-sm")}كتاب: عندما تولد في عائلة من الأشباح</a><a class="mlink" href="register.html">{ic("gift","icon icon-sm")}ابدأ بهدية مجانية</a></div>
    </div></div>'''


NAV2 = [("index.html","الرئيسية",""),("MEGA","الأدوات",""),("sessions.html","الاستشارات",""),("vip.html","برنامج استيقظ VIP","vip"),("about.html","عن مرفت",""),("contact.html","اتصل بنا","nav-contact")]

def header(active, hero=False):
    def item(h,t,c):
        if h == "MEGA":
            return f'<li class="has-mega"><button class="mega-btn" id="megaBtn" type="button" aria-expanded="false" aria-controls="mega" {"data-current=1" if active in MEGA_PAGES else ""}>الأدوات<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></button>{mega()}</li>'
        return f'<li><a href="{h}" class="{c}" {"aria-current=page" if h==active else ""}>{t}</a></li>'
    items = "".join(item(*n) for n in NAV2)
    return f'''<header class="site-header {"on-hero" if hero else "pill"}"><div class="nav">
  <a class="brand" href="index.html" aria-label="الصفحة الرئيسية"><img src="assets/brand/logo-icon-gold.webp" alt="" width="38" height="48"><span><b>مرفت سرور</b><small>Mervat Soror</small></span></a>
  <ul class="menu" id="menu">{items}</ul>
  <div class="tools">
    <a class="hdr-book" href="sessions.html#booking">{ic("cal")}<span>احجز جلسة</span></a>
    <a class="login-link js-user-text" href="login.html">تسجيل الدخول</a>
    <a class="iconbtn" href="cart.html" aria-label="السلة">{ic("bag")}<span class="count js-cart-count">٠</span></a>
    <button class="iconbtn" type="button" id="searchBtn" aria-label="بحث">{ic("search")}</button>
    <button class="iconbtn burger" id="burger" type="button" aria-expanded="false" aria-controls="menu" aria-label="القائمة"><svg class="icon" viewBox="0 0 24 24"><path d="M4 7h16M7 12h13M10 17h10"/></svg></button>
  </div>
</div></header>
<div class="search-ov" id="searchOv" hidden><div class="search-box"><div class="search">{ic("search")}<label class="sr" for="sq">ابحث في المواد</label><input id="sq" type="text" placeholder="ابحث: فك التعلّق، Decoding، تنفّس، كتاب…" autocomplete="off"><button class="iconbtn" type="button" id="searchClose" aria-label="إغلاق">{ic("x")}</button></div><div class="search-res" id="searchRes"></div></div></div>
<div class="help" id="help"><div class="help-panel" id="helpPanel" hidden><b>كيف يمكننا خدمتك؟</b><span class="muted">نرد عادةً خلال ساعات العمل.</span>
  <a href="https://wa.me/201095292748" target="_blank" rel="noopener">{ic("chat")}واتساب</a><a href="contact.html">{ic("mail")}راسلنا</a><a href="faq.html">{ic("book")}الأسئلة الشائعة</a><a href="sessions.html">{ic("cal")}احجز جلسة</a></div>
  <button class="help-btn" id="helpBtn" type="button" aria-expanded="false" aria-controls="helpPanel"><span class="help-logo"><img src="assets/brand/logo-icon-gold.webp" alt="" width="26" height="32"></span><span class="help-txt">كيف يمكننا خدمتك؟</span></button></div>
<nav class="tabbar" aria-label="تنقل سريع"><a href="index.html">{ic("home")}<span>الرئيسية</span></a><a href="library.html">{ic("lib")}<span>الأدوات</span></a><a href="vip.html" class="tb-vip">{ic("crown")}<span>VIP</span></a><a href="cart.html">{ic("bag")}<span>السلة</span><i class="count js-cart-count">٠</i></a><a href="account.html">{ic("user")}<span>حسابي</span></a></nav>'''

FOOTER = f'''<footer class="site-footer"><div class="wrap">
  <div class="f-grid">
    <div class="f-brand"><img src="assets/brand/logo-gold-transparent.webp" alt="د. مرفت سرور" width="158" height="118" loading="lazy" style="filter:drop-shadow(0 6px 18px rgba(0,0,0,.35))">
      <p>برامج وتمارين للوعي والتشافي، تعيدك إلى نسختك الأصلية بهدوء.</p><div class="f-news" style="margin-top:14px"><b style="color:#F1DDB0">انضم إلى مجتمع مرفت</b><form data-simple="تم اشتراكك في النشرة."><label class="sr" for="fnEmail">بريدك</label><input id="fnEmail" type="email" required placeholder="بريدك الإلكتروني"><button class="btn btn-pill btn-sm" type="submit">اشترك</button></form><div class="alert" hidden></div></div>
      <div class="social"><a href="#" aria-label="إنستغرام"><svg class="icon" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="5"/><circle cx="12" cy="12" r="3.6"/></svg></a><a href="#" aria-label="يوتيوب"><svg class="icon" viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="12" rx="4"/><path d="M10.5 9.5v5l4-2.5z"/></svg></a><a href="#" aria-label="تيك توك"><svg class="icon" viewBox="0 0 24 24"><path d="M14 4v10.5a3.5 3.5 0 1 1-3-3.4M14 4c.4 2.4 2 4 4.5 4.2"/></svg></a><a href="#" aria-label="فيسبوك"><svg class="icon" viewBox="0 0 24 24"><path d="M14 8h2.5V4.5H14A3.5 3.5 0 0 0 10.5 8v2.5H8V14h2.5v6H14v-6h2.5l.5-3.5h-3V8z"/></svg></a></div>
    </div>
    <div><h4>البرامج</h4><ul><li><a href="vip.html">استيقظ VIP</a></li><li><a href="course-ain-sahia.html">عين صاحية</a></li><li><a href="library.html">مكتبة الأدوات</a></li><li><a href="bundles.html">الباقات</a></li><li><a href="books.html">الكتب</a></li><li><a href="sessions.html">الجلسات الفردية</a></li></ul></div>
    <div><h4>المساعدة</h4><ul><li><a href="lp-serenity.html">✦ هبوط: السكينة والتنظيف</a></li><li><a href="lp-attach.html">✦ هبوط: فك التعلّق</a></li><li><a href="about.html">عن مرفت</a></li><li><a href="articles.html">المقالات</a></li><li><a href="faq.html">الأسئلة الشائعة</a></li><li><a href="contact.html">تواصل معنا</a></li><li><a href="account.html">حسابي</a></li><li><a href="cart.html">السلة</a></li></ul></div>
    <div><h4>تواصل</h4><ul class="f-contact"><li><a href="https://wa.me/201095292748">{ic("chat","icon icon-sm")}01095292748</a></li><li><a href="contact.html">{ic("mail","icon icon-sm")}support@mervatsoror.com</a></li><li><span>{ic("pin","icon icon-sm")}القاهرة، مصر</span></li></ul><h4 style="margin-top:18px">السياسات</h4><ul><li><a href="policies.html">كل السياسات</a></li><li><a href="terms.html">الشروط والأحكام</a></li><li><a href="privacy.html">سياسة الخصوصية</a></li><li><a href="refund.html">الاسترداد والإلغاء</a></li><li><a href="delivery.html">تقديم الخدمة</a></li></ul></div>
  </div>
  <div class="bottom"><span>© ٢٠٢٦ د. مرفت سرور. جميع الحقوق محفوظة. · <a href="terms.html" style="color:inherit">الشروط</a> · <a href="privacy.html" style="color:inherit">الخصوصية</a> · <a href="refund.html" style="color:inherit">الاسترداد</a> · <a href="delivery.html" style="color:inherit">تقديم الخدمة</a></span><div class="region foot-cur" role="group" aria-label="عرض الأسعار بـ"><button type="button" data-region="eg">جنيه مصري</button><button type="button" data-region="intl">دولار $</button></div><div class="pays" aria-label="طرق الدفع"><span>VISA</span><span>Mastercard</span><span>ميزة</span><span>فوري</span><span>محافظ</span><span>valU</span><span>PayPal</span></div></div>
</div></footer>'''

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&family=Almarai:wght@400;700&family=El+Messiri:wght@500;600;700&family=Amiri:ital@0;1&family=Great+Vibes&family=Noto+Naskh+Arabic:wght@500;700&family=Cormorant+Garamond:wght@300&display=swap">'

def page(file, title, desc, body, active="", schema=None, noindex=False, bare=False):
    full_title = title if NAME in title else f"{title} | {NAME}"
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in (schema or []))
    head = f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(full_title)}</title><meta name="description" content="{E(desc)}">
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="canonical" href="{SITE_URL}/{'' if file=='index.html' else file}">
{'<meta name="robots" content="noindex,nofollow">' if noindex else ''}
<meta property="og:type" content="website"><meta property="og:locale" content="ar_AR"><meta property="og:title" content="{E(full_title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:image" content="{SITE_URL}/assets/img/coach-white.webp">
<meta name="theme-color" content="#FDFAF5"><link rel="icon" href="assets/brand/favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="assets/brand/favicon-192.png">
{FONTS}<link rel="stylesheet" href="assets/css/site.css">{ld}'''
    content = f'''{SPRITE}
{'' if bare else header(active, hero=(file=='index.html'))}
<main id="main">{body}</main>
{'' if bare else FOOTER}
<script src="assets/js/data.js"></script><script src="assets/js/site.js"></script>'''
    doc = f'<!doctype html>\n<html lang="ar" dir="rtl"><head>{head}</head><body>{content}</body></html>\n'
    (OUT / file).write_text(doc, encoding="utf-8")
    PAGES.append((file, noindex))
    if file == "index.html":   # artifact entry: same page without the outer document tags
        (OUT / "_artifact_index.html").write_text(head.replace('<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n', "") + content, encoding="utf-8")

def crumbs(*items):
    li = "".join(f'<li><a href="{h}">{E(t)}</a></li>' if h else f'<li aria-current="page">{E(t)}</li>' for t, h in items)
    return f'<ol class="crumbs"><li><a href="index.html">الرئيسية</a></li>{li}</ol>'
def page_hero(title, lead="", *trail, eyebrow=""):
    return f'<section class="page-hero"><canvas class="sparkle" data-density="2400" aria-hidden="true"></canvas><div class="wrap">{crumbs(*(trail or [(title, None)]))}{f"<span class=eyebrow>{eyebrow}</span>" if eyebrow else ""}<h1 class="display">{title}</h1>{f"<p class=lead>{lead}</p>" if lead else ""}</div></section>'
def price(pid): p = BY[pid]; return f'<span class="price" data-price="{pid}">{p["eg"]:,} ج.م</span>'.replace(",", "")
def tabs(): return '<div class="tabs" role="group" aria-label="تصنيف التمارين">' + "".join(f'<button class="tab" type="button" data-filter="{k}" aria-pressed="{str(k=="all").lower()}">{v}</button>' for k, v in CATS) + "</div>"
def stage(img, f1=True):
    return f'''<div class="stage"><div class="arch"></div><img class="cut" src="{img}" alt="د. مرفت سرور" width="600" height="900">
      {'<div class="float f2"><span><span class="dot"></span>التسجيل مفتوح</span><b>استيقظ VIP</b></div><div class="float f1"><b>د. مرفت سرور</b>معتمدة من الاتحاد الدولي للتدريب</div>' if f1 else ''}</div>'''
GIFT = f'''<section class="wrap"><div class="gift"><div class="gift-copy"><span class="eyebrow">هدية لك</span><h2>ابدأ بهدية: مقدمة تأمل السكينة وفصل من الكتاب</h2>
  <p class="lead">أنشئ حسابك المجاني ببريدك، وتُفتح لك الهدية فوراً في مكتبتك.</p>
  <div class="ctas"><a class="btn btn-gold" href="register.html">{ic("gift")}أنشئ حسابي واستلم الهدية</a></div></div>
  <div class="fan" aria-hidden="true"><img src="assets/art/calm.webp" alt=""><img src="assets/art/book.webp" alt=""><img src="assets/art/morning.webp" alt=""></div></div></section>'''
MARQUEE = '<div class="vp-strip" aria-hidden="true"><div class="track">' + ('<span>الوعي <i>✦</i> التشافي <i>✦</i> السكينة <i>✦</i> القبول <i>✦</i> التحرّر من التعلّق <i>✦</i> الطفل الداخلي <i>✦</i> النسخة الأصلية <i>✦</i></span>' * 2) + '</div></div>'
ORG = {"@context":"https://schema.org","@type":"Organization","name":NAME,"url":SITE_URL,"logo":f"{SITE_URL}/assets/brand/logo-gold-transparent.png"}
PERSON = {"@context":"https://schema.org","@type":"Person","name":"مرفت سرور","jobTitle":"مدربة وعي وتشافي معتمدة من ICF","url":f"{SITE_URL}/about.html","image":f"{SITE_URL}/assets/img/coach-white.webp","memberOf":{"@type":"Organization","name":"International Coaching Federation (ICF)"}}

def vip_card():
    return f'''<div class="vip-card"><div class="vip-art"><div class="arch-img"><img src="assets/img/coach-green.webp" alt="د. مرفت سرور" width="900" height="1125" loading="lazy"></div></div>
  <div class="vip-body"><span class="eyebrow">البرنامج التدريبي الأساسي</span><h2><span class="foil-text">استيقظ VIP</span></h2>
    <p class="lead">رحلة شهرية متدرّجة مع د. مرفت، تجمع الوعي والتطبيق اليومي والمتابعة. هنا يبدأ التغيير الذي يستمر.</p>
    <ul class="inc">
      <li><span class="ico">{ic("live")}</span><span><b>جلسات خاصة</b>جلسات فردية بينك وبين د. مرفت فقط</span></li>
      <li><span class="ico">{ic("lib")}</span><span><b>المكتبة كاملة</b>كل التمارين مفتوحة طوال اشتراكك</span></li>
      <li><span class="ico">{ic("path")}</span><span><b>خطة يومية</b>تطبيق واضح ومتابعة لتقدّمك</span></li>
      <li><span class="ico">{ic("crown")}</span><span><b>مزايا الأعضاء</b>أولوية وخصم على الجلسات الفردية</span></li></ul>
    <div class="plans-bar"><div class="toggle" role="group" aria-label="مدة الاشتراك"><button type="button" data-plan="vip-m" aria-pressed="true">شهري</button><button type="button" data-plan="vip-q" aria-pressed="false">٣ أشهر</button><button type="button" data-plan="vip-y" aria-pressed="false">سنوي · شهران مجاناً</button></div>
      <div class="amount" id="vipAmount">٢٩٩٩ ج.م <small>/ شهرياً</small></div><a class="btn btn-gold" id="vipJoin" href="cart.html" data-buy="vip-m">اشترك الآن</a></div>
    <span class="demo" style="justify-self:start">الأسعار والمزايا للعرض حتى تعتمديها</span></div></div>'''

# ------------------------------------------------------------------ pages
PAGES = []
HOME = ''
def build():
    if OUT.exists(): shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    for d, s in [("assets/art","design/assets/art"),("assets/img","design/assets/img")]:
        shutil.copytree(ROOT/s, OUT/d, dirs_exist_ok=True)
    (OUT/"assets/brand").mkdir(parents=True, exist_ok=True)
    for f in ["logo-icon-gold.webp","logo-gold-transparent.webp","logo-gold-transparent.png","favicon-32.png","favicon-192.png","favicon-512.png"]:
        shutil.copy(ROOT/"brand"/f, OUT/"assets/brand"/f)
    for f in ["marvat-hero.webp","marvat-arch.webp","coach-white-square-cut.webp","coach-navy-cut.webp"]:
        (OUT/"assets/img"/f).unlink(missing_ok=True)
    (OUT/"assets/js/data.js").write_text("window.SITE_DATA=" + json.dumps(DATA, ensure_ascii=False) + ";\n", encoding="utf-8")

    # ---------- home
    global HOME
    HOME = home_body()
    course = BY["ain-sahia"]
    mods = "".join(f'<li><span class="n">{["٠","١","٢","٣"][i]}</span><b>{E(m["title"].split(": ")[-1])}</b><small class="{"free" if i==0 else ""}">{"استمع مجاناً" if i==0 else str(len(m["lessons"])).translate(str.maketrans("0123456789","٠١٢٣٤٥٦٧٨٩"))+" دروس"}</small></li>' for i, m in enumerate(course["modules"]))
    page("index.html", f"{NAME} | مدربة وعي وتشافي معتمدة من ICF",
         "برنامج استيقظ VIP، كورس عين صاحية، وتمارين Decoding وفك التعلق وتشافي الطفل الداخلي وتنفّس الاتزان الداخلي مع د. مرفت سرور، مدربة وعي وتشافي معتمدة من ICF.", HOME, schema=[ORG, PERSON])

    # ---------- VIP
    def vplan(pid, name, note, feats, tag="", best=False, cta=""):
        return (f'<article class="vp-plan{" is-best" if best else ""}">' + (f'<span class="vp-tag">{tag}</span>' if tag else '') +
                f'<h3>{name}</h3><div class="vp-price">{price(pid)}</div><p class="vp-note">{note}</p><span class="vp-rule" aria-hidden="true"></span>' +
                f'<ul>{"".join(f"<li><i class=vp-dot></i>{E(x)}</li>" for x in feats)}</ul>' +
                f'<button class="{"btn-safia" if best else "vp-btn"}" type="button" data-buy="{pid}"><span>{cta}</span></button></article>')
    plans = '<div class="vp-plans">' + vplan("vip-m","الاشتراك الشهري","يتجدد شهرياً وتلغينه متى شئت",["جلسات فردية خاصة بينك وبين د. مرفت","كل أدوات الموقع مفتوحة طوال الاشتراك","خطة تطبيق يومية ومتابعة التقدّم"],cta="اشتركي شهرياً") + \
        vplan("vip-q","اشتراك ٣ أشهر","كل ٣ أشهر · توفّرين ما يقارب ١٠٪",["كل مزايا الاشتراك الشهري","المدة الأنسب لتحوّل عميق ومستقر","متابعة متصلة لرحلتك دون انقطاع"],tag="الأكثر اختياراً",best=True,cta="اشتركي ٣ أشهر") + \
        vplan("vip-y","الاشتراك السنوي","تدفعين ما يقارب ١٠ أشهر وتحصلين على ١٢",["كل مزايا الاشتراك الشهري","شهران مجاناً","أولوية في حجز المواعيد","هدايا وتمارين حصرية للمشتركات السنويات"],tag="الأوفر · شهران مجاناً",cta="اشتركي سنوياً") + '</div>'
    page("vip.html", "برنامج استيقظ VIP", "استيقظ VIP: البرنامج التدريبي الأساسي مع د. مرفت سرور. جلسات فردية خاصة، كل التمارين، خطة يومية ومتابعة. اشتراك شهري أو سنوي.", f'''
<section class="vip-split"><canvas class="sparkle" data-density="1500" aria-hidden="true"></canvas>
  <div class="vs-copy">{crumbs(("استيقظ VIP", None))}<span class="vs-eyebrow">البرنامج التدريبي الخاص</span><h1>استيقظ <span>VIP</span></h1>
    <p>البرنامج الذي تبدأ منه الرحلة كلها. جلسات فردية خاصة مع د. مرفت أونلاين، تجمع الوعي والتطبيق اليومي والمتابعة، لتستيقظ على نسختك الأصلية وتعيش بها.</p>
    <div class="ctas"><a class="btn-safia" href="#plans">اختر اشتراكك</a><a class="vs-link" href="#inside">ماذا يشمل البرنامج؟</a></div></div>
  <figure class="vs-photo"><img src="assets/img/vip-zoom.webp" alt="د. مرفت سرور في جلسة خاصة أونلاين" width="1200" height="1500" fetchpriority="high"></figure></section>
<div class="vp-strip" aria-hidden="true"><div class="track"><span>الوعي <i>✦</i> التشافي <i>✦</i> السكينة <i>✦</i> القبول <i>✦</i> التحرّر من التعلّق <i>✦</i> الطفل الداخلي <i>✦</i> النسخة الأصلية <i>✦</i></span><span>الوعي <i>✦</i> التشافي <i>✦</i> السكينة <i>✦</i> القبول <i>✦</i> التحرّر من التعلّق <i>✦</i> الطفل الداخلي <i>✦</i> النسخة الأصلية <i>✦</i></span></div></div>
<section class="vp-sec vp-ivory" id="inside"><div class="vp-wrap">
  <header class="vp-head"><span class="vp-orn" aria-hidden="true">✦</span><h2>ماذا تحصلين عليه كعضوة؟</h2><p>كل ما تحتاجينه لرحلتك في مكان واحد.</p></header>
  <div class="vp-feats"><div class="vp-feat"><span class="vp-ico">{ic("live")}</span><h3>جلسات خاصة</h3><p>رحلة فردية بينك وبين د. مرفت فقط، أونلاين عبر Zoom، في سرية تامة.</p></div><div class="vp-feat"><span class="vp-ico">{ic("lib")}</span><h3>المكتبة كاملة</h3><p>كل التمارين الحالية والجديدة مفتوحة طوال اشتراكك.</p></div><div class="vp-feat"><span class="vp-ico">{ic("path")}</span><h3>خطة يومية</h3><p>رحلة متدرجة يوماً بيوم، وتتابعين تقدّمك من لوحة حسابك.</p></div><div class="vp-feat"><span class="vp-ico">{ic("chat")}</span><h3>متابعة شخصية</h3><p>متابعة مباشرة لرحلتك وأسئلتك.</p></div><div class="vp-feat"><span class="vp-ico">{ic("crown")}</span><h3>أولوية وخصم</h3><p>أولوية في حجز الجلسات الفردية وخصم عليها.</p></div><div class="vp-feat"><span class="vp-ico">{ic("gift")}</span><h3>مفاجآت شهرية</h3><p>تمارين وملفات حصرية للعضوات.</p></div></div>
  <p class="vp-small">المزايا مقترحة، تُعدّل حسب تفاصيل برنامجك الفعلية</p></div></section>
<section class="vp-sec vp-royal" id="plans"><canvas class="sparkle" data-density="2200" aria-hidden="true"></canvas><div class="vp-wrap">
  <header class="vp-head on-dark"><span class="vp-orn" aria-hidden="true">✦</span><h2>اختاري ما يناسبك</h2><p>الأسعار بالجنيه داخل مصر وبالدولار خارجها. يمكنك الإلغاء في أي وقت من حسابك.</p></header>
  {plans}</div></section>
<section class="vp-sec vp-ivory"><div class="vp-wrap vp-narrow"><header class="vp-head"><span class="vp-orn" aria-hidden="true">✦</span><h2>أسئلة عن البرنامج</h2></header><div class="vp-faq">{faq_items(FAQ["vip"])}</div></div></section>
<section class="vp-final"><canvas class="sparkle" data-density="2600" aria-hidden="true"></canvas><div class="vp-wrap"><h2>اتخذي الآن الخطوة التي تستحقينها</h2><a class="btn-safia" href="#plans">استيقظ VIP</a></div></section>''',
         active="vip.html", schema=[{"@context":"https://schema.org","@type":"Product","name":"استيقظ VIP","description":"برنامج تدريبي في الوعي والتشافي مع د. مرفت سرور","brand":NAME,"offers":[{"@type":"Offer","price":BY["vip-m"]["eg"],"priceCurrency":"EGP"},{"@type":"Offer","price":BY["vip-m"]["us"],"priceCurrency":"USD"}]}])

    # ---------- library
    page("library.html", "مكتبة الأدوات", "تمارين Decoding، فك التعلق، تشافي الطفل الداخلي، تنفّس الاتزان الداخلي، Priming الصباح، توكيدات السلام للتشافي العميق، وتأمل السكينة مع د. مرفت سرور.", page_hero("مكتبة الأدوات","كل تمرين يُشترى منفصلاً ويبقى في حسابك مدى الحياة، ومعه معاينة مجانية للدرس الأول.", eyebrow="تمارين صوتية ومرئية") + f'''
<section class="band-sm"><div class="wrap"><div class="search">{ic("search")}<label class="sr" for="q">ابحث في التمارين</label><input id="q" type="search" placeholder="ابحث: تعلّق، تنفّس، طفل داخلي…"></div>{tabs()}<div class="shelf" data-shelf="library"></div></div></section>
<section class="band" style="padding-top:0"><div class="wrap"><div class="vip-card" style="grid-template-columns:1fr"><div class="vip-body" style="text-align:center;justify-items:center"><h2 style="font-size:clamp(1.6rem,3vw,2.4rem)">كل هذه التمارين مفتوحة مع <span class="foil-text">استيقظ VIP</span></h2><p class="lead">بدلاً من الشراء واحداً واحداً، افتح المكتبة كاملة مع البرنامج.</p><a class="btn btn-gold" href="vip.html">اعرف البرنامج</a></div></div></div></section>''', active="library.html")

    # ---------- bundles
    page("bundles.html", "الباقات", "باقات بنظام يومي متكامل: تنفّس الاتزان الداخلي، وPriming الصباح، وتمرين لموضوع محدد (Decoding، الطفل الداخلي، فك التعلّق، السلام)، بسعر أقل من شرائها منفصلة.", page_hero("الباقات","كل باقة نظام يومي متكامل: تنفّس، وتوكيد صباحي، وتأمل السكينة والتنظيف، وتمرين يعالج موضوعاً محدداً، بسعر أقل من شرائها منفصلة.") + '<section class="band-sm"><div class="wrap"><div class="bundles" data-bundles></div></div></section>' + GIFT)

    # ---------- products
    for p in PRODUCTS:
        if p["kind"] in ("course","exercise"): product_page(p)
    book_page()

    # ---------- books
    page("books.html", "الكتب الإلكترونية", "كتب د. مرفت سرور الإلكترونية، تُقرأ داخل حسابك على أي جهاز.", page_hero("الكتب","تُقرأ داخل حسابك على الهاتف أو الكمبيوتر، بنسخة محمية باسمك.") + f'''
<section class="band"><div class="wrap split">{book3d()}<div class="split-body"><span class="eyebrow">الإصدار الأول</span><h2>عندما تولد في عائلة من الأشباح</h2><p class="lead">{BY["book-ghosts"]["short"]}</p>{book_feats()}
<div class="buy">{price("book-ghosts")}<a class="btn btn-plum" href="book-ghosts.html">صفحة الكتاب</a><a class="btn btn-line" href="reader.html">اقرأ الفصل الأول مجاناً</a></div></div></div></section>
<section class="wrap"><div class="card" style="text-align:center;display:grid;gap:10px;justify-items:center"><span class="ico">{ic("gift")}</span><h2 style="font-size:1.4rem">كتب مجانية قادمة</h2><p class="muted">سنضيف كتيبات مجانية تُفتح بمجرد إنشاء حساب.</p><a class="btn btn-gold btn-sm" href="register.html">أنشئ حسابك لتصلك أولاً</a></div></section>''', active="books.html")

    # ---------- sessions
    types = "".join(f'<label class="type"><input type="radio" name="stype" value="{sid}" {"checked" if sid=="s-single" else ""}><span><b>{E(BY[sid]["title"])}</b><small>{d}</small></span>{price(sid)}</label>' for sid, d in [("s-intro","تعرّف على طريقة العمل وحدّد احتياجك"),("s-single","جلسة عميقة حول موضوع واحد"),("s-pack","أربع جلسات أسبوعية بسعر أقل"),("s-coach","جلسة بمعايير ICF: أسئلة تساعدك تكتشف إجاباتك بنفسك وتضع خطوات واضحة نحو هدفك")])
    page("sessions.html", "الجلسات الفردية", "احجز جلسة استشارة فردية أونلاين مع د. مرفت سرور. اختر الموعد بتوقيت بلدك، وادفع بالبطاقة أو المحفظة أو PayPal.", page_hero("الجلسات الفردية","اختر نوع الجلسة والموعد، ويصلك التأكيد ورابط الجلسة على بريدك.") + f'''
<section class="band-sm"><div class="wrap split" id="booking" style="align-items:start">
  <div class="split-body"><h2 style="font-size:1.4rem;font-family:var(--body)">١. نوع الجلسة</h2><div class="types">{types}</div>
    <ul class="facts" style="margin-top:10px"><li>{ic("live")}أونلاين عبر Zoom أو Google Meet</li><li>{ic("globe")}يظهر الموعد بتوقيت بلدك</li><li>{ic("bell")}تذكير قبل الجلسة بيوم وبساعة</li><li>{ic("cal")}تغيير الموعد مجاناً حتى ٢٤ ساعة قبله</li></ul></div>
  <div class="cal"><div class="cal-head"><h3>٢. اختر الموعد · <span id="bkMonth"></span></h3><div class="cal-nav"><button class="iconbtn" id="bkPrev" type="button" aria-label="الأسبوع السابق">{ic("fwd")}</button><button class="iconbtn" id="bkNext" type="button" aria-label="الأسبوع التالي">{ic("back")}</button></div></div>
    <div class="days" id="bkDays"></div><div class="slots" id="bkSlots"></div><small class="muted">المواعيد بتوقيت القاهرة (GMT+2). المواعيد هنا للعرض.</small>
    <button class="btn btn-gold btn-block" id="bkGo" type="button">{ic("lock")}تأكيد الموعد والدفع</button></div></div></section>
<section class="band"><div class="wrap narrow"><div class="head center"><h2 class="title">أسئلة عن الجلسات</h2></div><div class="faq">{faq_items(FAQ["sessions"])}</div></div></section>''', active="sessions.html")

    # ---------- about
    page("about.html", "عن د. مرفت سرور", "تعرّف على د. مرفت سرور، مدربة وعي وتشافي معتمدة من الاتحاد الدولي للتدريب ICF، ومنهجها في الوعي والتشافي.", page_hero("عن د. مرفت سرور","مدربة وعي وتشافي معتمدة من الاتحاد الدولي للتدريب ICF.") + f'''
<section class="band"><div class="wrap split"><div class="round-ph"><div class="img"><img src="assets/img/coach-white-square.webp" alt="د. مرفت سرور" width="900" height="900"></div></div>
  <div class="split-body"><span class="eyebrow">القصة</span><h2>رحلتي إلى الوعي</h2><blockquote class="big">«التشافي ليس أن تصبح شخصاً آخر، بل أن تعود إلى نفسك التي نسيتها.»</blockquote>
  <div class="prose"><p>هنا تُكتب قصتك بصوتك: البداية، واللحظة التي غيّرت مسارك، ولماذا اخترتِ طريق الوعي والتشافي. <span class="demo">نص مؤقت</span></p><p>القصة الشخصية هي أكثر ما يقرّب الزائر منك، ويُفضّل أن تكون صادقة وقصيرة ومحددة.</p></div>
  <div class="chips"><span>{ic("award")}معتمدة من ICF</span><span>{ic("path")}مدربة وعي وتشافي</span><span>{ic("globe")}عملاء من مصر والخليج والعالم</span></div></div></div></section>
<section class="band tint-blush"><div class="wrap split rev" style="align-items:start"><div class="split-body"><span class="eyebrow">المنهج</span><h2>كيف أعمل؟</h2>
  <ol class="timeline"><li><b>الوعي</b><span class="muted">أن ترى ما يحدث داخلك دون حكم.</span></li><li><b>الـ Decoding</b><span class="muted">فكّ البرمجة والقناعات التي ليست لك.</span></li><li><b>التشافي</b><span class="muted">تحرير المشاعر العالقة واحتضان الطفل الداخلي.</span></li><li><b>التطبيق</b><span class="muted">عادات يومية صغيرة تثبّت التغيير.</span></li></ol></div>
  <div class="split-body"><span class="eyebrow">المؤهلات</span><h2>الاعتماد والخبرة</h2><div class="c-info">
  {"".join(f'<div class="c-item"><span class="ico">{ic(i)}</span><span><b>{t}</b><span class="muted">{d}</span></span></div>' for i,t,d in [("award","اعتماد الاتحاد الدولي للتدريب ICF","يُكتب هنا مستوى الاعتماد وسنته."),("book","الدراسة الأكاديمية","يُكتب هنا المؤهل العلمي."),("layers","شهادات التخصص","الشهادات في الوعي والتشافي والـ Decoding.")])}
  <span class="demo">بيانات مؤقتة</span></div></div></div></section>
<section class="band"><div class="wrap"><div class="gallery"><figure><img src="assets/img/coach-green.webp" alt="د. مرفت سرور" loading="lazy"></figure><figure><img src="assets/img/coach-white.webp" alt="د. مرفت سرور" loading="lazy"></figure><figure><img src="assets/img/coach-navy.webp" alt="د. مرفت سرور" loading="lazy"></figure></div>
  <div class="center-cta"><a class="btn btn-gold" href="vip.html">ابدأ معي في استيقظ VIP</a></div></div></section>''', active="about.html", schema=[PERSON])

    # ---------- faq
    allfaq = "".join(f'<h2 class="section-title" style="margin-top:26px">{t}</h2><div class="faq">{faq_items(FAQ[k])}</div>' for k, t in [("general","عام"),("pay","الدفع والأسعار"),("vip","استيقظ VIP"),("sessions","الجلسات"),("books","الكتب")])
    page("faq.html", "الأسئلة الشائعة", "إجابات عن الدفع، الأسعار داخل مصر وخارجها، الاشتراك في استيقظ VIP، الجلسات الفردية وقراءة الكتب.", page_hero("الأسئلة الشائعة","لم تجد إجابتك؟ راسلنا من صفحة التواصل.") + f'<section class="band-sm"><div class="wrap narrow">{allfaq}</div></section>',
         schema=[{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for k in FAQ for q, a in FAQ[k]]}])

    # ---------- contact
    page("contact.html", "تواصل معنا", "تواصل مع فريق د. مرفت سرور للاستفسارات والدعم الفني والتعاون.", page_hero("تواصل معنا","نرد خلال يوم عمل واحد.") + f'''
<section class="band-sm"><div class="wrap contact-grid">
  <div class="c-info">{"".join(f'<div class="c-item"><span class="ico">{ic(i)}</span><span><b>{t}</b><span class="copyable muted">{v}</span></span></div>' for i,t,v in [("mail","البريد الإلكتروني","support@mervatsoror.com"),("chat","واتساب","01095292748"),("clock","مواعيد الدعم","الأحد إلى الخميس · ١٠ ص حتى ٦ م بتوقيت القاهرة"),("pin","العنوان","القاهرة، مصر")])}<span class="demo">بيانات تواصل مؤقتة</span></div>
  <form class="card form" data-simple="وصلتنا رسالتك، وسنرد عليك على بريدك خلال يوم عمل.">
    <div class="row2"><div class="field"><label for="ctName">الاسم</label><input id="ctName" required></div><div class="field"><label for="ctEmail">البريد الإلكتروني</label><input id="ctEmail" type="email" required></div></div>
    <div class="field"><label for="ctTopic">الموضوع</label><select id="ctTopic"><option>استفسار عن البرامج</option><option>مشكلة في الدفع</option><option>الوصول إلى مادة اشتريتها</option><option>الجلسات الفردية</option><option>تعاون وإعلام</option></select></div>
    <div class="field"><label for="ctMsg">رسالتك</label><textarea id="ctMsg" required></textarea></div>
    <div class="alert" hidden></div><button class="btn btn-plum" type="submit">إرسال</button></form></div></section>''', active="contact.html")

    # ---------- auth
    auth_side = f'<div class="auth-art"><canvas class="sparkle" aria-hidden="true"></canvas>{stage("assets/img/coach-white-cut.webp", False)}</div>'
    page("login.html", "تسجيل الدخول", "سجّل الدخول إلى حسابك لمتابعة كورساتك وتمارينك.", f'''<div class="auth-wrap">{auth_side}<div class="auth-form"><div class="inner">
  <a class="brand" href="index.html"><img src="assets/brand/logo-icon-gold.webp" alt="" width="38" height="48"><span><b>د. مرفت سرور</b></span></a>
  <div><h1 class="title">أهلاً بعودتك</h1><p class="muted">سجّل الدخول لتكمل رحلتك من حيث توقفت.</p></div>
  <form class="form" id="loginForm" novalidate><div class="field"><label for="email">البريد الإلكتروني</label><input id="email" type="email" autocomplete="email" required></div>
    <div class="field"><label for="password">كلمة المرور</label><input id="password" type="password" autocomplete="current-password" required><a class="hint" href="forgot.html">نسيت كلمة المرور؟</a></div>
    <div class="alert" hidden></div><button class="btn btn-plum btn-block" type="submit">تسجيل الدخول</button></form>
  <div class="or">أو</div><div class="social-login"><button class="btn btn-line btn-sm" type="button" onclick="this.textContent='يُفعّل في الموقع الفعلي'">Google</button><button class="btn btn-line btn-sm" type="button" onclick="this.textContent='يُفعّل في الموقع الفعلي'">Apple</button></div>
  <button class="btn btn-ghost btn-sm js-demo-login" type="button">جرّب حساباً تجريبياً جاهزاً</button>
  <p class="muted" style="text-align:center">ليس لديك حساب؟ <a href="register.html">أنشئ حساباً مجانياً</a></p></div></div></div>''', bare=True, noindex=True)
    page("register.html", "إنشاء حساب", "أنشئ حسابك المجاني واحصل على هدية: مقدمة تأمل السكينة والفصل الأول من الكتاب.", f'''<div class="auth-wrap">{auth_side}<div class="auth-form"><div class="inner">
  <a class="brand" href="index.html"><img src="assets/brand/logo-icon-gold.webp" alt="" width="38" height="48"><span><b>د. مرفت سرور</b></span></a>
  <div><h1 class="title">ابدأ رحلتك</h1><p class="muted">حساب مجاني، ومعه هدية تُفتح فوراً.</p></div>
  <form class="form" id="registerForm" novalidate><div class="field"><label for="name">الاسم</label><input id="name" autocomplete="name" required></div>
    <div class="field"><label for="email">البريد الإلكتروني</label><input id="email" type="email" autocomplete="email" required></div>
    <div class="field"><label for="password">كلمة المرور</label><input id="password" type="password" autocomplete="new-password" minlength="6" required><span class="hint">٦ أحرف على الأقل</span></div>
    <label class="check"><input type="checkbox" id="gift" checked><span>أرسل لي هدية مقدمة تأمل السكينة وفصل الكتاب، وجديد د. مرفت على بريدي.</span></label>
    <label class="check"><input type="checkbox" required checked><span>أوافق على <a href="terms.html">الشروط</a> و<a href="privacy.html">سياسة الخصوصية</a>.</span></label>
    <div class="alert" hidden></div><button class="btn btn-gold btn-block" type="submit">{ic("gift")}أنشئ حسابي</button></form>
  <p class="muted" style="text-align:center">لديك حساب؟ <a href="login.html">سجّل الدخول</a></p></div></div></div>''', bare=True, noindex=True)
    page("forgot.html", "استعادة كلمة المرور", "استعادة كلمة المرور.", f'''<div class="auth-wrap">{auth_side}<div class="auth-form"><div class="inner"><a class="brand" href="index.html"><img src="assets/brand/logo-icon-gold.webp" alt="" width="38" height="48"><span><b>د. مرفت سرور</b></span></a>
  <div><h1 class="title">نسيت كلمة المرور؟</h1><p class="muted">اكتب بريدك وسنرسل لك رابطاً لتعيينها.</p></div>
  <form class="form" id="forgotForm"><div class="field"><label for="fEmail">البريد الإلكتروني</label><input id="fEmail" type="email" required></div><div class="alert" hidden></div><button class="btn btn-plum btn-block" type="submit">أرسل الرابط</button></form>
  <a href="login.html" class="muted" style="text-align:center">العودة لتسجيل الدخول</a></div></div></div>''', bare=True, noindex=True)

    # ---------- account
    nav = "".join(f'<a href="#{k}">{ic(i)}{t}</a>' for k,i,t in [("overview","home","نظرة عامة"),("mine","crown","اشتراكاتي"),("sessions","cal","جلساتي"),("orders","receipt","الطلبات والفواتير"),("favorites","heart","المفضلة"),("profile","user","بياناتي")])
    page("account.html", "حسابي", "لوحة حسابك.", f'''<section class="band-sm"><div class="wrap acc"><nav class="acc-nav" aria-label="أقسام الحساب"><div class="acc-user"><span class="avatar">م</span><span><b class="js-uname" style="color:var(--ink)"></b><br><small class="muted js-uemail"></small></span></div>{nav}<a href="#" id="logout">{ic("logout")}تسجيل الخروج</a></nav>
  <div class="panel" id="accountPage"></div></div></section>''', noindex=True)

    # ---------- learn / reader
    page("learn.html", "مشغّل الدروس", "مشغّل الدروس.", f'<section class="page-hero"><div class="wrap">{crumbs(("حسابي","account.html#mine"),("الدروس",None))}<h1 class="display js-learn-title" style="font-size:clamp(1.6rem,3.6vw,2.4rem)"></h1></div></section><section class="band-sm"><div class="wrap" id="playerPage"></div></section>', noindex=True)
    page("reader.html", "قارئ الكتاب", "قراءة الكتاب داخل الموقع.", f'<section class="page-hero"><div class="wrap">{crumbs(("الكتب","books.html"),("القراءة",None))}<h1 class="display" style="font-size:clamp(1.6rem,3.6vw,2.4rem)">عندما تولد في عائلة من الأشباح</h1></div></section><section class="band-sm"><div class="wrap narrow" id="readerPage" style="display:grid;gap:18px"></div></section>', noindex=True)

    # ---------- cart / checkout / results
    stepper = lambda n: '<div class="stepper">' + '<hr>'.join(f'<span class="{"on" if i<=n else ""}"><i>{"١٢٣"[i]}</i>{t}</span>' for i,t in enumerate(["السلة","الدفع","تم"])) + '</div>'
    page("cart.html", "السلة", "سلة المشتريات.", f'<section class="co-head"><canvas class="sparkle" data-density="2200" aria-hidden="true"></canvas><div class="wrap">{stepper(0)}<h1>سلتك</h1></div></section><section class="co-body"><div class="wrap"><div id="cartPage"></div></div></section>', noindex=True)
    page("checkout.html", "إتمام الشراء", "إتمام الشراء.", f'<section class="co-head"><canvas class="sparkle" data-density="2200" aria-hidden="true"></canvas><div class="wrap">{stepper(1)}<h1>إتمام الشراء</h1></div></section><section class="co-body"><div class="wrap"><div id="checkoutPage"></div></div></section>', noindex=True)
    page("success.html", "تم الدفع بنجاح", "تم الدفع بنجاح.", f'''<section class="band"><div class="wrap">{stepper(2)}<div class="result" id="successBox"><div class="badge">{ic("check")}</div><h1 class="title">شكراً لك، تم الدفع بنجاح</h1>
  <p class="lead">رقم طلبك <b id="oNo">MS-10241</b> بقيمة <b id="oTotal">—</b>. أرسلنا تأكيد الطلب وبيانات الدخول إلى <b id="oEmail">بريدك</b>.</p>
  <ul class="facts" id="oItems" style="justify-items:center"></ul>
  <div class="ctas" style="justify-content:center"><a class="btn btn-gold" href="account.html#mine">{ic("play")}ابدأ الآن</a><a class="btn btn-line" href="account.html#orders">عرض الفاتورة</a></div>
  <div class="upsell" id="successUpsell" style="text-align:start"><span class="ico">{ic("crown")}</span><div><b>خطوتك التالية: استيقظ VIP</b><p>افتح كل التمارين، وابدأ رحلتك الخاصة مع د. مرفت.</p></div><a class="btn btn-gold btn-sm" href="vip.html">اعرف البرنامج</a></div>
  <p class="muted" style="font-size:.85rem">لم تصلك الرسالة؟ راجع مجلد الرسائل غير المرغوبة أو <a href="contact.html">تواصل معنا</a>.</p></div></div></section>''', noindex=True)
    page("failed.html", "لم يكتمل الدفع", "لم يكتمل الدفع.", f'''<section class="band"><div class="wrap"><div class="result"><div class="badge err">{ic("x")}</div><h1 class="title">لم يكتمل الدفع</h1>
  <p class="lead">لم يُخصم أي مبلغ من حسابك. قد يكون السبب رفض البنك، أو رصيداً غير كافٍ، أو انتهاء مهلة الصفحة.</p>
  <div class="ctas" style="justify-content:center"><a class="btn btn-gold" href="checkout.html">حاول مرة أخرى</a><a class="btn btn-line" href="contact.html">تواصل مع الدعم</a></div>
  <p class="muted" style="font-size:.85rem">جرّب طريقة دفع أخرى: إن كنت خارج مصر استخدم PayPal، وداخل مصر جرّب المحفظة أو فوري.</p></div></div></section>''', noindex=True)

    # ---------- legal
    ltabs = lambda cur: '<nav class="ltabs" aria-label="السياسات">' + "".join(f'<a href="{f}" {"aria-current=page" if f==cur else ""}>{t}</a>' for f,t,_,_ in LEGAL) + '</nav>'
    for f, t, d, secs in LEGAL:
        toc = "".join(f'<li><a href="#s{i}">{h}</a></li>' for i,(h,_) in enumerate(secs))
        body = "".join(f'<section id="s{i}"><h2>{h}</h2>{b}</section>' for i,(h,b) in enumerate(secs))
        page(f, t, d, page_hero(t, "آخر تحديث: نوفمبر ٢٠٢٦", ("السياسات","policies.html"), (t, None)) + f'''<section class="band-sm"><div class="wrap">{ltabs(f)}<div class="legal">
  <aside class="toc"><b>محتويات الصفحة</b><ol>{toc}</ol><a class="btn btn-line btn-sm" href="contact.html">لديك سؤال؟ تواصل معنا</a></aside>
  <article class="prose card"><div class="alert info" style="margin-bottom:8px">يُرجى استكمال البيانات بين الأقواس [ ] ومراجعة النص مع مستشار قانوني قبل الإطلاق.</div>{body}</article></div></div></section>''', active="policies.html")
    cards = "".join(f'<a class="pcard" href="{f}"><span class="ico">{ic(i)}</span><b>{t}</b><span class="muted">{d}</span><span class="link">اقرأ السياسة ←</span></a>' for (f,t,d,_),i in zip(LEGAL,["receipt","shield","infinity","devices"]))
    page("policies.html", "السياسات والشروط", "الشروط والأحكام، سياسة الخصوصية، سياسة الاسترداد والإلغاء، وسياسة تقديم الخدمة لمنصة د. مرفت سرور.", page_hero("السياسات والشروط", "كل ما تحتاج معرفته قبل الشراء، بوضوح.") + f'''<section class="band-sm"><div class="wrap"><div class="pgrid">{cards}</div>
  <div class="card" style="margin-top:24px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between"><span><b style="color:var(--ink)">لم تجد إجابتك؟</b> <span class="muted">راجع الأسئلة الشائعة أو راسلنا مباشرة.</span></span><span class="ctas"><a class="btn btn-line btn-sm" href="faq.html">الأسئلة الشائعة</a><a class="btn btn-plum btn-sm" href="contact.html">تواصل معنا</a></span></div></div></section>''', active="policies.html")

    page("404.html", "الصفحة غير موجودة", "الصفحة غير موجودة.", f'<section class="band"><div class="wrap notfound"><span class="num foil-text">٤٠٤</span><h1 class="title">هذه الصفحة غير موجودة</h1><p class="lead">ربما تغيّر الرابط. جرّب البدء من هنا:</p><div class="ctas" style="justify-content:center"><a class="btn btn-gold" href="index.html">الرئيسية</a><a class="btn btn-line" href="library.html">مكتبة الأدوات</a></div></div></section>', noindex=True)

    # ---------- pages rebuilt on the reference layouts (overwrite earlier versions)
    import pages_v7; pages_v7.init(globals()); pages_v7.build_v7()

    # ---------- seo files
    urls = "".join(f"<url><loc>{SITE_URL}/{'' if f=='index.html' else f}</loc></url>" for f, ni in dict(PAGES).items() if not ni)
    (OUT/"sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (OUT/"robots.txt").write_text(f"User-agent: *\nDisallow: /account.html\nDisallow: /cart.html\nDisallow: /checkout.html\nDisallow: /learn.html\nDisallow: /reader.html\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"built {len(PAGES)} pages into {OUT}")

# ------------------------------------------------------------------ partials
def li(items): return "".join(f"<li>{ic('check')}<span>{E(x)}</span></li>" for x in items)
def book3d(): return '<div class="book3d"><div class="cover"><div class="face"><img src="assets/art/book.webp" alt="" width="600" height="800" loading="lazy"></div><div class="ttl"><b>عندما تولد في عائلة من الأشباح</b><small>د. مرفت سرور</small></div><div class="pages"></div></div></div>'
def book_feats(): return f'<div class="feats"><div class="feat">{ic("book")}<b>اقرأه داخل حسابك</b>على الهاتف أو الكمبيوتر</div><div class="feat">{ic("lock")}<b>نسخة باسمك</b>محمية وغير قابلة للتحميل</div><div class="feat">{ic("mark")}<b>يتذكّر صفحتك</b>تكمل من حيث توقفت</div></div>'
def voices():
    return '''<section class="band tint-pearl"><div class="wrap"><div class="head center"><span class="eyebrow center">تجارب</span><h2 class="title">بكلمات من سبقوك</h2><span class="demo">أمثلة توضيحية، تُستبدل بآراء المشتركين الحقيقية</span></div>
  <div class="qgrid"><div class="q big"><span class="mark">”</span><p>مكان رأي مشتركة في استيقظ VIP: ما الذي تغيّر في علاقتها بنفسها بعد شهر من الالتزام.</p><div class="who"><b>اسم المشتركة · البلد</b><a href="vip.html">استيقظ VIP ←</a></div></div>
  <div class="q"><span class="mark">”</span><p>مكان رأي عن تمرين فك التعلّق وما شعر به صاحبه بعده.</p><div class="who"><b>اسم المشترك</b><a href="exercise-detachment.html">فك التعلّق ←</a></div></div>
  <div class="q"><span class="mark">”</span><p>مكان رأي عن تنفّس الاتزان الداخلي قبل النوم.</p><div class="who"><b>اسم المشتركة</b><a href="heart-coherence-breathing.html">الاتساق القلبي ←</a></div></div></div></div></section>'''
def faq_items(items): return "".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in items)

def product_page(p):
    lessons = "".join(f'''<details {"open" if i==0 else ""}><summary>{E(m["title"])} <small>{len(m["lessons"])} دروس</small></summary>{"".join(f'<div class="lesson">{ic("play" if l[2:] else "lock", "icon icon-sm")}<span>{E(l[0])}</span>{f"<a href=learn.html#{p[chr(105)+chr(100)]}>معاينة مجانية</a>" if l[2:] else f"<small class=muted>{l[1]}</small>"}</div>' for l in m["lessons"])}</details>''' for i, m in enumerate(p["modules"]))
    is_course = p["kind"] == "course"
    trail = [("كورس عين صاحية", None)] if is_course else [("مكتبة الأدوات","library.html"), (p["title"], None)]
    page(p["page"], f'{p["title"]} · {p["catLabel"]}', p["short"] + f' {p["catLabel"]} مع د. مرفت سرور.', f'''
<section class="page-hero"><div class="wrap">{crumbs(*trail)}<span class="eyebrow">{E(p["catLabel"])}</span><h1 class="display">{E(p["title"])}</h1><p class="lead">{E(p["short"])}</p></div></section>
<section class="band-sm"><div class="wrap pd">
  <div class="pd-main">
    <div class="pd-media"><img src="{p["img"]}" alt="" width="600" height="800"><button class="playbig" type="button" data-preview="{p["id"]}" aria-label="شاهد المعاينة المجانية"><span>{ic("play")}</span></button><span class="cap">معاينة مجانية</span></div>
    <div><h2 class="section-title">عن {"الكورس" if is_course else "التمرين"}</h2><div class="prose">{"".join(f"<p>{E(x)}</p>" for x in p["desc"])}</div></div>
    <div><h2 class="section-title">مناسب لك إذا كنت…</h2><ul class="for-list">{li(p["forWho"])}</ul></div>
    <div><h2 class="section-title">محتوى المادة</h2><div class="lessons">{lessons}</div></div>
    <div><h2 class="section-title">التقييمات</h2><div class="rating-sum"><span class="big">—</span><span><span class="stars">★★★★★</span><br><small class="muted">تظهر تقييمات المشتركين هنا بعد أول مراجعات حقيقية.</small></span></div></div>
  </div>
  <aside class="pd-side"><div class="buybox">{price(p["id"])}
    <ul class="facts"><li>{ic("layers")}{E(p["meta"])}</li><li>{ic("clock")}وصول لمدة ٣٦٥ يوماً من تاريخ الشراء</li><li>{ic("devices")}على الهاتف والكمبيوتر</li><li>{ic("path")}يحفظ تقدّمك بين الدروس</li></ul>
    <button class="btn btn-gold btn-block" type="button" data-add="{p["id"]}">{ic("bag")}<span>أضف للسلة</span></button>
    <button class="btn btn-line btn-block" type="button" data-preview="{p["id"]}">{ic("play")}شاهد المعاينة المجانية</button>
    <div class="vip-note">{ic("crown")}<span>مشمول في <a href="vip.html"><b>استيقظ VIP</b></a> مع كل التمارين الأخرى.</span></div>
    <div class="share"><button class="btn btn-ghost btn-sm" type="button" data-fav="{p["id"]}" aria-pressed="false">{ic("heart")}احفظ</button><a class="btn btn-ghost btn-sm" href="contact.html">{ic("gift")}أهدِ لصديق</a></div></div>
    <p class="secure">{ic("shield")}دفع آمن · بطاقة، محفظة، فوري أو PayPal</p></aside>
</div></section>
<section class="band tint-blush"><div class="wrap"><div class="head split"><h2 class="title">قد يعجبك أيضاً</h2><a class="btn btn-line btn-sm" href="library.html">كل التمارين</a></div><div class="shelf" data-shelf="related" data-current="{p["id"]}"></div></div></section>''',
         active="course-ain-sahia.html" if is_course else "library.html",
         schema=[{"@context":"https://schema.org","@type":"Course","name":p["title"],"description":p["short"],"inLanguage":"ar","provider":{"@type":"Person","name":"مرفت سرور"},
                  "offers":[{"@type":"Offer","price":p["eg"],"priceCurrency":"EGP","category":"Paid"},{"@type":"Offer","price":p["us"],"priceCurrency":"USD","category":"Paid"}],
                  "hasCourseInstance":{"@type":"CourseInstance","courseMode":"online","courseWorkload":"PT1H"}}])

def book_page():
    b = BY["book-ghosts"]
    page("book-ghosts.html", b["title"], b["short"], page_hero(b["title"], b["short"], ("الكتب","books.html"), (b["title"], None), eyebrow="كتاب إلكتروني") + f'''
<section class="band-sm"><div class="wrap pd"><div class="pd-main"><div class="split" style="grid-template-columns:auto 1fr">{book3d()}<div class="prose"><h2 class="section-title">عن الكتاب</h2><p>نبذة الكتاب تُكتب هنا: لمن كُتب، وما الذي سيفهمه القارئ عن نفسه وعائلته بعد قراءته. <span class="demo">نص مؤقت</span></p><h3>ستقرأ في هذا الكتاب</h3><ul><li>كيف ننتقل ما لم يُقل في العائلة إلى الأبناء</li><li>علامات الأشباح العائلية في حياتك اليومية</li><li>تمارين قصيرة للتحرر بوعي ورحمة</li></ul></div></div>{book_feats()}</div>
  <aside class="pd-side"><div class="buybox">{price("book-ghosts")}<ul class="facts"><li>{ic("book")}يُقرأ داخل الموقع</li><li>{ic("lock")}نسخة محمية باسمك</li><li>{ic("devices")}هاتف وكمبيوتر</li></ul>
  <button class="btn btn-gold btn-block" type="button" data-buy="book-ghosts"><span>اشترِ الكتاب الآن</span></button><button class="btn btn-line btn-block" type="button" data-add="book-ghosts">{ic("bag")}<span>أضف للسلة</span></button><a class="btn btn-line btn-block" href="reader.html">اقرأ الفصل الأول مجاناً</a></div></aside></div></section>''',
         active="books.html", schema=[{"@context":"https://schema.org","@type":"Book","name":b["title"],"author":{"@type":"Person","name":"مرفت سرور"},"inLanguage":"ar","bookFormat":"https://schema.org/EBook","offers":{"@type":"Offer","price":b["eg"],"priceCurrency":"EGP"}}])

FAQ = {
 "general":[("هل أحتاج خبرة سابقة في الوعي؟","لا. كل مادة تبدأ بمقدمة وإرشادات واضحة، ويمكنك البدء بأي تمرين."),("هل المحتوى باللغة العربية؟","نعم، كل المحتوى بالعربية، وسنضيف لغات أخرى لاحقاً."),("هل يمكنني الاستماع من الهاتف؟","نعم، الموقع يعمل على الهاتف والكمبيوتر، ويحفظ تقدّمك على كل الأجهزة.")],
 "pay":[("لماذا يختلف السعر داخل مصر عن خارجها؟","نقدّم سعراً بالجنيه للمقيمين في مصر وسعراً بالدولار لباقي الدول، ويُحسب السعر النهائي حسب بلد الفاتورة."),("ما طرق الدفع المتاحة؟","داخل مصر: البطاقات البنكية وميزة والمحافظ الإلكترونية وفوري والتقسيط. من خارج مصر: البطاقات الدولية وPayPal."),("متى أحصل على المادة بعد الدفع؟","فوراً. تُفتح المادة في حسابك ويصلك بريد بالتأكيد وبيانات الدخول."),("هل يمكنني استرداد المبلغ؟","كل عمليات الشراء نهائية لأن الأدوات تُفتح فور الدفع. نرد المبلغ فقط في حالة الخصم المزدوج أو الخطأ التقني الذي لم يُحل، كما في سياسة الاسترداد والإلغاء.")],
 "vip":[("ماذا يشمل استيقظ VIP؟","جلسات فردية خاصة بينك وبين د. مرفت فقط، وكل التمارين، وخطة يومية، ومزايا على الجلسات."),("كيف ألغي الاشتراك؟","من حسابك، قسم «اشتراكي»، بضغطة واحدة. يبقى الوصول حتى نهاية الفترة المدفوعة."),("هل أحتفظ بالأدوات بعد الإلغاء؟","الأدوات المفتوحة بالاشتراك تتوقف بعد انتهاء الفترة المدفوعة، أما ما اشتريته منفصلاً فيبقى متاحاً لك ٣٦٥ يوماً من تاريخ شرائه."),("هل يمكنني مشاركة حسابي مع أحد أفراد عائلتي؟","لا. الحساب شخصي، ويُسمح بالدخول من جهازين فقط في نفس الوقت. مشاركة الحساب تؤدي لإيقافه دون استرداد.")],
 "sessions":[("كيف تتم الجلسة؟","أونلاين عبر Zoom أو Google Meet، ويصلك الرابط على بريدك."),("هل يمكن تغيير الموعد؟","نعم، حتى ٢٤ ساعة قبل الجلسة من حسابك دون رسوم."),("بأي توقيت تظهر المواعيد؟","تظهر بتوقيت القاهرة مع تحويلها تلقائياً لتوقيت بلدك في الموقع الفعلي.")],
 "books":[("هل يمكن تحميل الكتاب؟","لا، يُقرأ داخل حسابك فقط حفاظاً على حقوق المحتوى، بنسخة تحمل اسمك."),("هل أستطيع القراءة دون إنترنت؟","القراءة تحتاج اتصالاً بالإنترنت لأن الكتاب محفوظ في حسابك.")],
}
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from legal_content import LEGAL

def home_body():
    course = BY["ain-sahia"]
    mods = "".join(f'<li><span class="n">{["٠","١","٢","٣"][i]}</span><b>{E(m["title"].split(": ")[-1])}</b><small class="{"free" if i==0 else ""}">{"استمع مجاناً" if i==0 else str(len(m["lessons"])).translate(str.maketrans("0123456789","٠١٢٣٤٥٦٧٨٩"))+" دروس"}</small></li>' for i, m in enumerate(course["modules"]))
    voices_list = [("س","مكان رأي حقيقي لمشتركة عن تجربتها مع تمرين فك التعلّق، وما تغيّر بعده في علاقاتها.","اسم المشتركة · تمرين فك التعلّق"),
                   ("ن","مكان رأي عضوة في استيقظ VIP: كيف تغيّر يومها بعد شهر من الالتزام والخطة اليومية.","اسم العضوة · استيقظ VIP"),
                   ("ه","مكان رأي عن كورس عين صاحية وكيف غيّر الامتنان اليومي إحساسها بحياتها.","اسم المشتركة · عين صاحية"),
                   ("م","مكان رأي عن تنفّس الاتزان الداخلي قبل النوم وفي المواقف الصعبة.","اسم المشترك · تنفّس الاتزان الداخلي"),
                   ("ر","مكان رأي عن جلسة فردية مع د. مرفت وما خرجت به منها.","اسم المشتركة · جلسة فردية")]
    reel = "".join(f'<div class="voice {"hl" if i==1 else ""}"><span class="av">{a}</span><span class="qm">“</span><p>{E(t)}</p><b>{E(n)}</b></div>' for i,(a,t,n) in enumerate(voices_list))
    return f'''
<div class="popup" id="vipPop" hidden role="dialog" aria-modal="true" aria-labelledby="popT"><div class="pop-card"><button class="pop-close" type="button" id="popClose" aria-label="إغلاق">✕</button>
  <div class="pop-art pop-sq"><img src="assets/img/popup-vip.webp" alt="د. مرفت سرور" width="900" height="900"><div class="txt"><h2 id="popT">اتخذي الآن الخطوة التي تستحقينها</h2><a class="btn btn-gold" href="vip.html">استيقظ VIP</a></div></div></div></div>
<section class="hero-s"><canvas class="sparkle" data-density="1500" aria-hidden="true"></canvas>
  <div class="hs-in">
    <div class="hs-photo"><img src="assets/img/coach-seated-cut.webp" alt="د. مرفت سرور" width="839" height="1129" fetchpriority="high"></div>
    <div class="hs-copy"><div class="hs-wm" aria-hidden="true"><span class="script">Mervat</span><span class="serif">Soror</span></div>
      <h1><span class="hs-line">لديك الآن رفيق حقيقي في الرحلة</span> <span class="gold hs-line">يحمل شعلة نور</span> <span class="hs-line">ويمسك بيدك حتى تصل للجانب الآخر</span></h1>
      <a class="btn-safia" href="vip.html">نوّر</a></div>
  </div>
</section>
<section class="band tint-blush"><div class="wrap">
  <div class="head center"><span class="eyebrow center">ابدأ اليوم</span><h2 class="title">اختر أداتك، وابدأ فوراً</h2></div>
  {tabs()}<div class="shelf" data-shelf="home"></div><div class="center-cta"><a class="btn btn-gold" href="library.html">عرض كل الأدوات</a></div></div></section>
<section class="band"><div class="wrap statement"><span class="eyebrow center">من هي مرفت سرور؟</span>
  <h2>صوت هادئ يوقظ فيك <em>ما نسيته عن نفسك</em></h2>
  <p class="lead">إن كنت تبحث عن مساحة آمنة تفهم فيها مشاعرك، وتعود إلى سكينتك، فأنت في المكان الصحيح.</p></div></section>
{MARQUEE}
<section class="whois-split"><canvas class="sparkle" data-density="2200" aria-hidden="true"></canvas>
  <figure class="ws-photo"><img class="ws-bg" src="assets/img/whois-library.webp" alt="د. مرفت سرور" width="1122" height="1402" loading="lazy"><img class="ws-cut" src="assets/img/whois-library-cut.webp" alt="" aria-hidden="true" width="1122" height="1402" loading="lazy"></figure>
  <div class="ws-copy"><h2>مدربة وعي وتشافي، ورفيقة رحلة العودة إلى الذات</h2>
    <p>معتمدة من الاتحاد الدولي للتدريب ICF، تجمع بين عدة تقنيات وأدوات للتشافي، وترافقك من الفهم إلى التطبيق اليومي، الذي يُحدِث التغيير الحقيقي.</p>
    <div class="ws-stats"><div><b>٨</b><span>سنوات خبرة</span></div><div><b>+١٨ ألف</b><span>ساعة تدريبية</span></div><div><b>+١٠٠</b><span>متدرّب</span></div></div>
    <a class="btn-safia" href="about.html">تعرّف على مرفت</a></div></section>
<section class="vip-banner" aria-label="برنامج استيقظ VIP"><div class="vb-img"><img src="assets/img/vip-banner.webp" alt="د. مرفت سرور أمام بوابة النور" width="1672" height="941" loading="lazy"></div>
  <div class="vb-copy"><span class="vb-kicker">البرنامج التدريبي الخاص</span><h2><span class="vb-w">استيقظ</span> <span class="vb-vip">VIP</span></h2>
    <p>ليس مجرد رحلة من الوعي بل رحلة عميقة لتغيير نسخة لم تعد تمثلك</p>
    <p class="vb-sub">تفتح بوابات الشفاء وتهدم البرمجات القديمة لتولد نسختك الجديدة القوية القادرة على النجاح</p>
    <a class="btn btn-gold" href="vip.html">احجزي مكانك</a></div></section>
<section class="band tint-blush"><div class="wrap vip2">
  <div class="copy"><span class="eyebrow">البرنامج التدريبي الأساسي</span><h2><span class="foil-text">استيقظ VIP</span></h2>
    <p class="lead">رحلة شهرية متدرّجة مع د. مرفت، تجمع الوعي والتطبيق اليومي والمتابعة. هنا يبدأ التغيير الذي يستمر.</p>
    <div class="plans-bar"><div class="toggle" role="group" aria-label="مدة الاشتراك"><button type="button" data-plan="vip-m" aria-pressed="true">شهري</button><button type="button" data-plan="vip-q" aria-pressed="false">٣ أشهر</button><button type="button" data-plan="vip-y" aria-pressed="false">سنوي · شهران مجاناً</button></div>
      <div class="amount" id="vipAmount">٢٩٩٩ ج.م <small>/ شهرياً</small></div><a class="btn btn-gold" id="vipJoin" href="cart.html" data-buy="vip-m">انضم الآن</a></div>
    <a class="btn btn-line btn-sm" href="vip.html" style="justify-self:start">كل تفاصيل البرنامج</a></div>
  <div class="perks">{"".join(f'<div class="perk">{ic(i)}<b>{t}</b><span>{d}</span></div>' for i,t,d in [("live","جلسات فردية خاصة","رحلة خاصة بينك وبين د. مرفت فقط: تفتح بوابات الشفاء، وتفكّ البرمجات اللاواعية."),("lib","المكتبة كاملة","كل التمارين مفتوحة طوال اشتراكك."),("path","خطة يومية ومتابعة","تطبيق واضح يوماً بيوم، وتتابعين تقدّمك من حسابك."),("crown","أولوية الأعضاء","أولوية وخصم على الجلسات الفردية والبرامج الجديدة.")])}</div>
</div></section>
<section class="band"><div class="wrap"><div class="head center"><span class="eyebrow center">ابدأ من هنا</span><h2 class="title">لكل طريق قوته في التحوّل من الداخل</h2></div>
  <div class="tiles"><a class="tile" href="library.html"><img src="assets/art/attach.webp" alt="" loading="lazy"><span><b>التمارين المسجّلة</b><small>Decoding، فك تعلّق، تشافٍ وتأمل</small></span></a>
  <a class="tile" href="vip.html"><img src="assets/img/vip-bridge.webp" alt="" loading="lazy"><span><b>استيقظ VIP</b><small>البرنامج التدريبي المتكامل</small></span></a>
  <a class="tile tile-ses" href="sessions.html"><img src="assets/img/sessions-banner.webp" alt="" loading="lazy"><span><b>الجلسات الفردية</b><small>مساحة خاصة مع د. مرفت</small></span></a></div></div></section>
<section class="wrap" style="padding-bottom:clamp(56px,8vw,110px)"><div class="split"><div class="portal-img"><div class="img"><img src="{course["img"]}" alt="" width="600" height="800" loading="lazy"></div><div class="float"><b>كورس صوتي</b>تسمعه في أي وقت ومن أي جهاز</div></div>
  <div class="split-body"><span class="eyebrow">الكورس</span><h2>عين صاحية</h2><p class="lead">{course["short"]} كورس صوتي مقسّم إلى وحدات، يحفظ لك تقدّمك وتكمل من حيث توقفت.</p>
    <ul class="mods">{mods}</ul>
    <div class="buy">{price("ain-sahia")}<button class="btn btn-gold" type="button" data-buy="ain-sahia"><span>ابدأ الآن</span></button><button class="add" type="button" data-add="ain-sahia" aria-label="أضف عين صاحية للسلة" title="أضف للسلة"></button><a class="btn btn-line" href="{course["page"]}">تفاصيل الكورس</a></div></div></div></section>

<section class="band"><div class="wrap"><div class="head center"><h2 class="title">قالوا عنا</h2><span class="demo">أمثلة توضيحية، تُستبدل بآراء المشتركين الحقيقية</span></div><div class="reel" tabindex="0" aria-label="آراء المشتركين">{reel}</div></div></section>
<section class="ses-banner" aria-label="الجلسات الفردية"><img src="assets/img/sessions-banner.webp" alt="د. مرفت سرور في جلسة أونلاين" width="1672" height="941" loading="lazy">
  <div class="sb-copy"><span class="vb-kicker">الجلسات الفردية</span><h2>عمل مباشر مع مرفت في مساحة خاصة بك</h2><p>جلسة استشارة أونلاين تختار موعدها بتوقيت بلدك ويصلك التأكيد والرابط والتذكير تلقائياً</p><a class="btn btn-gold" href="sessions.html#booking">{ic("cal")}احجز جلستك</a></div></section>
<section class="band" style="padding-bottom:0"><div class="wrap"><div class="head split"><div style="display:grid;gap:10px"><span class="eyebrow">الباقات</span><h2 class="title">مسارات مترابطة بسعر مخفض</h2></div><a class="btn btn-line btn-sm" href="bundles.html">كل الباقات</a></div><div class="bundles" data-bundles></div></div></section>
<section class="band book-band" style="margin-top:clamp(56px,8vw,110px)"><div class="wrap split">{book3d()}
  <div class="split-body"><span class="eyebrow">الكتاب</span><h2>عندما تولد في عائلة من الأشباح</h2><p class="lead">{BY["book-ghosts"]["short"]} <span class="demo">نبذة مؤقتة</span></p>
    {book_feats()}<div class="buy">{price("book-ghosts")}<button class="btn btn-plum" type="button" data-buy="book-ghosts"><span>اشترِ الكتاب</span></button><a class="btn btn-line" href="reader.html">اقرأ الفصل الأول مجاناً</a></div></div></div></section>
<section class="journey" aria-label="كل شروق فرصة لتولد من جديد"><img src="assets/img/journey.webp" alt="د. مرفت سرور على شرفة عند الشروق" width="1914" height="822" loading="lazy">
  <div class="jr-copy"><h2>كل شروق <span class="gold">فرصة</span> لتولد من جديد</h2><p>أنشئ حسابك المجاني واستلم هديتك الأولى فوراً</p></div><div class="jr-cta"><a class="btn btn-gold" href="register.html">{ic("gift")}ابدأ الآن</a></div></section>'''

if __name__ == "__main__":
    build()
