// Drives the six instrumented audit pages headlessly and saves each JSON result.
// Usage: node run_audits.mjs <puppeteer dir> <base url> <out dir> [page ...]
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';

const [, , pptrDir, base, outDir, ...only] = process.argv;
const pages = [
  ['audit.html', 'start', 'qa-results', 'browser.json'],
  ['binder-audit.html', 'binder-start', 'binder-results', 'binder.json'],
  ['motion-fixture.html', 'motion-start', 'motion-results', 'motion.json'],
  ['refinement-audit.html', 'refinement-start', 'refinement-results', 'refinement.json'],
  ['ux-audit.html', 'ux-start', 'ux-results', 'ux.json'],
  ['qa-fixtures.html', 'qa-fixture-start', 'qa-fixture-results', 'qa-tampering.json'],
].filter(p => !only.length || only.includes(p[3]));

function passed(result) {
  const checks = result.pages ?? result.checks ?? result.results;
  return result.done === true && (result.ok === undefined || result.ok === true) && !result.error
    && Array.isArray(checks) && checks.length > 0 && checks.every(c => c?.ok === true)
    && !(result.problems || []).length;
}

let browser;
let failed = false;
try {
  if (!pptrDir || !base || !outDir || !pages.length) {
    throw new Error('Usage: run_audits.mjs <puppeteer dir> <base url> <out dir> [known result file ...]');
  }
  fs.mkdirSync(outDir, { recursive: true });
  // A failed launch or timeout must never leave an older success as this run's evidence.
  for (const [, , , file] of pages) fs.rmSync(path.join(outDir, file), { force: true });
  const require = createRequire(path.join(pptrDir, 'package.json'));
  const puppeteer = require(pptrDir);
  browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  for (const [page, button, pre, file] of pages) {
    const started = Date.now();
    let tab;
    let result;
    try {
      tab = await browser.newPage();
      await tab.setViewport({ width: 1440, height: 900 });
      await tab.goto(base + page, { waitUntil: 'load', timeout: 120000 });
      await tab.click('#' + button);
      while (Date.now() - started < 20 * 60 * 1000) {
        await new Promise(r => setTimeout(r, 2000));
        const text = await tab.$eval('#' + pre, el => el.textContent).catch(() => '');
        try { const parsed = JSON.parse(text); if (parsed?.done === true) { result = parsed; break; } } catch { }
      }
      if (!result) throw new Error('TIMEOUT: audit did not finish within 20 minutes');
    } catch (error) {
      result = { done: false, ok: false, error: String(error) };
    } finally {
      try { if (tab) await tab.close(); }
      catch (error) { failed = true; console.error(`${file}: closing page: ${error}`); }
    }
    fs.writeFileSync(path.join(outDir, file), JSON.stringify(result, null, 2) + '\n');
    const ok = passed(result);
    failed ||= !ok;
    console.log(`${file}: done ok=${ok} in ${Math.round((Date.now() - started) / 1000)}s`);
    if (result.error) console.error(`${file}: ${result.error}`);
    for (const pageResult of result.pages || []) {
      if (pageResult.ok !== true) console.error(`${file}: ${pageResult.href}: ${pageResult.error || 'page checks failed; see JSON evidence'}`);
    }
  }
} catch (error) {
  failed = true;
  console.error(`Audit runner: ${error.stack || error}`);
} finally {
  try { if (browser) await browser.close(); }
  catch (error) { failed = true; console.error(`Closing audit browser: ${error}`); }
}
process.exitCode = failed ? 1 : 0;
