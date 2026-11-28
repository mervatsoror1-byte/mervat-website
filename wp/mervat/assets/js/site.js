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

/* ---------- "coming soon": tools not recorded yet can't be bought ---------- */
const isSoon = id => !!(P[id] && P[id].soon);
function paintSoon(root){
  (root || document).querySelectorAll("[data-buy],[data-add]").forEach(b => {
    const id = b.dataset.buy || b.dataset.add;
    if (!isSoon(id) || b.dataset.soonDone) return;
    b.dataset.soonDone = "1";
    if (b.dataset.add && !b.dataset.buy){
      const tag = document.createElement("span"); tag.className = "soon-tag"; tag.textContent = "قريباً";
      b.replaceWith(tag); return;
    }
    b.classList.add("is-soon"); b.setAttribute("aria-disabled", "true");
    b.innerHTML = "<span>قريباً</span>";
  });
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-buy],[data-add]");
  if (b && isSoon(b.dataset.buy || b.dataset.add)){
    e.preventDefault(); e.stopImmediatePropagation();
    const t = document.querySelector(".toast") || Object.assign(document.createElement("div"), {className: "toast"});
    if (!t.parentNode) document.body.appendChild(t);
    t.textContent = "قريباً بإذن الله. تابعينا لتكوني أول من يعرف."; t.classList.add("show"); setTimeout(() => t.classList.remove("show"), 3200);
  }
}, true);
new MutationObserver(() => paintSoon()).observe(document.documentElement, {childList: true, subtree: true});
document.addEventListener("DOMContentLoaded", () => paintSoon());

