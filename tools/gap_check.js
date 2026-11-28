// Finds big empty vertical gaps between visible content on every page of the live site (desktop >150px, phone >110px).
// Usage: node tools/gap_check.js        (needs Playwright; reads the WordPress sitemap)
const { chromium } = require('playwright');
const SITE = 'https://mervatsror.com';
const extra = ['https://mervatsror.com/my-account/', 'https://mervatsror.com/cart/'];
(async () => {
  const sm = async u => ((await (await fetch(u)).text()).match(/<loc>[^<]+/g) || []).map(x => x.slice(5));
  const urls = [...(await sm(SITE + '/wp-sitemap-posts-page-1.xml')), ...(await sm(SITE + '/wp-sitemap-posts-product-1.xml'))];
  const b = await chromium.launch();
  const res = [];
  for (const [dev, w, h, lim] of [['desk', 1366, 768, 150], ['phone', 390, 844, 110]]) {
    const ctx = await b.newContext({ viewport: { width: w, height: h } });
    for (const u of [...urls, ...extra]) {
      const p = await ctx.newPage();
      try {
        await p.goto(u, { waitUntil: 'networkidle', timeout: 45000 }); await p.waitForTimeout(1200);
        // reveal-on-scroll content: force everything visible
        await p.addStyleTag({ content: '*{animation:none!important;transition:none!important}[class*=reveal],.rv,.in,.fade{opacity:1!important;transform:none!important}' });
        await p.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); } window.scrollTo(0, 0); });
        await p.waitForTimeout(600);
        const gaps = await p.evaluate((lim) => {
          const skip = el => el.closest('header.site-header,.help-wrap,.nour,[class*=pop],.site-footer,footer,.help-btn,[hidden],dialog');
          const boxes = [];
          const vis = el => { for (let e = el; e && e !== document.body; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false; } return true; };
          const add = (r, txt) => { if (r.width < 4 || r.height < 4 || r.right < 0 || r.left > innerWidth) return; boxes.push({ t: r.top + scrollY, b: r.bottom + scrollY, txt }); };
          // text
          const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          for (let n; (n = tw.nextNode());) {
            if (!n.textContent.trim() || skip(n.parentElement) || !vis(n.parentElement)) continue;
            const rg = document.createRange(); rg.selectNodeContents(n); for (const r of rg.getClientRects()) add(r, n.textContent.trim().slice(0, 50));
          }
          // media and boxed elements (cards, buttons, inputs) that are narrower than the page
          document.querySelectorAll('img,video,iframe,svg,canvas:not(.sparkle),input,select,textarea,button,a,div,section,article,figure,li').forEach(el => {
            if (skip(el) || !vis(el)) return;
            const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
            const media = /^(IMG|VIDEO|IFRAME|SVG|CANVAS|INPUT|SELECT|TEXTAREA)$/i.test(el.tagName);
            const boxed = r.width < innerWidth * .92 && ((cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent') || parseFloat(cs.borderTopWidth) > 0 || cs.backgroundImage !== 'none');
            if (media || boxed) add(r, el.tagName + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : ''));
          });
          boxes.sort((a, b) => a.t - b.t);
          const out = []; let maxB = -1, last = null;
          for (const x of boxes) {
            if (last && x.t - maxB > lim) out.push({ gap: Math.round(x.t - maxB), above: last.txt, below: x.txt, y: Math.round(maxB) });
            if (x.b > maxB) { maxB = x.b; last = x; }
          }
          return out;
        }, lim);
        for (const g of gaps) res.push({ dev, u: u.replace('https://mervatsror.com', ''), ...g });
      } catch (e) { res.push({ dev, u, err: String(e).slice(0, 80) }); }
      await p.close();
    }
    await ctx.close();
  }
  for (const r of res) console.log(r.dev, r.u, r.err || `${r.gap}px @${r.y} | ${r.above} || ${r.below}`);
  await b.close();
})();
