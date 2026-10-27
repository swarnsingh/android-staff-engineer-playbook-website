'use strict';
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const sourceRoot = 'https://github.com/swarnsingh/android-staff-engineer-playbook-website/blob/main/';
const escapeHtml = text => text.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');

// Highlight tokens once, preserving every source character and escaping markup.
const keywordNames = 'import package fun suspend val var class interface return if else try catch finally throw case switch new public final private protected internal object data sealed inline reified crossinline noinline override open abstract enum annotation companion constructor init by get set where is as in out when for while do break continue typealias expect actual const lateinit this super static void'.split(' ');
const keywordSet = new Set(keywordNames);
const tokenPattern = new RegExp('(\"\"\"[\\s\\S]*?\"\"\"|\"(?:\\\\.|[^\"\\\\\\n])*\"|\'(?:\\\\.|[^\'\\\\\\n])*\'|\\/\\*[\\s\\S]*?\\*\\/|\\/\\/[^\\n]*|@(?:\\w+:)?(?:\\w+\\.)*\\w+|\\b(?:'+keywordNames.join('|')+')\\b|\\b(?:true|false|null|\\d[\\d_]*(?:\\.\\d[\\d_]*)?)\\b|\\b[A-Z][A-Za-z0-9_]*\\b|\\b[A-Za-z_]\\w*(?=\\s*\\())','g');
$$('code.highlight').forEach(code => {
  code.innerHTML = code.textContent.split(tokenPattern).map((part,index) => {
    if (!(index % 2)) return escapeHtml(part);
    const kind = part.startsWith('"') || part.startsWith("'") ? 'string' : part.startsWith('//') || part.startsWith('/*') ? 'comment' : part.startsWith('@') ? 'annotation' : /^(true|false|null|\d)/.test(part) ? 'number' : keywordSet.has(part) ? 'key' : /^[A-Z]/.test(part) ? 'type' : 'call';
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

// Reading-font options come from the design tokens (build.py writes them into the select).
// A saved legacy ID maps to its successor; a missing choice follows the default without being saved.
const fontOptions = [...$('#font-family').options];
const defaultFont = fontOptions[0].value;
const legacyFonts = Object.fromEntries(fontOptions.flatMap(option => option.dataset.legacy.split(' ').filter(Boolean).map(id => [id,option.value])));
const readerFont = id => { const mapped = legacyFonts[id] || id; return fontOptions.some(option => option.value === mapped) ? mapped : defaultFont; };
let preferences = {};
try { preferences = JSON.parse(localStorage.getItem('playbook-reader-v1')) || {}; } catch {}
if (typeof preferences !== 'object' || Array.isArray(preferences)) preferences = {};
const systemMotion = matchMedia('(prefers-reduced-motion:reduce)');
let effectiveReducedMotion = false;
// Every animation registers its stop function here; dialogs and reduced motion stop them all.
const animationStops = [];
function pauseAnimation() { animationStops.forEach(stop => stop()); window.Playbook?.pauseAll(); }
function savePreferences() { try { localStorage.setItem('playbook-reader-v1',JSON.stringify(preferences)); } catch {} }
function applyPreferences() {
  const theme = ['light','dark','sepia','contrast'].includes(preferences.theme) ? preferences.theme : 'light';
  const font = readerFont(preferences.font);
  const size = Math.max(15,Math.min(22,Number(preferences.size) || 18));
  effectiveReducedMotion = systemMotion.matches || !!preferences.motion;
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.readerFont = font;
  document.documentElement.style.setProperty('--reader-size',`${size / 16}rem`);
  document.documentElement.classList.toggle('reduce-motion',effectiveReducedMotion);
  document.body.classList.toggle('code-wrap',!!preferences.wrap);
  $('#font-family').value = font; $('#font-size').value = size;
  $('#font-description').textContent = $('#font-family').selectedOptions[0].dataset.description;
  $('#font-size-value').textContent = `${size}px base`;
  $$('input[name=theme]').forEach(input => { input.checked = input.value === theme; });
  $('#reduce-motion').checked = effectiveReducedMotion;
  $('#reduce-motion').disabled = systemMotion.matches;
  $('#motion-note').textContent = systemMotion.matches ? 'Your system requests reduced motion. Manual steps stay available; automatic playback is off.' : effectiveReducedMotion ? 'Motion and automatic playback are off. Use Previous and Next to explore every state.' : 'Uses your system preference, plus this optional override.';
  $('#wrap-code').checked = !!preferences.wrap;
  const bookmark=$('#bookmark');
  if(bookmark){
    const saved=!!preferences.savedLessons?.[document.body.dataset.source];
    bookmark.setAttribute('aria-pressed',saved);
    bookmark.textContent=saved?'★ Lesson saved':'☆ Save lesson';
  }
  $('#play-model')?.setAttribute('aria-disabled',effectiveReducedMotion);
  if (effectiveReducedMotion) pauseAnimation();
  document.dispatchEvent(new Event('playbook:motion'));
}
if (legacyFonts[preferences.font]) { preferences.font = legacyFonts[preferences.font]; savePreferences(); }
applyPreferences();
// Text reflows when the font or size changes. Keep the line under the header where it was: anchor on the
// nearest visible block at that line, at the same fraction of its height.
const anchorBlocks = 'h2,h3,h4,p,li,pre,table,figure,blockquote,summary';
const shown = el => el.checkVisibility ? el.checkVisibility() : !el.closest('details:not([open]) > :not(summary)');
function readingAnchor() {
  const line = $('.topbar')?.getBoundingClientRect().bottom || 0;
  const panel = $$('.reading-content > section').find(view => !view.hidden) || $('.reading-content');
  if (!panel) return null;
  // The visible block closest to the line, by layout rather than DOM order. A container gives way to its own
  // block starting within about a line of the reading line; among blocks that all cross it, the smallest wins.
  const onScreen = [...panel.querySelectorAll(anchorBlocks)].map(el => ({el, box: el.getBoundingClientRect()}))
    .filter(({el, box}) => box.height > 0 && box.bottom > line + 8 && box.top < innerHeight && shown(el));
  const near = line + parseFloat(getComputedStyle(panel).fontSize) * 2;
  const best = onScreen.filter(({el}) => !onScreen.some(inner => inner.el !== el && el.contains(inner.el) && inner.box.top < near))
    .sort((a, b) => Math.max(a.box.top, line) - Math.max(b.box.top, line) || a.box.height - b.box.height)[0];
  if (!best) return null;
  const box = best.box;
  return {block: best.el, line, offset: box.top, fraction: box.top < line ? (line - box.top) / box.height : 0};
}
function keepReadingPosition(anchor) {
  if (!anchor || !anchor.block.isConnected) return;
  const box = anchor.block.getBoundingClientRect();
  const shift = anchor.fraction ? box.top + anchor.fraction * box.height - anchor.line : box.top - anchor.offset;
  if (Math.abs(shift) > 1) window.scrollBy({top: shift, behavior: 'instant'});
}
let readingChanges = 0;
async function changeReading(update) {
  const anchor = readingAnchor(), change = ++readingChanges;
  // The browser's own scroll anchoring would correct the same reflow a frame later and double the shift.
  document.documentElement.style.overflowAnchor = 'none';
  update();
  applyPreferences(); savePreferences(); keepReadingPosition(anchor);
  // Re-anchor once the newly chosen face has loaded and swapped in.
  try { await Promise.race([document.fonts.load(`400 1em ${getComputedStyle(document.documentElement).getPropertyValue('--font-prose')}`), new Promise(resolve => setTimeout(resolve,3000))]); } catch {}
  requestAnimationFrame(() => {
    if (change !== readingChanges) return;
    keepReadingPosition(anchor);
    document.documentElement.style.overflowAnchor = '';
  });
}
$('#font-family').addEventListener('change',e => changeReading(() => { preferences.font=e.target.value; }));
$('#font-size').addEventListener('input',e => changeReading(() => { preferences.size=e.target.value; }));
$$('input[name=theme]').forEach(input => input.addEventListener('change',() => { preferences.theme=input.value; applyPreferences(); savePreferences(); }));
$('#reduce-motion').addEventListener('change',e => { preferences.motion=e.target.checked; applyPreferences(); savePreferences(); });
$('#wrap-code').addEventListener('change',e => { preferences.wrap=e.target.checked; applyPreferences(); savePreferences(); });
systemMotion.addEventListener('change',applyPreferences);
$('#bookmark')?.addEventListener('click',() => {
  const key=document.body.dataset.source;
  if(!preferences.savedLessons || typeof preferences.savedLessons!=='object' || Array.isArray(preferences.savedLessons))preferences.savedLessons={};
  const saved=!preferences.savedLessons[key];
  if(saved)preferences.savedLessons[key]=true;else delete preferences.savedLessons[key];
  applyPreferences();savePreferences();toast(saved?'Saved on this device.':'Lesson unsaved on this device.');
});
$('#focus-toggle').addEventListener('click',() => { const enabled=document.body.classList.toggle('focus-mode'); $('#focus-toggle').setAttribute('aria-pressed',enabled); $('#focus-toggle').textContent=enabled?'Exit focus':'Focus'; placeCurriculum(); });

const settingsDialog = $('#reading-dialog');
const curriculumDialog = $('#curriculum-dialog');
const curriculum = $('#curriculum');
const drawerMedia = matchMedia('(max-width:1439px)'); // the curriculum rail shows only from 1440px (theme.css)
function syncModalState() { document.body.classList.toggle('modal-open',settingsDialog.open || curriculumDialog.open); }
function openSettings() { pauseAnimation(); settingsDialog.showModal(); syncModalState(); }
function useCurriculumDrawer() { return drawerMedia.matches || document.body.classList.contains('focus-mode'); }
function openCurriculum() { pauseAnimation(); if (useCurriculumDrawer() && !curriculumDialog.open) { curriculumDialog.showModal(); syncModalState(); } }
function closeCurriculum() { if(curriculumDialog.open) curriculumDialog.close(); }
function placeCurriculum() {
  if (useCurriculumDrawer()) curriculumDialog.append(curriculum);
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

// Move each practice block once: Content teaches; Q&A holds questions and answers.
// Static HTML preserves the complete chapter as a no-JS fallback. The build gate checks
// that stream; the browser gate independently checks both activated tabs against it.
const practice = $('#practice-questions');
const practiceBlocks = $('#tab-qa') && practice ? $$('[data-question], #panel-content .blend[data-kind="check"]') : [];
practiceBlocks.forEach(block => {
  if (block.closest('[data-question]') !== null && !block.hasAttribute('data-question')) return;
  const previous = block.previousElementSibling;
  if (previous?.matches('.blend[data-kind="review"]')) practice.append(previous);
  practice.append(block);
});
// Pair the original ordered lists once. Answer nodes retain their source identity;
// no answer text is copied, abbreviated or inferred from the prompt.
const questionSection=practice?.querySelector('#section-probing-questions');
const answerSection=practice?.querySelector('#section-answer-key');
const questionList=questionSection?.querySelector(':scope > ol');
const answerList=answerSection?.querySelector(':scope > ol');
const questionItems=questionList?[...questionList.children].filter(node=>node.tagName==='LI'):[];
const answerItems=answerList?[...answerList.children].filter(node=>node.tagName==='LI'):[];
// A changed source shape must remain intact rather than partially pairing unrelated items.
if(questionItems.length && questionItems.length===answerItems.length &&
   questionList.start===answerList.start){
  questionSection.insertBefore(answerSection,questionList);
  answerSection.classList.add('qa-key-intro');
  answerSection.querySelector(':scope > h2')?.classList.add('qa-key-heading');
  answerList.dataset.qaAnswerSlot=answerSection.id;
  answerList.hidden=true;
  questionItems.forEach((question,index)=>{
    const ordinal=questionList.start+index;
    question.dataset.qaQuestionIndex=String(ordinal);
    question.classList.add('qa-paired-question');
    const pair=document.createElement('div');pair.className='qa-answer-pair';
    const label=document.createElement('h3');label.className='qa-answer-label';label.textContent='Answer';
    const list=document.createElement('ol');list.className='qa-answer-list';list.start=ordinal;
    const answer=answerItems[index];
    answer.dataset.originalSection=answerSection.id;
    answer.dataset.originalAnswerIndex=String(ordinal);
    list.append(answer);pair.append(label,list);question.append(pair);
  });
}
// Supplemental answers are explicitly authored and labelled; never infer an answer
// from an unrelated checkpoint merely because both appear in the same chapter.
const guidanceGroups=new Map();
(practice?.querySelectorAll('[data-guidance-answer-for]') || []).forEach(answer=>{
  const section=answer.dataset.guidanceAnswerFor;
  if(!guidanceGroups.has(section))guidanceGroups.set(section,[]);
  guidanceGroups.get(section).push(answer);
});
for(const [sectionId,guidance] of guidanceGroups){
  const section=document.getElementById(sectionId);
  const list=section?.querySelector(':scope > ol');
  const questions=list?[...list.children].filter(node=>node.tagName==='LI'):[];
  const first=list?.start ?? 1;
  const byIndex=new Map(guidance.map(answer=>[Number(answer.dataset.questionIndex),answer]));
  if(!practice.contains(section) || !questions.length || guidance.length!==questions.length ||
     byIndex.size!==questions.length || questions.some((_,index)=>!byIndex.has(first+index)))continue;
  questions.forEach((question,index)=>{
    const ordinal=first+index;
    question.dataset.guidanceQuestionIndex=String(ordinal);
    question.classList.add('qa-paired-question');
    const pair=document.createElement('div');pair.className='qa-answer-pair';pair.dataset.supplementalAnswer='true';
    const label=document.createElement('h3');label.className='qa-answer-label';label.textContent='Answer';
    const answers=document.createElement('ol');answers.className='qa-answer-list';answers.start=ordinal;
    const item=document.createElement('li');item.dataset.guidanceAnswerIndex=String(ordinal);
    item.append(byIndex.get(ordinal));answers.append(item);pair.append(label,answers);question.append(pair);
  });
}
(practice?.querySelectorAll('.blend[data-kind="check"] details > summary') || []).forEach(summary => {
  const label=document.createElement('h4');label.className='qa-answer-label';label.textContent='Answer';
  summary.after(label);
  // The question and its authored answer are immediately available together.
  summary.parentElement.open=true;
});
// Hide empty story bands and remove practice links from the Content outline.
$$('.part-band').forEach(band => {
  let next = band.nextElementSibling;
  while (next?.classList.contains('blend')) next = next.nextElementSibling;
  if (!next || next.classList.contains('part-band')) band.hidden = true;
});
$$('.page-outline a,.mobile-outline a').forEach(link => {
  if (document.getElementById(link.hash.slice(1))?.closest('#panel-qa')) link.remove();
});
// An empty supplemental view should not be an extra stop in the reader.
if(!practice?.children.length){$('#tab-qa')?.remove();$('#panel-qa')?.remove();}
$('#qa-empty')?.remove();
const seenSources = new Set();
$$('#panel-content a[target=_blank],#panel-qa a[target=_blank],.lesson-about a[target=_blank]').forEach(link => {
  if(seenSources.has(link.href)) return;
  seenSources.add(link.href); const copy=link.cloneNode(true); copy.className='resource-row'; $('#resource-links')?.append(copy);
});
function markExternalLinks(root=document) {
  root.querySelectorAll('a[target=_blank]').forEach(link => { link.setAttribute('aria-describedby','external-note'); });
}
markExternalLinks();
if(!$('#resource-links')?.children.length){$('#tab-resources')?.remove();$('#panel-resources')?.remove();}
const countCopy = $('article').cloneNode(true); countCopy.querySelectorAll('pre,figure,table').forEach(node=>node.remove());
const words = countCopy.textContent.trim().split(/\s+/).length;
if($('#reading-time'))$('#reading-time').textContent=`About ${Math.ceil(words/200)} min reading · experiments extra`;

const tabs=$$('.lesson-tabs [role=tab]');
const availableViews=new Set(['content',...tabs.map(tab=>tab.id.replace('tab-',''))]);
if(tabs.length<2)$('.lesson-tabs')?.setAttribute('hidden','');
let activeView='content';
const positions={content:0,qa:0,playground:0,resources:0};
let lastReadingY=window.scrollY,readingScrollTimer;
window.addEventListener('scroll',()=>{
  if(activeView!=='content'||settingsDialog.open||curriculumDialog.open)return;
  clearTimeout(readingScrollTimer);
  readingScrollTimer=setTimeout(()=>{if(activeView==='content')lastReadingY=window.scrollY;},180);
},{passive:true});
let contentHash=document.getElementById(location.hash.slice(1))?.closest('#panel-qa') ? '' : location.hash;
function setView(view,{focus=false,anchor=null,writeHistory=true,restore=true}={}) {
  if(!availableViews.has(view)) view='content';
  if (anchor) view = availableViews.has('qa') && document.getElementById(anchor)?.closest('#panel-qa') ? 'qa' : 'content';
  clearTimeout(readingScrollTimer);
  positions[activeView]=activeView==='content'?lastReadingY:window.scrollY;
  if(activeView==='content' && location.hash && !document.getElementById(location.hash.slice(1))?.closest('#panel-qa')) contentHash=location.hash;
  activeView=view;
  tabs.forEach(tab=>{
    const selected=tab.id===`tab-${view}`;
    tab.setAttribute('aria-selected',selected); tab.tabIndex=selected?0:-1;
    const panel=$(`#${tab.getAttribute('aria-controls')}`);if(panel)panel.hidden=!selected;
  });
  $$('.reading-content > [role=tabpanel]').forEach(panel=>{panel.hidden=panel.id!==`panel-${view}`;});
  if($('.page-outline'))$('.page-outline').hidden=view!=='content';
  if($('.mobile-outline'))$('.mobile-outline').hidden=view!=='content';
  if(anchor && view==='content') contentHash=`#${anchor}`;
  if(writeHistory) {
    const url=new URL(location.href);
    if(view==='content') url.searchParams.delete('view'); else url.searchParams.set('view',view);
    url.hash=anchor ? `#${anchor}` : view==='content'?contentHash:'';
    history.pushState({view},'',url);
  }
  if(focus)($(`#tab-${view}`)||$('#panel-content')).focus({preventScroll:true});
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
  if(!link.hash)return;
  e.preventDefault(); if($('.mobile-outline'))$('.mobile-outline').open=false;
  setView('content',{anchor:link.hash.slice(1)});
}));
window.addEventListener('popstate',()=>setView(new URL(location.href).searchParams.get('view')||'content',{writeHistory:false,anchor:location.hash?location.hash.slice(1):null}));
window.addEventListener('hashchange',()=>{ if(location.hash && document.getElementById(location.hash.slice(1))) setView('content',{writeHistory:false,anchor:location.hash.slice(1)}); });
const initialView=new URL(location.href).searchParams.get('view');
if(initialView || location.hash) setView(initialView || 'content',{writeHistory:false,restore:false,anchor:location.hash.slice(1) || null});
const outlineLinks=$$('.page-outline a,.mobile-outline a');
// Observe each section with one shared observer.
const sectionObserver=new IntersectionObserver(entries=>{
  entries.forEach(entry=>{if(entry.isIntersecting){
    outlineLinks.forEach(link=>{const current=link.hash===`#${entry.target.querySelector('h2[id]')?.id || entry.target.id}`;link.classList.toggle('current',current);if(current)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
    const anchor=entry.target.querySelector('h2[id]')?.id || entry.target.id;
    const currentLink=$(`.page-outline a[href="#${anchor}"]`); if(currentLink && $('#mobile-current'))$('#mobile-current').textContent=currentLink.textContent.replace(/^\d+\. /,'');
  }});
},{rootMargin:'-15% 0px -65% 0px'});
$$('.lesson-section').forEach(section=>sectionObserver.observe(section));

// Scroll position, not a claim that the reader has completed or understood a lesson.
const readingProgress=$('.reading-progress');
let progressFrame=0;
function scheduleReadingProgress(){
  if(progressFrame||!readingProgress)return;
  progressFrame=requestAnimationFrame(()=>{
    progressFrame=0;
    const panel=$('#panel-'+activeView);if(!panel)return;
    const box=panel.getBoundingClientRect(),top=$('.topbar').getBoundingClientRect().bottom;
    const range=box.height-Math.max(1,innerHeight-top);
    const value=Math.round(Math.max(0,Math.min(1,range>0?(top-box.top)/range:(box.top<=top?1:0)))*100);
    readingProgress.firstElementChild.style.width=value+'%';readingProgress.setAttribute('aria-valuenow',value);
  });
}
window.addEventListener('scroll',scheduleReadingProgress,{passive:true});
window.addEventListener('resize',scheduleReadingProgress);
if(window.ResizeObserver)new ResizeObserver(scheduleReadingProgress).observe($('.reading-content'));
scheduleReadingProgress();


function chapterLink(chapter){
  const active=chapter.path===document.body.dataset.source;
  const link=document.createElement('a');link.textContent=chapter.title;
  if(active){link.href='#problem';link.setAttribute('aria-current','page');link.addEventListener('click',e=>{e.preventDefault();closeCurriculum();setView('content',{anchor:'problem'});});}
  else if(chapter.rendered){link.href=(document.body.dataset.base||'/')+chapter.path.replace(/\.md$/,'/');}
  else{link.href=sourceRoot+chapter.path;link.target='_blank';link.rel='noreferrer';link.setAttribute('aria-describedby','external-note');const cue=document.createElement('span');cue.className='external-cue';cue.textContent='GitHub ↗';link.append(cue);}
  return link;
}
// Curriculum scope is local to this page: the whole catalog remains one explicit action away.
const catalog=window.PLAYBOOK_CATALOG || [];
const currentTrack=catalog.find(topic=>document.body.dataset.source===topic.slug+'.md' || document.body.dataset.source?.startsWith(topic.slug+'/'));
let navigationScope=currentTrack?'track':'all';
const scopeControls=document.createElement('div');scopeControls.className='navigation-scope';
scopeControls.setAttribute('role','group');scopeControls.setAttribute('aria-label','Browse topics');
const trackButton=document.createElement('button');trackButton.type='button';trackButton.className='secondary-button';
trackButton.textContent=currentTrack?.title || 'This track';trackButton.hidden=!currentTrack;trackButton.setAttribute('aria-controls','topic-nav');
const allTopicsButton=document.createElement('button');allTopicsButton.type='button';allTopicsButton.className='secondary-button';
allTopicsButton.textContent='All topics';allTopicsButton.setAttribute('aria-controls','topic-nav');
scopeControls.append(trackButton,allTopicsButton);$('#topic-search').closest('.search-wrap').before(scopeControls);
const scopeHelp=$('.search-help');
function chooseNavigationScope(scope){
  navigationScope=scope;renderNavigation($('#topic-search').value.trim().toLowerCase());
}
trackButton.addEventListener('click',()=>chooseNavigationScope('track'));
allTopicsButton.addEventListener('click',()=>chooseNavigationScope('all'));
function renderNavigation(query=''){
  const nav=$('#topic-nav');nav.replaceChildren();let previousCategory='',count=0;
  const trackOnly=navigationScope==='track' && currentTrack;
  trackButton.setAttribute('aria-pressed',!!trackOnly);allTopicsButton.setAttribute('aria-pressed',!trackOnly);
  $('#curriculum-title').textContent=trackOnly?'Browse '+currentTrack.title:'All playbook topics';
  $('#topic-search').placeholder=trackOnly?'Find in '+currentTrack.title+'…':'Find across all topics…';
  $('#topic-search').setAttribute('aria-label',trackOnly?'Find a topic in '+currentTrack.title:'Find a topic across the playbook');
  scopeHelp.textContent=trackOnly?'Search titles and paths in this track. Choose All topics to browse the full catalog.':'Search titles and paths across the catalog. GitHub links open source chapters in a new tab.';
  const startLink=$('.learning-path');
  if(startLink){
    startLink.href=trackOnly?(document.body.dataset.base||'/')+currentTrack.slug+'/':(document.body.dataset.base||'/');
    startLink.removeAttribute('target');startLink.removeAttribute('aria-describedby');
    startLink.replaceChildren(document.createTextNode(trackOnly?currentTrack.title+' learning path →':'Choose a learning path →'));
  }
  for(const topic of (trackOnly?[currentTrack]:catalog)){
    const all=topic.title.toLowerCase().includes(query);
    const chapters=topic.chapters.filter(chapter=>!query||all||`${chapter.title} ${chapter.path} ${chapter.path.endsWith('/coroutines.md')?'suspend cancellation cancel viewmodelscope continuation async await':''}`.toLowerCase().includes(query));
    if(!chapters.length)continue;count+=chapters.length;
    if(!trackOnly && topic.category!==previousCategory){const label=document.createElement('p');label.className='nav-label';label.textContent=topic.category;nav.append(label);previousCategory=topic.category;}
    const group=document.createElement('details');group.className='nav-group';const here=document.body.dataset.source;group.open=!!query||here===topic.slug+'.md'||topic.chapters.some(c=>c.path===here);
    const summary=document.createElement('summary');const icon=document.createElement('span');icon.className='nav-icon';icon.textContent=topic.icon;icon.setAttribute('aria-hidden','true');
    const name=document.createElement('span');name.textContent=topic.title;const chevron=document.createElement('span');chevron.className='chevron';chevron.textContent='›';chevron.setAttribute('aria-hidden','true');summary.append(icon,name,chevron);group.append(summary);
    const children=document.createElement('div');children.className='nav-children';
    // Trees with lessons on this site open at their learning path; wide trees group by guided-reading phase.
    if(topic.chapters.some(c=>c.rendered)&&!query){const path=document.createElement('a');path.href=(document.body.dataset.base||'/')+topic.slug+'/';path.textContent='Learning path';if(here===topic.slug+'.md')path.setAttribute('aria-current','page');children.append(path);}
    if(!query&&new Set(chapters.map(c=>c.section)).size>1){
      let currentSection='',sectionGroup;
      for(const chapter of chapters){
        if(chapter.section!==currentSection){
          sectionGroup=document.createElement('details');sectionGroup.className='nav-group';
          sectionGroup.open=chapters.some(c=>c.path===here&&c.section===chapter.section);
          const heading=document.createElement('summary');heading.textContent=chapter.section;
          sectionGroup.append(heading);children.append(sectionGroup);currentSection=chapter.section;
        }
        sectionGroup.append(chapterLink(chapter));
      }
    }else chapters.forEach(c=>children.append(chapterLink(c)));
    group.append(children);nav.append(group);
  }
  $('#search-empty').hidden=count>0;
  $('#search-empty').textContent=trackOnly?'No matching topic in this track. Try All topics to search the complete catalog.':'No matching topic title or path. Try a broader search.';
  $('#search-status').textContent=query?`${count} matching topic${count===1?'':'s'} in ${trackOnly?currentTrack.title:'all topics'}. Search uses titles, paths and selected keywords, not full lesson text.`:`${count} chapters in ${trackOnly?currentTrack.title:'the full catalog'}.`;
}
renderNavigation();let searchTimer;
$('#topic-search').addEventListener('input',e=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>renderNavigation(e.target.value.trim().toLowerCase()),150);});
