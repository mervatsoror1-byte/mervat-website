/* د. مرفت سرور — front-end prototype logic.
   State lives in localStorage (demo only). In WordPress this is replaced by WooCommerce / Tutor LMS. */
(function(){
"use strict";
const D = window.SITE_DATA;
const P = Object.fromEntries(D.products.map(p => [p.id, p]));
const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => [...r.querySelectorAll(s)];
const ar = n => Number(n).toLocaleString("ar-EG");
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

/* ---------- state ---------- */
const KEY = "ms_state_v1";
const blank = {region:"eg", cart:[], favs:[], user:null, owned:[], vip:null, progress:{}, orders:[], bookings:[], page:{}};
let S;
try { S = Object.assign({}, blank, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch(e) { S = Object.assign({}, blank); }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(S)); } catch(e){} }
function ss(k, v){ try { if (v === undefined) return sessionStorage.getItem(k); if (v === null) sessionStorage.removeItem(k); else sessionStorage.setItem(k, v); } catch(e){ return null; } }

const money = (eg, us) => S.region === "eg" ? ar(eg) + " ج.م" : "$" + us;
const priceOf = p => S.region === "eg" ? p.eg : p.us;
const fmt = v => S.region === "eg" ? ar(v) + " ج.م" : "$" + (Math.round(v*100)/100);
const hasAccess = id => S.owned.includes(id) || (S.vip && P[id] && P[id].vipIncluded);
const icon = n => `<svg class="icon"><use href="#i-${n}"/></svg>`;

/* ---------- toast ---------- */
let toastT;
function toast(msg, link){
  let t = $(".toast");
  if (!t){ t = document.createElement("div"); t.className = "toast"; t.setAttribute("role","status"); document.body.appendChild(t); }
  t.innerHTML = esc(msg) + (link ? ` <a href="${link[1]}">${esc(link[0])}</a>` : "");
  t.classList.add("show"); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove("show"), 3200);
}

/* ---------- header ---------- */
function paintHeader(){
  $$(".js-cart-count").forEach(e => e.textContent = ar(S.cart.length));
  $$(".region button").forEach(b => b.setAttribute("aria-pressed", b.dataset.region === S.region));
  $$(".js-user").forEach(a => {
    if (S.user){ a.href = "account.html"; a.innerHTML = `<span class="avatar">${esc(S.user.name.trim()[0]||"م")}</span>`; a.setAttribute("aria-label","حسابي"); }
    else { a.href = "login.html"; a.innerHTML = icon("user"); a.setAttribute("aria-label","تسجيل الدخول"); }
  });
}
function paintPrices(){
  $$("[data-price]").forEach(e => { const p = P[e.dataset.price]; if (p) e.textContent = money(p.eg, p.us); });
  $$("[data-eg]").forEach(e => e.textContent = S.region === "eg" ? e.dataset.eg : e.dataset.us);
  $$("[data-was]").forEach(e => { const [eg, us] = e.dataset.was.split("|"); e.textContent = S.region === "eg" ? ar(eg) + " ج.م" : "$" + us; });
}
function paintButtons(){
  $$("[data-add]").forEach(b => {
    const id = b.dataset.add, inCart = S.cart.some(c => c.id === id), owned = hasAccess(id);
    if (b.classList.contains("add")){ b.classList.toggle("in", inCart); b.innerHTML = icon(inCart ? "check" : "plus"); }
    else if (b.dataset.label !== undefined || (b.dataset.label = b.textContent.trim())){
      const lbl = b.querySelector("span") || b;
      if (owned && P[id] && P[id].learn){ b.dataset.owned = "1"; lbl.textContent = "ابدأ الآن"; }
      else lbl.textContent = inCart ? "في السلة · إتمام الشراء" : b.dataset.label;
    }
  });
  $$("[data-fav]").forEach(b => b.setAttribute("aria-pressed", S.favs.includes(b.dataset.fav)));
}
function paintAll(){ paintHeader(); paintPrices(); paintButtons(); renderDynamic(); }

/* ---------- cart actions ---------- */
function addToCart(id, extra){
  const p = P[id]; if (!p) return;
  if (hasAccess(id) && p.learn){ location.href = p.learn; return; }
  if (p.kind === "vip") S.cart = S.cart.filter(c => P[c.id].kind !== "vip");
  if (!S.cart.some(c => c.id === id) || p.kind === "session") S.cart.push(Object.assign({id}, extra||{}));
  save(); paintAll(); toast("أُضيف إلى السلة: " + p.title, ["عرض السلة", "cart.html"]);
}

