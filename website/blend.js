'use strict';
// Step-through animations for the website's teaching layer.
//
// Markup (written in website/content/blend/*.blend):
//   <figure class="stepper" data-title="…">
//     <div class="stage">… elements marked data-el="id" (shown/hidden, data-state) and
//                            data-text="id" (text replaced per step) …</div>
//     <script type="application/json" class="steps">[{label, caption, add, remove, state, text, handoff}, …]</script>
//   </figure>
// Each step changes the previous frame: `add`/`remove` list data-el ids to show or hide,
// `state` sets data-state on data-el elements, `text` replaces the text of data-text elements. Frames are always
// folded from step 1, so any step can be shown directly. The build also prints every
// step as a numbered list, so the explanation never depends on JavaScript or motion.
(function () {
  const reducedMotion = () => window.Playbook ? window.Playbook.motion.reduced() : typeof effectiveReducedMotion !== 'undefined' && effectiveReducedMotion;

  function frames(steps, ids) {
    const visible = new Set(), state = {}, text = {};
    return steps.map(step => {
      (step.add || []).forEach(id => visible.add(id));
      (step.remove || []).forEach(id => visible.delete(id));
      Object.assign(state, step.state || {});
      Object.assign(text, step.text || {});
      ids.forEach(id => { if (!(id in state)) state[id] = ''; });
      return { visible: new Set(visible), state: { ...state }, text: { ...text }, step };
    });
  }

  function setup(figure) {
    const json = figure.querySelector('script.steps');
    if (!json) return;
    const steps = JSON.parse(json.textContent);
    const elements = [...figure.querySelectorAll('[data-el]')];
    const byId = Object.fromEntries(elements.map(el => [el.dataset.el, el]));
    const all = frames(steps, Object.keys(byId));
    const texts = [...figure.querySelectorAll('[data-text]')];
    const original = Object.fromEntries(texts.map(el => [el.dataset.text, el.textContent]));
    let position = 0, timer = null, shown = 0, flight = null;
    const stage = figure.querySelector('.stage');

    // A transfer must be authored explicitly as handoff: {from, to}. Active state alone does not mean data moved.
    function cancelFlight() {
      if (!flight) return;
      flight.cancel(); flight.effect.target.remove(); flight = null;
      if (!timer) { $('[data-act=play]').textContent = 'Play'; $('[data-act=play]').setAttribute('aria-pressed', 'false'); }
    }
    function handoff(prev, next) {
      if (figure.hasAttribute('data-no-handoff') || reducedMotion() || !prev || !next || !stage.animate) return;
      const transfer = next.step.handoff;
      if (!transfer) return;
      const live = (frame, el) => frame.visible.has(el.dataset.el);
      const from = byId[transfer.from], to = byId[transfer.to];
      if (!from || !to || from === to || !live(prev, from) || !live(next, from) || !live(next, to)) return;
      const box = stage.getBoundingClientRect(), a = from.getBoundingClientRect(), b = to.getBoundingClientRect();
      const at = r => `translate(${r.left - box.left + r.width / 2}px, ${r.top - box.top + r.height / 2}px)`;
      const dot = document.createElement('span');
      dot.className = 'stepper-packet' + (next.state[to.dataset.el] === 'active' ? '' : ' is-warn');
      dot.setAttribute('aria-hidden', 'true');
      stage.appendChild(dot);
      flight = dot.animate([{ transform: at(a), opacity: 0 }, { opacity: 1, offset: .15 }, { opacity: 1, offset: .85 }, { transform: at(b), opacity: 0 }],
        { duration: 750, easing: 'cubic-bezier(.45, 0, .55, 1)' });
      $('[data-act=play]').textContent = 'Pause'; $('[data-act=play]').setAttribute('aria-pressed', 'true');
      flight.onfinish = () => { dot.remove(); flight = null; if (!timer) { $('[data-act=play]').textContent = 'Play'; $('[data-act=play]').setAttribute('aria-pressed', 'false'); } };
    }

    const controls = document.createElement('div');
    controls.className = 'stepper-controls';
    controls.innerHTML = '<div class="stepper-status"><span class="stepper-count"></span><p class="stepper-caption" aria-live="polite"></p></div>' +
      '<div class="stepper-buttons"><button type="button" class="secondary-button" data-act="prev">← Previous</button>' +
      '<button type="button" class="primary-button" data-act="play" aria-pressed="false">Play</button>' +
      '<button type="button" class="secondary-button" data-act="next">Next →</button>' +
      '<button type="button" class="text-button" data-act="reset">Replay ↺</button></div>';
    figure.querySelector('.stage').after(controls);
    const $ = selector => controls.querySelector(selector);

    function render(animate) {
      cancelFlight();
      const frame = all[position], before = all[shown];
      elements.forEach(el => {
        const id = el.dataset.el;
        el.classList.toggle('is-off', !frame.visible.has(id));
        if (frame.state[id]) el.dataset.state = frame.state[id]; else delete el.dataset.state;
      });
      texts.forEach(el => { const id = el.dataset.text; el.textContent = id in frame.text ? frame.text[id] : original[id]; });
      figure.dataset.step = String(position + 1);
      $('.stepper-count').textContent = `Step ${position + 1} of ${all.length}` + (frame.step.label ? ` · ${frame.step.label}` : '');
      $('.stepper-caption').textContent = frame.step.caption || '';
      $('[data-act=prev]').setAttribute('aria-disabled', position === 0);
      $('[data-act=next]').setAttribute('aria-disabled', position === all.length - 1);
      $('[data-act=play]').setAttribute('aria-disabled', reducedMotion());
      if (animate && position === shown + 1) handoff(before, frame);
      shown = position;
    }
    function stop() {
      clearInterval(timer); timer = null; cancelFlight();
      $('[data-act=play]').textContent = 'Play'; $('[data-act=play]').setAttribute('aria-pressed', 'false');
    }
    const turn = window.Playbook?.registerSteps(stop);
    function go(delta) { stop(); if (delta > 0) turn?.claim(); position = Math.max(0, Math.min(all.length - 1, position + delta)); render(delta > 0); }
    controls.addEventListener('click', event => {
      const act = event.target.closest('button')?.dataset.act;
      if (act === 'prev') go(-1);
      if (act === 'next') go(1);
      if (act === 'reset') { stop(); position = 0; render(); }
      if (act === 'play') {
        if (reducedMotion()) { if (typeof toast === 'function') toast('Reduced motion is on. Use Previous and Next to see every step.'); return; }
        if (timer || flight) { stop(); return; }
        turn?.claim();
        if (position === all.length - 1) position = 0;
        render();
        $('[data-act=play]').textContent = 'Pause'; $('[data-act=play]').setAttribute('aria-pressed', 'true');
        timer = setInterval(() => {
          if (reducedMotion()) { stop(); return; }
          position++; render(true); if (position === all.length - 1) { clearInterval(timer); timer = null; if (!flight) { $('[data-act=play]').textContent = 'Play'; $('[data-act=play]').setAttribute('aria-pressed', 'false'); } }
        }, 2600);
      }
    });
    // Stop with every other animation (dialogs open, reduced motion turned on), and keep Play's state current.
    if (typeof animationStops !== 'undefined') animationStops.push(stop);
    document.addEventListener('playbook:motion', () => {
      if (reducedMotion()) stop();
      $('[data-act=play]').setAttribute('aria-disabled', reducedMotion());
    });
    new IntersectionObserver(entries => { if (!entries[0].isIntersecting) { stop(); turn?.release(); } }).observe(figure);
    window.addEventListener('resize', cancelFlight);
    document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
    figure.classList.add('is-ready');
    render();
  }

  document.querySelectorAll('figure.stepper').forEach(setup);
})();

