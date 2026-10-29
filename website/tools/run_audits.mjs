// Drives the six instrumented audit pages headlessly and saves each JSON result.
// Usage: node run_audits.mjs <puppeteer dir> <base url> <out dir> [page ...]
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';

const [, , pptrDir, base, outDir, ...only] = process.argv;
const require = createRequire(path.join(pptrDir, 'package.json'));
const puppeteer = require(pptrDir);
const pages = [
  ['audit.html', 'start', 'qa-results', 'browser.json'],
  ['binder-audit.html', 'binder-start', 'binder-results', 'binder.json'],
  ['motion-fixture.html', 'motion-start', 'motion-results', 'motion.json'],
  ['refinement-audit.html', 'refinement-start', 'refinement-results', 'refinement.json'],
  ['ux-audit.html', 'ux-start', 'ux-results', 'ux.json'],
  ['qa-fixtures.html', 'qa-fixture-start', 'qa-fixture-results', 'qa-tampering.json'],
].filter(p => !only.length || only.includes(p[3]));

fs.mkdirSync(outDir, { recursive: true });
const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
for (const [page, button, pre, file] of pages) {
  const started = Date.now();
  const tab = await browser.newPage();
  await tab.setViewport({ width: 1440, height: 900 });
  await tab.goto(base + page, { waitUntil: 'load', timeout: 120000 });
  await tab.click('#' + button);
  let result = null;
  while (Date.now() - started < 20 * 60 * 1000) {
    await new Promise(r => setTimeout(r, 2000));
    const text = await tab.$eval('#' + pre, el => el.textContent).catch(() => '');
    try { const parsed = JSON.parse(text); if (parsed.done) { result = parsed; break; } } catch { }
  }
  if (!result) { console.log(`${file}: TIMEOUT`); await tab.close(); continue; }
  fs.writeFileSync(path.join(outDir, file), JSON.stringify(result, null, 2) + '\n');
  const ok = result.ok ?? (result.pages ? result.pages.every(p => p.ok) : result.results ? result.results.every(r => r.ok) : !(result.problems || []).length);
  console.log(`${file}: done ok=${ok} in ${Math.round((Date.now() - started) / 1000)}s`);
  await tab.close();
}
await browser.close();