document.addEventListener("click", e => {
  const wa = e.target.closest('#checkoutPage a[href*="wa.me"]');
  if (!wa) return;
  if (!checkoutReady()){ e.preventDefault(); e.stopImmediatePropagation(); return; }
  const items = payItems(); wa.href = waOrderLink(items, totals(items));
}, true);
/* ---------- state ---------- */
const KEY = "ms_state_v1";
const blank = {region:"eg", cart:[], favs:[], user:null, owned:[], vip:null, progress:{}, orders:[], bookings:[], page:{}};
let S, fresh = false;
try { const raw = localStorage.getItem(KEY); fresh = !raw; S = Object.assign({}, blank, JSON.parse(raw || "{}")); } catch(e) { S = Object.assign({}, blank); fresh = true; }
// first visit: choose currency from the visitor's time zone (Egypt → EGP, elsewhere → USD)
if (fresh){ try { S.region = Intl.DateTimeFormat().resolvedOptions().timeZone === "Africa/Cairo" ? "eg" : "intl"; } catch(e){} }
// This site has no real accounts: purchases are delivered by email until the WordPress shop goes live.
// Clear anything the old demo stored in the browser (fake sign-in, "owned" tools, demo orders).
if (!window.MS_WP){
  const demo = S.user && /example\.com$/i.test(S.user.email || "");
  if (S.owned.length || S.vip || S.orders.length || S.bookings.length || demo){
    S.owned = []; S.vip = null; S.orders = []; S.bookings = []; S.progress = {};
    if (demo) S.user = null;
    try { localStorage.setItem(KEY, JSON.stringify(S)); } catch(e){}
  }
}
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
  $$(".js-user-text").forEach(a => { a.href = S.user ? "{{H}}/my-account/#mine" : "{{H}}/my-account/"; a.textContent = S.user ? "اشتراكاتي" : "تسجيل الدخول"; });
  $$(".js-user").forEach(a => {
    if (S.user){ a.href = "{{H}}/my-account/"; a.innerHTML = `<span class="avatar">${esc(S.user.name.trim()[0]||"م")}</span>`; a.setAttribute("aria-label","حسابي"); }
    else { a.href = "{{H}}/my-account/"; a.innerHTML = icon("user"); a.setAttribute("aria-label","تسجيل الدخول"); }
  });
}
function setPriceText(e, txt){
  const t = e.firstChild;
  if (t && t.nodeType === 3){ if (t.data !== txt) t.data = txt; }
  else e.prepend(document.createTextNode(txt));
}
/* small currency switch next to every price */
function curMini(){
  const t = S.region === "eg" ? "⇄ $" : "⇄ ج.م", lbl = S.region === "eg" ? "عرض الأسعار بالدولار" : "عرض الأسعار بالجنيه المصري";
  $$("[data-price], #vipAmount").forEach(el => {
    let b = [...el.children].find(c => c.classList.contains("cur-mini"));
    if (!b){ b = document.createElement("button"); b.type = "button"; b.className = "cur-mini"; el.appendChild(b); }
    if (b.textContent !== t){ b.textContent = t; b.title = lbl; b.setAttribute("aria-label", lbl); }
  });
}
function paintPrices(){
  $$("[data-price]").forEach(e => { const p = P[e.dataset.price]; if (p) setPriceText(e, money(p.eg, p.us)); });
  $$("[data-eg]").forEach(e => e.textContent = S.region === "eg" ? e.dataset.eg : e.dataset.us);
  $$("[data-wasof]").forEach(e => { const p = P[e.dataset.wasof]; e.hidden = !(p && p.wasEg && S.region === "eg"); if (!e.hidden && e.tagName === "S") e.textContent = ar(p.wasEg) + " ج.م"; });
  $$("[data-was]").forEach(e => { const [eg, us] = e.dataset.was.split("|"); e.textContent = S.region === "eg" ? ar(eg) + " ج.م" : "$" + us; });
}
function paintButtons(){
  $$("[data-add]").forEach(b => {
    const id = b.dataset.add, inCart = S.cart.some(c => c.id === id), owned = hasAccess(id);
    if (b.classList.contains("add")){ b.classList.toggle("in", inCart); b.innerHTML = icon(inCart ? "check" : "bag"); }
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
function addToCart(id, extra){ if (window.MS_WP && window.addToCart && window.addToCart !== addToCart) return window.addToCart(id, extra);
  const p = P[id]; if (!p) return;
  if (hasAccess(id) && p.learn){ location.href = p.learn; return; }
  if (p.kind === "vip") S.cart = S.cart.filter(c => P[c.id].kind !== "vip");
  if (!S.cart.some(c => c.id === id) || p.kind === "session") S.cart.push(Object.assign({id}, extra||{}));
  save(); paintAll(); toast("أُضيف إلى السلة: " + p.title, ["عرض السلة", "{{H}}/cart/"]);
}

/* ---------- product card ---------- */
function card(p){
  const owned = hasAccess(p.id), lessons = p.lessonsCount || 1;
  const kind = p.kind === "course" ? "كورس" : p.kind === "book" ? "كتاب" : "تمرين";
  return `<article class="scard" data-cat="${p.cat}">
    <div class="sc-img"><a class="ph${p.cover ? " has-cover" : ""}" href="${p.page}" aria-label="${esc(p.title)}"><img src="${p.cover || (window.MS_WP ? MS_WP.theme + "/" : "") + "assets/brand/logo-icon-gold.webp"}" alt="" loading="lazy"></a>
      <button class="sc-fav" type="button" data-fav="${p.id}" aria-pressed="false" aria-label="احفظ في المفضلة">${icon("heart")}</button>
      ${owned ? '<span class="sc-own">✓ اشتريته</span>' : ''}</div>
    <div class="sc-tags"><span>${kind}</span><span>${esc(p.catLabel)}</span></div>
    <h3><a href="${p.page}">${esc(p.title)}</a></h3><div class="rt-sum sm" data-rate-sum="${p.id}"></div>
    <span class="sc-meta">${icon("lessons")}${p.cardMeta ? esc(p.cardMeta) : ar(lessons) + " " + (lessons > 2 ? "دروس" : lessons == 2 ? "درسان" : "درس")}</span>
    <span class="sc-price" data-price="${p.id}">${money(p.eg,p.us)}</span>
    <div class="sc-act">${owned ? `<a class="btn btn-gold btn-sm" href="${p.learn}">ابدأ الآن</a>` : `<a class="btn btn-gold btn-sm" href="${p.page}">عرض التفاصيل</a><button class="add" type="button" data-add="${p.id}" aria-label="أضف ${esc(p.title)} للسلة">${icon("plus")}</button>`}</div>
  </article>`;
}
function bundleCard(b){
  const eg = b.items.reduce((s,i)=>s+P[i].eg,0), us = b.items.reduce((s,i)=>s+P[i].us,0), p = P[b.id];
  return `<article class="bundle">
    <div class="fan" aria-hidden="true">${b.fan.map(s=>`<img src="${s}" alt="">`).join("")}</div>
    <h3>${esc(p.title)}</h3><p class="inside">${b.items.map(i=>esc(P[i].title)).join(" · ")}</p>
    ${b.flow ? `<ol class="b-flow">${b.flow.map((f,n)=>`<li><i>${ar(n+1)}</i>${esc(f)}</li>`).join("")}</ol>` : ""}
    <span class="saving">توفّر ${S.region==="eg" ? ar(eg-p.eg)+" ج.م" : "$"+(us-p.us)}</span>
    <div class="buy"><span class="price">${money(p.eg,p.us)}<s>${S.region==="eg" ? ar(eg)+" ج.م" : "$"+us}</s></span>
      <span class="buy-ctas"><button class="btn btn-gold btn-sm" type="button" data-buy="${p.id}"><span>ابدأ الآن</span></button><button class="add" type="button" data-add="${p.id}" aria-label="أضف ${esc(p.title)} للسلة" title="أضف للسلة"></button></span></div>
  </article>`;
}

/* ---------- dynamic regions ---------- */
let shelfFilter = "all", shelfQuery = "", shelfSort = "new";
function renderDynamic(){
  $$("[data-shelf]").forEach(el => {
    const mode = el.dataset.shelf;
    let list = D.products.filter(p => p.kind === "exercise" || p.kind === "course");
    if (shelfSort === "low") list = list.slice().sort((a,b) => a.eg - b.eg);
    if (shelfSort === "high") list = list.slice().sort((a,b) => b.eg - a.eg);
    if (mode === "home") list = list.slice(0, 9);
    if (mode === "related"){ const cur = el.dataset.current; list = list.filter(p => p.id !== cur).slice(0, 3); }
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
  $$(".add[data-add]").forEach(b => { const inCart = S.cart.some(c => c.id === b.dataset.add); b.classList.toggle("in", inCart); b.innerHTML = icon(inCart ? "check" : "bag"); });
  if ($("#cartPage")) renderCart();
  if ($("#checkoutPage")) renderCheckout();
  if ($("#accountPage")) renderAccount();
  if ($("#vipAmount")) renderVipBar();
}
function paintPricesOnly(){ $$("[data-price]").forEach(e => { const p = P[e.dataset.price]; if (p) setPriceText(e, money(p.eg, p.us)); }); }

/* Discount codes for real occasions only, e.g. {"RAMADAN": .15}. Empty = no active codes. */
const COUPONS = {};

/* ---------- cart page ---------- */
function buyNow(){ try { return JSON.parse(ss("buynow") || "null"); } catch(e){ return null; } }
function payItems(){ const b = buyNow(); return b ? [b] : S.cart; }
function totals(list){
  list = list || S.cart;
  const sub = list.reduce((s,c) => s + priceOf(P[c.id]), 0);
  const code = ss("coupon"); const disc = (COUPONS[code] || 0) * sub;
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
  if (!S.cart.length){ box.innerHTML = `<div class="result"><div class="badge" style="background:var(--blush);color:var(--plum)">${icon("bag")}</div><h2>سلتك فارغة</h2><p class="lead">ابدأ بتمرين قصير، أو انضم إلى استيقظ VIP لرحلة خاصة مع د. مرفت.</p><div class="ctas" style="justify-content:center"><a class="btn btn-gold" href="{{H}}/vip/">استيقظ VIP</a><a class="btn btn-line" href="{{H}}/library/">تصفّح التمارين</a></div></div>`; return; }
  box.innerHTML = `<div class="cart-grid"><div class="lines">${S.cart.map((c,i)=>lineHTML(c,i)).join("")}${upsellHTML()}</div>
    <aside class="card summary"><h3>ملخص الطلب</h3>
      <div class="cur-switch"><span>عملة الدفع</span><div class="region" role="group" aria-label="عملة الدفع"><button type="button" data-region="eg" aria-pressed="${S.region==="eg"}">جنيه مصري</button><button type="button" data-region="intl" aria-pressed="${S.region!=="eg"}">دولار</button></div></div>
      <div class="sumrow"><span>المجموع</span><span>${fmt(t.sub)}</span></div>
      ${t.disc ? `<div class="sumrow" style="color:var(--ok)"><span>خصم ${esc(t.code)}</span><span>− ${fmt(t.disc)}</span></div>` : ""}
      <div class="sumrow total"><span>الإجمالي</span><span>${fmt(t.total)}</span></div>
      <form class="coupon" id="couponForm"><label class="sr" for="coupon">كود الخصم</label><input id="coupon" placeholder="كود الخصم" value="${esc(t.code||"")}"><button class="btn btn-ghost btn-sm" type="submit">تطبيق</button></form>
      <a class="btn btn-gold btn-block" href="{{H}}/checkout/" id="toCheckout">إتمام الشراء</a>
      <p class="secure">${icon("lock")}دفع آمن ومشفّر · وصول فوري بعد الدفع</p>
    </aside></div>`;
}

function upsellHTML(){
  const ids = S.cart.map(c => c.id), hasVip = ids.some(i => P[i].kind === "vip") || S.vip;
  // 1) a bundle that contains something in the cart
  const b = D.bundles.find(b => !ids.includes(b.id) && b.items.some(i => ids.includes(i)) && !b.items.every(i => hasAccess(i)));
  let h = "";
  if (b){ const p = P[b.id], full = b.items.reduce((s,i)=>s+priceOf(P[i]),0);
    h += `<div class="upsell"><span class="ico">${icon("layers")}</span><div><b>أكمل المسار: ${esc(p.title)}</b><p>${b.items.map(i=>esc(P[i].title)).join(" · ")}، بسعر ${money(p.eg,p.us)} بدلاً من ${fmt(full)}.</p></div><button class="btn btn-plum btn-sm" type="button" data-swap="${b.id}">استبدل بالباقة</button></div>`; }
  // 2) VIP when the cart holds 2+ paid items
  const paid = S.cart.filter(c => ["exercise","course","bundle"].includes(P[c.id].kind));
  if (!hasVip && paid.length){ const v = P["vip-m"];
    h += `<div class="upsell"><span class="ico">${icon("crown")}</span><div><b>رحلة أعمق مع استيقظ VIP</b><p>جلسات فردية خاصة مع د. مرفت، وتمرينات مخصصة لكِ، ومتابعة يومية، بـ ${money(v.eg,v.us)} شهرياً.</p></div><a class="btn btn-gold btn-sm" href="{{H}}/vip/">اعرف البرنامج</a></div>`; }
  return h;
}

/* ---------- checkout ---------- */
const GATEWAYS = {
  eg: [
    {id:"paymob-card", t:"بطاقة بنكية", s:"فيزا · ماستركارد · ميزة (Paymob)", l:["VISA","MC","ميزة"]},
    {id:"paymob-wallet", t:"محفظة إلكترونية", s:"فودافون كاش وغيرها", l:["محافظ"]},
  ],
  intl: [
    {id:"nbe-card", t:"بطاقة دولية", s:"Visa · Mastercard بالدولار (البنك الأهلي المصري)", l:["VISA","MC"]},
    {id:"paypal", t:"PayPal", s:"ادفع من رصيدك أو بطاقتك عبر PayPal", l:["PayPal"]}]
};
/* PayPal (USD): public client id of the "Mervat Website" live app. Orders are recorded by api/order.php, which emails Mervat. */
const PAYPAL_CLIENT_ID = "BAAuJ28XBWu2exv0mdBFYtzTRI-PG9UtXjBq6wj4OQbdd-UcK1cVMZOMXRe3Li9PeWiFGRPcypy-0CnvZY";
const usdTotal = items => (Math.round(items.reduce((s, c) => s + (+P[c.id].us || 0), 0) * 100) / 100).toFixed(2).replace(/\.00$/, "");
let ppLoading = null;
function loadPayPal(){
  if (window.paypal) return Promise.resolve(window.paypal);
  if (!ppLoading) ppLoading = new Promise((ok, no) => {
    const sc = document.createElement("script");
    sc.src = "https://www.paypal.com/sdk/js?client-id=" + encodeURIComponent(PAYPAL_CLIENT_ID) + "&currency=USD&intent=capture&components=buttons&disable-funding=card,credit,paylater,venmo";
    sc.onload = () => ok(window.paypal); sc.onerror = () => { ppLoading = null; no(new Error("paypal")); };
    document.head.appendChild(sc);
  });
  return ppLoading;
}
async function initPayPal(items){
  const box = $("#ppButtons"); if (!box) return;
  const usd = usdTotal(items), single = !!buyNow();
  const desc = items.map(c => P[c.id].title).join(" + ").slice(0, 120);
  try {
    const pp = await loadPayPal();
    box.innerHTML = "";
    await pp.Buttons({
      style: {layout: "horizontal", color: "white", shape: "pill", label: "paypal", height: 52, tagline: false},
      onClick: (d, actions) => checkoutReady() ? actions.resolve() : actions.reject(),
      createOrder: (d, actions) => actions.order.create({
        purchase_units: [{amount: {currency_code: "USD", value: (+usd).toFixed(2)}, description: desc}],
        application_context: {shipping_preference: "NO_SHIPPING", brand_name: "Mervat Soror"}
      }),
      onApprove: async (d, actions) => {
        box.innerHTML = `<span class="muted">جارٍ تأكيد الدفع…</span>`;
        const cap = await actions.order.capture();
        const c0 = (((cap.purchase_units || [])[0] || {}).payments || {}).captures || [];
        const capId = (c0[0] && c0[0].id) || cap.id;
        const paid = c0[0] && c0[0].amount ? c0[0].amount.currency_code + " " + c0[0].amount.value : "";
        const payer = cap.payer || {};
        let no = "MS-" + String(capId).slice(-6);
        try {
          const r = await fetch((window.MS_WP ? MS_WP.home + "/" : "") + "api/order.php", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({
            paypal_id: capId, paid, items: items.map(c => ({id: c.id, when: c.when || ""})),
            name: buyer().name, email: buyer().email, payer_email: payer.email_address || ""})});
          const j = await r.json(); if (j && j.no) no = j.no;
        } catch(e){}
        S.orders.unshift({no, date: new Date().toLocaleDateString("ar-EG"), items: items.map(c => P[c.id].title), total: "$" + usd, gw: "paypal", status: "قيد التفعيل"});
        ss("lastOrder", JSON.stringify({no, total: "$" + usd, items: items.map(c => P[c.id].title), email: buyer().email || payer.email_address || "", gw: "paypal"}));
        if (single){ S.cart = S.cart.filter(c => c.id !== items[0].id); ss("buynow", null); } else { S.cart = []; }
        save(); location.href = "{{H}}/my-account/orders/";
      },
      onCancel: () => toast("أُلغيت عملية الدفع، ولم يُخصم أي مبلغ."),
      onError: () => toast("تعذّر الدفع عبر PayPal. جرّبي مرة أخرى أو أكملي الطلب عبر واتساب.")
    }).render(box);
  } catch(e){ box.innerHTML = `<span class="muted">تعذّر تحميل زر PayPal. أكملي الطلب عبر واتساب.</span>`; }
}

/* Online payment switch: false until the payment gateway is connected; orders go through WhatsApp meanwhile. */
const PAY_LIVE = false;
function buyer(){
  if (S.user) return {name: S.user.name, email: S.user.email};
  const n = document.getElementById("buyerName"), e = document.getElementById("buyerEmail");
  const b = {name: n ? n.value.trim() : "", email: e ? e.value.trim() : ""};
  if (n || e){ S.buyer = b; save(); }
  return b;
}
function checkoutReady(){
  const b = buyer();
  if (!b.name){ toast("اكتبي اسمك أولاً."); const n = document.getElementById("buyerName"); n && n.focus(); return false; }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(b.email)){ toast("اكتبي بريداً إلكترونياً صحيحاً، فعليه يصلك التمرين."); const e = document.getElementById("buyerEmail"); e && e.focus(); return false; }
  const ok = document.getElementById("agreeTerms");
  if (ok && !ok.checked){ toast("يرجى الموافقة على الشروط وسياسة الاسترداد أولاً."); ok.focus(); return false; }
  return true;
}
function waOrderLink(items, t){
  const lines = items.map(c => "• " + P[c.id].title + (c.when ? " (" + c.when + ")" : "")).join("\n");
  const msg = "مرحباً د. مرفت، أريد إتمام طلبي من الموقع:\n" + lines + "\nالإجمالي: " + fmt(t.total) + (buyer().email ? "\nالاسم: " + buyer().name + "\nالبريد: " + buyer().email : "");
  return "https://wa.me/201095292748?text=" + encodeURIComponent(msg);
}
function renderCheckout(){
  const box = $("#checkoutPage"), items = payItems(), single = !!buyNow();
  if (!S.user && PAY_LIVE){ ss("next", "{{H}}/checkout/"); location.replace("{{H}}/my-account/"); return; }
  if (!items.length){ box.innerHTML = `<div class="result"><h2>لا يوجد ما تدفعه الآن</h2><a class="btn btn-gold" href="{{H}}/library/">تصفّح الأدوات</a></div>`; return; }
  const t = totals(items), recurring = items.some(c => P[c.id].kind === "vip");
  const gws = GATEWAYS[S.region].filter(g => !recurring || ["paymob-card","nbe-card","paypal"].includes(g.id));
  const last = S.lastGw && gws.some(g => g.id === S.lastGw) ? S.lastGw : gws[0].id;
  box.innerHTML = `<div class="cart-grid">
   <form class="form" id="payForm" novalidate>
    <div class="card form">
      ${S.user ? `<div class="alert info">تشتري باسم <b>${esc(S.user.name)}</b> · ${esc(S.user.email)}</div>`
        : `<div class="row2"><div class="field"><label for="buyerName">الاسم</label><input id="buyerName" autocomplete="name" value="${esc((S.buyer||{}).name||"")}"></div>
           <div class="field"><label for="buyerEmail">البريد الإلكتروني (يصلك عليه التمرين)</label><input id="buyerEmail" type="email" autocomplete="email" dir="ltr" value="${esc((S.buyer||{}).email||"")}"></div></div>`}
      ${PAY_LIVE ? `<h3>طريقة الدفع</h3>
      ${recurring ? `<div class="alert info">اشتراك متجدد تلقائياً، ويمكنك إلغاء التجديد في أي وقت من «حسابي ← اشتراكاتي».</div>` : ""}
      <div class="pay-opts">${gws.map(g=>`<label class="pay-opt"><input type="radio" name="gw" value="${g.id}" ${g.id===last?"checked":""}><span><b>${g.t}</b><small>${g.s}</small></span><span class="logos">${g.l.map(x=>`<span>${x}</span>`).join("")}</span></label>`).join("")}</div>` : `<h3>إتمام الطلب</h3>`}
      <div class="alert err" id="payErr" hidden></div>
      ${PAY_LIVE ? `<button class="btn btn-gold btn-block" type="submit">${icon("lock")}ادفع ${fmt(t.total)}</button>
      <p class="secure" style="text-align:center">بالضغط على «ادفع» أنت توافق على <a href="{{H}}/terms/">الشروط والأحكام</a> و<a href="{{H}}/refund/">سياسة الاسترداد</a>، والشراء نهائي.</p>`
      : `<label class="check agree-box"><input type="checkbox" id="agreeTerms"><span>قرأت وأوافق على <a href="{{H}}/terms/" target="_blank">الشروط والأحكام</a> و<a href="{{H}}/refund/" target="_blank">سياسة الاسترداد والإلغاء</a></span></label>
      <div class="pp-box"><div class="pp-head"><b>الدفع بالبيبال</b><span class="pp-amt">$${usdTotal(items)}</span></div>
        <div id="ppButtons" class="pp-buttons"><span class="muted">جارٍ تحميل زر الدفع…</span></div></div>
      <div class="pp-or"><span>أو</span></div>
      <div class="alert info pay-soon"><b>للدفع بالجنيه المصري أو بالتحويل (إنستاباي / فودافون كاش):</b> حتى تفعيل الدفع الإلكتروني بالبطاقة، يتم الطلب عبر واتساب.</div>
      <a class="btn btn-line btn-block" href="${waOrderLink(items, t)}" target="_blank" rel="noopener">${icon("chat")}الطلب عبر واتساب (${money(items.reduce((s,c)=>s+P[c.id].eg,0), items.reduce((s,c)=>s+P[c.id].us,0))})</a>
      <p class="secure" style="display:block;text-align:center">بإتمام الطلب أنتِ توافقين على <a href="{{H}}/terms/">الشروط والأحكام</a> و<a href="{{H}}/refund/">سياسة الاسترداد</a>.</p>`}
    </div>
   </form>
   <aside class="card summary"><h3>طلبك</h3>
     <div class="cur-switch"><span>عملة الدفع</span><div class="region" role="group" aria-label="عملة الدفع"><button type="button" data-region="eg" aria-pressed="${S.region==="eg"}">جنيه مصري</button><button type="button" data-region="intl" aria-pressed="${S.region!=="eg"}">دولار</button></div></div>
     <div class="lines">${items.map((c,i)=>lineHTML(c,i,true)).join("")}</div>
     <div class="sumrow"><span>المجموع</span><span>${fmt(t.sub)}</span></div>
     ${t.disc ? `<div class="sumrow" style="color:var(--ok)"><span>خصم</span><span>− ${fmt(t.disc)}</span></div>` : ""}
     <div class="sumrow total"><span>الإجمالي</span><span>${fmt(t.total)}</span></div>
     ${single ? `<button class="btn btn-line btn-sm" type="button" id="addInstead">أريد إضافة أدوات أخرى · انقل إلى السلة</button>` : ""}</aside>
  </div>`;
  if (!PAY_LIVE) initPayPal(items);
}
function submitPay(f){
  if (!PAY_LIVE) return;
  const items = payItems(), single = !!buyNow();
  const t = totals(items), gw = (f.querySelector("input[name=gw]:checked")||{}).value, no = "MS-" + (10240 + S.orders.length + 1);
  items.forEach(c => {
    const p = P[c.id];
    if (p.kind === "vip") S.vip = {plan:p.id, since:new Date().toISOString()};
    else if (p.kind === "bundle") D.bundles.find(b => b.id === p.id).items.forEach(i => S.owned.includes(i) || S.owned.push(i));
    else if (p.kind === "session") S.bookings.push({type:p.title, when:c.when, link:"يُرسل قبل الجلسة"});
    else { const g = p.grants || p.id; if (!S.owned.includes(g)) S.owned.push(g); }
  });
  S.lastGw = gw;
  S.orders.unshift({no, date:new Date().toLocaleDateString("ar-EG"), items:items.map(c=>P[c.id].title), total:fmt(t.total), gw, status:"مكتمل"});
  ss("lastOrder", JSON.stringify({no, total:fmt(t.total), items:items.map(c=>P[c.id].title), email:S.user.email, gw}));
  if (single){ S.cart = S.cart.filter(c => c.id !== items[0].id || P[c.id].kind === "session"); ss("buynow", null); }
  else { S.cart = []; }
  try { localStorage.removeItem("ms_pending_v1"); } catch(e){}
  ss("coupon", null); save();
  location.href = "{{H}}/my-account/orders/";
}
function startBuy(id, extra){ if (window.MS_WP && window.startBuy && window.startBuy !== startBuy) return window.startBuy(id, extra);
  const p = P[id]; if (!p) return;
  if (hasAccess(id) && p.learn){ location.href = p.learn; return; }
  ss("buynow", JSON.stringify(Object.assign({id}, extra||{})));
  try { localStorage.setItem("ms_pending_v1", JSON.stringify({id, extra: extra||null, t: Date.now(), shown: 0})); } catch(e){}
  if (!S.user && PAY_LIVE){ ss("next", "{{H}}/checkout/"); location.href = "{{H}}/my-account/"; return; }
  location.href = "{{H}}/checkout/";
}

/* ---------- VIP bar ---------- */
let vipPlan = "vip-m";
function renderVipBar(){
  const p = P[vipPlan];
  $("#vipAmount").innerHTML = money(p.eg, p.us) + ` <small>/ ${({"vip-m":"شهرياً","vip-q":"كل ٣ أشهر","vip-y":"سنوياً"})[p.id]}</small>`;
  const b = $("#vipJoin"); if (b){ b.dataset.buy = vipPlan; b.removeAttribute("data-add"); }
  if (S.vip && b){ b.textContent = "أنت عضو في استيقظ VIP"; b.removeAttribute("data-add"); b.href = "{{H}}/my-account/#subscription"; }
}

/* ---------- account ---------- */
function renderAccount(){
  const box = $("#accountPage");
  if (!S.user){ ss("next","{{H}}/my-account/"); location.replace("{{H}}/my-account/"); return; }
  let tab = (location.hash || "#overview").slice(1); if (["courses","books","subscription"].includes(tab)) tab = "mine";
  $$(".acc-nav a").forEach(a => a.setAttribute("aria-current", a.getAttribute("href") === "#" + tab));
  $$(".js-uname").forEach(e => e.textContent = S.user.name); $$(".js-uemail").forEach(e => e.textContent = S.user.email);
  const learnables = D.products.filter(p => p.learn && hasAccess(p.id) && p.kind !== "book");
  const books = D.products.filter(p => p.kind === "book" && hasAccess(p.id));
  const pct = id => { const p = P[id], total = p.lessonsCount || 1, done = (S.progress[id]||[]).length; return Math.round(done/total*100); };
  const mine = list => list.length ? `<div class="mine">${list.map(p => `<div class="mine-item"><img src="${p.img}" alt=""><div><span class="cat muted" style="font-size:.78rem">${esc(p.catLabel)}</span><h3>${esc(p.title)}</h3><div class="bar"><i style="width:${pct(p.id)}%"></i></div><small class="muted">${ar(pct(p.id))}٪ مكتمل</small></div><a class="btn btn-plum btn-sm" href="${p.learn}">${pct(p.id) ? "أكمل" : "ابدأ"}</a></div>`).join("")}</div>`
    : `<div class="card" style="text-align:center"><p class="muted">لا توجد مواد في مكتبتك بعد.</p><div class="ctas" style="justify-content:center;margin-top:12px"><a class="btn btn-gold btn-sm" href="{{H}}/vip/">استيقظ VIP</a><a class="btn btn-line btn-sm" href="{{H}}/library/">تصفّح التمارين</a></div></div>`;
  const views = {
    overview: `<h1 class="title">أهلاً ${esc(S.user.name.split(" ")[0])}</h1>
      <div class="stats"><div class="stat"><b>${ar(learnables.length)}</b><span>مواد في مكتبتك</span></div><div class="stat"><b>${ar(S.bookings.length)}</b><span>جلسات محجوزة</span></div><div class="stat"><b>${S.vip ? "فعّالة" : "—"}</b><span>عضوية استيقظ VIP</span></div></div>
      <h2 style="font-size:1.25rem">أكمل من حيث توقفت</h2>${mine(learnables.slice(0,3))}`,
    mine: `<h1 class="title">اشتراكاتي</h1>
      <div class="card form" style="gap:10px"><div style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px;align-items:center"><span><b style="color:var(--ink)">برنامج استيقظ VIP</b><br><small class="muted">${S.vip ? (S.vip.cancelled ? "أُلغي التجديد · الوصول متاح حتى نهاية الفترة" : "فعّال · " + esc(P[S.vip.plan].title) + " · يتجدد تلقائياً") : "غير مشترك"}</small></span>
        ${S.vip ? (S.vip.cancelled ? `<span class="pill wait">ينتهي بنهاية الفترة</span>` : `<button class="btn btn-line btn-sm" type="button" id="cancelVip">إلغاء التجديد التلقائي</button>`) : `<a class="btn btn-gold btn-sm" href="{{H}}/vip/">اشترك الآن</a>`}</div></div>
      <h2 style="font-size:1.25rem">الأدوات (${ar(learnables.length)})</h2>${mine(learnables)}
      ${books.length ? `<h2 style="font-size:1.25rem">الكتب</h2><div class="mine">${books.map(p=>`<div class="mine-item"><img src="${p.img}" alt=""><div><h3>${esc(p.title)}</h3><small class="muted">آخر صفحة: ${ar((S.page[p.id]||0)+1)}</small></div><a class="btn btn-plum btn-sm" href="{{H}}/my-account/">اقرأ</a></div>`).join("")}</div>` : ""}
      ${S.bookings.length ? `<h2 style="font-size:1.25rem">الجلسات</h2><div class="scroll-x"><table class="table"><thead><tr><th>الجلسة</th><th>الموعد</th><th>الرابط</th></tr></thead><tbody>${S.bookings.map(b=>`<tr><td>${esc(b.type)}</td><td>${esc(b.when)}</td><td><span class="pill wait">${esc(b.link)}</span></td></tr>`).join("")}</tbody></table></div>` : ""}`,
    books: `<h1 class="title">مكتبة الكتب</h1>${books.length ? `<div class="mine">${books.map(p=>`<div class="mine-item"><img src="${p.img}" alt=""><div><h3>${esc(p.title)}</h3><small class="muted">آخر صفحة: ${ar((S.page[p.id]||0)+1)}</small></div><a class="btn btn-plum btn-sm" href="{{H}}/my-account/">اقرأ</a></div>`).join("")}</div>` : `<div class="card" style="text-align:center"><p class="muted">لم تشترِ كتباً بعد. يمكنك قراءة الفصل الأول مجاناً.</p><div class="ctas" style="justify-content:center;margin-top:12px"><a class="btn btn-line btn-sm" href="{{H}}/my-account/">اقرأ الفصل الأول</a><a class="btn btn-gold btn-sm" href="{{H}}/tools/book-ghosts/">صفحة الكتاب</a></div></div>`}`,
    sessions: `<h1 class="title">جلساتي</h1>${S.bookings.length ? `<div class="scroll-x"><table class="table"><thead><tr><th>الجلسة</th><th>الموعد</th><th>الرابط</th></tr></thead><tbody>${S.bookings.map(b=>`<tr><td>${esc(b.type)}</td><td>${esc(b.when)}</td><td><span class="pill wait">${esc(b.link)}</span></td></tr>`).join("")}</tbody></table></div>` : `<div class="card" style="text-align:center"><p class="muted">لا توجد جلسات محجوزة.</p><a class="btn btn-gold btn-sm" style="margin-top:12px" href="{{H}}/sessions/">احجز جلسة</a></div>`}`,
    _old_subscription: `<h1 class="title">اشتراكي</h1>${S.vip ? `<div class="card form"><div class="alert ok">عضويتك في استيقظ VIP فعّالة (${P[S.vip.plan].title}).</div><p class="muted">التجديد التالي تلقائي. يمكنك الإلغاء في أي وقت ويبقى الوصول حتى نهاية الفترة المدفوعة.</p><div class="ctas"><button class="btn btn-line btn-sm" type="button" id="cancelVip">إلغاء التجديد التلقائي</button><a class="btn btn-ghost btn-sm" href="#payment">تغيير بطاقة الدفع</a></div></div>` : `<div class="card" style="text-align:center"><p class="muted">لست مشتركاً في استيقظ VIP بعد.</p><a class="btn btn-gold btn-sm" style="margin-top:12px" href="{{H}}/vip/">اعرف البرنامج</a></div>`}`,
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
        : `<div class="alert info" style="display:grid;gap:10px;justify-items:center">${icon("lock")}<span>هذا الدرس متاح بعد شراء المادة.</span><div class="ctas" style="justify-content:center"><button class="btn btn-gold btn-sm" type="button" data-add="${p.id}"><span>اشترِ ${esc(p.title)}</span></button><a class="btn btn-line btn-sm" href="{{H}}/vip/">استيقظ VIP</a></div></div>`}
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
    else if (e.target.id === "next"){ if (i < limit-1) i++; else if (!access){ toast("أكمل القراءة بعد شراء الكتاب", ["صفحة الكتاب","{{H}}/tools/book-ghosts/"]); return; } }
    else return;
    S.page[book.id] = i; save(); draw(); window.scrollTo({top:0,behavior:"smooth"});
  });
  draw();
}

/* ---------- booking ---------- */
function initBooking(){
  const root = $("#booking"); if (!root || !$("#bkDays")) return;
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
      startBuy(type, {when});
    }
  });
  drawDays(); drawSlots();
}

