// Checks every chapter page at 1440px: figures stay inside their frame, figures and maps fit without
// sideways scrolling, and every label fits its card, pill or note. Usage: node frame_check.mjs <puppeteer dir> <base url> <nav-data.js>
import { createRequire } from 'module'; import path from 'path';
const [, , pptr, base] = process.argv;
const puppeteer = createRequire(path.join(pptr, 'package.json'))(pptr);
const b = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
const page = await b.newPage(); await page.setViewport({ width: 1440, height: 900 });
await page.goto(base, { waitUntil: 'load' });
import fs from 'fs';
const nav = JSON.parse(fs.readFileSync(process.argv[4], 'utf8').split('=').slice(1).join('=').trim().replace(/;$/, ''));
const pages = nav.flatMap(t => t.chapters.filter(c => c.rendered).map(c => '/' + c.path.replace(/\.md$/, '') + '/'));
const kinds = {}; const sample = []; let figs = 0, maps = 0, labels = 0;
for (const p of pages) {
  await page.goto(base.replace(/\/$/, '') + p, { waitUntil: 'load' });
  const r = await page.evaluate(async () => {
    await document.fonts.ready; await new Promise(r => setTimeout(r, 150));
    const out = { figs: 0, maps: 0, labels: 0, issues: [] };
    for (const f of document.querySelectorAll('.fm-figure')) { out.figs++; const fb = f.getBoundingClientRect(); const s = f.querySelector('.fm-scroll');
      if (s.scrollWidth > s.clientWidth + 1) out.issues.push('figure-scrolls');
      for (const part of f.querySelectorAll('.fm-heading,.fm-legend,figcaption,.fm-sources')) { const b = part.getBoundingClientRect(); if (b.left < fb.left - 1 || b.right > fb.right + 1) out.issues.push('outside-frame'); } }
    for (const m of document.querySelectorAll('.relationship-map')) { out.maps++; if (m.scrollWidth > m.clientWidth + 1) out.issues.push('map-scrolls ' + m.scrollWidth + '/' + m.clientWidth); }
    for (const g of document.querySelectorAll('svg.fm-svg .fm-node, svg.fm-svg .fm-pill, svg.fm-svg .fm-note')) { out.labels++; const r = g.querySelector('rect').getBBox(); for (const t of g.querySelectorAll('text:not(.n)')) { const b = t.getBBox(); if (b.x < r.x + 2 || b.x + b.width > r.x + r.width - 2) out.issues.push('text-overflow'); } }
    // Common rule: nothing inside a box may extend past that box, except inside a scroll area.
    const boxes = '.blend,.fm-figure,.pb-figure,.stepper,.source-diagram,.original-diagram,.callout,.question,.deep-dive,.static-model,.checkpoint,.code-card,.decision-card,.relationship-map,details';
    const scrolls = el => { for (let e = el.parentElement; e; e = e.parentElement) { const o = getComputedStyle(e).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') return e; } return null; };
    // A box counts only when it is visible (border or background); each element is checked against its nearest one.
    const visible = el => { const c = getComputedStyle(el); return parseFloat(c.borderLeftWidth) > 0 || parseFloat(c.borderRightWidth) > 0 || (c.backgroundColor !== 'rgba(0, 0, 0, 0)' && c.backgroundColor !== 'transparent'); };
    const nearest = el => { for (let e = el.parentElement; e; e = e.parentElement) if (e.matches(boxes) && visible(e)) return e; return null; };
    for (const el of document.querySelectorAll('.reading-content :is(p,h2,h3,h4,li,figcaption,pre,table,svg,img,.fm-legend,.fm-heading,.blend-label,summary,.node,.pb-paper,.pb-interaction,.pb-controls,.stepper-status)')) {
      const box = nearest(el); if (!box) continue;
      const b = box.getBoundingClientRect(); if (!b.width) continue;
      {
        const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
        const clip = scrolls(el); if (clip && box.contains(clip) && clip !== box) continue;
        if (r.left < b.left - 1 || r.right > b.right + 1) out.issues.push('outside-box ' + (box.className || box.tagName).toString().split(' ')[0] + '>' + (el.className && typeof el.className === 'string' ? el.className.split(' ')[0] : el.tagName.toLowerCase()) + ' "' + (el.textContent || '').trim().slice(0, 40) + '"');
      }
    }
    return out; });
  figs += r.figs; maps += r.maps; labels += r.labels;
  for (const i of r.issues) { const k = i.split(' ')[0]; kinds[k] = (kinds[k] || 0) + 1; if (sample.length < 25) sample.push(p + ' ' + i); }
}
console.log(JSON.stringify({ pages: pages.length, figs, maps, labels, kinds, sample }));
await b.close();
