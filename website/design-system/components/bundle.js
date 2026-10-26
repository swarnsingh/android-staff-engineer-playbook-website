/* Playbook diagram runtime: one motion state, responsive layouts, FlowDiagram (looping) and FlowScene (stepped). No dependencies. */
(function () {
  var NS = 'http://www.w3.org/2000/svg';

  // One reactive motion state: the OS preference OR the reader's own setting (app.js toggles html.reduce-motion).
  var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  var subs = [];
  function reduced() { return !!(mq && mq.matches) || document.documentElement.classList.contains('reduce-motion'); }
  function notify() { var r = reduced(); subs.slice().forEach(function (f) { f(r); }); }
  if (mq) { if (mq.addEventListener) mq.addEventListener('change', notify); else if (mq.addListener) mq.addListener(notify); }
  if (window.MutationObserver) new MutationObserver(notify).observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  var motion = { reduced: reduced, subscribe: function (f) { subs.push(f); return function () { subs = subs.filter(function (g) { return g !== f; }); }; } };

  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  var uid = 0;
  // Smallest text in each layout, in drawing units (kept in step with bundle.css), and the smallest size it may render at.
  // A layout is used only if, at the scale it would render, handwritten labels stay >= 15px and other text >= 12px.
  var TEXT = { wide: { hand: 17, sans: 13 }, narrow: { hand: 19, sans: 15 } }, MIN = { hand: 15, sans: 12 };
  function needScale(key) { return Math.max(MIN.hand / TEXT[key].hand, MIN.sans / TEXT[key].sans); }
  function pickLayout(root, data) {
    if (!data.layouts) data.layouts = autoLayouts(data);
    var paper = root.querySelector('.pb-paper') || root, size = data.layouts.wide.size[0];
    var scale = Math.min(paper.clientWidth, size * 1.2) / size;
    return scale >= needScale('wide') ? 'wide' : 'narrow';
  }

  // Row flows (nodes in order, edges only between neighbours) need no hand-drawn layouts:
  // the wide layout is a row with forward edges above and return edges below; the narrow one is the same flow as a column.
  function autoLayouts(data) {
    var n = data.nodes.length, tall = data.nodes.some(function (x) { return x.chips || x.queue; }), h = tall ? 84 : 66;
    if (n < 2 || n > 5) throw new Error('Generated row flows take 2 to 5 nodes; give layouts.wide and layouts.narrow for this diagram.');
    var gap = 84, W = 48 + n * 168 + (n - 1) * gap, y = 78, ny = function (i) { return 26 + i * (h + 56); }; // 84 units leave room for a curve and its label
    var wide = { size: [W, y + h + 88], nodes: {}, edges: {}, labels: [], order: [] };
    var narrow = { size: [320, ny(n - 1) + h + 64], nodes: {}, edges: {}, labels: [], order: [], pk: { dx: 10, dy: 5, anchor: 'start' } };
    var at = {};
    data.nodes.forEach(function (node, i) {
      at[node.id] = i;
      wide.nodes[node.id] = { x: 24 + i * (168 + gap), y: y, w: 168, h: h };
      narrow.nodes[node.id] = { x: 40, y: ny(i), w: 240, h: h };
    });
    var count = 0;
    (data.edges || []).forEach(function (e) {
      var a = at[e.from], b = at[e.to], back = (e.lane || (e.tone === 'back' ? 'back' : 'fwd')) === 'back';
      var lo = Math.min(a, b), hi = Math.max(a, b);
      if (hi - lo !== 1) throw new Error('Auto layout needs neighbouring nodes: ' + e.id);
      var down = b > a, W = wide.nodes, N = narrow.nodes;
      var xl = W[data.nodes[lo].id].x + 170, xr = W[data.nodes[hi].id].x - 2, yy = back ? y + h - 18 : y + 18, cy = back ? y + h + 8 : y - 8;
      var x1 = down ? xl : xr, x2 = down ? xr : xl, mid = (xl + xr) / 2;
      wide.edges[e.id] = 'M' + x1 + ' ' + yy + ' C' + (x1 + (down ? 30 : -30)) + ' ' + cy + ' ' + (x2 + (down ? -30 : 30)) + ' ' + cy + ' ' + x2 + ' ' + yy;
      var yt = N[data.nodes[lo].id].y + h + 2, yb = N[data.nodes[hi].id].y - 2, lx = back ? 202 : 118, cx = back ? 218 : 102;
      var y1 = down ? yt : yb, y2 = down ? yb : yt, nmid = (yt + yb) / 2;
      narrow.edges[e.id] = 'M' + lx + ' ' + y1 + ' C' + cx + ' ' + (y1 + (down ? 18 : -18)) + ' ' + cx + ' ' + (y2 + (down ? -18 : 18)) + ' ' + lx + ' ' + y2;
      if (e.label) {
        wide.labels.push({ x: mid, y: back ? y + h + 36 : y - 18, text: e.label, tone: e.tone });
        narrow.labels.push({ x: back ? 228 : 92, y: nmid + 6, text: e.label, tone: e.tone, anchor: back ? 'start' : 'end' });
      }
      if (e.tone) {
        count++;
        wide.order.push({ x: down ? xl - 16 : xr + 16, y: back ? y + h + 32 : y - 22, n: count });
        narrow.order.push({ x: back ? 180 : 140, y: nmid, n: count });
      }
    });
    if (data.note) {
      wide.labels.push({ x: W / 2, y: wide.size[1] - 12, text: data.note.wide || data.note });
      narrow.labels.push({ x: 160, y: narrow.size[1] - 14, text: data.note.narrow || data.note });
    }
    return { wide: wide, narrow: narrow };
  }

  function draw(svg, data, key) {
    if (!data.layouts) data.layouts = autoLayouts(data);
    var L = data.layouts[key], id = 'pb' + (++uid);
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute('viewBox', '0 0 ' + L.size[0] + ' ' + L.size[1]);
    svg.setAttribute('data-layout', key);
    // Never scale far past the drawn size: the stacked layout stops at phone scale, the wide one at 1.2x.
    svg.style.maxWidth = key === 'narrow' ? '440px' : Math.round(L.size[0] * 1.2) + 'px'; svg.style.marginInline = 'auto';
    var defs = el('defs', {}, svg);
    var f = el('filter', { id: id + 'r', x: '-4%', y: '-12%', width: '108%', height: '124%' }, defs);
    el('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.035', numOctaves: '2', seed: '5' }, f);
    el('feDisplacementMap', { 'in': 'SourceGraphic', scale: '2.2' }, f);
    ['rest', 'fwd', 'back', 'stuck'].forEach(function (t) {
      var m = el('marker', { id: id + 'h' + t, viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto' }, defs);
      el('path', { 'class': 'pb-head ' + t, d: 'M0 1 L9 5 L0 9 z' }, m);
    });
    (L.regions || []).forEach(function (r) {
      var g = el('g', { 'class': 'pb-region' }, svg);
      el('rect', { x: r.x, y: r.y, width: r.w, height: r.h, rx: 14 }, g);
      el('text', { x: r.x + 12, y: r.y + 20 }, g).textContent = r.label;
    });
    var ref = { id: id, L: L, edges: {}, nodes: {} };
    var gE = el('g', {}, svg);
    Object.keys(L.edges).forEach(function (k) { ref.edges[k] = el('path', { 'class': 'pb-edge', d: L.edges[k], 'marker-end': 'url(#' + id + 'hrest)' }, gE); });
    var gN = el('g', {}, svg);
    data.nodes.forEach(function (n) {
      var p = L.nodes[n.id], g = el('g', { 'class': 'pb-node' }, gN);
      el('rect', { x: p.x, y: p.y, width: p.w, height: p.h, rx: 10, filter: 'url(#' + id + 'r)' }, g);
      el('text', { 'class': 't', x: p.x + 14, y: p.y + 27 }, g).textContent = n.label;
      var rec = { g: g, sub: el('text', { 'class': 's', x: p.x + 14, y: p.y + 47 }, g), chips: {}, dots: [] };
      if (n.chips) {
        var cw = Math.min(88, (p.w - 36) / 2);
        n.chips.forEach(function (c, i) {
          var cg = el('g', { 'class': 'pb-chip' }, g), cx = p.x + 14 + i * (cw + 8);
          el('rect', { x: cx, y: p.y + 56, width: cw, height: 24, rx: 12 }, cg);
          rec.chips[c] = { g: cg, t: el('text', { x: cx + cw / 2, y: p.y + 72 }, cg) };
        });
      }
      if (n.queue) for (var i = 0; i < 3; i++) rec.dots.push(el('circle', { 'class': 'pb-q', cx: p.x + 22 + i * 16, cy: p.y + p.h - 18, r: 6, opacity: 0 }, g));
      ref.nodes[n.id] = rec;
    });
    (L.labels || []).forEach(function (t) {
      var lines = String(t.text).split('\n');
      lines.forEach(function (line, i) {
        el('text', { 'class': 'pb-label ' + (t.tone || ''), x: t.x, y: t.y - (lines.length - 1 - i) * 18, 'text-anchor': t.anchor || 'middle' }, svg).textContent = line;
      });
    });
    var gO = el('g', { 'class': 'pb-order' }, svg);
    (L.order || []).forEach(function (o) { el('circle', { cx: o.x, cy: o.y, r: key === 'narrow' ? 11 : 9 }, gO); el('text', { x: o.x, y: o.y + 4 }, gO).textContent = o.n; });
    ref.packets = el('g', {}, svg);
    return ref;
  }

  function paint(ref, state, changed, still) {
    for (var id in ref.nodes) {
      var n = ref.nodes[id], v = (state.nodes || {})[id] || ['', ''];
      n.g.setAttribute('class', 'pb-node ' + v[0]);
      n.sub.textContent = v[1];
      for (var c in n.chips) {
        var st = (state.chips || {})[c] || 'idle';
        n.chips[c].g.setAttribute('class', 'pb-chip ' + st);
        n.chips[c].t.textContent = c + ' ' + st;
      }
      n.dots.forEach(function (d, i) { d.setAttribute('opacity', i < (state.queue || 0) ? 1 : 0); });
    }
    if (!still) (changed || []).forEach(function (id) {
      var g = ref.nodes[id] && ref.nodes[id].g;
      if (g) { g.classList.remove('pulse'); void g.getBoundingClientRect(); g.classList.add('pulse'); }
    });
  }
  function setEdge(ref, key, tone, moving) {
    var e = ref.edges[key];
    if (!e) return;
    e.setAttribute('class', 'pb-edge' + (tone ? ' ' + tone : '') + (moving ? ' moving' : ''));
    e.setAttribute('marker-end', 'url(#' + ref.id + 'h' + (tone || 'rest') + ')');
  }
  function packet(ref, tone, label) {
    var g = el('g', { 'class': 'pb-pk ' + tone, opacity: 0 }, ref.packets);
    if (tone === 'back') el('path', { d: 'M0 -7 L7 0 L0 7 L-7 0 z' }, g); else el('circle', { r: 6.5 }, g);
    if (label) {
      var pk = ref.L.pk || { dx: 0, dy: -12, anchor: 'middle' };
      el('text', { x: pk.dx, y: pk.dy, 'text-anchor': pk.anchor }, g).textContent = label;
    }
    return g;
  }
  function place(ref, g, key, k) {
    var path = ref.edges[key], len = path.getTotalLength();
    var e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2, pt = path.getPointAtLength(e * len);
    g.setAttribute('transform', 'translate(' + pt.x + ' ' + pt.y + ')');
    g.setAttribute('opacity', k < .1 ? k * 10 : k > .9 ? (1 - k) * 10 : 1);
  }
  function watch(root, onVisible, onResize) {
    var io = window.IntersectionObserver ? new IntersectionObserver(function (es) { es.forEach(function (e) { onVisible(e.isIntersecting); }); }) : null;
    if (io) io.observe(root);
    var ro = window.ResizeObserver ? new ResizeObserver(onResize) : null;
    if (ro) ro.observe(root); else window.addEventListener('resize', onResize);
  }

  // At most one diagram moves at a time. Loops register in document order; the first visible one that may move plays on
  // its own, the rest stay still with a Play button. Pressing Play on any diagram, or stepping a scene, takes the turn.
  var loops = [], owner = null;
  function eligible(c) { return c.visible && !c.userPaused && (!motion.reduced() || c.userPlayed); }
  function allowed(c) {
    if (owner) return owner === c && eligible(c);
    for (var i = 0; i < loops.length; i++) if (eligible(loops[i])) return loops[i] === c;
    return false;
  }
  function syncLoops() { loops.forEach(function (c) { c.sync(); }); }
  function claim(c) { if (owner !== c) { owner = c; syncLoops(); } }
  function release(c) { if (owner === c) { owner = null; syncLoops(); } }
  motion.subscribe(function (r) { if (r) loops.forEach(function (c) { c.userPlayed = false; }); syncLoops(); });

  // FlowDiagram: streams loop on their edges while running; the still version shows order markers instead.
  function FlowDiagram(root, data) {
    var svg = root.querySelector('svg'), btn = root.querySelector('[data-toggle]');
    var ref, key, raf = 0, live = [];
    var me = { visible: true, userPaused: false, userPlayed: false, sync: function () { if (ref) sync(); } };
    loops.push(me);
    function running() { return allowed(me); }
    function sync() {
      var run = running();
      cancelAnimationFrame(raf); raf = 0;
      while (ref.packets.firstChild) ref.packets.removeChild(ref.packets.firstChild);
      live = [];
      root.classList.toggle('is-still', !run);
      Object.keys(ref.edges).forEach(function (k) { setEdge(ref, k, null, false); });
      data.streams.forEach(function (s) {
        setEdge(ref, s.edge, s.tone, run);
        if (!run) return;
        var count = s.count || 3, period = (s.period || 2.4) * 1000;
        for (var i = 0; i < count; i++) live.push({ s: s, g: packet(ref, s.tone, s.label), phase: i / count, period: period });
      });
      btn.textContent = run ? 'Pause' : 'Play';
      btn.setAttribute('aria-pressed', run ? 'false' : 'true');
      if (run) raf = requestAnimationFrame(tick);
    }
    function tick(ts) {
      live.forEach(function (p) { place(ref, p.g, p.s.edge, (ts / p.period + p.phase) % 1); });
      raf = requestAnimationFrame(tick);
    }
    function build() { key = pickLayout(root, data); ref = draw(svg, data, key); paint(ref, data.state, [], true); sync(); }
    btn.addEventListener('click', function () {
      if (running()) { me.userPaused = true; me.userPlayed = false; } else { me.userPaused = false; me.userPlayed = true; }
      owner = me; syncLoops(); // pausing keeps the turn, so pausing one diagram never starts another
    });
    watch(root, function (v) {
      if (v === me.visible) return;
      me.visible = v;
      if (!v && owner === me) owner = null;
      syncLoops();
    }, function () { if (pickLayout(root, data) !== key) build(); });
    build();
  }

  // FlowScene: one system stepped through; packets land and change state. Pause or leaving the screen finishes the step at once.
  function FlowScene(root, data) {
    var svg = root.querySelector('svg'), countEl = root.querySelector('.pb-count'), capEl = root.querySelector('.pb-caption p'),
      bar = root.querySelector('.pb-progress i'), list = root.querySelector('.pb-steps ol');
    var btn = {}; root.querySelectorAll('[data-act]').forEach(function (b) { btn[b.dataset.act] = b; });
    var mode = Object.keys(data.modes)[0], idx = 0, token = 0, flying = false, playing = false, timer = 0, ref, key;
    var me = {};
    function track() { return data.modes[mode]; }
    function stateAt(k) {
      var s = JSON.parse(JSON.stringify(track().initial));
      for (var i = 0; i <= k; i++) {
        var set = track().steps[i].set || {};
        if (set.nodes) for (var id in set.nodes) s.nodes[id] = set.nodes[id];
        if (set.chips) for (var c in set.chips) s.chips[c] = set.chips[c];
        if (set.queue != null) s.queue = set.queue;
      }
      return s;
    }
    function edgesFor(step, moving) {
      Object.keys(ref.edges).forEach(function (k) { setEdge(ref, k, null, false); });
      (step.packets || []).forEach(function (p) { setEdge(ref, p.edge, p.tone, moving); });
    }
    function settle() { // show the current step's final state with no motion
      token++; flying = false; root.classList.remove('is-moving');
      while (ref.packets.firstChild) ref.packets.removeChild(ref.packets.firstChild);
      paint(ref, stateAt(idx), [], true); edgesFor(track().steps[idx], false);
    }
    function ui() {
      var n = track().steps.length;
      countEl.textContent = 'Step ' + (idx + 1) + ' of ' + n;
      capEl.innerHTML = track().steps[idx].caption;
      bar.style.width = ((idx + 1) / n * 100) + '%';
      btn.prev.disabled = idx === 0; btn.next.disabled = idx === n - 1;
      btn.play.textContent = playing ? 'Pause' : (idx === n - 1 ? 'Replay' : 'Play');
      btn.play.setAttribute('aria-pressed', playing ? 'true' : 'false');
    }
    function fly(p, my) {
      return new Promise(function (done) {
        var g = packet(ref, p.tone, p.label), t0 = null;
        function frame(ts) {
          if (my !== token) { if (g.parentNode) g.parentNode.removeChild(g); return done(false); }
          if (t0 === null) t0 = ts;
          var k = Math.min(1, (ts - t0) / 950);
          place(ref, g, p.edge, k);
          if (k < 1) requestAnimationFrame(frame); else { g.parentNode.removeChild(g); done(true); }
        }
        requestAnimationFrame(frame);
      });
    }
    function go(i, animate) {
      settle(); idx = i; ui();
      var step = track().steps[i], my = token, changed = Object.keys((step.set || {}).nodes || {});
      if (!animate || motion.reduced() || !(step.packets || []).length) {
        paint(ref, stateAt(i), changed, !animate || motion.reduced()); edgesFor(step, false);
        return Promise.resolve(true);
      }
      paint(ref, stateAt(i - 1), [], true); edgesFor(step, true);
      flying = true; root.classList.add('is-moving');
      return step.packets.reduce(function (pr, p) {
        return pr.then(function (ok) { return ok && my === token ? fly(p, my) : false; });
      }, Promise.resolve(true)).then(function (ok) {
        if (!ok || my !== token) return false;
        flying = false; root.classList.remove('is-moving');
        paint(ref, stateAt(i), changed, false); edgesFor(step, false);
        return true;
      });
    }
    function stop() { playing = false; clearTimeout(timer); timer = 0; if (flying) settle(); ui(); }
    function loop() {
      if (!playing) return;
      if (idx >= track().steps.length - 1) { stop(); return; }
      go(idx + 1, true).then(function (ok) { if (ok && playing) timer = setTimeout(loop, 2600); });
    }
    btn.next.addEventListener('click', function () { stop(); claim(me); if (idx < track().steps.length - 1) go(idx + 1, true); });
    btn.prev.addEventListener('click', function () { stop(); if (idx > 0) go(idx - 1, false); });
    btn.reset.addEventListener('click', function () { stop(); go(0, false); });
    btn.play.addEventListener('click', function () {
      if (playing) { stop(); return; }
      playing = true; claim(me);
      if (idx >= track().steps.length - 1) go(0, false);
      ui(); timer = setTimeout(loop, 400);
    });
    root.querySelectorAll('[data-mode]').forEach(function (b) {
      b.addEventListener('click', function () {
        stop(); mode = b.dataset.mode;
        root.querySelectorAll('[data-mode]').forEach(function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); });
        fillList(); go(0, false);
      });
    });
    function fillList() {
      list.innerHTML = '';
      track().steps.forEach(function (s) { var li = document.createElement('li'); li.innerHTML = s.caption; list.appendChild(li); });
    }
    function build() { key = pickLayout(root, data); ref = draw(svg, data, key); settle(); }
    motion.subscribe(function (r) { if (r && flying) settle(); });
    watch(root, function (v) { if (!v) { if (playing || flying) stop(); release(me); } }, function () { if (pickLayout(root, data) !== key) { stop(); build(); } });
    key = pickLayout(root, data); ref = draw(svg, data, key);
    fillList(); go(0, false);
  }

  function WideDiagram(root) {
    var box = root.querySelector('.pb-wide');
    function sync() {
      var more = box.scrollWidth > box.clientWidth + 1;
      root.classList.toggle('is-scrollable', more);
      root.classList.toggle('at-start', box.scrollLeft <= 1);
      root.classList.toggle('at-end', box.scrollLeft + box.clientWidth >= box.scrollWidth - 1);
      if (more) {
        box.setAttribute('tabindex', '0'); box.setAttribute('role', 'region');
        box.setAttribute('aria-label', (box.dataset.label || 'Diagram') + ', scrolls sideways');
      } else { box.removeAttribute('tabindex'); box.removeAttribute('role'); box.removeAttribute('aria-label'); }
    }
    box.addEventListener('scroll', sync, { passive: true });
    if (window.ResizeObserver) new ResizeObserver(sync).observe(box); else window.addEventListener('resize', sync);
    sync();
  }

  function mountAll(scope) {
    (scope || document).querySelectorAll('[data-pb-wide]').forEach(function (root) { if (!root.__pb) { root.__pb = true; WideDiagram(root); } });
    (scope || document).querySelectorAll('[data-pb-flow]').forEach(function (root) {
      if (root.__pb) return; root.__pb = true;
      try {
        var data = JSON.parse(root.querySelector('script[type="application/json"]').textContent);
        (root.dataset.pbFlow === 'scene' ? FlowScene : FlowDiagram)(root, data);
      } catch (e) { // one broken diagram must not stop the others; its caption and text alternative still read
        root.classList.add('pb-error');
        if (window.console) console.error('Playbook diagram failed to mount:', e.message, root);
      }
    });
  }
  window.Playbook = { motion: motion, FlowDiagram: FlowDiagram, FlowScene: FlowScene, WideDiagram: WideDiagram, mountAll: mountAll };
})();
