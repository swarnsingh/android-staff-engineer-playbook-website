// Disposable QA harness: prepare with prepare_browser_audit.py; never deploy the instrumented copy.
window.__runAudit = async (pages, widths = [320, 390, 768, 1181, 1280, 1439, 1440]) => {
  window.__R = {pages:[], done:false, widths, textSize:22, font:'Shantell Sans'};
  const show = () => {
    const output = document.getElementById('qa-results');
    if (output) output.textContent = JSON.stringify(window.__R, null, 2);
  };
  try {
    const diag = await (await fetch('/coverage/diagram-sources.json')).json();
    const units = await (await fetch('/coverage/original-units.json')).json();
    const frame = document.createElement('iframe');
    frame.style.cssText='width:1280px;height:900px;position:fixed;left:0;top:0;opacity:0.01;pointer-events:none';
    document.body.append(frame);
    for (const href of pages) {
      try {
        const response=await fetch(href);
        if(!response.ok)throw new Error('Page HTTP '+response.status);
        // Isolate the built document without accumulating iframe navigation/history state.
        const html=await response.text();
        frame.srcdoc=html.replace('<html ', '<html data-qa-route="'+href+'" ');
        await new Promise((resolve,reject)=>{
          const start=Date.now();
          function poll(){
            const doc=frame.contentDocument;
            if(doc?.readyState==='complete' && doc.documentElement.dataset.qaRoute===href && doc.body?.dataset.source && typeof frame.contentWindow.__inspectOriginalContent==='function')return resolve();
            if(Date.now()-start>30000)return reject(new Error('Page readiness timed out'));
            setTimeout(poll,50);
          }
          poll();
        });
        const d=frame.contentDocument,w=frame.contentWindow;
        if (typeof w.__inspectOriginalContent !== 'function') throw new Error('QA instrumentation missing');
        const viewAudits=[];
        for(const view of ['content','qa']) {
          w.setView(view,{writeHistory:false,restore:false});
          await Promise.race([new Promise(resolve=>w.requestAnimationFrame(resolve)),new Promise(resolve=>setTimeout(resolve,300))]);
          viewAudits.push(await Promise.race([w.__inspectOriginalContent(diag,units,view),new Promise(resolve=>setTimeout(()=>resolve({problems:['AUDIT TIMEOUT']}),20000))]));
        }
        const preservation={views:viewAudits,problems:viewAudits.flatMap(v=>v.problems),units:viewAudits.reduce((n,v)=>n+(v.units||0),0),diagrams:viewAudits.reduce((n,v)=>n+(v.diagrams||0),0),loadedDiagrams:viewAudits.reduce((n,v)=>n+(v.loadedDiagrams||0),0)};
        const steppers=d.querySelectorAll('figure.stepper').length,ready=d.querySelectorAll('figure.stepper.is-ready').length;
        const scenes=d.querySelectorAll('[data-pb-flow="scene"]').length;
        const sceneReady=[...d.querySelectorAll('[data-pb-flow="scene"]')].filter(e=>!e.classList.contains('pb-error')&&e.querySelector('.pb-count').textContent&&e.querySelector('.pb-node')).length;
        d.documentElement.style.setProperty('--reader-font','"Shantell Sans",sans-serif');
        d.documentElement.style.setProperty('--reader-size','1.375rem');
        await d.fonts.load('22px "Shantell Sans"');
        await d.fonts.load('19px "Patrick Hand"');
        await d.fonts.ready;
        // Reveal only teaching animation states to check worst-case card geometry. Original DOM stays intact.
        d.querySelectorAll('.blend .is-off').forEach(e=>e.classList.remove('is-off'));
        const layouts=[];
        for(const view of ['content','qa']) for(const width of widths){
          w.setView(view,{writeHistory:false,restore:false});
          frame.style.width=width+'px';
          await Promise.race([new Promise(resolve=>w.requestAnimationFrame(()=>w.requestAnimationFrame(()=>w.requestAnimationFrame(resolve)))),new Promise(resolve=>setTimeout(resolve,300))]);
          const overflow=d.documentElement.scrollWidth>d.documentElement.clientWidth+1;
          const clipped=[...d.querySelectorAll('.blend .node,.blend .mark')].filter(e=>e.getClientRects().length&&e.scrollWidth>e.clientWidth+2).length;
          const labels=[...d.querySelectorAll('.pb-svg text')].filter(e=>e.getClientRects().length&&e.textContent.trim()).map(e=>{
            const css=w.getComputedStyle(e),m=e.getScreenCTM(),size=parseFloat(css.fontSize)*Math.hypot(m.a,m.b);
            const hand=css.fontFamily.includes('Hand'),floor=hand?15:12;
            return {text:e.textContent,size,floor};
          });
          const smallLabels=labels.filter(t=>t.size+.1<t.floor);
          layouts.push({view,width,overflow,clipped,smallLabels});
        }
        const runtimeErrors=w.__qaErrors||[];
        const sceneChecks=[];
        if(scenes) {
          w.setView('content',{writeHistory:false,restore:false});
          d.documentElement.classList.add('reduce-motion');
          for(const width of [320,768,1280,1440]) for(const theme of ['light','dark','sepia','contrast']) {
            frame.style.width=width+'px';d.documentElement.dataset.theme=theme;
            await Promise.race([new Promise(resolve=>w.requestAnimationFrame(()=>w.requestAnimationFrame(()=>w.requestAnimationFrame(resolve)))),new Promise(resolve=>setTimeout(resolve,300))]);
            for(const scene of d.querySelectorAll('[data-pb-flow="scene"]')) {
              const data=JSON.parse(scene.querySelector('script[type="application/json"]').textContent);
              for(const [mode,track] of Object.entries(data.modes)) {
                const button=[...scene.querySelectorAll('[data-mode]')].find(b=>b.dataset.mode===mode);
                if(button)button.click();else scene.querySelector('[data-act=reset]').click();
                for(let i=0;i<track.steps.length;i++) {
                  if(i)scene.querySelector('[data-act=next]').click();
                  const problems=[];
                  if(scene.querySelector('.pb-count').textContent!=='Step '+(i+1)+' of '+track.steps.length)problems.push('wrong step counter');
                  const svg=scene.querySelector('svg'),viewBox=svg.viewBox.baseVal;
                  for(const text of svg.querySelectorAll('text')) {
                    if(!text.textContent)continue;
                    const css=w.getComputedStyle(text),ctm=text.getScreenCTM(),floor=css.fontFamily.includes('Hand')?15:12;
                    if(parseFloat(css.fontSize)*Math.hypot(ctm.a,ctm.b)+.05<floor)problems.push('small label: '+text.textContent);
                    const box=text.getBBox(),rect=text.closest('.pb-chip,.pb-node')?.querySelector('rect');
                    if(box.x<-.5||box.y<-.5||box.x+box.width>viewBox.width+.5||box.y+box.height>viewBox.height+.5)problems.push('outside SVG: '+text.textContent);
                    if(rect&&(box.x<Number(rect.getAttribute('x'))||box.x+box.width>Number(rect.getAttribute('x'))+Number(rect.getAttribute('width'))))problems.push('outside node: '+text.textContent);
                  }
                  sceneChecks.push({width,theme,mode,step:i+1,problems,ok:!problems.length});
                }
              }
            }
          }
          d.documentElement.classList.remove('reduce-motion');
        }
        const qaSeparation = d.querySelectorAll('#panel-content [data-question],#panel-content .blend[data-kind="check"]').length === 0;
        const answers = [...d.querySelectorAll('#panel-qa #section-answer-key > ol > li')];
        const answerLabels = answers.every(item=>item.querySelector('.qa-answer-label'));
        window.__R.pages.push({href,preservation,steppers,ready,scenes,sceneReady,runtimeErrors,sceneChecks,layouts,qaSeparation,answerLabels,ok:runtimeErrors.length===0&&sceneChecks.every(c=>c.ok)&&preservation.problems.length===0&&steppers===ready&&scenes===sceneReady&&qaSeparation&&answerLabels&&layouts.every(l=>!l.overflow&&!l.clipped&&!l.smallLabels.length)});
      } catch(error) {
        window.__R.pages.push({href,ok:false,error:String(error),loadState:frame.contentDocument?.readyState,title:frame.contentDocument?.title,runtimeErrors:frame.contentWindow?.__qaErrors});
      } finally {
        show();
      }
    }
    frame.remove();
  } catch(error) {window.__R.error=String(error);}
  window.__R.done=true;show();
};
