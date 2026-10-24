'use strict';
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const sourceRoot = 'https://github.com/swarnsingh/android-staff-engineer-playbook/blob/main/';
const sample = $('#concurrent-code').textContent;
const escapeHtml = text => text.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');

// The source text remains readable without this optional highlighting pass.
const tokenPattern = /("[^"\n]*"|\/\/[^\n]*|\b(?:import|fun|suspend|val|var|class|return|if|else|try|catch|finally|throw|case|switch|new|public|final|private|object)\b|\b(?:true|false|null|\d[\d_]*)\b|\b[A-Za-z_][\w]*(?=\s*\())/g;
$$('code.highlight').forEach(code => {
  code.innerHTML = code.textContent.split(tokenPattern).map((part,index) => {
    if (!(index % 2)) return escapeHtml(part);
    const kind = part.startsWith('"') ? 'string' : part.startsWith('//') ? 'comment' : /^(true|false|null|\d)/.test(part) ? 'number' : /^(import|fun|suspend|val|var|class|return|if|else|try|catch|finally|throw|case|switch|new|public|final|private|object)$/.test(part) ? 'key' : 'call';
    return `<span class="syntax-${kind}">${escapeHtml(part)}</span>`;
  }).join('');
});
let toastTimer;
function toast(message) {
  clearTimeout(toastTimer); $('#toast').textContent = message; $('#toast').hidden = false;
  toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 3500);
}
$$('[data-copy]').forEach(button => button.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText($(`#${button.dataset.copy}`).textContent);
    button.textContent = 'Copied ✓';
    setTimeout(() => { button.textContent = 'Copy code'; }, 2000);
  } catch { toast('Clipboard unavailable. Select the code to copy it.'); }
}));

const fonts = {sans:'-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',serif:'Georgia,"Palatino Linotype",serif',times:'"Times New Roman",Times,serif',hand:'"Chalkboard SE","Segoe Print","Comic Sans MS",cursive'};
let preferences = {};
try { preferences = JSON.parse(localStorage.getItem('playbook-reader-v1')) || {}; } catch {}
if (typeof preferences !== 'object' || Array.isArray(preferences)) preferences = {};
const systemMotion = matchMedia('(prefers-reduced-motion:reduce)');
let effectiveReducedMotion = false;
let pauseAnimation = () => {};
function savePreferences() { try { localStorage.setItem('playbook-reader-v1',JSON.stringify(preferences)); } catch {} }
function applyPreferences() {
  const theme = ['light','dark','sepia','contrast'].includes(preferences.theme) ? preferences.theme : 'light';
  const font = Object.hasOwn(fonts,preferences.font) ? preferences.font : 'sans';
  const size = Math.max(15,Math.min(22,Number(preferences.size) || 18));
  effectiveReducedMotion = systemMotion.matches || !!preferences.motion;
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.setProperty('--reader-font',fonts[font]);
  document.documentElement.style.setProperty('--reader-size',`${size / 16}rem`);
  document.documentElement.classList.toggle('reduce-motion',effectiveReducedMotion);
  document.body.classList.toggle('code-wrap',!!preferences.wrap);
  $('#font-family').value = font; $('#font-size').value = size;
  $('#font-size-value').textContent = `${size}px base`;
  $$('input[name=theme]').forEach(input => { input.checked = input.value === theme; });
  $('#reduce-motion').checked = effectiveReducedMotion;
  $('#reduce-motion').disabled = systemMotion.matches;
  $('#motion-note').textContent = systemMotion.matches ? 'Your system requests reduced motion. Manual steps stay available; automatic playback is off.' : effectiveReducedMotion ? 'Motion and automatic playback are off. Use Previous and Next to explore every state.' : 'Uses your system preference, plus this optional override.';
  $('#wrap-code').checked = !!preferences.wrap;
  $('#bookmark').setAttribute('aria-pressed',!!preferences.bookmarked);
  $('#bookmark').textContent = preferences.bookmarked ? '★ Lesson saved' : '☆ Save lesson';
  $('#play-model').setAttribute('aria-disabled',effectiveReducedMotion);
  if (effectiveReducedMotion) pauseAnimation();
}
applyPreferences();
$('#font-family').addEventListener('change',e => { preferences.font=e.target.value; applyPreferences(); savePreferences(); });
$('#font-size').addEventListener('input',e => { preferences.size=e.target.value; applyPreferences(); savePreferences(); });
$$('input[name=theme]').forEach(input => input.addEventListener('change',() => { preferences.theme=input.value; applyPreferences(); savePreferences(); }));
$('#reduce-motion').addEventListener('change',e => { preferences.motion=e.target.checked; applyPreferences(); savePreferences(); });
$('#wrap-code').addEventListener('change',e => { preferences.wrap=e.target.checked; applyPreferences(); savePreferences(); });
systemMotion.addEventListener('change',applyPreferences);
$('#bookmark').addEventListener('click',() => { preferences.bookmarked=!preferences.bookmarked; applyPreferences(); savePreferences(); toast(preferences.bookmarked?'Saved on this device.':'Lesson removed from your saved list.'); });
$('#focus-toggle').addEventListener('click',() => { const enabled=document.body.classList.toggle('focus-mode'); $('#focus-toggle').setAttribute('aria-pressed',enabled); $('#focus-toggle').textContent=enabled?'Exit focus':'Focus'; });

