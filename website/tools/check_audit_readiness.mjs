// Real-browser fault injection for the disposable audit harness.
// node check_audit_readiness.mjs <puppeteer-dir> <qa-base-url> <result-file>
import {createRequire} from 'module';
import fs from 'fs';
import path from 'path';
const [,,lib,base,out]=process.argv;
const puppeteer=createRequire(path.join(lib,'package.json'))(lib);
const browser=await puppeteer.launch({headless:true,args:['--no-sandbox']});
const route='/mobile-system-design/caching-library/';
const checks=[];
try{
 for(const kind of ['normal','missing-app','missing-inspector','missing-source']){
  const page=await browser.newPage();await page.setCacheEnabled(false);
  const response=await page.goto(new URL(route,base).href,{waitUntil:'load'});const html=await response.text();
  let inspectorRequests=0;
  await page.setRequestInterception(true);
  page.on('request',async request=>{
   const url=new URL(request.url());
   if(url.pathname==='/fx/audit.js'){inspectorRequests++;return request.abort();}
   if(kind==='missing-app'&&url.pathname==='/app.js')return request.respond({status:404,contentType:'text/javascript',body:''});
   if(url.pathname===route&&request.resourceType()==='fetch'){
    let body=html;
    if(kind==='missing-inspector')body=body.replace('window.__inspectOriginalContent = ','window.__removedInspector = ');
    if(kind==='missing-source')body=body.replace('data-source="mobile-system-design/caching-library.md"','data-source=""');
    return request.respond({status:200,contentType:'text/html',body});
   }
   return request.continue();
  });
  await page.goto(new URL('/audit.html',base).href,{waitUntil:'load'});
  const started=Date.now();
  const result=await page.evaluate(async route=>{await window.__runAudit([route],[390]);return window.__R;},route);
  const item=result.pages[0],elapsedMs=Date.now()-started;
  const expected={normal:null,'missing-app':'Page resources failed:','missing-inspector':'QA inspector missing','missing-source':'Page source identity missing'}[kind];
  const ok=result.done===true&&result.pages.length===1&&inspectorRequests===0
   &&(expected?item.ok===false&&item.error.includes(expected)&&item.readiness?.route===route&&elapsedMs<30000:item.ok===true&&item.preservation?.problems.length===0)
   &&(kind!=='missing-app'||item.readiness.resourceErrors.some(r=>r.tag==='SCRIPT'&&new URL(r.url).pathname==='/app.js'));
  checks.push({name:kind,ok,elapsedMs,inspectorRequests,page:item});await page.close();
 }
 const ok=checks.length===4&&checks.every(c=>c.ok);
 fs.writeFileSync(out,JSON.stringify({ok,checks,scope:'Headless Chromium; controlled missing reader asset, inspector and source identity. No retries or timeout changes.'},null,2)+'\n');
 if(!ok)throw Error('Readiness regression failed: '+checks.filter(c=>!c.ok).map(c=>c.name).join(', '));
 console.log('PASS audit readiness: '+checks.length+' real-browser fault-injection cases; inspector requests: 0');
}finally{await browser.close();}