/* ---------- product card ---------- */
function card(p){
  const owned = hasAccess(p.id);
  return `<article class="item" data-cat="${p.cat}">
    <a class="pic" href="${p.page}"><img src="${p.img}" alt="" width="600" height="800" loading="lazy">
      ${p.isNew ? '<span class="new">جديد</span>' : ''}${owned ? '<span class="owned">في مكتبتك</span>' : ''}
      <span class="listen">${icon("play")}معاينة مجانية</span></a>
    <button class="fav" type="button" data-fav="${p.id}" aria-pressed="false" aria-label="احفظ في المفضلة">${icon("heart")}</button>
    <span class="cat">${esc(p.catLabel)}</span>
    <h3><a href="${p.page}">${esc(p.title)}</a></h3>
    <span class="meta">${esc(p.meta)}</span>
    <div class="row"><span class="price" data-price="${p.id}">${money(p.eg,p.us)}</span>
      ${owned ? `<a class="add in" href="${p.learn}" aria-label="ابدأ ${esc(p.title)}">${icon("play")}</a>` : `<button class="add" type="button" data-add="${p.id}" aria-label="أضف ${esc(p.title)} للسلة">${icon("plus")}</button>`}</div>
  </article>`;
}
function bundleCard(b){
  const eg = b.items.reduce((s,i)=>s+P[i].eg,0), us = b.items.reduce((s,i)=>s+P[i].us,0), p = P[b.id];
  return `<article class="bundle">
    <div class="fan" aria-hidden="true">${b.fan.map(s=>`<img src="${s}" alt="">`).join("")}</div>
    <h3>${esc(p.title)}</h3><p class="inside">${b.items.map(i=>esc(P[i].title)).join(" · ")}</p>
    <span class="saving">توفّر ${S.region==="eg" ? ar(eg-p.eg)+" ج.م" : "$"+(us-p.us)}</span>
    <div class="buy"><span class="price">${money(p.eg,p.us)}<s>${S.region==="eg" ? ar(eg)+" ج.م" : "$"+us}</s></span>
      <button class="btn btn-plum btn-sm" type="button" data-add="${p.id}"><span>أضف للسلة</span></button></div>
  </article>`;
}

/* ---------- dynamic regions ---------- */
let shelfFilter = "all", shelfQuery = "";
function renderDynamic(){
  $$("[data-shelf]").forEach(el => {
    const mode = el.dataset.shelf;
    let list = D.products.filter(p => p.kind === "exercise");
    if (mode === "home") list = list.slice(0, 8);
    if (mode === "related"){ const cur = el.dataset.current; list = list.filter(p => p.id !== cur).slice(0, 4); }
    if (mode === "favs") list = D.products.filter(p => S.favs.includes(p.id));
    if (mode === "library" || mode === "home"){
      if (shelfFilter !== "all") list = list.filter(p => p.cat === shelfFilter);
      if (shelfQuery) list = list.filter(p => (p.title + p.catLabel + p.short).includes(shelfQuery));
    }
    el.innerHTML = list.length ? list.map(card).join("") : `<p class="empty">${mode === "favs" ? "لم تحفظ أي مادة بعد. اضغط على القلب في أي تمرين ليظهر هنا." : "لا توجد نتائج مطابقة."}</p>`;
  });
  $$("[data-bundles]").forEach(el => el.innerHTML = D.bundles.map(bundleCard).join(""));
  paintPricesOnly();
  $$("[data-fav]").forEach(b => b.setAttribute("aria-pressed", S.favs.includes(b.dataset.fav)));
  $$(".add[data-add]").forEach(b => { const inCart = S.cart.some(c => c.id === b.dataset.add); b.classList.toggle("in", inCart); b.innerHTML = icon(inCart ? "check" : "plus"); });
  if ($("#cartPage")) renderCart();
  if ($("#checkoutPage")) renderCheckout();
  if ($("#accountPage")) renderAccount();
  if ($("#vipAmount")) renderVipBar();
}
function paintPricesOnly(){ $$("[data-price]").forEach(e => { const p = P[e.dataset.price]; if (p) e.textContent = money(p.eg, p.us); }); }

/* ---------- cart page ---------- */
function totals(){
  const sub = S.cart.reduce((s,c) => s + priceOf(P[c.id]), 0);
  const code = ss("coupon"); const disc = code === "WELCOME10" ? sub * .10 : 0;
  return {sub, disc, total: sub - disc, code};
}
function lineHTML(c, i, compact){
  const p = P[c.id];
  return `<div class="line"><img src="${p.img}" alt="">
    <div><span class="cat muted" style="font-size:.78rem">${esc(p.catLabel)}</span><h3>${esc(p.title)}</h3>
      ${c.when ? `<small class="muted">${esc(c.when)}</small><br>` : ""}
      ${compact ? "" : `<button class="rm" type="button" data-rm="${i}">إزالة</button>`}</div>
    <span class="price" style="font-size:1.1rem">${money(p.eg,p.us)}</span></div>`;
}
function renderCart(){
  const box = $("#cartPage"), t = totals();
  if (!S.cart.length){ box.innerHTML = `<div class="result"><div class="badge" style="background:var(--blush);color:var(--plum)">${icon("bag")}</div><h2>سلتك فارغة</h2><p class="lead">ابدأ بتمرين قصير، أو انضم إلى استيقظ VIP لتفتح المكتبة كلها.</p><div class="ctas" style="justify-content:center"><a class="btn btn-gold" href="vip.html">استيقظ VIP</a><a class="btn btn-line" href="library.html">تصفّح التمارين</a></div></div>`; return; }
  box.innerHTML = `<div class="cart-grid"><div class="lines">${S.cart.map((c,i)=>lineHTML(c,i)).join("")}</div>
    <aside class="card summary"><h3>ملخص الطلب</h3>
      <div class="sumrow"><span>المجموع</span><span>${fmt(t.sub)}</span></div>
      ${t.disc ? `<div class="sumrow" style="color:var(--ok)"><span>خصم ${esc(t.code)}</span><span>− ${fmt(t.disc)}</span></div>` : ""}
      <div class="sumrow total"><span>الإجمالي</span><span>${fmt(t.total)}</span></div>
      <form class="coupon" id="couponForm"><label class="sr" for="coupon">كود الخصم</label><input id="coupon" placeholder="كود الخصم (جرّب WELCOME10)" value="${esc(t.code||"")}"><button class="btn btn-ghost btn-sm" type="submit">تطبيق</button></form>
      <a class="btn btn-gold btn-block" href="checkout.html">إتمام الشراء</a>
      <p class="secure">${icon("lock")}دفع آمن ومشفّر · وصول فوري بعد الدفع</p>
    </aside></div>`;
}

