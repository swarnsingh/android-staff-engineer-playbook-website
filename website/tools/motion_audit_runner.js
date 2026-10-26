// Runs only in the disposable QA fixture. Uses real reader controls and runtime.
window.runMotionAudit = async () => {
  const results = [], output = document.getElementById('motion-results');
  const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
  const scenes = [...document.querySelectorAll('[data-pb-flow="scene"]')];
  const [legacy, inferred, optedOut] = document.querySelectorAll('.stepper');
  const loop = document.querySelector('[data-pb-flow="loop"]');
  const click = (root, action) => root.querySelector('[data-act="'+action+'"]').click();
  const packets = root => root.querySelectorAll('.pb-pk,.stepper-packet').length;
  const moving = root => root.querySelectorAll('.pb-edge.moving').length;
  const assert = (ok, detail) => { if (!ok) throw Error(detail); };
  async function test(name, fn) {
    try { await fn(); results.push({name,ok:true}); }
    catch (e) { results.push({name,ok:false,error:String(e)}); }
    finally { window.Playbook.pauseAll(); scenes.forEach(s=>click(s,'reset')); [legacy,inferred,optedOut].forEach(s=>click(s,'reset')); document.documentElement.classList.remove('reduce-motion'); }
    output.textContent=JSON.stringify({done:false,results},null,2);
  }
  await document.fonts.ready;
  await delay(100);
  await test('Numbered navigation compares states without starting motion', async () => {
    const scene=scenes[0],buttons=scene.querySelectorAll('[data-step]');
    assert(buttons.length===6,'Missing authored step navigation');
    buttons[5].click();
    assert(scene.querySelector('.pb-count').textContent==='Step 6 of 6','Jump did not reach final state');
    assert(buttons[5].getAttribute('aria-current')==='step','Current step not exposed');
    assert(packets(scene)===0,'Jump started motion');
    buttons[0].click();
    assert(scene.querySelector('.pb-count').textContent==='Step 1 of 6','Backward jump did not restore initial state');
    assert(!buttons[5].hasAttribute('aria-current'),'Stale current step');
  });
  await test('State changes do not infer transfers', async () => {
    click(inferred,'next'); await delay(80);
    assert(packets(inferred)===0,'Inferred packet appeared');
  });
  await test('Explicit transfer has an immediate Pause control', async () => {
    click(legacy,'next'); await delay(80);
    assert(packets(legacy)===1,'Authored transfer did not start');
    assert(legacy.querySelector('[data-act=play]').textContent==='Pause','Manual packet lacks Pause');
    click(legacy,'play'); assert(packets(legacy)===0,'Pause left the legacy packet');
  });
  await test('data-no-handoff suppresses an authored transfer', async () => {
    click(optedOut,'next'); await delay(80);
    assert(packets(optedOut)===0,'Opt-out ignored');
  });
  await test('Scene Next can be paused mid-flight', async () => {
    click(scenes[0],'next'); await delay(80);
    assert(packets(scenes[0])===1,'Scene packet did not start');
    assert(scenes[0].querySelector('[data-act=play]').textContent==='Pause','Scene Next lacks Pause');
    click(scenes[0],'play');
    assert(packets(scenes[0])===0 && moving(scenes[0])===0,'Pause left scene motion');
    assert(scenes[0].querySelector('.pb-node.is-active .s')?.textContent==='inspect request','Pause did not settle target state');
  });
  await test('Two scenes share one motion turn', async () => {
    click(scenes[0],'next'); await delay(80);
    click(scenes[1],'next'); await delay(80);
    assert(packets(scenes[0])===0 && packets(scenes[1])===1,'Two scenes moved at once');
  });
  await test('Scene and legacy stepper share one motion turn', async () => {
    click(scenes[0],'next'); await delay(80);
    click(legacy,'next'); await delay(80);
    assert(packets(scenes[0])===0 && packets(legacy)===1,'Legacy claim did not stop scene');
    click(scenes[1],'next'); await delay(80);
    assert(packets(legacy)===0 && packets(scenes[1])===1,'Scene claim did not stop legacy');
  });
  await test('Loop, scene and legacy stepper share one motion turn', async () => {
    loop.querySelector('[data-toggle]').click(); await delay(80);
    assert(packets(loop)>0,'Loop did not play');
    click(scenes[0],'next'); await delay(80);
    assert(packets(loop)===0 && packets(scenes[0])===1,'Loop survived scene claim');
    loop.querySelector('[data-toggle]').click(); await delay(80);
    assert(packets(scenes[0])===0 && packets(loop)>0,'Scene survived loop claim');
    click(legacy,'next'); await delay(80);
    assert(packets(loop)===0 && packets(legacy)===1,'Loop survived legacy claim');
  });
  await test('Live reduced motion cancels autoplay and permits manual steps', async () => {
    click(scenes[0],'play'); await delay(520);
    document.documentElement.classList.add('reduce-motion'); await delay(60);
    const count=scenes[0].querySelector('.pb-count').textContent;
    assert(packets(scenes[0])===0 && moving(scenes[0])===0,'Reduced motion left packets or marching edges');
    assert(scenes[0].querySelector('[data-act=play]').disabled,'Reduced motion permits autoplay');
    await delay(3000);
    assert(scenes[0].querySelector('.pb-count').textContent===count,'Autoplay continued under reduced motion');
    click(scenes[0],'next'); await delay(60);
    assert(scenes[0].querySelector('.pb-count').textContent!==count && packets(scenes[0])===0,'Manual still step failed');
  });
  await test('Packet labels stay inside the drawing at edge lanes', async () => {
    const scene=scenes[1];
    // WorkManager: registration, waiting, start, then the long return edge carrying retry.
    for(let i=0;i<4;i++)click(scene,'next');
    await delay(180);
    const svg=scene.querySelector('svg'),label=scene.querySelector('.pb-pk text');
    assert(label,'Return packet did not start');
    const box=label.getBoundingClientRect(),paper=svg.getBoundingClientRect();
    assert(box.left>=paper.left-.5 && box.right<=paper.right+.5,'Packet label escaped the drawing');
  });
  await test('Reader pause hook cancels motion immediately', async () => {
    click(scenes[0],'next'); await delay(80); window.Playbook.pauseAll();
    assert(packets(document)===0 && moving(document)===0,'Reader pause hook left motion');
  });
  await test('Leaving the rendered area cancels a scene', async () => {
    click(scenes[0],'next'); await delay(80);
    scenes[0].style.display='none'; await delay(120);
    assert(packets(scenes[0])===0 && moving(scenes[0])===0,'Offscreen scene kept moving');
    scenes[0].style.display='';
  });
  const result={done:true,ok:results.every(r=>r.ok),results};
  output.textContent=JSON.stringify(result,null,2);
};
