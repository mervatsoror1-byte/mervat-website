// Full health check of the live site, the way a visitor uses it (phone + desktop).
// Usage: node tools/site_check.js [base]   (default https://mervatsror.com)
// Prints a report and exits 1 if anything failed.
const { chromium, devices } = require('playwright');
const BASE = (process.argv[2] || 'https://mervatsror.com').replace(/\/$/, '');
const PAGES = ['/', '/library/', '/vip/', '/sessions/', '/marriage/', '/gift/', '/review/', '/voices/', '/bundles/', '/books/', '/about/',
  '/contact/', '/faq/', '/articles/', '/policies/', '/terms/', '/privacy/', '/refund/', '/delivery/', '/my-account/', '/cart/',
  '/tools/exercise-detachment/', '/tools/decoding-original-version/', '/tools/decoding-light-of-acceptance/', '/tools/decoding-energy-stagnation/',
  '/tools/inner-child-healing/', '/tools/heart-coherence-breathing/', '/tools/morning-priming/', '/tools/peace-affirmations/',
  '/tools/serenity-cleansing-meditation/', '/tools/course-ain-sahia/', '/tools/book-ghosts/', '/lp-attach/', '/lp-serenity/'];
const IGNORE = /googletagmanager|google-analytics|mediadelivery|b-cdn|facebook|paypal|ERR_TUNNEL|ERR_BLOCKED|net::ERR_ABORTED/i;
const problems = [], notes = [];
const bad = (where, what) => problems.push(`${where}: ${what}`);