/* ---------- login note when coming from a purchase ---------- */
const lf = $("#loginForm") || $("#registerForm");
if (lf && ss("next") === "{{H}}/checkout/"){ const b = buyNow(); const n = document.createElement("div"); n.className = "alert info";
  n.innerHTML = b ? `سجّل دخولك لإتمام شراء <b>${esc(P[b.id].title)}</b> بضغطة واحدة.` : "سجّل دخولك لإتمام الشراء."; lf.prepend(n); }

/* ---------- password eye ---------- */
$$('input[type="password"]').forEach(inp => {
  const w = document.createElement("span"); w.className = "pw-wrap"; inp.parentNode.insertBefore(w, inp); w.appendChild(inp);
  const b = document.createElement("button"); b.type = "button"; b.className = "pw-eye"; b.setAttribute("aria-label", "إظهار كلمة المرور");
  const eye = '<svg class="icon" viewBox="0 0 24 24"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/></svg>';
  const off = '<svg class="icon" viewBox="0 0 24 24"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/><path d="M4 4l16 16"/></svg>';
  b.innerHTML = eye; w.appendChild(b);
  b.addEventListener("click", () => { const show = inp.type === "password"; inp.type = show ? "text" : "password"; b.innerHTML = show ? off : eye; b.setAttribute("aria-label", show ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"); });
});

/* ---------- forms ---------- */
function initForms(){
  document.addEventListener("submit", e => {
    const f = e.target;
    if (f.id === "couponForm"){ e.preventDefault(); const v = $("#coupon").value.trim().toUpperCase(); if (COUPONS[v]){ ss("coupon", v); toast("تم تطبيق خصم " + ar(Math.round(COUPONS[v]*100)) + "٪"); } else { ss("coupon", null); toast("كود الخصم غير صحيح"); } renderCart(); return; }
    if (f.id === "payForm"){ e.preventDefault(); submitPay(f); return; }
    if (f.id === "registerForm"){
      e.preventDefault();
      const email = $("#email", f).value.trim(), name = $("#name", f).value.trim(), msg = $(".alert", f), btn = f.querySelector("[type=submit]");
      if (!name || !/^\S+@\S+\.\S+$/.test(email)){ msg.className = "alert err"; msg.textContent = "اكتب اسمك وبريدك الإلكتروني بشكل صحيح."; msg.hidden = false; return; }
      const gift = $("#gift", f) ? $("#gift", f).checked : false;
      if (btn) btn.disabled = true;
      fetch("api/lead.php", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({name, email, news: gift, source: document.referrer ? new URL(document.referrer).pathname : "", website: (f.querySelector("[name=website]")||{}).value || ""})})
        .then(r => { if (!r.ok) throw 0; })
        .then(() => {
          S.user = {name, email, since:new Date().toISOString()};
          if (gift && !S.owned.includes("serenity-gift")) S.owned.push("serenity-gift");
          save(); const next = ss("next") || "{{H}}/my-account/"; ss("next", null); location.href = next;
        })
        .catch(() => { if (btn) btn.disabled = false; msg.className = "alert err"; msg.textContent = "تعذّر التسجيل الآن. حاول مرة أخرى بعد قليل، أو راسلنا على واتساب."; msg.hidden = false; });
      return;
    }
    if (f.id === "loginForm"){
      e.preventDefault();
      const email = $("#email", f).value.trim(), pass = $("#password", f).value, name = f.id === "registerForm" ? $("#name", f).value.trim() : "";
      const msg = $(".alert", f);
      if (!/^\S+@\S+\.\S+$/.test(email) || pass.length < 6 || (f.id === "registerForm" && !name)){ msg.className = "alert err"; msg.textContent = "تأكد من البريد الإلكتروني، وأن كلمة المرور ٦ أحرف على الأقل" + (f.id === "registerForm" ? "، وأن الاسم مكتوب." : "."); msg.hidden = false; return; }
      S.user = {name: name || (S.user && S.user.email === email ? S.user.name : email.split("@")[0]), email, since:new Date().toISOString()};
      if (f.id === "registerForm" && $("#gift", f) && $("#gift", f).checked && !S.owned.includes("serenity-gift")) S.owned.push("serenity-gift");
      save(); const next = ss("next") || "{{H}}/my-account/"; ss("next", null); location.href = next; return;
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
  const buy = e.target.closest("[data-buy]");
  if (buy){ e.preventDefault(); startBuy(buy.dataset.buy); return; }
  if (e.target.closest("#addInstead")){ const b = buyNow(); if (b && !S.cart.some(c => c.id === b.id)) S.cart.push(b); ss("buynow", null); save(); location.href = "{{H}}/cart/"; return; }
  if (e.target.closest("#toCheckout")){ ss("buynow", null); if (!S.user){ e.preventDefault(); ss("next","{{H}}/checkout/"); location.href = "{{H}}/my-account/"; } return; }
  const add = e.target.closest("[data-add]");
  if (add){ e.preventDefault(); const id = add.dataset.add; if (S.cart.some(c => c.id === id) && !add.classList.contains("add") && P[id].kind !== "session"){ location.href = "{{H}}/cart/"; return; } addToCart(id); return; }
  const fav = e.target.closest("[data-fav]");
  if (fav){ e.preventDefault(); const id = fav.dataset.fav; S.favs = S.favs.includes(id) ? S.favs.filter(x => x !== id) : S.favs.concat(id); save(); fav.setAttribute("aria-pressed", S.favs.includes(id)); toast(S.favs.includes(id) ? "حُفظت في المفضلة" : "أُزيلت من المفضلة"); return; }
  const sw = e.target.closest("[data-swap]");
  if (sw){ const b = D.bundles.find(x => x.id === sw.dataset.swap); S.cart = S.cart.filter(c => !b.items.includes(c.id)); S.cart.push({id:b.id}); save(); paintAll(); toast("تم الاستبدال بالباقة ووفّرت"); return; }
  const rm = e.target.closest("[data-rm]");
  if (rm){ S.cart.splice(+rm.dataset.rm, 1); save(); paintAll(); return; }
  const rg = e.target.closest(".region button");
  if (rg){ S.region = rg.dataset.region; save(); paintAll(); return; }
  const tab = e.target.closest("[data-filter]");
  if (tab){ shelfFilter = tab.dataset.filter; $$("[data-filter]").forEach(t => t.setAttribute("aria-pressed", t === tab)); renderDynamic(); return; }
  const plan = e.target.closest("[data-plan]");
  if (plan){ vipPlan = plan.dataset.plan; $$("[data-plan]").forEach(t => t.setAttribute("aria-pressed", t === plan)); renderVipBar(); return; }
  const nx = e.target.closest("[data-next]");
  if (nx){ ss("next", nx.dataset.next); return; }
  if (e.target.closest("#logout")){ S.user = null; save(); location.href = "{{H}}/"; return; }
  if (e.target.closest("#cancelVip")){ if (S.vip){ S.vip.cancelled = true; save(); renderAccount(); } toast("أُلغي التجديد التلقائي. يبقى وصولك حتى نهاية الفترة."); return; }
  const prev = e.target.closest("[data-preview]");
  if (prev){ location.href = "{{H}}/my-account/#" + prev.dataset.preview; return; }
  if (e.target.closest(".js-demo-login")){ S.user = {name:"مشتركة تجريبية", email:"demo@example.com", since:new Date().toISOString()}; if (!S.owned.length) S.owned = ["ain-sahia","attach","breath"]; save(); location.href = "{{H}}/my-account/"; return; }
});
document.addEventListener("change", e => { if (e.target.id === "sortSel"){ shelfSort = e.target.value; renderDynamic(); } });
document.addEventListener("input", e => { if (e.target.id === "q"){ shelfQuery = e.target.value.trim(); renderDynamic(); } });
window.addEventListener("hashchange", () => { if ($("#accountPage")) renderAccount(); });

/* ---------- mega menu ---------- */
const megaBtn = $("#megaBtn");
if (megaBtn){
  const li = megaBtn.parentElement;
  megaBtn.addEventListener("click", e => { e.stopPropagation(); const o = li.classList.toggle("open"); megaBtn.setAttribute("aria-expanded", o); });
  document.addEventListener("click", e => { if (!li.contains(e.target)){ li.classList.remove("open"); megaBtn.setAttribute("aria-expanded", "false"); } });
  document.addEventListener("keydown", e => { if (e.key === "Escape"){ li.classList.remove("open"); megaBtn.setAttribute("aria-expanded", "false"); } });
}

/* ---------- header on hero: becomes a pill after scrolling ---------- */
const hh = $(".site-header.on-hero");
if (hh){ const onS = () => hh.classList.toggle("scrolled", scrollY > 40); addEventListener("scroll", onS, {passive:true}); onS(); }


/* ---------- gentle "you were about to choose yourself" message ----------
   1) Desktop: leaving the checkout/login page with an unfinished order (mouse heads for the tab bar).
   2) Any device: coming back to the site later with an order left unfinished (within 7 days, once a day). */
const PKEY = "ms_pending_v1";
const pend = (() => { try { return JSON.parse(localStorage.getItem(PKEY) || "null"); } catch(e){ return null; } })();
const pendSave = v => { try { localStorage.setItem(PKEY, JSON.stringify(v)); } catch(e){} };
const here = location.pathname.split("/").pop() || "{{H}}/";
const onPayPage = ["{{H}}/checkout/", "{{H}}/my-account/"].includes(here);
function showChoose(id, onPay){
  const p = P[id]; if (!p || $("#choosePop")) return;
  const el = document.createElement("div");
  el.className = "popup ch-pop"; el.id = "choosePop"; el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true"); el.setAttribute("aria-labelledby", "chT");
  el.innerHTML = `<div class="ch-card"><button class="pop-close" type="button" data-ch-close aria-label="إغلاق">✕</button>
    <div class="ch-stars" aria-hidden="true"><i>✦</i><i>✦</i><i>✦</i></div>
    ${p.cover ? `<img class="ch-img" src="${p.cover}" alt="">` : ""}
    <h2 id="chT">توقّفتِ في منتصف الطريق إلى نفسك</h2>
    <p>كنتِ على بُعد خطوة من شعورٍ أخفّ وأهدأ.<br>هل ما زلتِ ترينه في <b>${esc(p.title)}</b>؟</p>
    <p class="ch-soft">وإن كان التردد هو ما أوقفك، فهذا طبيعي تماماً؛ خذي وقتك.</p>
    <div class="ch-acts"><button class="btn btn-gold" type="button" data-ch-go>${onPay ? "نعم، أكمل طلبي" : "نعم، أكمل من حيث توقفت"}</button>
    <a class="ch-ask" href="{{H}}/contact/">عندي سؤال قبل أن أكمل</a></div>
    <button class="ch-later" type="button" data-ch-close>ليس الآن</button></div>`;
  document.body.appendChild(el);
  const close = () => el.remove();
  el.addEventListener("click", e => {
    if (e.target === el || e.target.closest("[data-ch-close]")) close();
    if (e.target.closest("[data-ch-go]")){ if (onPay) close(); else startBuy(id, pend && pend.extra || undefined); }
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") close(); }, {once: true});
  setTimeout(() => { const b = el.querySelector("[data-ch-go]"); b && b.focus(); }, 50);
}
if (pend && P[pend.id]){
  const stale = Date.now() - pend.t > 7 * 864e5, done = hasAccess(pend.id) && P[pend.id].kind !== "session";
  if (stale || done){ try { localStorage.removeItem(PKEY); } catch(e){} }
  else if (onPayPage && ss("buynow")){
    if (matchMedia("(hover: hover) and (pointer: fine)").matches)
      document.addEventListener("mouseout", e => { if (!e.relatedTarget && e.clientY <= 0 && !ss("exitSeen")){ ss("exitSeen", "1"); showChoose(pend.id, true); } });
  }
  else if (!onPayPage && here !== "{{H}}/my-account/orders/" && Date.now() - (pend.shown || 0) > 864e5 && Date.now() - pend.t > 30 * 6e4){
    ss("popSeen", "1"); // don't stack it with the VIP popup
    setTimeout(() => { pend.shown = Date.now(); pendSave(pend); showChoose(pend.id, false); }, 1500);
  }
}
/* ---------- VIP popup (home, once per visit) ---------- */
const pop = $("#vipPop");
if (pop && !ss("popSeen")){
  setTimeout(() => { pop.hidden = false; ss("popSeen", "1"); }, 1800);
  const close = () => pop.hidden = true;
  $("#popClose").addEventListener("click", close);
  pop.addEventListener("click", e => { if (e.target === pop) close(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") close(); });
}

/* ---------- floating help ---------- */
const helpBtn = $("#helpBtn"), helpPanel = $("#helpPanel");
if (helpBtn){
  helpBtn.addEventListener("click", e => { e.stopPropagation(); helpPanel.hidden = !helpPanel.hidden; helpBtn.setAttribute("aria-expanded", !helpPanel.hidden); });
  document.addEventListener("click", e => { if (!$("#help").contains(e.target)){ helpPanel.hidden = true; helpBtn.setAttribute("aria-expanded","false"); } });
}

/* ---------- search ---------- */
const sOv = $("#searchOv"), sq = $("#sq"), sRes = $("#searchRes");
function searchDraw(){
  const q = (sq.value || "").trim();
  const list = D.products.filter(p => p.page && !["gift","session","offer"].includes(p.kind) && p.id !== "vip-y" && (!q || (p.title + " " + (p.catLabel||"") + " " + (p.short||"")).includes(q)));
  sRes.innerHTML = list.length ? list.map(p => `<a href="${p.page}"><img src="${p.img}" alt=""><span><b>${esc(p.title)}</b><br><small>${esc(p.catLabel||"")}</small></span><small>${p.eg ? money(p.eg,p.us) : ""}</small></a>`).join("") : `<p class="empty">لا توجد نتائج. جرّب كلمة أخرى.</p>`;
}
if (sOv){
  $("#searchBtn").addEventListener("click", () => { sOv.hidden = false; searchDraw(); setTimeout(() => sq.focus(), 50); });
  $("#searchClose").addEventListener("click", () => sOv.hidden = true);
  sOv.addEventListener("click", e => { if (e.target === sOv) sOv.hidden = true; });
  sq.addEventListener("input", searchDraw);
  document.addEventListener("keydown", e => { if (e.key === "Escape") sOv.hidden = true; });
}

/* ---------- menu ---------- */
const burger = $("#burger"), menu = $("#menu");
if (burger) burger.addEventListener("click", () => { const o = menu.classList.toggle("open"); burger.setAttribute("aria-expanded", o); });

/* ---------- success page ---------- */
const sx = $("#successBox");
if (sx){ let o = null; try { o = JSON.parse(ss("lastOrder") || "null"); } catch(e){}
  const up = $("#successUpsell"); if (up && S.vip) up.hidden = true;
  if (o){ $("#oNo").textContent = o.no; $("#oTotal").textContent = o.total; $("#oEmail").textContent = o.email; $("#oItems").innerHTML = o.items.map(i => `<li>${esc(i)}</li>`).join(""); } }

/* ---------- gold dust ---------- */
$$("canvas.sparkle").forEach(c => {
  const x = c.getContext("2d"), reduce = matchMedia("(prefers-reduced-motion: reduce)").matches; let w, h, dots = [];
  function size(){ const r = c.getBoundingClientRect(), d = Math.min(devicePixelRatio||1, 2); w = r.width; h = r.height; c.width = w*d; c.height = h*d; x.setTransform(d,0,0,d,0,0);
    dots = Array.from({length: Math.round(w*h/(+c.dataset.density || 9000))}, () => ({x:Math.random()*w, y:Math.random()*h, r:Math.random()*1.6+.4, p:Math.random()*6.28, s:Math.random()*.25+.05})); }
  function draw(t){ x.clearRect(0,0,w,h);
    for (const d of dots){ const a = .35 + .65*Math.abs(Math.sin(d.p + t/1400));
      if (!reduce){ d.y -= d.s; if (d.y < -4){ d.y = h + 4; d.x = Math.random()*w; } }
      x.beginPath(); x.fillStyle = `rgba(214,170,70,${a*.85})`; x.arc(d.x, d.y, d.r, 0, 6.28); x.fill();
      if (d.r > 1.6){ x.strokeStyle = `rgba(230,190,90,${a*.5})`; x.lineWidth = .6; x.beginPath(); x.moveTo(d.x-d.r*3,d.y); x.lineTo(d.x+d.r*3,d.y); x.moveTo(d.x,d.y-d.r*3); x.lineTo(d.x,d.y+d.r*3); x.stroke(); } }
    if (!reduce) requestAnimationFrame(draw); }
  size(); addEventListener("resize", size); requestAnimationFrame(draw);
});


/* ---------- voice reviews: recorded on the site, saved on the server, shown after Mervat approves ---------- */
const VAPI = (window.MS_WP ? MS_WP.home + "/" : "") + "api/voice.php";
const wave = seed => { let h = ""; for (let i = 0; i < 34; i++){ const v = 22 + Math.round(70 * Math.abs(Math.sin(seed * 7.3 + i * 1.7) * Math.cos(i * .53 + seed))); h += `<i style="height:${v}%"></i>`; } return h; };
const fmtT = s => { s = Math.max(0, Math.round(s)); return (Math.floor(s/60) + ":" + String(s%60).padStart(2,"0")).replace(/\d/g, d => "٠١٢٣٤٥٦٧٨٩"[d]); };
const vSrc = id => `${VAPI}?action=audio&id=${encodeURIComponent(id)}`;
const vWhen = d => { const days = Math.floor((Date.now() - new Date(d)) / 864e5); return days < 1 ? "اليوم" : days < 2 ? "أمس" : days < 30 ? "منذ " + ar(days) + " أيام" : new Date(d).toLocaleDateString("ar-EG", {month:"long", year:"numeric"}); };
let vCache = null;
function vFetch(){
  if (!vCache) vCache = fetch(VAPI + "?action=list", {cache:"no-store"}).then(r => r.ok ? r.json() : {voices: []}).then(j => j.voices || []).catch(() => []);
  return vCache;
}
function voiceCard(v, n){
  return `<article class="vr-card">
    <button class="vr-play" type="button" data-vrplay aria-label="تشغيل تجربة ${esc(v.name)}">${icon("play")}</button>
    <div class="vr-main"><div class="vr-wave">${wave(n + 3)}</div>
      <div class="vr-meta"><b>${esc(v.name)}</b><span>${vWhen(v.date)}${v.len ? " · " + fmtT(v.len) : ""}</span></div></div>
    <audio preload="none" src="${vSrc(v.id)}"></audio>
  </article>`;
}
window.renderVoices = (...a) => renderVoices(...a);
async function renderVoices(){
  const all = await vFetch();
  $$("[data-vr]").forEach(el => {
    const id = el.dataset.vr;
    if (id === "page"){
      const n2 = k => String(k).padStart(2,"0").replace(/\d/g, d => "٠١٢٣٤٥٦٧٨٩"[d]);
      el.innerHTML = all.length ? all.map((v, i) => `<article class="vr-pill"><button class="vr-play" type="button" data-vrplay aria-label="تشغيل رأي ${esc(v.name)}">${icon("play")}</button>
        <div class="vr-pill-t"><b>${esc(v.name)}</b><small>${P[v.pid] ? esc(P[v.pid].title) + " · " : ""}${vWhen(v.date)}${v.len ? " · " + fmtT(v.len) : ""}</small></div>
        <span class="vr-listen">استمع <i class="vr-mini"><i></i><i></i><i></i><i></i><i></i></i></span><audio preload="none" src="${vSrc(v.id)}"></audio></article>`).join("")
        : `<p class="vr-empty">تُنشر الآراء الصوتية هنا قريباً بعد مراجعتها.</p>`;
      return;
    }
    if (id === "all"){
      const n2 = k => String(k).padStart(2,"0").replace(/\d/g, d => "٠١٢٣٤٥٦٧٨٩"[d]);
      const items = all.slice(0, 6);
      el.innerHTML = items.map((v, i) => `<article class="vr-pill"><button class="vr-play" type="button" data-vrplay aria-label="تشغيل رأي عملائنا ${n2(i+1)}">${icon("play")}</button>
        <div class="vr-pill-t"><b>رأي عملائنا ${n2(i+1)}</b><small>${esc(v.name)}${P[v.pid] ? " · " + esc(P[v.pid].title) : ""}</small></div>
        <span class="vr-listen">استمع <i class="vr-mini"><i></i><i></i><i></i><i></i><i></i></i></span><audio preload="none" src="${vSrc(v.id)}"></audio></article>`).join("");
      const wrap = el.closest("[data-vr-wrap]"); if (wrap) wrap.hidden = !items.length;
      return;
    }
    el.innerHTML = all.filter(v => v.pid === id).map(voiceCard).join("");
  });
  $$("[data-vrrec]").forEach(el => {
    if (el.dataset.state && el.dataset.state !== "idle") return;
    el.innerHTML = `<button class="vr-start" type="button" data-vrstart="${el.dataset.vrrec}">${icon("chat")}<span>سجّلي تجربتك بصوتك</span></button><small>حتى دقيقتين · تُنشر بعد مراجعة د. مرفت</small>`;
  });
}
async function vStart(el, id){
  if (!navigator.mediaDevices || !window.MediaRecorder){ toast("التسجيل الصوتي غير مدعوم في هذا المتصفح. جرّبي متصفحاً آخر مثل Chrome أو Safari."); return; }
  let stream;
  try { stream = await navigator.mediaDevices.getUserMedia({audio:true}); }
  catch(e){ toast("لم يُسمح باستخدام الميكروفون. اسمحي للموقع باستخدامه من إعدادات المتصفح ثم أعيدي المحاولة."); return; }
  const chunks = [], mr = new MediaRecorder(stream), t0 = Date.now();
  el.dataset.state = "rec";
  el.innerHTML = `<div class="vr-live"><span class="vr-dot"></span><b class="vr-time">٠:٠٠</b><span>جارٍ التسجيل…</span><button class="vr-stop" type="button">إيقاف</button></div>`;
  const tick = setInterval(() => { const s = (Date.now()-t0)/1000; const t = el.querySelector(".vr-time"); if (t) t.textContent = fmtT(s); if (s >= 120 && mr.state === "recording") mr.stop(); }, 250);
  mr.ondataavailable = e => e.data.size && chunks.push(e.data);
  mr.onstop = () => {
    clearInterval(tick); stream.getTracks().forEach(t => t.stop());
    const blob = new Blob(chunks, {type: mr.mimeType || "audio/webm"}), len = Math.min(120, (Date.now()-t0)/1000);
    if (len < 2){ el.dataset.state = "idle"; renderVoices(); toast("التسجيل قصير جداً، جرّبي مرة أخرى."); return; }
    const url = URL.createObjectURL(blob);
    el.dataset.state = "review";
    const first = S.user && S.user.name ? S.user.name.trim().split(/\s+/)[0] : "";
    el.innerHTML = `<div class="vr-review"><audio controls src="${url}"></audio>
      <div class="vr-opts"><label><input type="radio" name="vrn" value="first" checked><span>اسمي الأول</span></label><input class="vr-first" type="text" maxlength="30" placeholder="اسمك الأول" aria-label="اسمك الأول" value="${esc(first)}">
      <label><input type="radio" name="vrn" value="city"><span>عميلة من</span></label><input class="vr-city" type="text" maxlength="30" placeholder="المدينة أو البلد" aria-label="المدينة أو البلد"></div>
      <input class="vr-hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
      <label class="check"><input type="checkbox" class="vr-ok"><span>أوافق على نشر تسجيلي الصوتي في الموقع بعد مراجعته</span></label>
      <div class="vr-actions"><button class="btn-safia vr-pub" type="button">أرسلي تجربتي</button><button class="vp-btn vr-redo" type="button">إعادة التسجيل</button></div></div>`;
    el.querySelector(".vr-redo").onclick = () => { URL.revokeObjectURL(url); el.dataset.state = "idle"; renderVoices(); };
    const pub = el.querySelector(".vr-pub");
    pub.onclick = async () => {
      if (!el.querySelector(".vr-ok").checked){ toast("ضعي علامة الموافقة على النشر أولاً."); return; }
      const byCity = el.querySelector("input[name=vrn]:checked").value === "city";
      const city = el.querySelector(".vr-city").value.trim(), firstName = el.querySelector(".vr-first").value.trim();
      const name = byCity ? "عميلة من " + (city || "مصر") : (firstName || "عميلة");
      const fd = new FormData();
      fd.append("pid", id); fd.append("name", name); fd.append("len", len.toFixed(1)); fd.append("consent", "1");
      fd.append("website", el.querySelector(".vr-hp").value);
      fd.append("audio", blob, "voice");
      pub.disabled = true; pub.textContent = "جارٍ الإرسال…";
      try {
        const r = await fetch(VAPI + "?action=submit", {method: "POST", body: fd}), j = await r.json().catch(() => ({}));
        if (r.ok && j.ok){ URL.revokeObjectURL(url); el.dataset.state = "idle"; el.innerHTML = `<div class="vr-thanks">${icon("check")}<span>وصلت تجربتك، شكراً لك. ستظهر هنا بعد مراجعة د. مرفت.</span></div>`; return; }
        toast(j.error === "limit" ? "أرسلتِ عدة تسجيلات خلال وقت قصير. جرّبي بعد ساعة." : j.error === "size" || j.error === "length" ? "التسجيل أطول من المسموح، سجّلي حتى دقيقتين." : "لم يُرسل التسجيل. حاولي مرة أخرى.");
      } catch(e){ toast("تعذّر الإرسال. تأكدي من الاتصال بالإنترنت وحاولي مرة أخرى."); }
      pub.disabled = false; pub.textContent = "أرسلي تجربتي";
    };
  };
  el.querySelector(".vr-stop").onclick = () => { if (mr.state === "recording") mr.stop(); };
  mr.start();
}
document.addEventListener("click", e => {
  const st = e.target.closest("[data-vrstart]"); if (st){ vStart(st.closest("[data-vrrec]"), st.dataset.vrstart); return; }
  const pl = e.target.closest("[data-vrplay]");
  if (pl){ const card = pl.closest(".vr-card,.vr-pill"), a = card.querySelector("audio"); $$(".vr-card audio,.vr-pill audio").forEach(x => { if (x !== a){ x.pause(); x.closest(".vr-card,.vr-pill").classList.remove("on"); } });
    if (a.paused){ a.play().catch(() => toast("تعذّر تشغيل التسجيل.")); card.classList.add("on"); a.onended = () => card.classList.remove("on"); } else { a.pause(); card.classList.remove("on"); } }
});
renderVoices();

/* ---------- session cards with month calendars ---------- */
function initSessCards(){
  const cards = $$("[data-sess]"); if (!cards.length) return;
  const months = ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"];
  const today = new Date(); today.setHours(0,0,0,0);
  const OPEN = [0, 1, 2, 3, 4, 5, 6]; // every day is open
  cards.forEach(card => {
    const st = {y: today.getFullYear(), m: today.getMonth(), day: null, slot: null};
    const daysEl = card.querySelector(".ss-days"), slotsEl = card.querySelector(".ss-slots"), title = card.querySelector(".ss-month");
    function draw(){
      title.textContent = months[st.m] + " " + ar(st.y);
      const first = new Date(st.y, st.m, 1), lead = (first.getDay() + 1) % 7, n = new Date(st.y, st.m + 1, 0).getDate();
      let h = "";
      for (let k = 0; k < lead; k++) h += "<span></span>";
      for (let d = 1; d <= n; d++){
        const dt = new Date(st.y, st.m, d), key = `${st.y}-${st.m+1}-${d}`;
        const ok = dt > today && OPEN.includes(dt.getDay());
        h += `<button type="button" class="ss-d${ok ? " ok" : ""}" ${ok ? "" : "disabled"} data-k="${key}" aria-pressed="${st.day===key}">${ar(d)}</button>`;
      }
      daysEl.innerHTML = h;
      if (!st.day){ slotsEl.innerHTML = ""; return; }
      const seed = Number(st.day.split("-")[2]);
      slotsEl.innerHTML = `<small>الأوقات المتاحة (بتوقيت القاهرة)</small>` + D.slots.map((s,k) => `<button type="button" class="ss-s" data-s="${s}" ${(seed+k)%4===0?"disabled":""} aria-pressed="${st.slot===s}">${s}</button>`).join("");
    }
    card.addEventListener("click", e => {
      const b = e.target.closest("button"); if (!b || b.disabled) return;
      if (b.classList.contains("ss-nav")){ const dir = +b.dataset.dir; const t = new Date(st.y, st.m + dir, 1);
        if (t < new Date(today.getFullYear(), today.getMonth(), 1) || t > new Date(today.getFullYear(), today.getMonth() + 3, 1)) return;
        st.y = t.getFullYear(); st.m = t.getMonth(); draw(); }
      else if (b.classList.contains("ss-d")){ st.day = b.dataset.k; st.slot = null; draw(); }
      else if (b.classList.contains("ss-s")){ st.slot = b.dataset.s; draw(); }
      else if (b.classList.contains("ss-go")){
        if (!st.day){ toast("اختاري يوماً من التقويم أولاً"); return; }
        if (!st.slot){ toast("اختاري وقت الجلسة"); return; }
        const [y, m, d] = st.day.split("-").map(Number), dt = new Date(y, m - 1, d);
        const names = ["الأحد","الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت"];
        startBuy(card.dataset.sess, {when: `${names[dt.getDay()]} ${ar(d)} ${months[m-1]} · ${st.slot} (بتوقيت القاهرة)`});
      }
    });
    draw();
  });
}
initSessCards();

/* ---------- marriage counseling: choose the plan for the booking calendar ---------- */
(function(){
  const card = $(".mz-book"); if (!card) return;
  const pick = id => {
    if (!P[id]) return;
    card.dataset.sess = id;
    card.querySelector(".mz-bt").textContent = P[id].title;
    const pr = card.querySelector(".mz-bp [data-price]"); if (pr) pr.dataset.price = id;
    card.querySelectorAll(".mz-bp [data-wasof]").forEach(e => e.dataset.wasof = id);
    paintPrices();
    $$(".mz-chip").forEach(c => c.setAttribute("aria-pressed", String(c.dataset.mplan === id)));
  };
  document.addEventListener("click", e => {
    const c = e.target.closest("[data-mplan]"); if (c){ pick(c.dataset.mplan); return; }
    const a = e.target.closest("[data-mpick]"); if (a) pick(a.dataset.mpick);
  });
})();

/* ---------- Nour assistant (prototype: scripted answers) ---------- */
(function(){
  const log = $("#nourLog"), chips = $("#nourChips"), form = $("#nourForm"), q = $("#nourQ"), x = $("#nourX");
  if (!log) return;
  const L = (href, t) => `<a href="${href}">${t}</a>`;
  const pr = id => P[id] ? money(P[id].eg, P[id].us) : "";
  const A = {
    attach: () => `يبدو أن قلبك متعلّق بشيء يُثقله. أرشّح لك ${L("{{H}}/tools/exercise-detachment/","تمرين فك التعلّق")}: تأمل موجّه ١٠ دقائق، مستواه مبتدئ، بسعر ${pr("attach")}. وإن أردتِ نظاماً يومياً كاملاً ${L("{{H}}/bundles/","باقة فك التعلّق")}.`,
    peace: () => `للسلام الداخلي أرشّح لك ${L("{{H}}/tools/serenity-cleansing-meditation/","تأمل السكينة والتنظيف")} (${pr("serenity")})، و${L("{{H}}/tools/peace-affirmations/","توكيدات السلام للتشافي العميق")} (${pr("peace-affirmations")}) للاستماع اليومي.`,
    reject: () => `جرح الرفض يحتاج عملاً أعمق. أرشّح لك ${L("{{H}}/tools/decoding-light-of-acceptance/","Decoding نور القبول")}: تمرين لإعادة برمجة العقل اللاواعي يساعدك على قبول ذاتك أولاً (${pr("decode-acceptance")}).`,
    child: () => `للطفولة وجروحها أرشّح لك ${L("{{H}}/tools/inner-child-healing/","تمرين تشافي الطفل الداخلي")}: تمرين عميق ١٠ دقائق، مستواه متوسط (${pr("inner-child")}).`,
    lazy: () => `إن كنتِ تشعرين بالكسل والتأجيل والتجمّد أمام أهدافك، أرشّح لك ${L("{{H}}/tools/decoding-energy-stagnation/","Decoding الركود والخمول")} (${pr("decode-stagnation")}).`,
    diff: () => `باختصار: <b>التأملات</b> للتهدئة والتحرّر، و<b>Decoding</b> تمارين لإعادة برمجة العقل اللاواعي (متقدمة)، و<b>التوكيدات و Priming</b> للبرمجة اليومية. وإن لم تعرفي من أين تبدئين، ${L("{{H}}/sessions/#booking","جلسة التعارف")} هي الأنسب.`,
    vip: () => `${L("{{H}}/vip/","استيقظ VIP")} هو البرنامج الكامل: جلسات فردية خاصة مع د. مرفت عبر Zoom، وتمرينات مخصصة لكِ، وخطة يومية ومتابعة شخصية. يبدأ من ${pr("vip-m")} شهرياً.`,
    book: () => `يمكنك الحجز من ${L("{{H}}/sessions/#booking","صفحة الجلسات")}: جلسة تعارف ٣٠ دقيقة (${pr("s-intro")})، أو استشارة فردية (${pr("s-single")})، أو كوتشينج (${pr("s-coach")}).`,
    pay: () => `داخل مصر: البطاقات البنكية والمحافظ الإلكترونية. وخارج مصر: PayPal. تُفتح الأداة في حسابك فوراً بعد الدفع، والوصول ٣٦٥ يوماً.`,
    human: () => `بكل سرور، تواصلي مع فريق د. مرفت على ${L("https://wa.me/201095292748","واتساب")} أو من ${L("{{H}}/contact/","صفحة التواصل")}.`,
    crisis: () => `أنا آسفة لأنك تمرّين بهذا، ومشاعرك مهمة. لست بديلاً عن المساعدة المتخصصة، فأرجو أن تتواصلي الآن مع شخص تثقين به أو مع خط دعم نفسي. في مصر: الخط الساخن للأمانة العامة للصحة النفسية <b>08008880700</b>، وفي الطوارئ <b>123</b>. إن كنتِ خارج مصر، اتصلي برقم الطوارئ في بلدك.`,
    fallback: () => `لم أفهم سؤالك تماماً. اختاري من الأزرار بالأسفل، أو اكتبي ما تشعرين به بكلمات بسيطة، أو ${L("https://wa.me/201095292748","تواصلي مع الفريق على واتساب")}.`
  };
  const RULES = [
    ["crisis", /انتحار|أنتحر|انهي حياتي|أنهي حياتي|أؤذي نفسي|اذي نفسي|أموت نفسي|مش عايزة أعيش|لا أريد أن أعيش/],
    ["attach", /تعل|فراق|انسى|أنسى|بنساه|ترك|انفصال|حب/],
    ["reject", /رفض|هجر|قبول|محدش بيحب|لا أحد يحب/],
    ["child", /طفول|الطفل|أهلي|ابويا|أبي|أمي|صدمة/],
    ["lazy", /كسل|خمول|تأجيل|اجل|موبايل|سكرول|هدف|اهدافي|أهدافي|ركود/],
    ["peace", /سلام|هدوء|قلق|توتر|سكين|نوم|مشاعر سلبية|طاقة سلبية/],
    ["vip", /vip|استيقظ|برنامج|اشتراك/i],
    ["book", /جلس|حجز|احجز|استشار|كوتش|تعارف|موعد/],
    ["pay", /دفع|سعر|بكام|كام|فلوس|فيزا|باي ?بال|محفظ|فوري/],
    ["diff", /فرق|ابدأ|أبدأ|منين|من أين|ايه المناسب|ما المناسب/],
    ["human", /حد|شخص|فريق|واتس|تواصل|مرفت/]
  ];
  const CHIPS = [["جرح في العلاقات والتعلّق","attach"],["أبحث عن سلام داخلي","peace"],["أشعر بالرفض","reject"],["الكسل والتأجيل","lazy"],["من أين أبدأ؟","diff"],["ما هو استيقظ VIP؟","vip"],["أريد حجز جلسة","book"],["طرق الدفع","pay"]];
  const add = (who, html) => { const d = document.createElement("div"); d.className = "nour-m " + who; d.innerHTML = html; log.appendChild(d); log.scrollTop = log.scrollHeight; };
  const reply = key => { const t = document.createElement("div"); t.className = "nour-m bot typing"; t.innerHTML = "<i></i><i></i><i></i>"; log.appendChild(t); log.scrollTop = log.scrollHeight;
    setTimeout(() => { t.remove(); add("bot", A[key]()); }, 650); };
  const ask = text => { add("me", esc(text)); const r = RULES.find(([, re]) => re.test(text)); reply(r ? r[0] : "fallback"); };
  let started = false;
  const start = () => { if (started) return; started = true;
    add("bot", `أهلاً بك 🤍<br>أنا <b>نور</b>، مساعدتك الخاصة في موقع د. مرفت سرور.<br>ما الذي يشغل قلبك اليوم؟ اختاري من الأسفل أو اكتبي لي.`);
    chips.innerHTML = CHIPS.map(([t,k]) => `<button type="button" data-k="${k}">${t}</button>`).join(""); };
  $("#helpBtn").addEventListener("click", () => setTimeout(() => { if (!$("#helpPanel").hidden){ start(); q.focus({preventScroll:true}); } }, 0));
  chips.addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; add("me", esc(b.textContent)); reply(b.dataset.k); });
  form.addEventListener("submit", e => { e.preventDefault(); const t = q.value.trim(); if (!t) return; q.value = ""; ask(t); });
  x.addEventListener("click", e => { e.stopPropagation(); $("#helpPanel").hidden = true; $("#helpBtn").setAttribute("aria-expanded","false"); });
})();
(function(){ const b = $("#helpCBtn"), pnl = $("#helpCPanel"); if (!b) return;
  b.addEventListener("click", e => { e.stopPropagation(); pnl.hidden = !pnl.hidden; b.setAttribute("aria-expanded", !pnl.hidden); });
  document.addEventListener("click", e => { if (!$("#helpC").contains(e.target)){ pnl.hidden = true; b.setAttribute("aria-expanded","false"); } });
})();

/* ---------- testimonial slider: arrows, dots, autoplay ---------- */
window.msReel = reel => {
  if (reel.dataset.ready) return; reel.dataset.ready = 1;
  // long reviews are cut to a few lines (so one long review doesn't stretch every card) with «اقرئي المزيد»
  requestAnimationFrame(() => reel.querySelectorAll(".voice > p").forEach(p => {
    if (p.scrollHeight <= p.clientHeight + 4 || p.nextElementSibling?.classList.contains("vo-more")) return;
    const m = document.createElement("button"); m.type = "button"; m.className = "vo-more"; m.textContent = "اقرئي المزيد";
    m.addEventListener("click", () => { const open = p.classList.toggle("open"); m.textContent = open ? "إخفاء" : "اقرئي المزيد"; });
    p.after(m);
  }));
  const cards = [...reel.children]; if (cards.length < 2) return;
  const wrap = document.createElement("div"); wrap.className = "slider";
  reel.parentNode.insertBefore(wrap, reel); wrap.appendChild(reel);
  const prev = document.createElement("button"), next = document.createElement("button"), dots = document.createElement("div");
  prev.type = next.type = "button"; prev.className = "sl-arrow sl-prev"; next.className = "sl-arrow sl-next";
  prev.setAttribute("aria-label", "الرأي السابق"); next.setAttribute("aria-label", "الرأي التالي");
  prev.innerHTML = "›"; next.innerHTML = "‹"; dots.className = "sl-dots";
  wrap.append(prev, next, dots);
  dots.innerHTML = cards.map((_, i) => `<button type="button" aria-label="الرأي ${ar(i+1)}"></button>`).join("");
  const step = () => (cards[1].getBoundingClientRect().left - cards[0].getBoundingClientRect().left) || cards[0].offsetWidth;
  const current = () => { const r = reel.getBoundingClientRect(); let best = 0, bd = 1e9;
    cards.forEach((c, i) => { const cr = c.getBoundingClientRect(), d = Math.abs((cr.left + cr.width/2) - (r.left + r.width/2)); if (d < bd){ bd = d; best = i; } }); return best; };
  const go = i => { i = (i + cards.length) % cards.length; const c = cards[i], r = reel.getBoundingClientRect(), cr = c.getBoundingClientRect();
    reel.scrollBy({left: (cr.left + cr.width/2) - (r.left + r.width/2), behavior: "smooth"}); };
  const paint = () => { const k = current(); [...dots.children].forEach((d, i) => d.setAttribute("aria-current", i === k)); cards.forEach((c, i) => c.classList.toggle("hl", i === k)); };
  // RTL: "next" moves visually to the left
  next.onclick = () => { go(current() + 1); restart(); };
  prev.onclick = () => { go(current() - 1); restart(); };
  dots.onclick = e => { const b = e.target.closest("button"); if (!b) return; go([...dots.children].indexOf(b)); restart(); };
  reel.addEventListener("scroll", () => requestAnimationFrame(paint), {passive: true});
  let t = null, paused = false;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const restart = () => { clearInterval(t); if (!reduce) t = setInterval(() => { if (!paused && !document.hidden) go(current() + 1); }, 5000); };
  wrap.addEventListener("mouseenter", () => paused = true); wrap.addEventListener("mouseleave", () => paused = false);
  reel.addEventListener("touchstart", () => { paused = true; }, {passive: true}); reel.addEventListener("touchend", () => { setTimeout(() => paused = false, 4000); }, {passive: true});
  paint(); restart();
};
// a reel that waits for approved reviews (home page) is started by the reviews code
$$(".reel:not([data-rv-reel])").forEach(window.msReel);

/* ---------- star ratings (prototype: kept in this browser) ---------- */
const RKEY = "ms_ratings_v1", RMIN = 3;
const rLoad = () => { try { return JSON.parse(localStorage.getItem(RKEY) || "{}"); } catch(e){ return {}; } };
const rSave = v => { try { localStorage.setItem(RKEY, JSON.stringify(v)); } catch(e){} };
const starRow = (val, cls) => `<span class="rt-stars ${cls||""}" aria-hidden="true">${[1,2,3,4,5].map(i => `<i class="${val >= i ? "f" : val >= i - .5 ? "h" : ""}">★</i>`).join("")}</span>`;
function rStats(id){ const r = rLoad()[id] || {}, list = (r.others || []).concat(r.mine ? [r.mine] : []);
  return {n: list.length, avg: list.length ? list.reduce((a,b) => a+b, 0) / list.length : 0, mine: r.mine || 0}; }
const fmt1 = v => v.toFixed(1).replace(".", "٫").replace(/\d/g, d => "٠١٢٣٤٥٦٧٨٩"[d]);
function paintRatings(){
  $$("[data-rate-sum]").forEach(el => { const st = rStats(el.dataset.rateSum);
    el.innerHTML = st.n >= RMIN ? `${starRow(st.avg)}<b>${fmt1(st.avg)}</b><span>(${ar(st.n)} ${st.n > 10 ? "تقييماً" : "تقييمات"})</span>` : "";
    el.hidden = st.n < RMIN; });
  $$("[data-rate-box]").forEach(el => { const id = el.dataset.rateBox, st = rStats(id);
    if (!hasAccess(id)){ el.innerHTML = ""; el.hidden = true; return; }
    el.hidden = false;
    el.innerHTML = `<h2>قيّمي ${P[id] && P[id].kind === "course" ? "الكورس" : "التمرين"}</h2>
      <div class="rt-pick" role="radiogroup" aria-label="تقييمك من ٥">${[1,2,3,4,5].map(i => `<button type="button" role="radio" aria-checked="${st.mine === i}" aria-label="${ar(i)} من ٥" data-rate="${id}|${i}" class="${st.mine >= i ? "f" : ""}">★</button>`).join("")}</div>
      <small>${st.mine ? "شكراً لتقييمك، ويمكنك تغييره في أي وقت." : "اختاري عدد النجوم. يظهر متوسط التقييم بجانب الاسم بعد " + ar(RMIN) + " تقييمات."}</small>`; });
}
document.addEventListener("click", e => { const b = e.target.closest("[data-rate]"); if (!b) return;
  const [id, n] = b.dataset.rate.split("|"), all = rLoad(); all[id] = all[id] || {}; all[id].mine = +n; rSave(all); paintRatings(); toast("سُجّل تقييمك: " + ar(n) + " من ٥"); });
document.addEventListener("mouseover", e => { const b = e.target.closest("[data-rate]"); if (!b) return; const k = +b.dataset.rate.split("|")[1];
  [...b.parentNode.children].forEach((x, i) => x.classList.toggle("hv", i < k)); });
document.addEventListener("mouseout", e => { const b = e.target.closest("[data-rate]"); if (b) [...b.parentNode.children].forEach(x => x.classList.remove("hv")); });
paintRatings();
new MutationObserver(() => { if ($$("[data-rate-sum]:empty").some(x => !x.hidden && rStats(x.dataset.rateSum).n >= RMIN)) paintRatings(); }).observe(document.body, {childList:true, subtree:true});
initForms(); initPlayer(); initReader(); initBooking();
paintAll();
curMini();
let cmRaf = 0;
new MutationObserver(() => { if (!cmRaf) cmRaf = requestAnimationFrame(() => { cmRaf = 0; curMini(); }); }).observe(document.body, {childList:true, subtree:true});
document.addEventListener("click", e => {
  const b = e.target.closest(".cur-mini"); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  S.region = S.region === "eg" ? "intl" : "eg"; save(); paintAll(); curMini();
}, true);
})();

/* ---------- gift: «أسئلة كشف الهوية» (steps, autosave, send) ---------- */
(function(){
  const app = document.querySelector("[data-gift-app]"); if (!app) return;
  const K = "ms_gift_v1", steps = [...app.querySelectorAll(".gf-step")], last = steps.length - 1;
  let st = {}; try { st = JSON.parse(localStorage.getItem(K) || "{}"); } catch(e) {}
  st.answers = st.answers || {};
  const save = () => { try { localStorage.setItem(K, JSON.stringify(st)); } catch(e) {} };
  const nameEl = app.querySelector("#gName"), mailEl = app.querySelector("#gEmail"), ok = app.querySelector("#gConsent"), news = app.querySelector("#gNews"), msg = app.querySelector(".alert");
  if (st.name) nameEl.value = st.name; if (st.email) mailEl.value = st.email; if (st.consent) ok.checked = true;
  app.querySelectorAll("textarea[data-q]").forEach(t => { t.value = st.answers[t.dataset.q] || ""; t.addEventListener("input", () => { st.answers[t.dataset.q] = t.value; save(); }); });
  function show(i, scroll){
    steps.forEach((s, k) => s.hidden = k !== i); st.step = i; save();
    if (scroll !== false) app.closest("section").scrollIntoView({behavior: "smooth", block: "start"});
  }
  const err = t => { msg.className = "alert err"; msg.textContent = t; msg.hidden = false; };
  app.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    const cur = steps.findIndex(s => !s.hidden);
    if (b.hasAttribute("data-gf-start")){
      const n = nameEl.value.trim(), m = mailEl.value.trim();
      if (!n){ err("اكتب اسمك."); return; }
      if (!/^\S+@\S+\.\S+$/.test(m)){ err("اكتب بريدك الإلكتروني بشكل صحيح، فعليه يصلك التحليل."); return; }
      if (!ok.checked){ err("يرجى الموافقة على اطلاع د. مرفت على إجاباتك لإعداد التحليل."); return; }
      msg.hidden = true; st.name = n; st.email = m; st.consent = true; st.news = news.checked; show(1); return;
    }
    if (b.hasAttribute("data-gf-next")) { show(Math.min(cur + 1, last - 1)); return; }
    if (b.hasAttribute("data-gf-back")) { show(Math.max(cur - 1, 0)); return; }
    if (b.hasAttribute("data-gf-send")){
      const filled = Object.values(st.answers).filter(v => (v || "").trim()).length;
      if (!filled){ toast("اكتب إجابة سؤال واحد على الأقل، فعلى إجاباتك يُبنى تحليلك."); return; }
      if (filled < 6 && !confirm("أجبت عن " + String(filled).replace(/\d/g, d => "٠١٢٣٤٥٦٧٨٩"[d]) + " أسئلة فقط. كلما أجبت أكثر كان تحليلك أدق. هل تريد الإرسال الآن؟")) return;
      b.disabled = true; const old = b.innerHTML; b.textContent = "جارٍ الإرسال…";
      fetch("/api/gift.php", {method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name: st.name, email: st.email, consent: 1, news: st.news ? 1 : 0, answers: st.answers, website: (app.querySelector("[name=website]") || {}).value || ""})})
        .then(r => { if (!r.ok) throw 0; return r.json(); })
        .then(() => { try { localStorage.removeItem(K); } catch(e) {} st = {answers: {}}; show(last); })
        .catch(() => { b.disabled = false; b.innerHTML = old; toast("تعذّر الإرسال الآن. إجاباتك محفوظة، حاول بعد قليل أو راسلنا على واتساب."); });
    }
  });
  if (st.step && st.step > 0 && st.step < last && st.email) show(st.step, false);
})();

/* ---------- motion: reveal sections while scrolling; gold buttons bounce every time they come into view ---------- */
(function(){
  if (!("IntersectionObserver" in window) || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const SEL = [".vp-head", ".vp-feat", ".vp-plan", ".vp-faq details", ".sc", ".tile", ".ss-card", ".ss-mz", ".mz-pains li", ".mz-steps li", ".mz-alone",
    ".mz-chips", ".gift", ".bundle", ".vr-pill", ".split-body", ".portal-img", ".round-ph", ".perk", ".mine-item", ".c-item",
    ".gf-card", ".gf-img", ".gf-copy", ".mz-home-in", ".mz-home-img", ".jr-copy", ".head", ".card", ".timeline li", ".gallery figure", ".pd3-sec", ".lp-sec"].join(",");
  const BTN = ".btn-safia,.btn-gold,.vp-btn";
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target); } }),
    {rootMargin: "0px 0px -8% 0px", threshold: 0.08});
  // buttons: bounce each time they enter the screen (replays when you scroll away and back)
  const bo = new IntersectionObserver(es => es.forEach(e => {
    const b = e.target;
    if (e.isIntersecting){
      if (b.classList.contains("bnc")) return;
      const host = b.closest(".rv"); const delay = host && !host.classList.contains("in") ? 450 : 120;
      clearTimeout(b._bt); b._bt = setTimeout(() => { b.classList.remove("bnc"); void b.offsetWidth; b.classList.add("bnc"); }, delay);
    } else { clearTimeout(b._bt); b.classList.remove("bnc"); }
  }), {threshold: 0.6});
  document.addEventListener("animationend", ev => { if (ev.animationName === "msBounce") ev.target.classList.remove("bnc"); });
  function setup(){
    const fold = window.innerHeight * 0.92;
    document.querySelectorAll(SEL).forEach(el => {
      if (el.classList.contains("rv") || el.closest(".rv") || el.closest(".site-header,.mega,.popup,.tabbar,.nour,.chat")) return;
      if (el.getBoundingClientRect().top < fold) return;
      const sib = el.parentElement ? [...el.parentElement.children].filter(c => c.matches(SEL)) : [];
      el.style.setProperty("--rv-d", Math.min(Math.max(0, sib.indexOf(el)), 5) * 0.09 + "s");
      el.classList.add("rv"); io.observe(el);
    });
    document.querySelectorAll(BTN).forEach(b => {
      if (b.closest(".site-header,.mega,.popup,.tabbar,.nour,.chat,.hdr-book")) return;
      if (b.classList.contains("btn-safia")) b.classList.add("alive");
      bo.observe(b);
    });
  }
  if (document.readyState === "complete") setTimeout(setup, 60); else window.addEventListener("load", () => setTimeout(setup, 60));
})();