const settingsDialog = $('#reading-dialog');
const curriculumDialog = $('#curriculum-dialog');
const curriculum = $('#curriculum');
const drawerMedia = matchMedia('(max-width:1180px)');
function syncModalState() { document.body.classList.toggle('modal-open',settingsDialog.open || curriculumDialog.open); }
function openSettings() { pauseAnimation(); settingsDialog.showModal(); syncModalState(); }
function openCurriculum() { pauseAnimation(); if (drawerMedia.matches && !curriculumDialog.open) { curriculumDialog.showModal(); syncModalState(); } }
function closeCurriculum() { if(curriculumDialog.open) curriculumDialog.close(); }
function placeCurriculum() {
  if (drawerMedia.matches) curriculumDialog.append(curriculum);
  else { closeCurriculum(); $('#sidebar-slot').append(curriculum); }
}
placeCurriculum(); drawerMedia.addEventListener('change',placeCurriculum);
$('#reading-settings-toggle').addEventListener('click',openSettings);
$('#close-reading-dialog').addEventListener('click',() => settingsDialog.close());
$('#menu-toggle').addEventListener('click',openCurriculum);
$('#close-curriculum').addEventListener('click',closeCurriculum);
[settingsDialog,curriculumDialog].forEach(dialog => {
  dialog.addEventListener('close',syncModalState);
  dialog.addEventListener('keydown',event=>{
    if(event.key!=='Tab') return;
    const controls=[...dialog.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary,[tabindex]:not([tabindex="-1"])')].filter(node=>node.getClientRects().length && getComputedStyle(node).visibility!=='hidden');
    if(!controls.length) return;
    const first=controls[0],last=controls[controls.length-1];
    if(event.shiftKey && (document.activeElement===first || !dialog.contains(document.activeElement))){event.preventDefault();last.focus();}
    else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
  });
  dialog.addEventListener('click',e => {
    if(e.target!==dialog) return;
    const r=dialog.getBoundingClientRect();
    if(e.clientX<r.left || e.clientX>r.right || e.clientY<r.top || e.clientY>r.bottom) dialog.close();
  });
});
document.addEventListener('keydown',e => {
  if(e.key==='/' && !e.ctrlKey && !e.metaKey && !e.altKey && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName) && !document.activeElement.isContentEditable && !settingsDialog.open) {
    e.preventDefault(); openCurriculum(); $('#topic-search').focus();
  }
});

