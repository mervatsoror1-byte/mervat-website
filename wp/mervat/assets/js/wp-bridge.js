/* Connects the design's buttons to WooCommerce (loaded after site.js).
   - "ابدأ الآن" (data-buy) -> straight to checkout with the item
   - cart icon (data-add)    -> added to the WooCommerce cart without leaving the page
   - currency buttons        -> switch the shop currency (EGP for Egypt, USD elsewhere)
   - any leftover "*.html" link -> the matching WordPress address */
(function () {
  "use strict";
  var W = window.MS_WP || {};
  var ids = W.ids || {};
  var map = {cart: "/cart/", checkout: "/checkout/", account: "/my-account/", login: "/my-account/", register: "/my-account/",
             forgot: "/my-account/lost-password/", learn: "/my-account/", reader: "/my-account/", success: "/my-account/orders/", failed: "/checkout/", index: "/"};
  var productPages = {};
  ((window.SITE_DATA || {}).products || []).forEach(function (p) {
    if (p.page && p.page.indexOf("/tools/") > -1) { var m = p.page.match(/\/tools\/([^/]+)\//); if (m) productPages[m[1]] = p.page; }
  });

  function wpUrl(href) {
    var m = /^([a-z0-9-]+)\.html([?#].*)?$/.exec(href || "");
    if (!m) return null;
    var stem = m[1], rest = m[2] || "";
    if (map[stem]) return W.home + map[stem] + rest;
    if (productPages[stem]) return productPages[stem] + rest;
    return W.home + "/" + stem + "/" + rest;
  }
  function fixLinks(root) {
    (root.querySelectorAll ? root.querySelectorAll("a[href$='.html'], a[href*='.html#']") : []).forEach(function (a) {
      var u = wpUrl(a.getAttribute("href")); if (u) a.setAttribute("href", u);
    });
  }
  fixLinks(document);
  new MutationObserver(function (list) { list.forEach(function (r) { r.addedNodes.forEach(function (n) { if (n.nodeType === 1) fixLinks(n); }); }); })
    .observe(document.body, {childList: true, subtree: true});

  function say(msg) { if (typeof window.toast === "function") window.toast(msg); }
  function setCount(n) {
    var t = String(n).replace(/\d/g, function (d) { return "٠١٢٣٤٥٦٧٨٩"[d]; });
    document.querySelectorAll(".js-cart-count").forEach(function (e) { e.textContent = t; });
  }
  setCount(W.cartCount || 0);

  function checkoutUrl(sku, extra) {
    var id = ids[sku];
    if (!id) return null;
    var u = W.checkout + (W.checkout.indexOf("?") > -1 ? "&" : "?") + "add-to-cart=" + id;
    if (extra && extra.when) u += "&ms_when=" + encodeURIComponent(extra.when);
    return u;
  }
  function buy(sku, extra) {
    var u = checkoutUrl(sku, extra);
    if (!u) { say("هذه الأداة غير متاحة للشراء الآن."); return; }
    location.href = u;
  }
  function add(sku, btn) {
    var id = ids[sku];
    if (!id) { say("هذه الأداة غير متاحة للشراء الآن."); return; }
    if ((W.inCart || []).indexOf(sku) > -1) { location.href = W.cart; return; }
    var body = new URLSearchParams({product_id: id, quantity: 1});
    if (btn) btn.classList.add("busy");
    fetch(W.ajax, {method: "POST", body: body, credentials: "same-origin", headers: {"Content-Type": "application/x-www-form-urlencoded"}})
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.error) { if (j.product_url) location.href = j.product_url; else say("تعذّرت الإضافة للسلة."); return; }
        (W.inCart = W.inCart || []).push(sku);
        setCount((j && j.fragments && j.fragments.ms_count) || ((W.cartCount || 0) + 1));
        document.querySelectorAll('.add[data-add="' + sku + '"]').forEach(function (b) { b.classList.add("in"); });
        say("أُضيفت إلى السلة");
      })
      .catch(function () { say("تعذّرت الإضافة للسلة. حاولي مرة أخرى."); })
      .finally(function () { if (btn) btn.classList.remove("busy"); });
  }

  // site.js calls these by name (session calendars, VIP plans): send them to WooCommerce instead.
  window.startBuy = function (sku, extra) { buy(sku, extra); };
  window.addToCart = function (sku) { add(sku); };

  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-buy]");
    if (b) { e.preventDefault(); e.stopImmediatePropagation(); buy(b.dataset.buy); return; }
    var a = e.target.closest("[data-add]");
    if (a) { e.preventDefault(); e.stopImmediatePropagation(); add(a.dataset.add, a); return; }
    var r = e.target.closest("[data-region]");
    if (r) {
      e.preventDefault(); e.stopImmediatePropagation();
      var want = r.dataset.region === "eg" ? "EGP" : "USD";
      if (want === W.currency) return;
      var u = new URL(location.href); u.searchParams.set("wcpbc-manual-country", want === "EGP" ? "EG" : "US");
      location.href = u.toString(); return;
    }
    var c = e.target.closest(".cur-mini, [data-cur-toggle]");
    if (c) {
      e.preventDefault(); e.stopImmediatePropagation();
      var u2 = new URL(location.href); u2.searchParams.set("wcpbc-manual-country", W.currency === "EGP" ? "US" : "EG");
      location.href = u2.toString(); return;
    }
    if (e.target.closest("#logout")) { e.preventDefault(); e.stopImmediatePropagation(); location.href = W.account + "customer-logout/"; }
  }, true);

  // Header login link -> account
  document.querySelectorAll(".js-user-text").forEach(function (l) { l.setAttribute("href", W.account); if (W.user) l.textContent = "حسابي"; });
})();
