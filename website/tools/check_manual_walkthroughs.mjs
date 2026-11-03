// Check the reader's actual view and keyboard navigation across a complete topic.
// node ... <puppeteer-dir> <base-url> <tree> <review-dir>
import {createRequire} from 'module';
import fs from 'fs';
import path from 'path';
const [,,lib,base,tree,out]=process.argv;
const puppeteer=createRequire(path.join(lib,'package.json'))(lib);
const browser=await puppeteer.launch({headless:true,args:['--no-sandbox']});
const checks=[],geometry=[],errors=[],pages=[];
fs.mkdirSync(out,{recursive:true});
const sc='[data-pb-flow="scene"]';
function check(name,ok){checks.push({name,ok:!!ok});if(!ok)throw Error(name);}
const page=await browser.newPage();
page.on('pageerror',e=>errors.push(String(e)));
page.on('console',m=>{if(m.type()==='error'&&!(m.location().url||'').endsWith('/favicon.ico'))errors.push(m.text());});
async function settle(){await page.waitForFunction(s=>!document.querySelector(s).classList.contains('is-moving'),{},sc);}
const known={
 'idempotency':{retained:'effects: 1',pruned:'effects: 2'},
 'mobile-client-consistency-contracts':{version:'visible v8',arrival:'visible v7'},
 'vector-clocks':{causal:'siblings x1,x2',arrival:'only x2 retained'},
 'crdts':{components:'total 2',scalar:'scalar total 1'},
 'consensus-basics':{majority:'X committed',isolated:'X uncommitted'},
 'replication-and-leader-election':{fenced:'value 8',unchecked:'value 7: regressed'},
 'delivery-semantics':{retry:'effects: 1; R42',unsafe:'effects: 2; R43'}
};
try{
 const routes=fs.readdirSync('website/dist/'+tree,{withFileTypes:true}).filter(x=>x.isDirectory()).map(x=>x.name);
 for(const slug of routes){
  const route=tree+'/'+slug+'/';await page.setViewport({width:1280,height:900});
  await page.goto(base+route,{waitUntil:'networkidle0'});
  if(!await page.$(sc))continue;
  const data=await page.$eval(sc,e=>JSON.parse(e.querySelector('script').textContent));
  if(data.playback!=='manual'||!data.responsive)continue;
  pages.push(route);const select=sc+' select',next=sc+' [data-act=next]';
  check(route+' has two comparable runs',Object.keys(data.modes).length>=2&&data.compareAtCurrentStep);
  const firstMode=Object.keys(data.modes)[0];
  // An explicit Next really moves a packet, rather than merely tinting a path.
  await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'no-preference'}]);
  await page.select(select,'0');
  for(let i=1;i<data.modes[firstMode].steps.length;i++){
   if(!data.modes[firstMode].steps[i].packets?.length)continue;
   await page.select(select,String(i-1));await page.$eval(next,e=>e.scrollIntoView({block:'end'}));await page.click(next);
   await page.waitForSelector(sc+' .pb-pk');
   const initial=await page.$eval(sc+' .pb-pk',e=>e.getAttribute('transform'));
   await page.waitForFunction(([s,t])=>{const p=document.querySelector(s+' .pb-pk');return p?.getAttribute('transform')&&p.getAttribute('transform')!==t;},{},[sc,initial]);
   check(route+' animates a declared transfer',await page.$eval(sc,e=>e.classList.contains('is-moving')));await settle();
  }
  await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
  for(const [width,height] of [[375,812],[1024,768],[1280,900]]){
   await page.setViewport({width,height});
   for(const [mode,run] of Object.entries(data.modes)){
    await page.$eval(sc+' [data-mode='+mode+']',e=>e.click());await page.select(select,'0');
    await page.$eval(next,e=>e.scrollIntoView({block:'end'}));await page.focus(next);
    for(let i=0;i<run.steps.length;i++){
     if(i)await page.keyboard.press('Enter');
     const g=await page.$eval(sc,e=>{
      const header=Math.max(0,...[...document.querySelectorAll('.topbar,.lesson-tabs,.mobile-outline')].filter(e=>getComputedStyle(e).position==='sticky').map(e=>e.getBoundingClientRect().bottom));
      const boxes=[...e.querySelectorAll('.pb-node,.pb-caption,.pb-controls')].map(e=>{const r=e.getBoundingClientRect();return {top:r.top,bottom:r.bottom,text:e.textContent};});
      const labels=[...e.querySelectorAll('.pb-label,.pb-region text')].map(e=>e.getBoundingClientRect());
      const labelOverlap=labels.some((a,i)=>labels.slice(i+1).some(b=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1));
      return {header,boxes,labelOverlap,ok:boxes.every(r=>r.top>=header-1&&r.bottom<=innerHeight+1),focused:e.querySelector('[data-act=next]')===document.activeElement,moving:e.classList.contains('is-moving'),packets:e.querySelectorAll('.pb-pk').length};
     });
     geometry.push({route,mode,width,height,step:i+1,...g});
     check(route+' '+mode+' '+width+' step '+(i+1)+' fits with stable focus',g.ok&&g.focused&&!g.moving&&!g.packets);
     check(route+' '+mode+' '+width+' step '+(i+1)+' labels do not overlap',!g.labelOverlap);
     if(run.steps[i].packets?.some(p=>p.lost)){
      const loss=await page.$eval(sc,e=>!![...e.querySelectorAll('.pb-edge')].find(p=>p.getAttribute('marker-end')?.includes('hlost')));
      check(route+' '+mode+' '+width+' settled loss remains marked',loss);
     }
    }
    const expected=known[slug]?.[mode];
    if(expected)check(route+' '+mode+' shows the intended final outcome',await page.$eval(sc,(e,t)=>e.querySelector('svg').textContent.includes(t),expected));
    if(width===375||width===1280)await page.screenshot({path:path.join(out,slug+'-'+width+'-'+mode+'.png')});
   }
   check(route+' '+width+' has no page overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  }
  const last=data.modes[Object.keys(data.modes).at(-1)].steps.length-1;
  await page.$eval(sc+' [data-mode='+firstMode+']',e=>e.click());
  check(route+' comparison retains the selected step',await page.$eval(select,(e,i)=>Number(e.value)===i,last));
  await page.setViewport({width:320,height:768});
  check(route+' 320px has no page overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  const staticPage=await browser.newPage();await staticPage.setJavaScriptEnabled(false);await staticPage.goto(base+route,{waitUntil:'load'});
  check(route+' static transcript retains every run',await staticPage.$$eval(sc+' ol > li',e=>e.length)===Object.values(data.modes).reduce((n,r)=>n+r.steps.length,0));
  await staticPage.close();
 }
 check(tree+' includes the expected walkthroughs',pages.length>=Object.keys(known).filter(s=>fs.existsSync('website/dist/'+tree+'/'+s+'/index.html')).length);
 check(tree+' has no application console or runtime errors',errors.length===0);
}finally{
 fs.writeFileSync(path.join(out,'manual-walkthroughs.json'),JSON.stringify({ok:checks.length>0&&checks.every(c=>c.ok),checks,geometry,pages,errors,limits:'Headless Chromium; default reading size. Favicon 404 is excluded. No physical-device, network or service integration certification.'},null,2)+'\n');
 await browser.close();
}
console.log('PASS manual walkthroughs: '+pages.length+' pages, '+checks.length+' checks, '+geometry.length+' visible states');