/* ---------- written reviews: show approved ones; «شاركينا تجربتك» form ---------- */
(function(){
  const RAPI = (window.MS_WP ? MS_WP.home : "") + "/api/review.php";
  const holders = document.querySelectorAll("[data-rv]");
  const star = n => "★".repeat(n) + "☆".repeat(5 - n);
  const esc = t => String(t).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const titles = {}, pages = {}; ((window.SITE_DATA || {}).products || []).forEach(x => { titles[x.id] = x.title; pages[x.id] = x.page; });
  const pageOf = id => id && id !== "general" && titles[id] ? pages[id] : "";
  const toast = window.toast || (m => alert(m));
  const nameOf = id => id === "general" ? "" : (titles[id] || "").replace(/ · /g, " – ");   // «·» next to a digit reads like the Arabic zero (٣٠)
  const reels = document.querySelectorAll("[data-rv-reel]");
  if (reels.length){   // approved written reviews also lead the «قالوا عنا» strip on the home page
    fetch(RAPI + "?action=list", {cache: "no-store"}).then(r => r.ok ? r.json() : {reviews: []}).then(j => {
      const cards = (j.reviews || []).slice(0, 8).map(r => `<div class="voice"><span class="av">${esc(r.name.charAt(0))}</span><span class="qm">“</span><span class="vo-stars" aria-label="${r.stars} من ٥">${star(r.stars)}</span><p>${esc(r.text)}</p><b>${esc(r.name)}</b>${pageOf(r.pid) ? `<a class="vo-p" href="${pageOf(r.pid)}">${esc(nameOf(r.pid))}</a>` : `<small class="vo-p">${esc(nameOf(r.pid) || "تجربة مع د. مرفت")}</small>`}</div>`).join("");
      if (cards) reels.forEach(el => el.insertAdjacentHTML("afterbegin", cards));
    }).catch(() => {}).finally(() => reels.forEach(el => window.msReel(el)));
  }
  if (holders.length){
    fetch(RAPI + "?action=list", {cache: "no-store"}).then(r => r.ok ? r.json() : {reviews: []}).then(j => {
      const all = j.reviews || [];
      holders.forEach(el => {
        const id = el.dataset.rv, ids = id.split(/\s+/), list = id === "all" ? all : all.filter(r => ids.includes(r.pid));
        el.innerHTML = list.map(r => `<article class="rv-card"><div class="rv-stars" aria-label="${r.stars} من ٥">${star(r.stars)}</div><p>${esc(r.text)}</p><b>${esc(r.name)}${nameOf(r.pid) ? `<small> · ${esc(nameOf(r.pid))}</small>` : ""}</b></article>`).join("")
          || (id === "all" ? `<p class="vr-empty">تُنشر الآراء المكتوبة هنا بعد مراجعتها.</p>` : "");
      });
    }).catch(() => {});
  }
  const app = document.querySelector("[data-review-app]"); if (!app) return;
  const sel = app.querySelector("#rwAbout"), rec = app.querySelector("[data-vrrec]");
  const about = new URLSearchParams(location.search).get("about");
  if (about && sel.querySelector(`option[value="${CSS.escape(about)}"]`)) sel.value = about;
  const syncRec = () => { rec.dataset.vrrec = sel.value; if (!rec.dataset.state || rec.dataset.state === "idle") { rec.dataset.state = "idle"; if (window.renderVoices) window.renderVoices(); } };
  sel.addEventListener("change", syncRec); syncRec();
  let stars = 5;
  const paint = () => app.querySelectorAll(".rw-star").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.star <= stars)));
  app.addEventListener("click", e => {
    const s = e.target.closest(".rw-star"); if (s){ stars = +s.dataset.star; paint(); return; }
    const b = e.target.closest("[data-rw-send]"); if (!b) return;
    const text = app.querySelector("#rwText").value.trim();
    if (text.length < 10){ toast("اكتبي تجربتك في سطر أو أكثر."); return; }
    if (!app.querySelector("#rwOk").checked){ toast("ضعي علامة الموافقة على النشر أولاً."); return; }
    const byCity = app.querySelector("input[name=rwN]:checked").value === "city";
    const name = byCity ? "عميلة من " + (app.querySelector("#rwCity").value.trim() || "مصر") : (app.querySelector("#rwFirst").value.trim() || "عميلة");
    b.disabled = true; b.textContent = "جارٍ الإرسال…";
    fetch(RAPI + "?action=submit", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({pid: sel.value, stars, text, name,
      email: app.querySelector("#rwEmail").value.trim(), consent: 1, website: (app.querySelector("[name=website]") || {}).value || ""})})
      .then(r => r.json().then(j => ({ok: r.ok && j.ok, j})))
      .then(({ok, j}) => {
        if (ok){ b.hidden = true; app.querySelector(".rw-done").hidden = false; app.querySelector("#rwText").value = ""; return; }
        b.disabled = false; b.textContent = "أرسلي رأيي";
        toast(j.error === "limit" ? "أرسلتِ عدة آراء خلال وقت قصير. جرّبي بعد ساعة." : "تعذّر الإرسال. حاولي مرة أخرى.");
      })
      .catch(() => { b.disabled = false; b.textContent = "أرسلي رأيي"; toast("تعذّر الإرسال. تأكدي من الاتصال بالإنترنت."); });
  });
})();

