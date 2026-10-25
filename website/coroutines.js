'use strict';
const sample = $('#concurrent-code').textContent;
// Pure teaching frames live in lesson-model.js; this layer only presents them.
let sceneId='success',position=0,playTimer=null;
function statusKind(value){if(value==='Failed')return'error';if(value==='Cancelled')return'cancelled';return'normal';}
function renderModel(rebuildTable=false){
  const frame=COROUTINE_MODEL.frame(sceneId,position);position=frame.index;
  const {scene,step}=frame;
  $('#parent-status').textContent=step.parent;$('#name-status').textContent=step.name;$('#avatar-status').textContent=step.avatar;$('#thread-status').textContent=step.thread;
  [['#parent-status',step.parent],['#name-status',step.name],['#avatar-status',step.avatar]].forEach(([id,status])=>$(id).parentElement.dataset.status=statusKind(status));
  const tree=$('#job-tree');tree.dataset.signal='';
  requestAnimationFrame(()=>{tree.dataset.signal=effectiveReducedMotion?'':step.signal;});
  $('#step-count').textContent=`Step ${position+1} of ${scene.steps.length}`;$('#model-time').textContent=step.time;$('#model-caption').textContent=step.caption;
  $('#previous-step').setAttribute('aria-disabled',position===0);$('#next-step').setAttribute('aria-disabled',position===scene.steps.length-1);
  $('#model-position').max=scene.steps.length-1;$('#model-position').value=position;$('#model-position').setAttribute('aria-valuetext',`Step ${position+1}: ${step.time}`);
  const code=$('#model-code');code.replaceChildren();
  scene.code.forEach((line,index)=>{const span=document.createElement('span');span.className='model-line';if(step.lines.includes(index)){const mark=document.createElement('mark');mark.textContent=line;span.append(mark);}else span.textContent=line;code.append(span);});
  if(rebuildTable){
    $('#step-table-caption').textContent=scene.description;
    $('#step-table').replaceChildren();
    scene.steps.forEach((s,i)=>{const row=document.createElement('tr');[`${i+1}. ${s.time}`,s.name,s.avatar,s.parent,s.caption].forEach(value=>{const cell=document.createElement('td');cell.textContent=value;row.append(cell);});$('#step-table').append(row);});
  }
}
function stopPlayback(){clearInterval(playTimer);playTimer=null;$('#play-model').textContent='Play steps';$('#play-model').setAttribute('aria-pressed','false');}
animationStops.push(stopPlayback);
function moveStep(delta){stopPlayback();position+=delta;renderModel();}
$('#previous-step').addEventListener('click',()=>moveStep(-1));$('#next-step').addEventListener('click',()=>moveStep(1));
$('#reset-model').addEventListener('click',()=>{stopPlayback();position=0;renderModel();});
$('#scene-select').addEventListener('change',e=>{stopPlayback();sceneId=e.target.value;position=0;renderModel(true);});
$('#model-position').addEventListener('input',e=>{stopPlayback();position=Number(e.target.value);renderModel();});
$('#play-model').addEventListener('click',()=>{
  if(effectiveReducedMotion){toast('Reduced motion is active. Use Previous and Next to explore every step.');return;}
  if(playTimer){stopPlayback();return;}
  if(position===COROUTINE_MODEL.scenes[sceneId].steps.length-1){position=0;renderModel();}
  $('#play-model').textContent='Pause steps';$('#play-model').setAttribute('aria-pressed','true');
  playTimer=setInterval(()=>{position++;renderModel();if(position===COROUTINE_MODEL.scenes[sceneId].steps.length-1)stopPlayback();},2800);
});
new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)stopPlayback();}).observe($('#model-figure'));
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopPlayback();});
renderModel(true);

let playgroundLoading=false,kotlinInstance;
$('#execute-kotlin').addEventListener('click',()=>{if(kotlinInstance)kotlinInstance.execute();});
$('#load-playground').addEventListener('click',()=>{
  $('#inline-playground').hidden=false;
  if(playgroundLoading){$('#inline-playground').scrollIntoView({block:'center',behavior:'instant'});return;}
  playgroundLoading=true;$('#load-playground').textContent='Loading editor…';$('#load-playground').setAttribute('aria-disabled','true');
  $('#runnable-code').textContent=sample;$('#playground-status').textContent='Loading the Kotlin editor…';
  const script=document.createElement('script');script.src='https://unpkg.com/kotlin-playground@1';
  function fail(){playgroundLoading=false;$('#load-playground').textContent='Retry loading Kotlin editor';$('#load-playground').setAttribute('aria-disabled','false');$('#playground-status').textContent='The editor could not load. Copy the code into the standalone Kotlin Playground linked above.';script.remove();}
  script.onload=()=>{try{
    if(typeof window.KotlinPlayground!=='function')throw new Error('Editor unavailable');
    $('#runnable-code').setAttribute('theme',['dark','contrast'].includes(document.documentElement.dataset.theme)?'darcula':'idea');
    KotlinPlayground('#runnable-code',{getInstance(instance){kotlinInstance=instance;$('#execute-kotlin').disabled=false;}});
    $('#load-playground').textContent='Return to the live editor';$('#load-playground').setAttribute('aria-disabled','false');$('#playground-status').textContent='Edit concurrent = true to false, then choose Run Kotlin. Timestamps and thread names are real compiler-service output.';
  }catch{fail();}};
  script.onerror=fail;document.head.append(script);
});

