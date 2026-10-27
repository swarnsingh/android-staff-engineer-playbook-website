// Disposable QA only. Exercise the actual shared reader controls in isolated frames.
window.runUXAudit = async () => {
  const report={done:false,ok:false,checks:[]},out=document.querySelector('#ux-results');
  const save=()=>out.textContent=JSON.stringify(report,null,2);
  const check=(name,ok,details={})=>{report.checks.push({name,ok,...details});save();};
  let frame=document.querySelector('iframe');
  const tick=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  async function load(route,width=390){
    frame.style.width=width+'px';
    const response=await fetch(route);if(!response.ok)throw Error(route+' HTTP '+response.status);
    const loaded=new Promise(r=>frame.onload=r);frame.srcdoc=await response.text();await loaded;
    await frame.contentDocument.fonts.ready;await tick();
    // srcdoc has no navigable URL. Keep this fixture's tab/keyboard checks isolated
    // from History; real route/query behavior is checked in a top-level browser tab.
    const readerSetView=frame.contentWindow.setView;
    frame.contentWindow.setView=(view,options={})=>readerSetView(view,{...options,writeHistory:false});
    return {d:frame.contentDocument,w:frame.contentWindow};
  }
  const visible=e=>!!e?.getClientRects().length;
  const routes=['/kotlin/','/android/','/android/architecture/activity/','/kotlin/language-core/variables/','/kotlin/coroutines-and-flow/coroutines/','/android/os-internals/the-binder/','/android/data-and-di/health-connect/'];
  try{
    for(const route of routes){
      const {d,w}=await load(route),path=d.body.dataset.pageKind==='learning-path';
      check(route+' ready',!(w.__qaErrors||[]).length,{errors:w.__qaErrors||[]});
      check(route+' page controls',path?!d.querySelector('.lesson-tabs,#bookmark,#panel-qa,#panel-playground'):!!d.querySelector('#bookmark'));
      check(route+' no draft or empty states',!d.querySelector('#qa-empty')&&!d.querySelector('.lesson-footer').textContent.includes('reader draft'));
      check(route+' no correction notices in lesson',!d.querySelector('#panel-content .correction-note,#panel-qa .correction-note,#panel-content .correction-mark,#panel-qa .correction-mark'));
      if(path){
        const phaseLinks=[...d.querySelectorAll('.path-phase-grid a')];
        check(route+' phase destinations',phaseLinks.length===(route==='/android/'?9:6)&&phaseLinks.every(a=>d.getElementById(a.hash.slice(1))));
      }
      const nav=d.querySelector('#topic-nav');
      check(route+' current track default',nav.querySelectorAll(':scope > details').length===1&&d.querySelector('.navigation-scope button').getAttribute('aria-pressed')==='true');
      d.querySelector('#menu-toggle').focus();d.querySelector('#menu-toggle').click();await tick();
      check(route+' curriculum focus',d.querySelector('#curriculum-dialog').open&&d.querySelector('#curriculum-dialog').contains(d.activeElement));
      const scope=d.querySelectorAll('.navigation-scope button');scope[1].click();
      check(route+' full catalog explicit',nav.querySelectorAll(':scope > details').length>2&&scope[1].getAttribute('aria-pressed')==='true');
      scope[0].click();const search=d.querySelector('#topic-search');search.value='zzzx-no-topic';search.dispatchEvent(new w.Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,220));
      check(route+' scoped empty search',!d.querySelector('#search-empty').hidden&&d.querySelector('#search-status').textContent.includes('0 matching'));
      search.value='';search.dispatchEvent(new w.Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,220));d.querySelector('#close-curriculum').click();await tick();
      check(route+' curriculum restores focus',!d.querySelector('#curriculum-dialog').open&&d.activeElement.id==='menu-toggle');
      d.querySelector('#reading-settings-toggle').click();await tick();
      check(route+' settings available',d.querySelector('#reading-dialog').open);
      d.querySelector('#close-reading-dialog').click();await tick();
      const tabs=[...d.querySelectorAll('.lesson-tabs [role=tab]')];
      for(const tab of tabs){
        tab.click();await tick();const panel=d.getElementById(tab.getAttribute('aria-controls'));
        check(route+' '+tab.id+' works',tab.getAttribute('aria-selected')==='true'&&visible(panel));
        if(tab.id==='tab-qa')check(route+' populated practice',!!d.querySelector('#practice-questions').children.length);
        if(tab.id==='tab-qa'){
          const paired=[...d.querySelectorAll('[data-qa-question-index]')];
          check(route+' answers beside original questions',paired.every((question,index)=>{const answer=question.querySelector(':scope > .qa-answer-pair > ol > li');return answer&&Number(answer.dataset.originalAnswerIndex)===index+1&&visible(answer)}));
          check(route+' checkpoint answers visible',[...d.querySelectorAll('#panel-qa .blend[data-kind="check"] details')].every(detail=>detail.open));
          if(route.includes('health-connect')){
            const guidance=[...d.querySelectorAll('[data-guidance-question-index]')];
            check(route+' all five guidance answers paired',guidance.length===5&&guidance.every((question,index)=>question.querySelector(':scope > .qa-answer-pair [data-guidance-answer-index="'+(index+1)+'"] .blend[data-guidance-answer-for]')));
          }
        }
      }
      if(tabs.length>1){
        tabs[0].focus();tabs[0].dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));
        check(route+' tab keyboard',d.activeElement===tabs[1]&&tabs[1].getAttribute('aria-selected')==='true');
      }
      w.setView('content',{writeHistory:false,restore:false});
      const question=d.querySelector('#panel-qa [id]');
      if(question){w.setView('content',{anchor:question.id,writeHistory:false});check(route+' question anchor selects QA',!d.querySelector('#panel-qa').hidden);w.setView('content',{writeHistory:false,restore:false});}
      const invalid=[];
      for(const a of d.querySelectorAll('.path-actions a,.chapter-navigation a')){
        if(a.hash){if(!d.getElementById(a.hash.slice(1)))invalid.push(a.getAttribute('href'));}
        else if(!(await fetch(a.getAttribute('href'))).ok)invalid.push(a.getAttribute('href'));
      }
      check(route+' next/start destinations',!invalid.length,{invalid});
      check(route+' interaction errors',!(w.__qaErrors||[]).length,{errors:w.__qaErrors||[]});
      for(const width of [320,390,768,1440])for(const theme of ['light','dark','sepia','contrast']){
        frame.style.width=width+'px';d.documentElement.dataset.theme=theme;await tick();
        check(route+' geometry '+width+' '+theme,d.documentElement.scrollWidth<=d.documentElement.clientWidth+1);
      }
      frame.style.width='1440px';await tick();
      const focus=d.querySelector('#focus-toggle');focus.click();await tick();
      const topics=d.querySelector('#menu-toggle');
      check(route+' desktop focus keeps topics',visible(topics));
      topics.focus();topics.click();await tick();
      check(route+' desktop focus opens curriculum',d.querySelector('#curriculum-dialog').open);
      d.querySelector('#close-curriculum').click();await tick();
      check(route+' desktop focus restores opener',d.activeElement===topics);
      focus.click();await tick();
      check(route+' desktop exit focus restores rail',!d.querySelector('#curriculum-dialog').open&&d.querySelector('#sidebar-slot').contains(d.querySelector('#curriculum')));
      frame.style.width='390px';await tick();
      const short=[...d.querySelectorAll('.pb-btn,.stepper-controls button,.path-actions a,.navigation-scope button')].filter(visible).filter(e=>e.getBoundingClientRect().height<43.9).map(e=>e.textContent.trim());
      check(route+' touch controls',!short.length,{short});
    }
    // Verify lesson identity rather than a global saved flag, restoring the real device preference.
    const prior=localStorage.getItem('playbook-reader-v1');
    try{
      const pref=JSON.parse(prior||'{}');pref.savedLessons={};localStorage.setItem('playbook-reader-v1',JSON.stringify(pref));
      let page=await load(routes[2]);page.d.querySelector('#bookmark').click();
      check('save selected lesson',page.d.querySelector('#bookmark').getAttribute('aria-pressed')==='true');
      page=await load(routes[3]);check('other lesson remains unsaved',page.d.querySelector('#bookmark').getAttribute('aria-pressed')==='false');
      page=await load(routes[2]);check('saved lesson survives revisit',page.d.querySelector('#bookmark').getAttribute('aria-pressed')==='true');
    }finally{if(prior===null)localStorage.removeItem('playbook-reader-v1');else localStorage.setItem('playbook-reader-v1',prior);}
  }catch(e){check('runner',false,{error:String(e)});}
  report.done=true;report.ok=report.checks.every(c=>c.ok);save();
};