// Supplemental views derive from the same in-lesson answers and source links.
$$('[data-question]').forEach(question => { const clone=question.cloneNode(true); clone.removeAttribute('id'); clone.removeAttribute('data-question'); $('#practice-questions').append(clone); });
const seenSources = new Set();
$$('article a[target=_blank]').forEach(link => {
  if(seenSources.has(link.href)) return;
  seenSources.add(link.href); const copy=link.cloneNode(true); copy.className='resource-row'; $('#resource-links').append(copy);
});
function markExternalLinks(root=document) {
  root.querySelectorAll('a[target=_blank]').forEach(link => { link.setAttribute('aria-describedby','external-note'); });
}
markExternalLinks();
const countCopy = $('article').cloneNode(true); countCopy.querySelectorAll('pre,figure,table').forEach(node=>node.remove());
const words = countCopy.textContent.trim().split(/\s+/).length;
$('#reading-time').textContent=`About ${Math.ceil(words/200)} min reading · experiments extra`;

const tabs=$$('[role=tab]');
let activeView='content';
const positions={content:0,qa:0,playground:0,resources:0};
let lastReadingY=window.scrollY,readingScrollTimer;
window.addEventListener('scroll',()=>{
  if(activeView!=='content'||settingsDialog.open||curriculumDialog.open)return;
  clearTimeout(readingScrollTimer);
  readingScrollTimer=setTimeout(()=>{if(activeView==='content')lastReadingY=window.scrollY;},180);
},{passive:true});
let contentHash=location.hash;
function setView(view,{focus=false,anchor=null,writeHistory=true,restore=true}={}) {
  if(!['content','qa','playground','resources'].includes(view)) view='content';
  clearTimeout(readingScrollTimer);
  positions[activeView]=activeView==='content'?lastReadingY:window.scrollY;
  if(activeView==='content' && location.hash) contentHash=location.hash;
  activeView=view;
  tabs.forEach(tab=>{
    const selected=tab.id===`tab-${view}`;
    tab.setAttribute('aria-selected',selected); tab.tabIndex=selected?0:-1;
    $(`#${tab.getAttribute('aria-controls')}`).hidden=!selected;
  });
  $('.page-outline').hidden=view!=='content'; $('.mobile-outline').hidden=view!=='content';
  if(anchor) contentHash=`#${anchor}`;
  if(writeHistory) {
    const url=new URL(location.href);
    if(view==='content') url.searchParams.delete('view'); else url.searchParams.set('view',view);
    url.hash=view==='content'?contentHash:'';
    history.pushState({view},'',url);
  }
  if(focus) $(`#tab-${view}`).focus({preventScroll:true});
  if(anchor && document.getElementById(anchor)) document.getElementById(anchor).scrollIntoView({block:'start',behavior:'instant'});
  else if(restore) window.scrollTo({top:positions[view],behavior:'instant'});
  if(view==='content')lastReadingY=window.scrollY;
}
tabs.forEach((tab,index)=>{
  tab.addEventListener('click',()=>setView(tab.id.replace('tab-','')));
  tab.addEventListener('keydown',e=>{
    let next;
    if(e.key==='ArrowRight') next=(index+1)%tabs.length;
    if(e.key==='ArrowLeft') next=(index+tabs.length-1)%tabs.length;
    if(e.key==='Home') next=0;
    if(e.key==='End') next=tabs.length-1;
    if(next!==undefined){e.preventDefault();setView(tabs[next].id.replace('tab-',''),{focus:true});}
  });
});
$$('[data-open-tab]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.openTab,{focus:true})));
$$('[data-go]').forEach(button=>button.addEventListener('click',()=>setView('content',{anchor:button.dataset.go,focus:true})));
$$('.page-outline a,.mobile-outline a,.brand').forEach(link=>link.addEventListener('click',e=>{
  e.preventDefault(); $('.mobile-outline').open=false;
  setView('content',{anchor:link.hash.slice(1)});
}));
window.addEventListener('popstate',()=>setView(new URL(location.href).searchParams.get('view')||'content',{writeHistory:false,anchor:location.hash?location.hash.slice(1):null}));
window.addEventListener('hashchange',()=>{ if(location.hash && document.getElementById(location.hash.slice(1))) setView('content',{writeHistory:false,anchor:location.hash.slice(1)}); });
const initialView=new URL(location.href).searchParams.get('view');
if(initialView) setView(initialView,{writeHistory:false,restore:false});
const outlineLinks=$$('.page-outline a,.mobile-outline a');
// Observe each section with one shared observer.
const sectionObserver=new IntersectionObserver(entries=>{
  entries.forEach(entry=>{if(entry.isIntersecting){
    outlineLinks.forEach(link=>{const current=link.hash===`#${entry.target.id}`;link.classList.toggle('current',current);if(current)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
    $('#mobile-current').textContent=$(`.page-outline a[href="#${entry.target.id}"]`).textContent.replace(/^\d+\. /,'');
  }});
},{rootMargin:'-15% 0px -65% 0px'});
$$('.lesson-section').forEach(section=>sectionObserver.observe(section));

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
pauseAnimation=stopPlayback;
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

function chapterLink(chapter){
  const active=chapter.path==='kotlin/coroutines-and-flow/coroutines.md';
  const link=document.createElement('a');link.textContent=chapter.title;
  if(active){link.href='#problem';link.setAttribute('aria-current','page');link.addEventListener('click',e=>{e.preventDefault();closeCurriculum();setView('content',{anchor:'problem'});});}
  else{link.href=sourceRoot+chapter.path;link.target='_blank';link.rel='noreferrer';link.setAttribute('aria-describedby','external-note');const cue=document.createElement('span');cue.className='external-cue';cue.textContent='GitHub ↗';link.append(cue);}
  return link;
}
function renderNavigation(query=''){
  const nav=$('#topic-nav');nav.replaceChildren();let previousCategory='',count=0;
  for(const topic of window.PLAYBOOK_CATALOG){
    const all=topic.title.toLowerCase().includes(query);
    const chapters=topic.chapters.filter(chapter=>!query||all||`${chapter.title} ${chapter.path} ${chapter.path.endsWith('/coroutines.md')?'suspend cancellation cancel viewmodelscope continuation async await':''}`.toLowerCase().includes(query));
    if(!chapters.length)continue;count+=chapters.length;
    if(topic.category!==previousCategory){const label=document.createElement('p');label.className='nav-label';label.textContent=topic.category;nav.append(label);previousCategory=topic.category;}
    const group=document.createElement('details');group.className='nav-group';group.open=!!query||topic.slug==='kotlin';
    const summary=document.createElement('summary');const icon=document.createElement('span');icon.className='nav-icon';icon.textContent=topic.icon;icon.setAttribute('aria-hidden','true');
    const name=document.createElement('span');name.textContent=topic.title;const chevron=document.createElement('span');chevron.className='chevron';chevron.textContent='›';chevron.setAttribute('aria-hidden','true');summary.append(icon,name,chevron);group.append(summary);
    const children=document.createElement('div');children.className='nav-children';
    if(topic.slug==='kotlin'&&!query){
      const section=document.createElement('p');section.className='nav-subtitle';section.textContent='COROUTINES & FLOW';children.append(section);
      const order=['coroutines.md','channels-and-select.md','flow-operators-and-backpressure.md','callbackflow-and-bridging-callbacks.md','coroutines-debugging-and-profiling.md','test-dispatchers-virtual-time.md'];
      chapters.filter(c=>c.path.includes('coroutines-and-flow/')).sort((a,b)=>order.indexOf(a.path.split('/').pop())-order.indexOf(b.path.split('/').pop())).forEach(c=>children.append(chapterLink(c)));
      const more=document.createElement('details');more.className='nav-group';const moreSummary=document.createElement('summary');moreSummary.textContent='Language, types & runtime';more.append(moreSummary);chapters.filter(c=>!c.path.includes('coroutines-and-flow/')).forEach(c=>more.append(chapterLink(c)));children.append(more);
    }else chapters.forEach(c=>children.append(chapterLink(c)));
    group.append(children);nav.append(group);
  }
  $('#search-empty').hidden=count>0;$('#search-status').textContent=query?`${count} matching topic${count===1?'':'s'}. Titles, paths and a few sample-lesson keywords; not full-text search.`:'';
}
renderNavigation();let searchTimer;
$('#topic-search').addEventListener('input',e=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>renderNavigation(e.target.value.trim().toLowerCase()),150);});
