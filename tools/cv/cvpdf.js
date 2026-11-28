const { chromium } = require('playwright');
// Rebuild the CV PDF: node tools/cv/cvpdf.js tools/cv  then copy Mervat-Soror-CV.pdf to src/assets/docs/
const D = require('path').resolve(process.argv[2]);
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + D + '/cv.html', { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
  await p.pdf({ path: D + '/Mervat-Soror-CV.pdf', format: 'A4', printBackground: true, preferCSSPageSize: true });
  await p.setViewportSize({ width: 794, height: 1123 });
  const pages = await p.$$('.page');
  for (let i = 0; i < pages.length; i++) await pages[i].screenshot({ path: `${D}/cv-p${i + 1}.png` });
  console.log('fits:', await p.evaluate(() => [...document.querySelectorAll('.main')].map(m => { const last = m.lastElementChild.getBoundingClientRect().bottom, pg = m.closest('.page').getBoundingClientRect().bottom; return Math.round(pg - last); })));
  await b.close();
})();