(async () => {
  const b = await chromium.launch();
  for (const [label, ctxOpts] of [['موبايل', {...devices['Pixel 7']}], ['كمبيوتر', {viewport: {width: 1366, height: 900}}]]) {
    const c = await b.newContext(ctxOpts);
    await c.addInitScript(() => { try { localStorage.setItem('ms_state_v1', JSON.stringify({popSeen: 1})); } catch (e) {} });
    const p = await c.newPage();
    for (const path of PAGES) {
      const errs = [], fails = [];
      p.removeAllListeners('pageerror'); p.removeAllListeners('requestfailed'); p.removeAllListeners('response');
      p.on('pageerror', e => errs.push(e.message));
      p.on('response', r => { const u = r.url(); if (r.status() >= 400 && u.startsWith(BASE) && !IGNORE.test(u)) fails.push(r.status() + ' ' + u.replace(BASE, '')); });
      p.on('requestfailed', r => { const t = (r.failure() || {}).errorText || ''; if (r.url().startsWith(BASE) && !IGNORE.test(t)) fails.push('failed ' + r.url().replace(BASE, '')); });
      let resp;
      try { resp = await p.goto(BASE + path, {waitUntil: 'networkidle', timeout: 45000}); } catch (e) { bad(`${label} ${path}`, 'الصفحة لم تفتح (' + e.message.split('\n')[0] + ')'); continue; }
      if (!resp || resp.status() >= 400) { bad(`${label} ${path}`, 'كود ' + (resp && resp.status())); continue; }
      await p.waitForTimeout(500);
      // scroll to the bottom so lazy parts and reveal animations run
      const H = await p.evaluate(() => document.body.scrollHeight);
      for (let y = 0; y < H; y += 700) { await p.evaluate(v => scrollTo(0, v), y); await p.waitForTimeout(40); }
      await p.waitForTimeout(1300);
      const r = await p.evaluate(() => {
        const W = document.documentElement.clientWidth;
        const txt = document.body.innerText;
        const imgs = [...document.images].filter(i => i.complete && i.naturalWidth === 0 && i.getBoundingClientRect().width > 0 && !/googletag|facebook/.test(i.src)).map(i => i.src.split('/').pop());
        const hidden = [...document.querySelectorAll('.rv:not(.in)')].length;
        const words = ['Sorry, it seems there are no available payment methods', 'Fatal error', 'Warning:', 'Notice:', 'Deprecated:', 'كان هناك خطأ فادح', 'undefined', 'NaN', '{{', 'lorem'];
        return {sw: document.documentElement.scrollWidth, W, imgs, hidden, found: words.filter(w => txt.includes(w)), title: document.title, h1: !!document.querySelector('h1')};
      });
      if (r.sw > r.W + 2) bad(`${label} ${path}`, `الصفحة أعرض من الشاشة (${r.sw} بدل ${r.W}) فتتحرك يمين وشمال`);
      if (r.imgs.length) bad(`${label} ${path}`, 'صور لا تظهر: ' + r.imgs.slice(0, 4).join(', '));
      if (r.hidden) bad(`${label} ${path}`, `${r.hidden} عنصر بقي مخفياً بعد النزول للآخر`);
      if (r.found.length) bad(`${label} ${path}`, 'نص غريب ظاهر للزائر: ' + r.found.join(' | '));
      if (errs.length) bad(`${label} ${path}`, 'خطأ في الكود: ' + errs.slice(0, 2).join(' | '));
      if (fails.length) bad(`${label} ${path}`, 'ملفات لا تتحمّل: ' + fails.slice(0, 4).join(', '));
      if (label === 'كمبيوتر' && !r.h1 && path !== '/cart/' && path !== '/my-account/') notes.push(`${path}: الصفحة بدون عنوان رئيسي (h1)`);
    }
    await c.close();
  }

  // buying works: each product type reaches checkout with a payment method, in USD and EGP
  const c = await b.newContext({viewport: {width: 1280, height: 900}}); const p = await c.newPage();
  for (const [country, cur] of [['US', 'دولار'], ['EG', 'جنيه']]) {
    for (const [page, sel, name] of [['/tools/exercise-detachment/', '[data-buy="attach"]', 'تمرين'], ['/vip/', '[data-buy="vip-m"]', 'VIP شهري'],
      ['/vip/', '[data-buy="vip-y"]', 'VIP سنوي'], ['/bundles/', '[data-buy^="b-"]', 'باقة'], ['/marriage/', null, 'استشارة زوجية'], ['/sessions/', null, 'جلسة فردية']]) {
      try {
        await p.goto(`${BASE}${page}?wcpbc-manual-country=${country}`, {waitUntil: 'networkidle', timeout: 45000});
        if (sel) { await p.locator(sel).first().click(); }
        else {
          const card = p.locator('[data-sess]').first();
          await card.locator('.ss-nav[data-dir="1"]').click(); await card.locator('.ss-d.ok').nth(3).click(); await card.locator('.ss-s:not([disabled])').first().click();
          await card.locator('.ss-go').click();
        }
        await p.waitForLoadState('networkidle'); await p.waitForTimeout(2000);
        const g = await p.$$eval('.wc_payment_method', els => els.map(e => e.className));
        const body = await p.textContent('body');
        if (!/checkout/.test(p.url())) bad(`شراء ${name} (${cur})`, 'لم يصل لصفحة الدفع: ' + p.url().replace(BASE, ''));
        else if (!g.length) bad(`شراء ${name} (${cur})`, 'صفحة الدفع بدون أي وسيلة دفع');
        else if (cur === 'دولار' && !g.some(x => x.includes('ppcp'))) bad(`شراء ${name} (${cur})`, 'PayPal غير ظاهر');
        if (/no available payment methods/i.test(body)) bad(`شراء ${name} (${cur})`, 'رسالة «لا توجد وسائل دفع»');
      } catch (e) { bad(`شراء ${name} (${cur})`, 'تعذّر: ' + e.message.split('\n')[0]); }
      await p.goto(`${BASE}/cart/`, {waitUntil: 'networkidle'}).catch(() => {});
      await p.$$eval('a.remove', as => as.forEach(a => a.click())).catch(() => {});
      await p.waitForTimeout(800);
    }
  }
  // site services answer
  for (const [u, want] of [['/api/voice.php?action=list', '"ok":true'], ['/api/review.php?action=list', '"ok":true'], ['/wp-sitemap.xml', '<sitemapindex'], ['/robots.txt', 'Sitemap']]) {
    const r = await p.request.get(BASE + u).catch(() => null);
    const t = r ? await r.text() : '';
    if (!r || r.status() !== 200 || !t.includes(want)) bad('خدمة ' + u, 'لا تعمل كما يجب (كود ' + (r && r.status()) + ')');
  }
  const home = await (await p.request.get(BASE + '/')).text();
  if (/noindex/.test((home.match(/<meta name=.robots[^>]*>/) || [''])[0])) bad('جوجل', 'الصفحة الرئيسية مخفية عن جوجل (noindex)');
  await b.close();

  console.log(`فحص ${BASE}: ${PAGES.length} صفحة × موبايل وكمبيوتر + الشراء بالدولار والجنيه + الخدمات`);
  if (problems.length) { console.log(`\n❌ ${problems.length} مشكلة:`); problems.forEach(x => console.log(' - ' + x)); }
  else console.log('\n✅ لا مشاكل');
  if (notes.length) { console.log('\nملاحظات:'); notes.forEach(x => console.log(' - ' + x)); }
  process.exit(problems.length ? 1 : 0);
})();