/* ---------- checkout ---------- */
const GATEWAYS = {
  eg: [
    {id:"paymob-card", t:"بطاقة بنكية", s:"فيزا · ماستركارد · ميزة (Paymob)", l:["VISA","MC","ميزة"]},
    {id:"paymob-wallet", t:"محفظة إلكترونية", s:"فودافون كاش وغيرها", l:["محافظ"]},
    {id:"fawry", t:"فوري / أمان", s:"ادفع نقداً من أقرب منفذ خلال ٤٨ ساعة", l:["فوري"]},
    {id:"valu", t:"تقسيط", s:"valU وغيرها حسب القيمة", l:["valU"]}],
  intl: [
    {id:"nbe-card", t:"بطاقة دولية", s:"Visa · Mastercard بالدولار (البنك الأهلي المصري)", l:["VISA","MC"]},
    {id:"paypal", t:"PayPal", s:"ادفع من رصيدك أو بطاقتك عبر PayPal", l:["PayPal"]}]
};
function renderCheckout(){
  const box = $("#checkoutPage");
  if (!S.cart.length){ box.innerHTML = `<div class="result"><h2>لا يوجد ما تدفعه الآن</h2><a class="btn btn-gold" href="library.html">تصفّح التمارين</a></div>`; return; }
  const t = totals(), recurring = S.cart.some(c => P[c.id].kind === "vip");
  const gws = GATEWAYS[S.region].filter(g => !recurring || ["paymob-card","nbe-card","paypal"].includes(g.id));
  box.innerHTML = `<div class="cart-grid">
   <form class="form" id="payForm" novalidate>
    <div class="card form">
      <h3>١. بياناتك</h3>
      ${S.user ? `<div class="alert info">ستُضاف المشتريات إلى حساب <b>${esc(S.user.email)}</b></div>` :
      `<p class="muted" style="font-size:.9rem">سننشئ حسابك تلقائياً لتصلك المواد. لديك حساب؟ <a href="login.html" data-next="checkout.html">سجّل الدخول</a></p>
       <div class="row2"><div class="field"><label for="cName">الاسم</label><input id="cName" required autocomplete="name"></div>
       <div class="field"><label for="cEmail">البريد الإلكتروني</label><input id="cEmail" type="email" required autocomplete="email"></div></div>
       <div class="field"><label for="cPass">كلمة المرور لحسابك</label><input id="cPass" type="password" minlength="6" required autocomplete="new-password"><span class="hint">٦ أحرف على الأقل</span></div>`}
      <div class="row2"><div class="field"><label for="cCountry">بلد الفاتورة</label><select id="cCountry">${D.countries.map(c=>`<option value="${c[0]}" ${(S.region==="eg")===(c[0]==="EG")&&(c[0]==="EG"||c[0]==="SA")?"selected":""}>${c[1]}</option>`).join("")}</select><span class="hint">السعر يُحسب حسب بلد الفاتورة</span></div>
      <div class="field"><label for="cPhone">رقم الهاتف</label><input id="cPhone" type="tel" autocomplete="tel" placeholder="اختياري"></div></div>
    </div>
    <div class="card form">
      <h3>٢. طريقة الدفع</h3>
      ${recurring ? `<div class="alert info">اشتراك متجدد تلقائياً، ويمكنك إلغاؤه في أي وقت من حسابك.</div>` : ""}
      <div class="pay-opts">${gws.map((g,i)=>`<label class="pay-opt"><input type="radio" name="gw" value="${g.id}" ${i?"":"checked"}><span><b>${g.t}</b><small>${g.s}</small></span><span class="logos">${g.l.map(x=>`<span>${x}</span>`).join("")}</span></label>`).join("")}</div>
      <label class="check"><input type="checkbox" id="cTerms" required><span>أوافق على <a href="terms.html">الشروط والأحكام</a> و<a href="refund.html">سياسة الاسترداد</a>، وأفهم أن المحتوى الرقمي يُتاح فور الدفع.</span></label>
      <div class="alert err" id="payErr" hidden></div>
      <button class="btn btn-gold btn-block" type="submit">${icon("lock")}ادفع ${fmt(t.total)}</button>
      <p class="secure">نموذج تجريبي: لن يُخصم أي مبلغ. <a href="failed.html">شاهد صفحة فشل الدفع</a></p>
    </div>
   </form>
   <aside class="card summary"><h3>طلبك</h3><div class="lines">${S.cart.map((c,i)=>lineHTML(c,i,true)).join("")}</div>
     <div class="sumrow"><span>المجموع</span><span>${fmt(t.sub)}</span></div>
     ${t.disc ? `<div class="sumrow" style="color:var(--ok)"><span>خصم</span><span>− ${fmt(t.disc)}</span></div>` : ""}
     <div class="sumrow total"><span>الإجمالي</span><span>${fmt(t.total)}</span></div></aside>
  </div>`;
}
function submitPay(f){
  const err = $("#payErr"); err.hidden = true;
  if (!S.user){
    const n = $("#cName").value.trim(), e = $("#cEmail").value.trim(), pw = $("#cPass").value;
    if (!n || !/^\S+@\S+\.\S+$/.test(e) || pw.length < 6){ err.textContent = "أكمل الاسم وبريداً صحيحاً وكلمة مرور من ٦ أحرف."; err.hidden = false; return; }
    S.user = {name:n, email:e, since:new Date().toISOString()};
  }
  if (!$("#cTerms").checked){ err.textContent = "يجب الموافقة على الشروط والأحكام قبل الدفع."; err.hidden = false; return; }
  const t = totals(), gw = (f.querySelector("input[name=gw]:checked")||{}).value, no = "MS-" + (10240 + S.orders.length + 1);
  S.cart.forEach(c => {
    const p = P[c.id];
    if (p.kind === "vip") S.vip = {plan:p.id, since:new Date().toISOString()};
    else if (p.kind === "bundle") D.bundles.find(b => b.id === p.id).items.forEach(i => S.owned.includes(i) || S.owned.push(i));
    else if (p.kind === "session") S.bookings.push({type:p.title, when:c.when, link:"يُرسل قبل الجلسة"});
    else if (!S.owned.includes(p.id)) S.owned.push(p.id);
  });
  S.orders.unshift({no, date:new Date().toLocaleDateString("ar-EG"), items:S.cart.map(c=>P[c.id].title), total:fmt(t.total), gw, status:"مكتمل"});
  ss("lastOrder", JSON.stringify({no, total:fmt(t.total), items:S.cart.map(c=>P[c.id].title), email:S.user.email, gw}));
  S.cart = []; ss("coupon", null); save();
  location.href = "success.html";
}

