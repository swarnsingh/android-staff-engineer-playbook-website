// Usage: window.__runAudit(['/android/...', ...]) then poll window.__R
window.__runAudit = async (pages) => {
  window.__R = {pg:[], done:false};
  try {
    const code = await (await fetch('/fx/audit.js')).text();
    const diag = await (await fetch('/coverage/diagram-sources.json')).json();
    const units = await (await fetch('/coverage/original-units.json')).json();
    for (const href of pages) {
      const f=document.createElement('iframe'); f.style.cssText='width:1200px;height:900px;position:fixed;left:0;top:0;opacity:0.01;pointer-events:none'; document.body.append(f);
      await new Promise(r=>{f.onload=r; f.src=href;}); await new Promise(r=>setTimeout(r,300));
      const d=f.contentDocument, w=f.contentWindow;
      const r = await Promise.race([w.eval(code)(diag, units), new Promise(r=>setTimeout(()=>r({problems:['AUDIT TIMEOUT']}),9000))]);
      const steppers=d.querySelectorAll('figure.stepper').length, ready=d.querySelectorAll('figure.stepper.is-ready').length;
      const blends=d.querySelectorAll('.blend').length, figs=d.querySelectorAll('.blend figure').length;
      f.style.width='320px'; await new Promise(r=>setTimeout(r,200));
      d.querySelectorAll('.is-off').forEach(e=>e.classList.remove('is-off'));
      const overflow = d.documentElement.scrollWidth > d.documentElement.clientWidth+1;
      const clipped=[...d.querySelectorAll('.blend .node, .blend .mark')].filter(e=>e.scrollWidth>e.clientWidth+2).length;
      const bad = r.problems.length || steppers!==ready || overflow || clipped;
      __R.pg.push(`${bad?'PROBLEMS':'ok'} ${href} diagrams=${r.loadedDiagrams}/${r.diagrams} steppers=${ready}/${steppers} blends=${blends} figs=${figs} overflow320=${overflow} clipped=${clipped} ${r.problems.slice(0,2).join(' | ')}`);
      f.remove();
    }
  } catch(e) { __R.err=String(e); }
  __R.done=true;
};
'loaded'
