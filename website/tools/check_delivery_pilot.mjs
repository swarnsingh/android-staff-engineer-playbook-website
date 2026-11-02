// Focused browser regression: manual progression, responsive state, keyboard, Q&A, source links and no-JS fallback.
// Usage: node website/tools/check_delivery_pilot.mjs <puppeteer-dir> <base-url> <review-dir>
import {createRequire} from 'module';
import fs from 'fs';
import path from 'path';
const [,,dir,base,out]=process.argv;
const puppeteer=createRequire(path.join(dir,'package.json'))(dir);
const browser=await puppeteer.launch({headless:true,args:['--no-sandbox']});
fs.mkdirSync(out,{recursive:true});
const page=await browser.newPage();
const checks=[];
async function check(name,body){const ok=await body();checks.push({name,ok:!!ok});if(!ok)throw new Error(name);}
try {
 await page.setViewport({width:1440,height:1000});
 await page.goto(base+'distributed-systems/delivery-semantics/',{waitUntil:'networkidle0'});
 await page.waitForSelector('.pb-node');
 const scene='[data-pb-flow="scene"]';
 await check('manual mode exposes no Play control',()=>page.$eval(scene,e=>e.querySelector('[data-act=play]').hidden&&e.querySelector('[data-act=play]').disabled));
 await page.focus(scene+' [data-act=next]');
 for(let i=0;i<6;i++)await page.keyboard.press('Enter');
 await check('last step retains focus and stops advancing',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 7 of 7'&&e.querySelector('[data-act=next]')===document.activeElement&&e.querySelector('[data-act=next]').getAttribute('aria-disabled')==='true'));
 await page.keyboard.press('Enter');
 await check('two deliveries leave one local effect and sender confirmed',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 7 of 7'&&e.textContent.includes('deliveries: 2')&&e.textContent.includes('effects: 1; R42')&&e.textContent.includes('M42 confirmed')&&!e.classList.contains('is-moving')));
 await page.$eval(scene,e=>e.scrollIntoView());
 await page.screenshot({path:path.join(out,'desktop.png'),fullPage:false});
 await (await page.$(scene)).screenshot({path:path.join(out,'desktop-scene.png')});
 await page.setViewport({width:390,height:1000});
 await page.waitForFunction(()=>document.querySelector('[data-pb-flow=scene] svg').dataset.layout==='narrow');
 await check('phone resize preserves the selected state',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 7 of 7'&&e.textContent.includes('effects: 1; R42')));
 await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
 await page.click(scene+' [data-act=reset]');
 await page.click(scene+' [data-act=next]');
 await check('reduced motion preserves manual transitions with no animation',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 2 of 7'&&!e.classList.contains('is-moving')&&!e.querySelector('.pb-packets')?.children.length));
 await page.$eval(scene,e=>e.scrollIntoView({block:'start'}));
 await page.evaluate(()=>scrollBy(0,-210));
 await page.screenshot({path:path.join(out,'phone-scene.png')});
 await page.$eval(scene+' .pb-interaction',e=>e.scrollIntoView({block:'center'}));
 await page.screenshot({path:path.join(out,'phone-controls.png')});
 await check('phone has no page horizontal overflow',()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await page.click('#tab-qa');
 await check('all original answers remain open and adjacent',()=>page.evaluate(()=>{const q=document.querySelectorAll('#section-probing-questions > ol > li');return q.length===10&&[...q].every(e=>e.querySelector('.qa-answer-pair')&&!e.querySelector('.qa-answer-pair details'))&&document.querySelector('#section-answer-key').textContent.includes('Scope the original answers');}));
 await page.goto(base+'distributed-systems/',{waitUntil:'networkidle0'});
 await check('unconverted chapter source links use approved canonical revision',()=>page.evaluate(()=>[...document.querySelectorAll('a[href*="cap-theorem.md"]')].some(a=>a.href.includes('android-staff-engineer-playbook/blob/fb8354edb079e901edf18710ca9388a124712a5b/'))));
 const staticPage=await browser.newPage();await staticPage.setJavaScriptEnabled(false);
 await staticPage.goto(base+'distributed-systems/delivery-semantics/',{waitUntil:'load'});
 await check('no-JS fallback has all seven steps, original text and answers',()=>staticPage.evaluate(()=>document.querySelectorAll('.pb-steps ol > li').length===7&&document.querySelector('#section-answer-key')?.textContent.includes('Two Generals')&&document.querySelector('#section-internal-mechanics')?.textContent.includes('class IdempotentConsumer')));
 await staticPage.close();
} finally {
 fs.writeFileSync(path.join(out,'pilot-browser.json'),JSON.stringify({checks,ok:checks.every(c=>c.ok),browser:await browser.version(),limits:'Headless Chromium viewport emulation only; no physical device, screen reader or other browser engine.'},null,2)+'\n');
 await browser.close();
}
console.log('PASS focused pilot browser: '+checks.length+' checks');
