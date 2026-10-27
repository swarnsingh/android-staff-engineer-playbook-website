// Run only in the disposable root-path browser QA copy.
window.runRefinementAudit=async()=>{
  const report={done:false,ok:false,checks:[]},out=document.querySelector('#refinement-results');
  const save=()=>out.textContent=JSON.stringify(report,null,2);
  const check=(name,problems,details={})=>{report.checks.push({name,ok:!problems.length,problems,...details});save()};
  const frame=document.querySelector('iframe'),tick=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  async function load(route,width=390){frame.style.width=width+'px';const response=await fetch(route);if(!response.ok)throw Error(route+' HTTP '+response.status);const html=await response.text();frame.srcdoc=html;await new Promise(r=>frame.onload=r);await frame.contentDocument.fonts.ready;await tick();return {d:frame.contentDocument,w:frame.contentWindow,html}}
  try{
    for(const route of ['/','/design-system/']){
      const {d,w}=await load(route);
      for(const width of [320,390,768,1181,1280,1439,1440])for(const theme of ['light','dark','sepia','contrast']){
        frame.style.width=width+'px';d.documentElement.dataset.theme=theme;await tick();
        const problems=[];if(d.documentElement.scrollWidth>d.documentElement.clientWidth+1)problems.push('page overflow');
        if(!d.querySelector('h1')?.textContent.trim())problems.push('missing heading');
        if(d.querySelector('.pb-error'))problems.push('scene initialization failure');
        check(route+' '+width+' '+theme,problems);
      }
      const links=[...d.querySelectorAll('a[href]')].map(a=>new URL(a.getAttribute('href'),location.origin+route));
      const invalid=[];for(const url of links.filter(u=>u.origin===location.origin)){const response=await fetch(url.pathname);if(!response.ok)invalid.push(url.pathname+' HTTP '+response.status)}
      check(route+' navigation',invalid);
    }
    for(const route of ['/android/compose/form-factors-matrix/','/android/kotlin-multiplatform/kmp-decision-matrix/','/android/networking-and-security/ktor-vs-retrofit/']){
      const {d}=await load(route);const maps=[...d.querySelectorAll('.decision-map')];
      check(route+' static decision map',maps.length!==1?['expected one static diagram']:maps.flatMap(m=>[...(m.querySelector('button')?['unexpected playback controls']:[]),...([...m.querySelectorAll('.decision-card')].some(c=>!c.querySelector('p')?.textContent.trim())?['missing authored explanation']:[])]),{cards:d.querySelectorAll('.decision-card').length});
    }
    for(const route of ['/android/os-internals/the-binder/','/android/concurrency/shared-flow-and-state-flow/']){
      const {d,w,html}=await load(route);const source=new DOMParser().parseFromString(html,'text/html');
      const expected=[...source.querySelectorAll('code.highlight')].map(c=>c.textContent),actual=[...d.querySelectorAll('code.highlight')].map(c=>c.textContent);
      check(route+' code text preservation',JSON.stringify(expected)===JSON.stringify(actual)?[]:['code changed during highlighting'],{blocks:actual.length,annotations:d.querySelectorAll('.syntax-annotation').length,types:d.querySelectorAll('.syntax-type').length});
      for(const view of ['content','qa']){
        w.setView(view,{writeHistory:false,restore:false});w.scrollTo(0,0);await tick();const bar=d.querySelector('.reading-progress'),start=Number(bar.getAttribute('aria-valuenow'));
        w.scrollTo(0,d.documentElement.scrollHeight);await tick();const end=Number(bar.getAttribute('aria-valuenow'));
        check(route+' '+view+' reading position',start===0&&end===100?[]:['expected position 0 to 100'],{start,end});
      }
      w.setView('content',{writeHistory:false,restore:false});await tick();
      const small=[...d.querySelectorAll('.pb-btn,.pb-step-jump,.stepper-controls button,.pb-modes button')].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().height<47.9).map(e=>e.textContent.trim());
      check(route+' phone control targets',small.map(s=>'short control: '+s));
    }
  }catch(e){check('runner',[String(e)])}
  report.done=true;report.ok=report.checks.every(c=>c.ok);save();
};
