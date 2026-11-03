// Review regressions: moving/lost packets, compared effects and visible controls at phone/tablet sizes.
// Usage: node website/tools/check_delivery_pilot.mjs <puppeteer-dir> <base-url> <review-dir>
import {createRequire} from 'module';
import fs from 'fs';
import path from 'path';
const [,,dir,base,out]=process.argv;
const puppeteer=createRequire(path.join(dir,'package.json'))(dir);
const browser=await puppeteer.launch({headless:true,args:['--no-sandbox']});
fs.mkdirSync(out,{recursive:true});
const page=await browser.newPage(),checks=[],geometry=[];
const scene='[data-pb-flow="scene"]',next=scene+' [data-act=next]',select=scene+' .pb-step-select';
const runtimeErrors=[],auxiliaryErrors=[];page.on('pageerror',e=>runtimeErrors.push(String(e)));page.on('console',m=>{
 if(m.type()==='error'){
  const url=m.location().url || '';
  (url.endsWith('/favicon.ico')?auxiliaryErrors:runtimeErrors).push({text:m.text(),url});
 }
});
async function lossMarked(){return page.$eval(scene,e=>{
 const edge=e.querySelector('.pb-edge.stuck'),id=edge?.getAttribute('marker-end')?.match(/#([^)]*)/)[1];
 const marker=id&&document.getElementById(id),cross=marker?.querySelector('.pb-loss');
 return !!cross&&getComputedStyle(cross).stroke!=='none'&&getComputedStyle(cross).fill==='none'&&!e.querySelector('.pb-pk');
});}
async function check(name,body){const ok=await body();checks.push({name,ok:!!ok});if(!ok)throw new Error(name);}
async function chooseMode(mode){const button=scene+' [data-mode='+mode+']';await page.$eval(button,e=>e.scrollIntoView({block:'center'}));await page.click(button);await page.waitForFunction(mode=>document.querySelector('[data-mode='+mode+']').getAttribute('aria-pressed')==='true',{},mode);}
async function settled(){await page.waitForFunction(()=>!document.querySelector('[data-pb-flow=scene]').classList.contains('is-moving'));}
async function visibleWork(){return page.$eval(scene,e=>{
 const sticky=[...document.querySelectorAll('.topbar,.lesson-tabs,.mobile-outline')].filter(e=>getComputedStyle(e).position==='sticky');
 const header=Math.max(0,...sticky.map(e=>e.getBoundingClientRect().bottom));
 const boxes=[...e.querySelectorAll('.pb-node,.pb-caption,.pb-controls')].map(e=>{const r=e.getBoundingClientRect();return {label:e.classList.contains('pb-node')?e.textContent:e.className,top:r.top,bottom:r.bottom};});
 return {width:innerWidth,height:innerHeight,paperHeight:e.querySelector('.pb-paper').getBoundingClientRect().height,step:e.querySelector('.pb-count').textContent,mode:e.querySelector('[data-mode][aria-pressed=true]').dataset.mode,header,boxes,ok:boxes.every(r=>r.top>=header-1&&r.bottom<=innerHeight+1)};
});}
try{
 await page.setViewport({width:1024,height:768});
 await page.goto(base+'distributed-systems/delivery-semantics/',{waitUntil:'networkidle0'});
 await page.waitForSelector('.pb-node');
 await check('manual advancement has no automatic Play control',()=>page.$eval(scene,e=>e.querySelector('[data-act=play]').hidden&&e.querySelector('[data-act=play]').disabled));
 await check('help names the step dropdown',()=>page.$eval(scene,e=>e.querySelector('.pb-guide').textContent.includes('the step dropdown')&&!e.querySelector('.pb-guide').textContent.includes('a numbered step')));
 await page.$eval(next,e=>e.scrollIntoView({block:'end'}));
 await page.click(next);
 await page.waitForSelector('.pb-pk');
 const first=await page.$eval('.pb-pk',e=>e.getAttribute('transform'));
 await page.waitForFunction(t=>{const p=document.querySelector('.pb-pk');return p&&p.getAttribute('transform')&&p.getAttribute('transform')!==t;},{},first);
 await check('Next moves a labelled message on the send path',()=>page.$eval(scene,e=>e.classList.contains('is-moving')&&e.querySelector('.pb-pk')?.textContent==='M42'&&!!e.querySelector('.pb-edge.fwd.moving')));
 await settled();
 await page.select(select,'2');
 await check('native step selection reaches the requested state',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 3 of 7'&&e.querySelector('svg').textContent.includes('effects: 1; R42')));
 await page.click(next);await page.waitForSelector('.pb-pk.stuck');
 await page.waitForFunction(()=>Number(document.querySelector('.pb-pk.stuck')?.getAttribute('opacity'))>.9);
 await check('lost acknowledgement moves on a warning path that stops before the sender',()=>page.$eval(scene,e=>{
  const edge=e.querySelector('.pb-edge.stuck'),data=JSON.parse(e.querySelector('script').textContent),L=data.layouts[e.querySelector('svg').dataset.layout],n=L.nodes.sender;
  const end=edge.getPointAtLength(edge.getTotalLength());
  return e.querySelector('.pb-pk.stuck').textContent==='R42 lost'&&!(end.x>=n.x&&end.x<=n.x+n.w&&end.y>=n.y&&end.y<=n.y+n.h);
 }));
 await page.screenshot({path:path.join(out,'lost-reply.png')});await settled();
 await check('lost reply retains a visible cross after its packet disappears',lossMarked);
 await page.screenshot({path:path.join(out,'lost-reply-settled.png')});
 await check('lost reply leaves sender uncertain after one committed effect',()=>page.$eval(scene,e=>e.querySelector('svg').textContent.includes('outcome unknown')&&e.querySelector('svg').textContent.includes('effects: 1; R42')));
 await page.select(select,'6');
 await chooseMode('unsafe');
 await check('comparison retains step and shows two deliveries with two effects',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 7 of 7'&&e.querySelector('svg').textContent.includes('deliveries: 2')&&e.querySelector('svg').textContent.includes('effects: 2; R43')));
 await chooseMode('retry');
 await check('same-step comparison restores one effect and original result',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 7 of 7'&&e.querySelector('svg').textContent.includes('effects: 1; R42')&&!e.querySelector('svg').textContent.includes('effects: 2; R43')));
 await page.focus(next);await page.keyboard.press('Enter');
 await check('last step retains keyboard focus and stops advancing',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 7 of 7'&&e.querySelector('[data-act=next]')===document.activeElement&&e.querySelector('[data-act=next]').getAttribute('aria-disabled')==='true'));
 await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
 await page.select(select,'0');await page.click(next);
 await check('reduced motion retains transfer highlighting without a travelling packet',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 2 of 7'&&!e.classList.contains('is-moving')&&!e.querySelector('.pb-pk')&&!!e.querySelector('.pb-edge.fwd')));
 await chooseMode('unsafe');await page.select(select,'1');
 await check('duplicate run delivery caption explicitly omits the replay record',()=>page.$eval(scene,e=>e.querySelector('.pb-caption').textContent.includes('keeps no replay record')&&!e.querySelector('.pb-caption').textContent.includes('bind the payload')));
 for(const [width,height] of [[375,812],[1024,768],[1280,900]]){
  await page.setViewport({width,height});
  // Each mode starts with one scroll to its controls; subsequent keyboard steps must keep the work visible.
  for(const mode of ['retry','unsafe']){
   await chooseMode(mode);await page.select(select,'0');
   await page.$eval(next,e=>e.scrollIntoView({block:'end'}));await page.focus(next);
   for(let i=0;i<7;i++){
    if(i)await page.keyboard.press('Enter');
    const g=await visibleWork();geometry.push(g);
    await check(width+'×'+height+' '+mode+' step '+(i+1)+' keeps every actor, caption and control in view',()=>g.ok);
    if(i===3){
     await check(width+'px '+mode+' reduced-motion lost step retains cross',lossMarked);
     await page.screenshot({path:path.join(out,width+'-'+mode+'-loss.png')});
    }
   }
   await page.screenshot({path:path.join(out,width+'-'+mode+'.png')});
  }
  await check(width+'px has no page horizontal overflow',()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 }
 await page.setViewport({width:320,height:768});
 await check('320px remains bounded without page overflow',()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await page.select(select,'3');await page.setViewport({width:1440,height:1000});
 await check('resize retains mode and selected step',()=>page.$eval(scene,e=>e.querySelector('.pb-count').textContent==='Step 4 of 7'&&e.querySelector('[data-mode=unsafe]').getAttribute('aria-pressed')==='true'));
 await check('direct selection and resize retain the lost-reply cross',lossMarked);
 await page.select(select,'4');
 await check('selecting another step clears the lost marker from every edge',()=>page.$eval(scene,e=>![...e.querySelectorAll('.pb-edge')].some(p=>p.getAttribute('marker-end').includes('hlost'))));
 await page.click('#tab-qa');
 await check('ten original answer pairs stay open with forward-looking scope guidance',()=>page.evaluate(()=>{const q=document.querySelectorAll('#section-probing-questions > ol > li');return q.length===10&&[...q].every(e=>e.querySelector('.qa-answer-pair')&&!e.querySelector('.qa-answer-pair details'))&&document.querySelector('#section-answer-key').textContent.includes('As you read the answers');}));
 const staticPage=await browser.newPage();await staticPage.setJavaScriptEnabled(false);
 await staticPage.goto(base+'distributed-systems/delivery-semantics/',{waitUntil:'load'});
 await check('no-JS fallback includes both seven-step runs and original answers',()=>staticPage.evaluate(()=>document.querySelectorAll('[data-pb-flow=scene] ol > li').length===14&&document.querySelector('#section-answer-key').textContent.includes('Two Generals')&&[...document.querySelectorAll('[data-pb-flow=scene] ol > li')].some(e=>e.textContent.includes('Deliveries: 2; effects: 2.'))));
 await staticPage.close();
 await check('preview has no application console or runtime errors (favicon excluded)',()=>runtimeErrors.length===0);
}finally{
 fs.writeFileSync(path.join(out,'pilot-browser.json'),JSON.stringify({checks,geometry,runtimeErrors,auxiliaryErrors,ok:checks.length>0&&checks.every(c=>c.ok),browser:await browser.version(),limits:'Headless Chromium emulation only. Default reading size at specified viewport sizes; no physical device or screen-reader certification. The local server has no favicon; that request is recorded separately.'},null,2)+'\n');
 await browser.close();
}
console.log('PASS focused pilot browser: '+checks.length+' checks');