// Design-system diagrams (website/design-system): moving diagrams, and static Mermaid figures that keep a readable size.
(() => {
  // Mermaid draws text at 16px. Rendering a figure at no less than 0.75 of its drawn width keeps that text at 12px or more;
  // narrower screens scroll the figure sideways instead of shrinking it.
  document.querySelectorAll('.source-diagram img[data-original-diagram], .original-diagram img[data-original-diagram]').forEach(img => {
    const box = img.closest('.source-diagram, .original-diagram');
    fetch(img.src).then(r => r.ok ? r.text() : '').then(svg => {
      const m = /viewBox="[-\d.]+ [-\d.]+ ([\d.]+)/.exec(svg);
      if (!m) return;
      img.style.minWidth = Math.round(parseFloat(m[1]) * 0.75) + 'px';
      img.classList.add('is-sized');
      box.setAttribute('data-pb-wide', '');
      box.dataset.label = img.alt || 'Diagram';
      if (window.Playbook) window.Playbook.mountAll(box.parentNode);
    }).catch(() => {});
  });
  // Code cards: mark cards whose lines run past the edge, so theme.css can fade the hidden edge and show a hint.
  document.querySelectorAll('.code-card pre').forEach(pre => {
    const card = pre.closest('.code-card');
    const sync = () => {
      const more = pre.scrollWidth > pre.clientWidth + 1;
      card.classList.toggle('is-scrollable', more);
      card.classList.toggle('at-end', pre.scrollLeft + pre.clientWidth >= pre.scrollWidth - 1);
    };
    pre.addEventListener('scroll', sync, { passive: true });
    if (window.Playbook) window.Playbook.observeResize(pre, sync);
    new MutationObserver(sync).observe(document.body, { attributes: true, attributeFilter: ['class'] }); // the reader's wrap setting
    sync();
  });
  if (window.Playbook) window.Playbook.mountAll(document);
})();
