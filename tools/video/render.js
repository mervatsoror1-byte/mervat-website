// Renders each caption as a transparent PNG (browser = correct Arabic shaping and word order), then
// writes an ffmpeg filter that slides/fades each one in at its time over the video.
const { chromium } = require('playwright');
const fs = require('fs');
const D = __dirname + '/';
const cues = JSON.parse(fs.readFileSync(D + 'cues.json', 'utf8'));
const css = `
@font-face{font-family:Taj;src:url(data:font/ttf;base64,${fs.readFileSync(D+'fonts/f4.ttf').toString('base64')})}       /* Tajawal ExtraBold */
@font-face{font-family:TajM;src:url(data:font/ttf;base64,${fs.readFileSync(D+'fonts/f3.ttf').toString('base64')})}      /* Tajawal Medium */
@font-face{font-family:Mes;src:url(data:font/ttf;base64,${fs.readFileSync(D+'fonts/f1.ttf').toString('base64')})}       /* El Messiri Bold */
html,body{margin:0;background:transparent}
#b{width:1500px;height:520px;display:flex;align-items:center;justify-content:center;text-align:center;direction:rtl}
.t{color:#F5F5DC;text-shadow:0 3px 16px rgba(10,14,50,.85),0 0 4px rgba(10,14,50,.7),0 0 30px rgba(20,24,90,.45)}
.n{font-family:Taj;font-size:98px;line-height:1.45;max-width:1120px;text-wrap:balance}
.g{font-family:Mes;font-size:168px;line-height:1.2;color:#E2B866}
.s{font-family:TajM;font-size:70px;line-height:1.4}
.t b{color:#E2B866;font-weight:inherit}
.rule{width:480px;height:5px;border-radius:3px;background:linear-gradient(90deg,transparent,#E2B866 15%,#E2B866 85%,transparent)}
`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({viewport: {width: 1500, height: 520}});
  for (const [i, c] of cues.entries()) {
    const html = c.kind === 'rule' ? '<div class="rule"></div>'
      : `<div class="t ${c.kind}">${c.html}</div>`;
    await p.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body><div id="b">${html}</div></body></html>`);
    await p.evaluate(async () => { await Promise.all(['40px Taj','40px TajM','40px Mes'].map(f => document.fonts.load(f, 'عربي'))); await document.fonts.ready; if (!document.fonts.check('40px Taj') || !document.fonts.check('40px Mes')) throw new Error('font not loaded'); }); await p.waitForTimeout(60);
    await p.locator('#b').screenshot({path: `${D}cap_${String(i).padStart(2, '0')}.png`, omitBackground: true});
  }
  await b.close();
  // ffmpeg filter: each caption box (1500x520) is centred at (cx, cy) of the 1920x1080 frame
  const inputs = [], f = [];
  let last = '0:v';
  cues.forEach((c, i) => {
    const dur = (c.end - c.start).toFixed(2), x0 = c.cx - 750, y0 = c.cy - 260, slide = c.slide || 0, zoom = c.zoom;
    inputs.push(`-loop 1 -t ${dur} -i ${D}cap_${String(i).padStart(2, '0')}.png`);
    let chain = `[${i + 1}:v]format=rgba`;
    if (zoom) chain += `,scale=w='iw*(0.84+0.16*min(1,t/0.26))':h=-1:eval=frame`;
    chain += `,fade=t=in:st=0:d=${c.fin}:alpha=1,fade=t=out:st=${(c.end - c.start - c.fout).toFixed(2)}:d=${c.fout}:alpha=1,setpts=PTS+${c.start}/TB[c${i}]`;
    f.push(chain);
    const x = zoom ? `${c.cx}-overlay_w/2` : (slide ? `${x0}+${slide}*max(0\\,1-(t-${c.start})/0.32)^2` : `${x0}`);
    const y = zoom ? `${c.cy}-overlay_h/2` : `${y0}`;
    f.push(`[${last}][c${i}]overlay=x='${x}':y='${y}':eof_action=pass:enable='between(t,${c.start},${c.end})'[v${i}]`);
    last = `v${i}`;
  });
  fs.writeFileSync(D + 'inputs.txt', inputs.join(' '));
  fs.writeFileSync(D + 'filter.txt', f.join(';\n'));
  fs.writeFileSync(D + 'last.txt', last);
  console.log(cues.length, 'captions rendered');
})();
