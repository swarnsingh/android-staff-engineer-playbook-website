// Disposable full-lesson matrix. Original Content and Q&A are inspected separately by the page sweep.
window.runBinderAudit = async () => {
  const result={done:false,checks:[],problems:[]}, output=document.getElementById('binder-results');
  const frame=document.getElementById('binder-frame');
  await new Promise((resolve,reject)=>{frame.onload=resolve;frame.onerror=reject;frame.src='/android/os-internals/the-binder/';});
  const d=frame.contentDocument,w=frame.contentWindow;
  const tick=()=>new Promise(resolve=>w.requestAnimationFrame(()=>w.requestAnimationFrame(()=>w.requestAnimationFrame(resolve))));
  const scene=d.querySelector('[data-pb-flow=scene]');
  const fonts={sans:'Inter,sans-serif',serif:'"Source Serif 4",serif',times:'"Times New Roman",serif',hand:'"Shantell Sans",sans-serif'};
  for(const theme of ['light','dark','sepia','contrast']) for(const [font,family] of Object.entries(fonts)) for(const size of [15,22]) {
    d.documentElement.dataset.theme=theme;
    d.documentElement.style.setProperty('--reader-font',family);
    d.documentElement.style.setProperty('--reader-size',size/16+'rem');
    await d.fonts.load(size+'px '+family.split(',')[0]);await d.fonts.ready;
    for(const width of [320,390,768,1181,1280,1439,1440]) for(const view of ['content','qa']) {
      frame.style.width=width+'px';w.setView(view,{writeHistory:false,restore:false});await tick();
      const problems=[];
      if(d.documentElement.scrollWidth>d.documentElement.clientWidth+1)problems.push('page overflow');
      if(view==='content') {
        d.documentElement.classList.add('reduce-motion');await tick();
        for(const modeButton of scene.querySelectorAll('[data-mode]')) {
          modeButton.click();
          const data=JSON.parse(scene.querySelector('script').textContent),mode=data.modes[modeButton.dataset.mode];
          for(let i=0;i<mode.steps.length;i++) {
            if(i)scene.querySelector('[data-act=next]').click();
            if(scene.querySelector('.pb-count').textContent!=='Step '+(i+1)+' of '+mode.steps.length)problems.push('track did not reach step '+(i+1));
            for(const t of scene.querySelectorAll('.pb-svg text')) {
              if(!t.textContent)continue;
              const css=w.getComputedStyle(t),m=t.getScreenCTM(),floor=css.fontFamily.includes('Hand')?15:12;
              const actual=parseFloat(css.fontSize)*Math.hypot(m.a,m.b);
              if(actual+.05<floor)problems.push('small label: '+t.textContent+' = '+actual);
              const box=t.getBBox(),svg=scene.querySelector('svg').viewBox.baseVal;
              if(box.x<-.5||box.y<-.5||box.x+box.width>svg.width+.5||box.y+box.height>svg.height+.5)problems.push('label outside SVG: '+t.textContent);
              const node=t.closest('.pb-node'),chip=t.closest('.pb-chip');
              const rect=(chip||node)?.querySelector('rect');
              if(rect&&(box.x<Number(rect.getAttribute('x'))||box.x+box.width>Number(rect.getAttribute('x'))+Number(rect.getAttribute('width'))))problems.push('label outside node: '+t.textContent);
            }
          }
        }
        d.documentElement.classList.remove('reduce-motion');
      }
      if(view==='qa') {
        const items=[...d.querySelectorAll('#section-answer-key > ol > li')];
        if(!items.length||items.some(li=>!li.querySelector('.qa-answer-label'))||d.querySelectorAll('#panel-qa .qa-answer-label').length!==13)problems.push('answer labels');
      }
      result.checks.push({theme,font,size,width,view,ok:!problems.length});
      if(problems.length)result.problems.push({theme,font,size,width,view,problems:[...new Set(problems)]});
    }
    output.textContent=JSON.stringify({...result,completed:result.checks.length},null,2);
  }
  if(w.__qaErrors?.length)result.problems.push({runtimeErrors:w.__qaErrors});
  result.done=true;result.ok=!result.problems.length;
  output.textContent=JSON.stringify(result,null,2);
};
