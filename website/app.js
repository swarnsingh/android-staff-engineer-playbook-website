'use strict';
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const sourceRoot = 'https://github.com/swarnsingh/android-staff-engineer-playbook/blob/main/';
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
// Every animation registers its stop function here; dialogs and reduced motion stop them all.
const animationStops = [];
function pauseAnimation() { animationStops.forEach(stop => stop()); }
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
  $('#play-model')?.setAttribute('aria-disabled',effectiveReducedMotion);
  if (effectiveReducedMotion) pauseAnimation();
  document.dispatchEvent(new Event('playbook:motion'));
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
$$('[data-question]').forEach(question => { const clone=question.cloneNode(true); [clone,...clone.querySelectorAll('[id]')].forEach(node=>node.removeAttribute('id')); clone.removeAttribute('data-question'); $('#practice-questions').append(clone); });
$('#qa-empty').hidden=!!$('#practice-questions').children.length;
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
    outlineLinks.forEach(link=>{const current=link.hash===`#${entry.target.querySelector('h2[id]')?.id || entry.target.id}`;link.classList.toggle('current',current);if(current)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
    const anchor=entry.target.querySelector('h2[id]')?.id || entry.target.id;
    const currentLink=$(`.page-outline a[href="#${anchor}"]`); if(currentLink)$('#mobile-current').textContent=currentLink.textContent.replace(/^\d+\. /,'');
  }});
},{rootMargin:'-15% 0px -65% 0px'});
$$('.lesson-section').forEach(section=>sectionObserver.observe(section));

function chapterLink(chapter){
  const active=chapter.path===document.body.dataset.source;
  const link=document.createElement('a');link.textContent=chapter.title;
  if(active){link.href='#problem';link.setAttribute('aria-current','page');link.addEventListener('click',e=>{e.preventDefault();closeCurriculum();setView('content',{anchor:'problem'});});}
  else if(chapter.path.startsWith('kotlin/')){link.href=(document.body.dataset.base||'/')+chapter.path.replace(/\.md$/,'/');}
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
      let currentFolder='',folderGroup;
      for(const chapter of chapters){
        const folder=chapter.path.split('/')[1];
        if(folder!==currentFolder){
          folderGroup=document.createElement('details');folderGroup.className='nav-group';
          folderGroup.open=chapters.some(c=>c.path===document.body.dataset.source && c.path.split('/')[1]===folder);
          const heading=document.createElement('summary');heading.textContent=folder.replaceAll('-',' ');
          folderGroup.append(heading);children.append(folderGroup);currentFolder=folder;
        }
        folderGroup.append(chapterLink(chapter));
      }
    }else chapters.forEach(c=>children.append(chapterLink(c)));
    group.append(children);nav.append(group);
  }
  $('#search-empty').hidden=count>0;$('#search-status').textContent=query?`${count} matching topic${count===1?'':'s'}. Titles, paths and a few sample-lesson keywords; not full-text search.`:'';
}
renderNavigation();let searchTimer;
$('#topic-search').addEventListener('input',e=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>renderNavigation(e.target.value.trim().toLowerCase()),150);});