/* ---------- brand video player (Bunny MP4, our own gold/royal controls) ---------- */
window.msPlayer = (host, guid, auto) => {
  const CDN = "https://vz-d470dd2c-1fa.b-cdn.net/" + guid + "/";
  const svg = d => '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + d + '"/></svg>';
  const I = {play: "M8 5.2v13.6a.8.8 0 0 0 1.2.7l10.6-6.8a.8.8 0 0 0 0-1.4L9.2 4.5A.8.8 0 0 0 8 5.2z", pause: "M7 5h3.4v14H7zM13.6 5H17v14h-3.4z",
    vol: "M4 9h4l5-4v14l-5-4H4zM16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12", mute: "M4 9h4l5-4v14l-5-4H4zM16.5 9.5l5 5M21.5 9.5l-5 5",
    fs: "M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5", gear: "M12 15.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4zM19.4 13.5l1.7 1.3-1.8 3.1-2-.8a7.6 7.6 0 0 1-1.9 1.1l-.3 2.1h-3.6l-.3-2.1a7.6 7.6 0 0 1-1.9-1.1l-2 .8-1.8-3.1 1.7-1.3a7.7 7.7 0 0 1 0-2.9L2.9 9.2l1.8-3.1 2 .8a7.6 7.6 0 0 1 1.9-1.1l.3-2.1h3.6l.3 2.1a7.6 7.6 0 0 1 1.9 1.1l2-.8 1.8 3.1-1.7 1.3a7.7 7.7 0 0 1 0 2.9z", fsx: "M9 4v5H4M20 9h-5V4M15 20v-5h5M4 15h5v5"};
  host.classList.add("msp"); host.setAttribute("dir", "ltr");
  host.innerHTML = '<video playsinline preload="metadata" poster="' + (host.dataset.poster || "") + '"></video>' +
    '<button type="button" class="msp-big" aria-label="تشغيل">' + svg(I.play) + '</button>' +
    '<div class="msp-bar"><button type="button" class="msp-b msp-pp" aria-label="تشغيل">' + svg(I.play) + '</button>' +
    '<div class="msp-track" role="slider" aria-label="التقدم" tabindex="0"><i class="msp-buf"></i><i class="msp-fill"></i><b class="msp-knob"></b></div>' +
    '<span class="msp-time">0:00</span>' +
    '<button type="button" class="msp-b msp-set" aria-label="الإعدادات" aria-expanded="false">' + svg(I.gear) + '</button>' +
    '<button type="button" class="msp-b msp-vol" aria-label="الصوت">' + svg(I.vol) + '</button>' +
    '<button type="button" class="msp-b msp-fs" aria-label="ملء الشاشة">' + svg(I.fs) + '</button></div>' +
    '<div class="msp-menu" dir="rtl" hidden><b>السرعة</b><div class="msp-opts" data-k="spd">' +
    [0.75, 1, 1.25, 1.5, 2].map(x => '<button type="button" data-v="' + x + '"' + (x === 1 ? ' class="on"' : '') + '>' + (x === 1 ? "عادية" : x + "×") + '</button>').join("") +
    '</div><b>الجودة</b><div class="msp-opts" data-k="q">' +
    [["720p", "عالية"], ["480p", "متوسطة"], ["360p", "منخفضة"]].map(([r, t], i) => '<button type="button" data-v="' + r + '"' + (i ? "" : ' class="on"') + '>' + t + '</button>').join("") + '</div></div>';
  const v = host.querySelector("video"), q = c => host.querySelector(c);
  const src = r => CDN + "play_" + r + ".mp4";
  const sizes = ["720p", "480p", "360p"]; let si = 0;
  v.src = src(sizes[0]);
  v.addEventListener("error", () => { if (++si < sizes.length) { const t = v.currentTime; v.src = src(sizes[si]); v.currentTime = t; v.play().catch(() => {}); } });
  const fmt = t => { t = Math.max(0, Math.floor(t || 0)); return Math.floor(t / 60) + ":" + String(t % 60).padStart(2, "0"); };
  const toggle = () => v.paused ? v.play().catch(() => {}) : v.pause();
  let hideT; const wake = () => { host.classList.add("msp-awake"); clearTimeout(hideT); if (!v.paused) hideT = setTimeout(() => { if (!host.classList.contains("msp-menu-on")) host.classList.remove("msp-awake"); }, 2600); };
  const sync = () => { const on = !v.paused; host.classList.toggle("msp-playing", on); q(".msp-pp").innerHTML = svg(on ? I.pause : I.play);
    q(".msp-pp").setAttribute("aria-label", on ? "إيقاف مؤقت" : "تشغيل"); wake(); };
  v.addEventListener("play", () => { host.classList.add("msp-started"); sync(); if (window.gtag && !host.dataset.ga) { host.dataset.ga = 1; gtag("event", "video_play", {item: guid}); } });
  v.addEventListener("pause", sync);
  v.addEventListener("timeupdate", () => { const p = v.duration ? v.currentTime / v.duration : 0;
    q(".msp-fill").style.width = q(".msp-knob").style.left = (p * 100) + "%";
    q(".msp-time").textContent = fmt(v.currentTime) + " / " + fmt(v.duration); });
  v.addEventListener("progress", () => { try { if (v.duration && v.buffered.length) q(".msp-buf").style.width = (v.buffered.end(v.buffered.length - 1) / v.duration * 100) + "%"; } catch (e) {} });
  v.addEventListener("loadedmetadata", () => { q(".msp-time").textContent = "0:00 / " + fmt(v.duration); });
  v.addEventListener("ended", () => host.classList.add("msp-awake"));
  v.addEventListener("click", toggle); q(".msp-big").addEventListener("click", toggle); q(".msp-pp").addEventListener("click", toggle);
  host.addEventListener("pointermove", wake); host.addEventListener("touchstart", wake, {passive: true});
  const tr = q(".msp-track");
  const seek = e => { const r = tr.getBoundingClientRect(); const x = e.clientX - r.left;
    if (v.duration) v.currentTime = Math.min(1, Math.max(0, x / r.width)) * v.duration; };
  tr.addEventListener("pointerdown", e => { seek(e); tr.setPointerCapture(e.pointerId); const mv = ev => seek(ev);
    tr.addEventListener("pointermove", mv); tr.addEventListener("pointerup", () => tr.removeEventListener("pointermove", mv), {once: true}); });
  tr.addEventListener("keydown", e => { if (e.key === "ArrowRight") v.currentTime += 5; if (e.key === "ArrowLeft") v.currentTime -= 5; });
  const menu = q(".msp-menu"), setB = q(".msp-set");
  const openMenu = on => { menu.hidden = !on; setB.setAttribute("aria-expanded", on ? "true" : "false"); host.classList.toggle("msp-menu-on", on); };
  setB.addEventListener("click", e => { e.stopPropagation(); openMenu(menu.hidden); });
  document.addEventListener("click", e => { if (!menu.hidden && !menu.contains(e.target)) openMenu(false); });
  menu.addEventListener("click", e => {
    const b = e.target.closest("button[data-v]"); if (!b) return; e.stopPropagation();
    b.parentNode.querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b));
    if (b.parentNode.dataset.k === "spd") v.playbackRate = +b.dataset.v;
    else { const t = v.currentTime, was = !v.paused, rate = v.playbackRate; si = sizes.indexOf(b.dataset.v); v.src = src(b.dataset.v);
      v.addEventListener("loadedmetadata", () => { v.currentTime = t; v.playbackRate = rate; if (was) v.play().catch(() => {}); }, {once: true}); }
    openMenu(false);
  });
  q(".msp-vol").addEventListener("click", e => { v.muted = !v.muted; e.currentTarget.innerHTML = svg(v.muted ? I.mute : I.vol); });
  q(".msp-fs").addEventListener("click", () => {
    if (document.fullscreenElement || document.webkitFullscreenElement) (document.exitFullscreen || document.webkitExitFullscreen).call(document);
    else if (host.requestFullscreen) host.requestFullscreen().catch(() => {});
    else if (host.webkitRequestFullscreen) host.webkitRequestFullscreen();
    else if (v.webkitEnterFullscreen) v.webkitEnterFullscreen(); });
  ["fullscreenchange", "webkitfullscreenchange"].forEach(ev => document.addEventListener(ev, () => {
    q(".msp-fs").innerHTML = svg((document.fullscreenElement || document.webkitFullscreenElement) === host ? I.fsx : I.fs); }));
  if (auto) v.play().catch(() => {});
  return v;
};
document.querySelectorAll("[data-msp]").forEach(el => window.msPlayer(el, el.dataset.msp, false));

/* ---------- free intro video on a tool page: the cover turns into the player ---------- */
(function(){
  const box = document.querySelector("[data-intro]"); if (!box) return;
  const play = (auto) => {
    if (box.dataset.on) return; box.dataset.on = 1;
    const img = box.querySelector("img"), host = document.createElement("div");
    host.className = "pd3-player"; host.dataset.poster = img ? img.currentSrc || img.src : "";
    host.setAttribute("aria-label", box.getAttribute("aria-label") || "المقدمة");
    box.removeAttribute("id"); box.replaceWith(host); host.id = "intro";
    window.msPlayer(host, box.dataset.intro, auto);
  };
  box.addEventListener("click", () => play(true));
  document.addEventListener("click", e => {
    const a = e.target.closest("[data-intro-open]"); if (!a) return;
    e.preventDefault(); (document.getElementById("intro") || box).scrollIntoView({behavior: "smooth", block: "center"}); play(true);
  });
  if (location.hash === "#intro") { setTimeout(() => { (document.getElementById("intro") || box).scrollIntoView({block: "center"}); play(false); }, 300); }
})();
