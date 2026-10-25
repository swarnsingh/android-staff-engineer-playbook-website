// Disposable QA harness: prepare with prepare_browser_audit.py; never deploy the instrumented copy.
window.__runAudit = async (pages, widths = [320, 390, 768, 1280]) => {
  window.__R = {pages:[], done:false, widths, textSize:22, font:'Playbook Hand'};
  const show = () => {
    const output = document.getElementById('qa-results');
    if (output) output.textContent = JSON.stringify(window.__R, null, 2);
  };
  try {
    const diag = await (await fetch('/coverage/diagram-sources.json')).json();
    const units = await (await fetch('/coverage/original-units.json')).json();
    for (const href of pages) {
      const frame = document.createElement('iframe');
      frame.style.cssText='width:1280px;height:900px;position:fixed;left:0;top:0;opacity:0.01;pointer-events:none';
      document.body.append(frame);
      try {
        await Promise.race([new Promise((resolve,reject)=>{frame.onload=resolve;frame.onerror=reject;frame.src=href;}),new Promise((_,reject)=>setTimeout(()=>reject(new Error('Page load timed out')),15000))]);
        const d=frame.contentDocument,w=frame.contentWindow;
        if (typeof w.__inspectOriginalContent !== 'function') throw new Error('QA instrumentation missing');
        const viewAudits=[];
        for(const view of ['content','qa']) {
          d.getElementById('tab-'+view).click();
          await new Promise(resolve=>w.requestAnimationFrame(resolve));
          viewAudits.push(await Promise.race([w.__inspectOriginalContent(diag,units,view),new Promise(resolve=>setTimeout(()=>resolve({problems:['AUDIT TIMEOUT']}),20000))]));
        }
        const preservation={views:viewAudits,problems:viewAudits.flatMap(v=>v.problems),units:viewAudits.reduce((n,v)=>n+(v.units||0),0),diagrams:viewAudits.reduce((n,v)=>n+(v.diagrams||0),0),loadedDiagrams:viewAudits.reduce((n,v)=>n+(v.loadedDiagrams||0),0)};
        const steppers=d.querySelectorAll('figure.stepper').length,ready=d.querySelectorAll('figure.stepper.is-ready').length;
        d.documentElement.style.setProperty('--reader-font','"Playbook Hand",sans-serif');
        d.documentElement.style.setProperty('--reader-size','1.375rem');
        await d.fonts.load('22px "Playbook Hand"');
        await d.fonts.ready;
        // Reveal only teaching animation states to check worst-case card geometry. Original DOM stays intact.
        d.querySelectorAll('.blend .is-off').forEach(e=>e.classList.remove('is-off'));
        const layouts=[];
        for(const view of ['content','qa']) for(const width of widths){
          d.getElementById('tab-'+view).click();
          frame.style.width=width+'px';
          await new Promise(resolve=>w.requestAnimationFrame(()=>w.requestAnimationFrame(resolve)));
          const overflow=d.documentElement.scrollWidth>d.documentElement.clientWidth+1;
          const clipped=[...d.querySelectorAll('.blend .node,.blend .mark')].filter(e=>e.getClientRects().length&&e.scrollWidth>e.clientWidth+2).length;
          layouts.push({view,width,overflow,clipped});
        }
        const qaSeparation = d.querySelectorAll('#panel-content [data-question],#panel-content .blend[data-kind="check"]').length === 0;
        const answers = [...d.querySelectorAll('#panel-qa #section-answer-key > ol > li')];
        const answerLabels = answers.every(item=>item.querySelector('.qa-answer-label'));
        window.__R.pages.push({href,preservation,steppers,ready,layouts,qaSeparation,answerLabels,ok:preservation.problems.length===0&&steppers===ready&&qaSeparation&&answerLabels&&layouts.every(l=>!l.overflow&&!l.clipped)});
      } catch(error) {
        window.__R.pages.push({href,ok:false,error:String(error)});
      } finally {
        frame.remove();show();
      }
    }
  } catch(error) {window.__R.error=String(error);}
  window.__R.done=true;show();
};