/* ---------- VIP bar ---------- */
let vipPlan = "vip-m";
function renderVipBar(){
  const p = P[vipPlan];
  $("#vipAmount").innerHTML = money(p.eg, p.us) + ` <small>/ ${p.id === "vip-m" ? "شهرياً" : "سنوياً"}</small>`;
  const b = $("#vipJoin"); if (b){ b.dataset.add = vipPlan; }
  if (S.vip && b){ b.textContent = "أنت عضو في استيقظ VIP"; b.removeAttribute("data-add"); b.href = "account.html#subscription"; }
}

/* ---------- account ---------- */
function renderAccount(){
  const box = $("#accountPage");
  if (!S.user){ ss("next","account.html"); location.replace("login.html"); return; }
  const tab = (location.hash || "#overview").slice(1);
  $$(".acc-nav a").forEach(a => a.setAttribute("aria-current", a.getAttribute("href") === "#" + tab));
  $$(".js-uname").forEach(e => e.textContent = S.user.name); $$(".js-uemail").forEach(e => e.textContent = S.user.email);
  const learnables = D.products.filter(p => p.learn && hasAccess(p.id) && p.kind !== "book");
  const books = D.products.filter(p => p.kind === "book" && hasAccess(p.id));
  const pct = id => { const p = P[id], total = p.lessonsCount || 1, done = (S.progress[id]||[]).length; return Math.round(done/total*100); };
  const mine = list => list.length ? `<div class="mine">${list.map(p => `<div class="mine-item"><img src="${p.img}" alt=""><div><span class="cat muted" style="font-size:.78rem">${esc(p.catLabel)}</span><h3>${esc(p.title)}</h3><div class="bar"><i style="width:${pct(p.id)}%"></i></div><small class="muted">${ar(pct(p.id))}٪ مكتمل</small></div><a class="btn btn-plum btn-sm" href="${p.learn}">${pct(p.id) ? "أكمل" : "ابدأ"}</a></div>`).join("")}</div>`
    : `<div class="card" style="text-align:center"><p class="muted">لا توجد مواد في مكتبتك بعد.</p><div class="ctas" style="justify-content:center;margin-top:12px"><a class="btn btn-gold btn-sm" href="vip.html">استيقظ VIP</a><a class="btn btn-line btn-sm" href="library.html">تصفّح التمارين</a></div></div>`;
  const views = {
    overview: `<h1 class="title">أهلاً ${esc(S.user.name.split(" ")[0])}</h1>
      <div class="stats"><div class="stat"><b>${ar(learnables.length)}</b><span>مواد في مكتبتك</span></div><div class="stat"><b>${ar(S.bookings.length)}</b><span>جلسات محجوزة</span></div><div class="stat"><b>${S.vip ? "فعّالة" : "—"}</b><span>عضوية استيقظ VIP</span></div></div>
      <h2 style="font-size:1.25rem">أكمل من حيث توقفت</h2>${mine(learnables.slice(0,3))}`,
    courses: `<h1 class="title">كورساتي وتمارينـي</h1>${mine(learnables)}`,
    books: `<h1 class="title">مكتبة الكتب</h1>${books.length ? `<div class="mine">${books.map(p=>`<div class="mine-item"><img src="${p.img}" alt=""><div><h3>${esc(p.title)}</h3><small class="muted">آخر صفحة: ${ar((S.page[p.id]||0)+1)}</small></div><a class="btn btn-plum btn-sm" href="reader.html">اقرأ</a></div>`).join("")}</div>` : `<div class="card" style="text-align:center"><p class="muted">لم تشترِ كتباً بعد. يمكنك قراءة الفصل الأول مجاناً.</p><div class="ctas" style="justify-content:center;margin-top:12px"><a class="btn btn-line btn-sm" href="reader.html">اقرأ الفصل الأول</a><a class="btn btn-gold btn-sm" href="book-ghosts.html">صفحة الكتاب</a></div></div>`}`,
    sessions: `<h1 class="title">جلساتي</h1>${S.bookings.length ? `<div class="scroll-x"><table class="table"><thead><tr><th>الجلسة</th><th>الموعد</th><th>الرابط</th></tr></thead><tbody>${S.bookings.map(b=>`<tr><td>${esc(b.type)}</td><td>${esc(b.when)}</td><td><span class="pill wait">${esc(b.link)}</span></td></tr>`).join("")}</tbody></table></div>` : `<div class="card" style="text-align:center"><p class="muted">لا توجد جلسات محجوزة.</p><a class="btn btn-gold btn-sm" style="margin-top:12px" href="sessions.html">احجز جلسة</a></div>`}`,
    subscription: `<h1 class="title">اشتراكي</h1>${S.vip ? `<div class="card form"><div class="alert ok">عضويتك في استيقظ VIP فعّالة (${P[S.vip.plan].title}).</div><p class="muted">التجديد التالي تلقائي. يمكنك الإلغاء في أي وقت ويبقى الوصول حتى نهاية الفترة المدفوعة.</p><div class="ctas"><button class="btn btn-line btn-sm" type="button" id="cancelVip">إلغاء التجديد التلقائي</button><a class="btn btn-ghost btn-sm" href="#payment">تغيير بطاقة الدفع</a></div></div>` : `<div class="card" style="text-align:center"><p class="muted">لست مشتركاً في استيقظ VIP بعد.</p><a class="btn btn-gold btn-sm" style="margin-top:12px" href="vip.html">اعرف البرنامج</a></div>`}`,
    orders: `<h1 class="title">الطلبات والفواتير</h1>${S.orders.length ? `<div class="scroll-x"><table class="table"><thead><tr><th>رقم الطلب</th><th>التاريخ</th><th>المحتوى</th><th>الإجمالي</th><th>الحالة</th></tr></thead><tbody>${S.orders.map(o=>`<tr><td>${o.no}</td><td>${o.date}</td><td>${o.items.map(esc).join("، ")}</td><td>${o.total}</td><td><span class="pill ok">${o.status}</span></td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">لا توجد طلبات بعد.</p>`}`,
    favorites: `<h1 class="title">المفضلة</h1><div class="shelf three" data-shelf="favs"></div>`,
    profile: `<h1 class="title">بياناتي</h1><form class="card form" id="profileForm"><div class="row2"><div class="field"><label for="pName">الاسم</label><input id="pName" value="${esc(S.user.name)}"></div><div class="field"><label for="pEmail">البريد الإلكتروني</label><input id="pEmail" type="email" value="${esc(S.user.email)}"></div></div><div class="field"><label for="pLang">لغة الموقع</label><select id="pLang"><option>العربية</option><option disabled>English (قريباً)</option></select></div><label class="check"><input type="checkbox" checked><span>أرسل لي تذكيرات الجلسات والجديد على البريد</span></label><button class="btn btn-plum" type="submit">حفظ</button></form><button class="btn btn-line btn-sm" type="button" id="logout" style="justify-self:start">تسجيل الخروج</button>`
  };
  box.innerHTML = views[tab] || views.overview;
  if (tab === "favorites") renderDynamicFavs();
}
function renderDynamicFavs(){ const el = $("[data-shelf=favs]"); if (!el) return; const list = D.products.filter(p => S.favs.includes(p.id)); el.innerHTML = list.length ? list.map(card).join("") : `<p class="empty">لم تحفظ أي مادة بعد.</p>`; }

/* ---------- learning player ---------- */
function initPlayer(){
  const root = $("#playerPage"); if (!root) return;
  const id = (location.hash || "#" + D.defaultLearn).slice(1), p = P[id] || P[D.defaultLearn];
  const lessons = p.modules.flatMap((m, mi) => m.lessons.map((l, li) => ({m:m.title, t:l[0], d:l[1], free:!!l[2]})));
  const access = hasAccess(p.id);
  let cur = Math.max(0, lessons.findIndex((l, i) => !(S.progress[p.id]||[]).includes(i)));
  if (!access) cur = lessons.findIndex(l => l.free) < 0 ? 0 : lessons.findIndex(l => l.free);
  let playing = false, t = 0, timer = null, speed = 1;
  const dur = l => { const [mm, s] = l.d.split(":").map(Number); return mm*60 + (s||0); };
  const fmtT = s => `${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,"0")}`;
  function draw(){
    const l = lessons[cur], open = access || l.free, done = S.progress[p.id] || [];
    root.innerHTML = `<div class="player-wrap">
      <div class="player ${playing?"playing":""}" style="position:relative">
        <span class="cat" style="color:var(--gold-deep);font-weight:700">${esc(p.title)} · ${esc(l.m)}</span>
        <div class="disc"><img src="${p.img}" alt=""></div>
        <h1 style="font-size:1.5rem">${esc(l.t)}</h1>
        ${open ? `<div class="seek"><input type="range" id="seek" min="0" max="${dur(l)}" value="${t}" aria-label="موضع التشغيل"><div class="t"><span>${fmtT(t)}</span><span>${l.d}</span></div></div>
        <div class="controls"><button class="speed" id="spd" type="button">${speed}×</button><button class="iconbtn" id="back" type="button" aria-label="رجوع ١٥ ثانية">${icon("back")}</button><button class="main" id="pp" type="button" aria-label="${playing?"إيقاف":"تشغيل"}">${icon(playing?"pause":"play")}</button><button class="iconbtn" id="fwd" type="button" aria-label="تقديم ١٥ ثانية">${icon("fwd")}</button></div>
        <button class="btn ${done.includes(cur)?"btn-ghost":"btn-plum"} btn-sm" id="markDone" type="button">${done.includes(cur)?"✓ تم إكمال الدرس":"علّم الدرس كمكتمل"}</button>
        <p class="muted" style="font-size:.8rem">في الموقع الفعلي يُبث الصوت والفيديو من Bunny Stream برابط محمي باسمك.</p>`
        : `<div class="alert info" style="display:grid;gap:10px;justify-items:center">${icon("lock")}<span>هذا الدرس متاح بعد شراء المادة أو مع عضوية استيقظ VIP.</span><div class="ctas" style="justify-content:center"><button class="btn btn-gold btn-sm" type="button" data-add="${p.id}"><span>اشترِ ${esc(p.title)}</span></button><a class="btn btn-line btn-sm" href="vip.html">استيقظ VIP</a></div></div>`}
        <div class="watermark">${S.user ? esc(S.user.email) : ""}</div>
      </div>
      <aside class="outline"><h3>محتوى المادة · ${ar(done.length)}/${ar(lessons.length)}</h3>
        ${lessons.map((x,i)=>`<button type="button" data-lesson="${i}" aria-current="${i===cur}"><span class="${done.includes(i)?"done":""}">${done.includes(i)?"✓":(access||x.free?"▶":"🔒")}</span><span>${esc(x.t)}</span><small class="muted">${x.d}</small></button>`).join("")}
        <div style="padding:14px 18px"><div class="bar"><i style="width:${Math.round(done.length/lessons.length*100)}%"></i></div></div>
      </aside></div>`;
  }
  function tick(){ const l = lessons[cur]; t += speed; if (t >= dur(l)){ t = dur(l); markDone(true); stop(); } updSeek(); }
  function updSeek(){ const s = $("#seek"); if (s){ s.value = t; s.nextElementSibling.firstElementChild.textContent = fmtT(t); } }
  function stop(){ playing = false; clearInterval(timer); draw(); }
  function markDone(auto){ const d = S.progress[p.id] = S.progress[p.id] || []; if (!d.includes(cur)){ d.push(cur); save(); if (!auto) toast("أحسنت! تم حفظ تقدّمك."); } }
  root.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    if (b.id === "pp"){ playing = !playing; clearInterval(timer); if (playing) timer = setInterval(tick, 1000); draw(); }
    if (b.id === "back"){ t = Math.max(0, t-15); updSeek(); }
    if (b.id === "fwd"){ t = Math.min(dur(lessons[cur]), t+15); updSeek(); }
    if (b.id === "spd"){ speed = speed === 1 ? 1.25 : speed === 1.25 ? 1.5 : 1; b.textContent = speed + "×"; }
    if (b.id === "markDone"){ markDone(); draw(); }
    if (b.dataset.lesson){ cur = +b.dataset.lesson; t = 0; playing = false; clearInterval(timer); draw(); }
  });
  root.addEventListener("input", e => { if (e.target.id === "seek") t = +e.target.value; });
  $$(".js-learn-title").forEach(x => x.textContent = p.title);
  draw();
  window.addEventListener("hashchange", () => location.reload());
}

/* ---------- book reader ---------- */
function initReader(){
  const root = $("#readerPage"); if (!root) return;
  const book = D.products.find(p => p.kind === "book"), pages = D.bookPages, access = hasAccess(book.id);
  const limit = access ? pages.length : D.freePages;
  let i = Math.min(S.page[book.id] || 0, limit - 1);
  function draw(){
    const pg = pages[i], wm = S.user ? S.user.email : "نسخة معاينة";
    root.innerHTML = `<div class="reader-bar"><span class="muted">${esc(book.title)} · صفحة ${ar(i+1)} من ${ar(pages.length)}</span>
      <div class="ctas"><button class="btn btn-line btn-sm" id="prev" type="button" ${i===0?"disabled":""}>السابقة</button><button class="btn btn-plum btn-sm" id="next" type="button" ${i>=pages.length-1?"disabled":""}>التالية</button></div></div>
      <div class="reader" oncontextmenu="return false"><div class="pg">${pg}</div><div class="wm">${Array(8).fill(`<span>${esc(wm)}</span>`).join("")}</div></div>
      ${!access && i >= limit-1 ? `<div class="alert info" style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between"><span>انتهت المعاينة المجانية. أكمل القراءة بعد شراء الكتاب.</span><button class="btn btn-gold btn-sm" type="button" data-add="${book.id}"><span>اشترِ الكتاب</span></button></div>` : ""}`;
  }
  root.addEventListener("click", e => {
    if (e.target.id === "prev" && i > 0){ i--; }
    else if (e.target.id === "next"){ if (i < limit-1) i++; else if (!access){ toast("أكمل القراءة بعد شراء الكتاب", ["صفحة الكتاب","book-ghosts.html"]); return; } }
    else return;
    S.page[book.id] = i; save(); draw(); window.scrollTo({top:0,behavior:"smooth"});
  });
  draw();
}

/* ---------- booking ---------- */
function initBooking(){
  const root = $("#booking"); if (!root) return;
  const days = $("#bkDays"), slots = $("#bkSlots"), title = $("#bkMonth");
  const names = ["الأحد","الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت"];
  const months = ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"];
  let start = 1, sel = null, slot = null;
  const base = new Date(); base.setHours(0,0,0,0);
  function drawDays(){
    let h = "";
    for (let k = 0; k < 7; k++){
      const d = new Date(base); d.setDate(base.getDate() + start + k);
      const off = d.getDay() === 5; // Friday off (example)
      const key = d.toISOString().slice(0,10);
      h += `<button class="day" type="button" data-day="${key}" ${off?"disabled":""} aria-pressed="${sel===key}">${names[d.getDay()]}<b>${ar(d.getDate())}</b></button>`;
    }
    days.innerHTML = h;
    const d0 = new Date(base); d0.setDate(base.getDate()+start); title.textContent = months[d0.getMonth()] + " " + ar(d0.getFullYear());
  }
  function drawSlots(){
    if (!sel){ slots.innerHTML = `<p class="muted" style="grid-column:1/-1;font-size:.88rem">اختر يوماً لعرض الأوقات المتاحة.</p>`; return; }
    const seed = Number(sel.slice(-2));
    slots.innerHTML = D.slots.map((s,k) => `<button class="slot" type="button" data-slot="${s}" ${(seed+k)%4===0?"disabled":""} aria-pressed="${slot===s}">${s}</button>`).join("");
  }
  root.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b || b.disabled) return;
    if (b.dataset.day){ sel = b.dataset.day; slot = null; drawDays(); drawSlots(); }
    if (b.dataset.slot){ slot = b.dataset.slot; drawSlots(); }
    if (b.id === "bkPrev" && start > 1){ start -= 7; drawDays(); }
    if (b.id === "bkNext" && start < 50){ start += 7; drawDays(); }
    if (b.id === "bkGo"){
      const type = (root.querySelector("input[name=stype]:checked")||{}).value;
      if (!sel || !slot){ toast("اختر اليوم والوقت أولاً"); return; }
      const d = new Date(sel); const when = `${names[d.getDay()]} ${ar(d.getDate())} ${months[d.getMonth()]} · ${slot} (بتوقيت القاهرة)`;
      S.cart.push({id:type, when}); save(); paintAll(); location.href = "cart.html";
    }
  });
  drawDays(); drawSlots();
}

/* ---------- forms ---------- */
function initForms(){
  document.addEventListener("submit", e => {
    const f = e.target;
    if (f.id === "couponForm"){ e.preventDefault(); const v = $("#coupon").value.trim().toUpperCase(); if (v === "WELCOME10"){ ss("coupon", v); toast("تم تطبيق خصم ١٠٪"); } else { ss("coupon", null); toast("كود الخصم غير صحيح"); } renderCart(); return; }
    if (f.id === "payForm"){ e.preventDefault(); submitPay(f); return; }
    if (f.id === "loginForm" || f.id === "registerForm"){
      e.preventDefault();
      const email = $("#email", f).value.trim(), pass = $("#password", f).value, name = f.id === "registerForm" ? $("#name", f).value.trim() : "";
      const msg = $(".alert", f);
      if (!/^\S+@\S+\.\S+$/.test(email) || pass.length < 6 || (f.id === "registerForm" && !name)){ msg.className = "alert err"; msg.textContent = "تأكد من البريد الإلكتروني، وأن كلمة المرور ٦ أحرف على الأقل" + (f.id === "registerForm" ? "، وأن الاسم مكتوب." : "."); msg.hidden = false; return; }
      S.user = {name: name || (S.user && S.user.email === email ? S.user.name : email.split("@")[0]), email, since:new Date().toISOString()};
      if (f.id === "registerForm" && $("#gift", f) && $("#gift", f).checked && !S.owned.includes("serenity-gift")) S.owned.push("serenity-gift");
      save(); const next = ss("next") || "account.html"; ss("next", null); location.href = next; return;
    }
    if (f.id === "forgotForm"){ e.preventDefault(); const m = $(".alert", f); m.className = "alert ok"; m.textContent = "إن كان البريد مسجلاً لدينا، ستصلك رسالة بها رابط لتعيين كلمة مرور جديدة."; m.hidden = false; return; }
    if (f.id === "profileForm"){ e.preventDefault(); S.user.name = $("#pName").value.trim() || S.user.name; S.user.email = $("#pEmail").value.trim() || S.user.email; save(); paintHeader(); toast("تم حفظ بياناتك"); return; }
    if (f.matches("[data-simple]")){
      e.preventDefault();
      if (!f.checkValidity()){ f.reportValidity(); return; }
      const m = $(".alert", f) || f.parentElement.querySelector(".alert"); if (m){ m.className = "alert ok"; m.textContent = f.dataset.simple; m.hidden = false; }
      f.reset();
    }
  });
}

/* ---------- clicks ---------- */
document.addEventListener("click", e => {
  const add = e.target.closest("[data-add]");
  if (add){ e.preventDefault(); const id = add.dataset.add; if (S.cart.some(c => c.id === id) && !add.classList.contains("add") && P[id].kind !== "session"){ location.href = "cart.html"; return; } addToCart(id); return; }
  const fav = e.target.closest("[data-fav]");
  if (fav){ e.preventDefault(); const id = fav.dataset.fav; S.favs = S.favs.includes(id) ? S.favs.filter(x => x !== id) : S.favs.concat(id); save(); fav.setAttribute("aria-pressed", S.favs.includes(id)); toast(S.favs.includes(id) ? "حُفظت في المفضلة" : "أُزيلت من المفضلة"); return; }
  const rm = e.target.closest("[data-rm]");
  if (rm){ S.cart.splice(+rm.dataset.rm, 1); save(); paintAll(); return; }
  const rg = e.target.closest(".region button");
  if (rg){ S.region = rg.dataset.region; save(); paintAll(); if ($("#checkoutPage")) renderCheckout(); return; }
  const tab = e.target.closest("[data-filter]");
  if (tab){ shelfFilter = tab.dataset.filter; $$("[data-filter]").forEach(t => t.setAttribute("aria-pressed", t === tab)); renderDynamic(); return; }
  const plan = e.target.closest("[data-plan]");
  if (plan){ vipPlan = plan.dataset.plan; $$("[data-plan]").forEach(t => t.setAttribute("aria-pressed", t === plan)); renderVipBar(); return; }
  const nx = e.target.closest("[data-next]");
  if (nx){ ss("next", nx.dataset.next); return; }
  if (e.target.closest("#logout")){ S.user = null; save(); location.href = "index.html"; return; }
  if (e.target.closest("#cancelVip")){ toast("أُلغي التجديد التلقائي. يبقى وصولك حتى نهاية الفترة."); return; }
  const prev = e.target.closest("[data-preview]");
  if (prev){ location.href = "learn.html#" + prev.dataset.preview; return; }
  if (e.target.closest(".js-demo-login")){ S.user = {name:"مشتركة تجريبية", email:"demo@example.com", since:new Date().toISOString()}; if (!S.owned.length) S.owned = ["ain-sahia","attach","breath"]; save(); location.href = "account.html"; return; }
});
document.addEventListener("input", e => { if (e.target.id === "q"){ shelfQuery = e.target.value.trim(); renderDynamic(); } });
window.addEventListener("hashchange", () => { if ($("#accountPage")) renderAccount(); });

/* ---------- menu ---------- */
const burger = $("#burger"), menu = $("#menu");
if (burger) burger.addEventListener("click", () => { const o = menu.classList.toggle("open"); burger.setAttribute("aria-expanded", o); });

/* ---------- success page ---------- */
const sx = $("#successBox");
if (sx){ let o = null; try { o = JSON.parse(ss("lastOrder") || "null"); } catch(e){}
  if (o){ $("#oNo").textContent = o.no; $("#oTotal").textContent = o.total; $("#oEmail").textContent = o.email; $("#oItems").innerHTML = o.items.map(i => `<li>${esc(i)}</li>`).join(""); } }

/* ---------- gold dust ---------- */
$$("canvas.sparkle").forEach(c => {
  const x = c.getContext("2d"), reduce = matchMedia("(prefers-reduced-motion: reduce)").matches; let w, h, dots = [];
  function size(){ const r = c.getBoundingClientRect(), d = Math.min(devicePixelRatio||1, 2); w = r.width; h = r.height; c.width = w*d; c.height = h*d; x.setTransform(d,0,0,d,0,0);
    dots = Array.from({length: Math.round(w*h/9000)}, () => ({x:Math.random()*w, y:Math.random()*h, r:Math.random()*1.6+.4, p:Math.random()*6.28, s:Math.random()*.25+.05})); }
  function draw(t){ x.clearRect(0,0,w,h);
    for (const d of dots){ const a = .35 + .65*Math.abs(Math.sin(d.p + t/1400));
      if (!reduce){ d.y -= d.s; if (d.y < -4){ d.y = h + 4; d.x = Math.random()*w; } }
      x.beginPath(); x.fillStyle = `rgba(214,170,70,${a*.85})`; x.arc(d.x, d.y, d.r, 0, 6.28); x.fill();
      if (d.r > 1.6){ x.strokeStyle = `rgba(230,190,90,${a*.5})`; x.lineWidth = .6; x.beginPath(); x.moveTo(d.x-d.r*3,d.y); x.lineTo(d.x+d.r*3,d.y); x.moveTo(d.x,d.y-d.r*3); x.lineTo(d.x,d.y+d.r*3); x.stroke(); } }
    if (!reduce) requestAnimationFrame(draw); }
  size(); addEventListener("resize", size); requestAnimationFrame(draw);
});

initForms(); initPlayer(); initReader(); initBooking();
paintAll();
})();
