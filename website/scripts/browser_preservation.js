/** Read-only browser audit. Evaluate this function after the Content view finishes loading.
 * Static source/order/heading checks remain in check_preservation.py; this checks actual CSS.
 * Returns JSON evidence and never changes DOM, preferences, scroll position or disclosures.
 */
(async function inspectOriginalContent(expectedDiagrams = {}) {
  const panel = document.querySelector('#panel-content');
  if (!panel || panel.hidden) return {problems: ['Content must be present and selected'], checked: 0};
  const problems = [], reported = new Set();
  const ignore = '.blend,.correction-note,.code-header,.part-band,.steps-text';
  const sourceZones = '.original-opening,section[id^="section-"]';
  let checked = 0, diagrams = 0;
  function report(element, why) {
    const section = element.closest('section[id]')?.id || 'page-title';
    const message = `${section}: ${why}`;
    if (!reported.has(message)) {reported.add(message);problems.push(message);}
  }
  async function inspect(node) {
    const element = node;
    let folded = false;
    for (let ancestor = element; ancestor; ancestor = ancestor.parentElement) {
      const css = getComputedStyle(ancestor);
      if (ancestor.hidden || ancestor.getAttribute('aria-hidden') === 'true' || css.display === 'none' || ['hidden','collapse'].includes(css.visibility) || Number(css.opacity) === 0 || css.contentVisibility === 'hidden') {
        report(element,'original content is hidden by CSS or an accessibility attribute');
        return;
      }
      if (css.clipPath === 'inset(50%)' || /^rect\(0px[, ]+0px[, ]+0px[, ]+0px\)$/.test(css.clip)) {
        report(element,'original content is clipped out of view');return;
      }
      if (ancestor.tagName === 'DETAILS' && !ancestor.open && !ancestor.querySelector(':scope > summary')?.contains(element)) folded = true;
    }
    if (folded) {
      // Only a real diagram's exact source is allowed behind an original-diagram disclosure.
      const code = element.closest('code[data-original-diagram-source]');
      const containerCode = element.matches('pre,details') ? element.querySelector('code[data-original-diagram-source]') : null;
      const sourceCode = code || containerCode;
      if (!sourceCode || expectedDiagrams[sourceCode.dataset.originalDiagramSource] !== sourceCode.textContent) report(element,'original prose or code is folded into a disclosure');
      return;
    }
    if (getComputedStyle(element).display !== 'contents' && ![...element.getClientRects()].some(r => r.width > 0 && r.height > 0)) report(element,'original content has no rendered area');
  }
  const title = document.querySelector('main .lesson-hero h1');
  if (!title) problems.push('Original page title is missing');else await inspect(title);
  const seen = new Set();
  for (const zone of panel.querySelectorAll(sourceZones)) {
    for (const element of [zone, ...zone.querySelectorAll('*')]) {
      if (seen.has(element) || !element.textContent.trim() || element.closest(ignore) || element.closest('script,style,button,summary,figcaption')) continue;
      seen.add(element);checked++;await inspect(element);
    }
  }
  for (const image of panel.querySelectorAll('img[data-original-diagram]')) {
    diagrams++;
    if (image.complete && !image.naturalWidth) report(image,'original diagram image failed to load');
  }
  return {source: document.body.dataset.source || 'fixture', checked, diagrams, problems};
})
