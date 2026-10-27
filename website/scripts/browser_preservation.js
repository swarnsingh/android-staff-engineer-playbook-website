/** Read-only rendered audit. Invoke with diagram-sources.json and original-units.json.
 * Checks source-unit presence/order plus specific hiding and diagram readiness failures.
 * This is not a proof of contrast, arbitrary clipping, occlusion, or accessibility.
 * It never changes DOM, preferences, scroll positions, or disclosures.
 */
(async function inspectOriginalContent(expectedDiagrams = {}, unitManifest = {}, view = 'content', pairManifest = {}) {
  const panel = document.querySelector(view === 'qa' ? '#panel-qa' : '#panel-content');
  if (!panel || panel.hidden) return {problems: [`${view} must be present and selected`], checked: 0};
  const source = document.body.dataset.source || 'fixture';
  const allUnits = Array.isArray(unitManifest) ? unitManifest : unitManifest[source];
  const expectedUnits = allUnits?.filter(unit => unit.view ? unit.view === view : view === 'content');
  const problems = [], reported = new Set(), concealed = new Set();
  const ignore = '.blend,.correction-note,.code-header,.part-band,.steps-text,.qa-answer-label';
  const sourceZones = '.original-opening,section[id^="section-"]';
  let checked = 0, loadedDiagrams = 0;
  function report(element, why) {
    const section = element.closest('section[id]')?.id || 'page-title';
    const message = `${section}: ${why}`;
    if (!reported.has(message)) {reported.add(message);problems.push(message);}
    concealed.add(element);
  }
  function compact(text) { return (text || '').replace(/\s+/g, ''); }
  function folded(element) {
    for (let parent = element; parent; parent = parent.parentElement) {
      if (parent.tagName === 'DETAILS' && !parent.open && !parent.querySelector(':scope > summary')?.contains(element)) return true;
    }
    return false;
  }
  function inspect(element) {
    let opacity = 1;
    for (let ancestor = element; ancestor; ancestor = ancestor.parentElement) {
      const css = getComputedStyle(ancestor);
      opacity *= Number(css.opacity);
      if (['TEMPLATE','NOSCRIPT','SCRIPT','STYLE'].includes(ancestor.tagName) || ancestor.hidden || ancestor.getAttribute('aria-hidden') === 'true' || css.display === 'none' || ['hidden','collapse'].includes(css.visibility) || css.contentVisibility === 'hidden' || opacity <= 0.01) {
        report(element,'original content is hidden or nearly transparent');return;
      }
      const filterOpacity = [...css.filter.matchAll(/opacity\(([^)]+)\)/g)];
      if (filterOpacity.some(match => Number(match[1].replace('%','')) === 0)) {
        report(element,'original content is hidden by a filter');return;
      }
      if (/^inset\((?:50|100)%\)$/.test(css.clipPath) || /^rect\(0px[, ]+0px[, ]+0px[, ]+0px\)$/.test(css.clip)) {
        report(element,'original content is clipped out of view');return;
      }
      const rect = ancestor.getBoundingClientRect();
      if (['absolute','fixed'].includes(css.position) && (rect.right <= 0 || rect.left >= window.innerWidth || rect.bottom <= 0)) {
        report(element,'original content is positioned outside the reading viewport');return;
      }
      if (css.transform !== 'none' && (rect.right <= 0 || rect.left >= window.innerWidth)) {
        report(element,'original content is transformed outside the reading viewport');return;
      }
      if (Number((css.textIndent.match(/^-?[0-9.]+/) || [])[0]) <= -rect.width && ['hidden','clip'].includes(css.overflowX)) {
        report(element,'original content is indented outside a clipped box');return;
      }
    }
    const own = getComputedStyle(element);
    if (/rgba\([^)]*,\s*0(?:\.0+)?\)$/.test(own.color) || own.color === 'transparent' || own.webkitTextFillColor === 'transparent' || /rgba\([^)]*,\s*0(?:\.0+)?\)$/.test(own.webkitTextFillColor || '')) {
      report(element,'original text has a transparent fill');return;
    }
    if (folded(element)) {
      const code = element.closest('code[data-original-diagram-source]') || (element.matches('pre,details') ? element.querySelector('code[data-original-diagram-source]') : null);
      if (!code || expectedDiagrams[code.dataset.originalDiagramSource] !== code.textContent) report(element,'original prose or code is folded into a disclosure');
      return;
    }
    if (own.display !== 'contents' && ![...element.getClientRects()].some(r => r.width > 0 && r.height > 0)) report(element,'original content has no rendered area');
  }
  const title = document.querySelector('main .lesson-hero h1');
  if (!title) problems.push('Original page title is missing');else inspect(title);
  const zones = [...panel.querySelectorAll(sourceZones)];
  const seen = new Set();
  for (const zone of zones) {
    for (const element of [zone, ...zone.querySelectorAll('*')]) {
      if (seen.has(element) || !element.textContent.trim() || element.closest(ignore) || element.closest('script,style,button,summary,figcaption')) continue;
      seen.add(element);checked++;inspect(element);
    }
  }
  // Walk actual rendered text rather than textContent: templates, noscript, hidden descendants,
  // folded prose and labelled additions must not satisfy a missing original unit.
  const paired = view === 'qa' && !!panel.querySelector('[data-qa-answer-slot]');
  function rendered(element, owner = null) {
    // Pairing moves original nodes, while their source section/ordinal remains
    // explicit. Reconstruct the source reading order without changing the DOM.
    // Visibility is still inspected at each node's actual rendered location.
    if (owner && element !== owner && element.matches(sourceZones)) return '';
    if (owner && element.matches('.qa-answer-pair')) return '';
    if (owner && element.hasAttribute('data-qa-answer-slot')) {
      const key = element.dataset.qaAnswerSlot;
      if (key !== owner.id) return '';
      return [...panel.querySelectorAll('[data-original-answer-index]')]
        .filter(answer => answer.dataset.originalSection === key)
        .sort((a,b) => Number(a.dataset.originalAnswerIndex)-Number(b.dataset.originalAnswerIndex))
        .map(answer => rendered(answer, owner)).join(' ');
    }
    if (element.matches(ignore + ',template,noscript,script,style,button,summary,figcaption') || concealed.has(element) || folded(element) || !element.innerText) return '';
    let text = '';
    for (const child of element.childNodes) {
      if (child.nodeType === 3) text += child.textContent;
      else if (child.nodeType === 1) text += rendered(child, owner);
    }
    return text + ' ';
  }
  const stream = compact(paired
    ? [...zones].sort((a,b) => Number(a.dataset.sourceOrder ?? -1)-Number(b.dataset.sourceOrder ?? -1)).map(zone => rendered(zone,zone)).join(' ')
    : zones.filter(zone => !zone.parentElement?.closest(sourceZones)).map(zone => rendered(zone)).join(' '));
  // Independently verify which answer is displayed under which question. Source
  // order reconstruction alone must never permit a swapped or duplicated pair.
  const pairChecks = [];
  const expectedPairs = view === 'qa' ? (pairManifest[source] || []) : [];
  if (view === 'qa' && (paired || expectedPairs.length)) {
    const questions = [...panel.querySelectorAll('#section-probing-questions > ol > li')];
    const answers = [...panel.querySelectorAll('[data-original-answer-index]')];
    if (!expectedPairs.length) problems.push('Independent question/answer manifest is required');
    if (questions.length !== expectedPairs.length || answers.length !== expectedPairs.length) problems.push('Question/answer pair count differs from the source');
    if (panel.querySelectorAll('[data-qa-answer-slot]').length !== 1) problems.push('Expected exactly one original answer-list slot');
    const originalText = (node, question = false) => {
      if (node.nodeType === 3) return node.textContent;
      if (node.nodeType !== 1 || node.matches(ignore + ',script,style') || (question && node.matches('.qa-answer-pair'))) return '';
      return [...node.childNodes].map(child => originalText(child,question)).join('');
    };
    const digest = async text => [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text.replace(/\s+/g,' ').trim())))].map(b=>b.toString(16).padStart(2,'0')).join('');
    for (const [index, expected] of expectedPairs.entries()) {
      const question = questions[index], own = question?.querySelectorAll(':scope > .qa-answer-pair > ol > li') || [], answer = own[0], failures = [];
      if (!question || Number(question.dataset.qaQuestionIndex) !== expected.number) failures.push('question ordinal mismatch');
      if (own.length !== 1 || !answer || Number(answer.dataset.originalAnswerIndex) !== expected.number || Number(answer.parentElement.start) !== expected.number || answer.dataset.originalSection !== 'section-answer-key') failures.push('answer is not paired with its original question');
      if (question && await digest(originalText(question,true)) !== expected.question_sha256) failures.push('question changed or duplicated');
      if (answer && await digest(originalText(answer)) !== expected.answer_sha256) failures.push('answer changed or duplicated');
      pairChecks.push({number:expected.number,ok:!failures.length,problems:failures});
      failures.forEach(failure => problems.push('Question '+expected.number+': '+failure));
    }
  }
  let position = 0;
  if (!allUnits?.length) problems.push('Original-unit manifest is required; rendered preservation is unverified');
  else for (let i = 0; i < expectedUnits.length; i++) {
    const unit = expectedUnits[i];
    if (unit.title || (!unit.view && i === 0 && unit.kind === 'heading')) {
      if (compact(title?.innerText) !== compact(unit.text)) problems.push('Original title text is missing or changed');
      continue;
    }
    if (unit.kind === 'diagram') {
      const found = [...panel.querySelectorAll('code[data-original-diagram-source]')].some(code => expectedDiagrams[code.dataset.originalDiagramSource] === code.textContent && code.textContent.trimEnd() === unit.text.trimEnd());
      if (!found) problems.push('Original diagram source is missing or changed');
      continue;
    }
    const text = compact(unit.text);
    const at = stream.indexOf(text, position);
    if (at < 0) problems.push(`Original ${unit.kind} is not rendered in order: ${unit.text.slice(0, 90)}`);
    else position = at + text.length;
  }
  const images = [...panel.querySelectorAll('img[data-original-diagram]')];
  const diagramResources = [];
  for (const image of images) {
    // decode() can stay pending forever for an off-screen lazy image (Chrome 152), so the wait is
    // bounded. Restricted read-only runners may omit decode; either way an image that is still
    // incomplete is reported as unverified, never counted as loaded.
    let failed = false;
    if (typeof image.decode === 'function') {
      const decoded = image.decode().then(() => 'decoded', () => 'failed');
      const timeout = new Promise(resolve => setTimeout(resolve, 5000, 'pending'));
      failed = await Promise.race([decoded, timeout]) === 'failed';
    }
    const status = failed || (image.complete && !image.naturalWidth) ? 'failed' : image.complete && image.naturalWidth ? 'loaded' : 'not-ready';
    diagramResources.push({source: image.getAttribute('src'), status});
    if (status === 'loaded') loadedDiagrams++;
    else report(image, status === 'failed' ? 'original diagram image failed to load' : 'original diagram image has not loaded; resource validation is incomplete');
  }
  if (expectedUnits && images.length !== expectedUnits.filter(unit => unit.kind === 'diagram').length) problems.push('Original diagram image count does not match the source');
  return {source, view, checked, units: expectedUnits?.length || 0, diagrams: images.length, loadedDiagrams, diagramResources, pairChecks, problems};
})
