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

  // Original SVG objects: a scene's data chooses the object and its visible state.
  // No flow, queue length or runtime outcome is inferred from a node becoming active.
  function illustrate(g, kind, value, status) {
    while (g.firstChild) g.removeChild(g.firstChild);
    value = value || {};
    g.setAttribute('opacity', value.visible === false ? '.18' : '1');
    function shape(tag, attrs, cls) { attrs['class'] = cls || 'art-outline'; return el(tag, attrs, g); }
    function rect(x,y,w,h,r,cls) { return shape('rect',{x:x,y:y,width:w,height:h,rx:r},cls); }
    function path(d,cls) { return shape('path',{d:d},cls); }
    function circle(x,y,r,cls) { return shape('circle',{cx:x,cy:y,r:r},cls); }
    function count(v) { circle(59,12,11,'art-solid'); el('text',{'class':'art-count',x:59,y:17,'text-anchor':'middle'},g).textContent=v; }
    if (kind === 'phone' || kind === 'screen') {
      rect(18,2,38,60,8,'art-solid'); rect(22,10,30,43,3,'art-paper');
      path('M30 6 H44','art-light'); circle(37,57,1.8,'art-light-fill');
      var rows = value.rows == null ? 2 : Math.min(4,value.rows);
      for(var i=0;i<rows;i++)rect(26,16+i*9,i%2?17:22,5,2,'art-soft-fill');
      if(value.playing)path('M32 24 L44 31 L32 38 Z','art-solid');
    } else if (kind === 'server') {
      [8,31].forEach(function(y){rect(7,y,58,19,5,'art-solid');circle(15,y+9,2.5,'art-light-fill');path('M25 '+(y+7)+' H55 M25 '+(y+12)+' H45','art-light');});
      path('M37 50 V59 M23 59 H51','art-outline');
    } else if (kind === 'worker') {
      circle(35,18,12,'art-solid'); path('M15 57 V46 C15 31 55 31 55 46 V57 Z','art-soft-fill');
      rect(43,37,22,25,4,'art-paper');path('M48 44 H59 M48 49 H59 M48 54 H55','art-outline');
      if(value.busy)circle(59,9,6,'art-warn');
    } else if (kind === 'queue') {
      var queued=value.items || [],amount=value.count == null?queued.length:value.count;
      for(var q=0;q<Math.min(3,amount);q++) {
        var x=5+q*19,y=8+q*3;
        rect(x,y,24,32,4,'art-soft-fill');path('M'+(x+4)+' '+(y+9)+' H'+(x+19)+' M'+(x+4)+' '+(y+15)+' H'+(x+16),'art-outline');
        if(queued[q]!=null)el('text',{'class':'art-item',x:x+12,y:y+28,'text-anchor':'middle'},g).textContent=queued[q];
      }
      path('M4 37 H22 L27 44 H46 L51 37 H68 V59 H4 Z','art-solid');
      if(value.count != null)count(value.count);
    } else if (kind === 'database') {
      path('M8 13 V48 C8 61 64 61 64 48 V13 Z','art-soft-fill');
      shape('ellipse',{cx:36,cy:13,rx:28,ry:9},'art-solid');
      path('M8 28 C8 41 64 41 64 28 M8 42 C8 55 64 55 64 42','art-outline');
      if(value.rows != null)count(value.rows);
    } else if (kind === 'clock') {
      circle(35,32,26,'art-soft-fill');circle(35,32,22,'art-paper');
      path('M35 14 V32 L48 39 M35 8 V12 M35 52 V56 M11 32 H15 M55 32 H59','art-outline');
      if(value.ready)path('M46 13 L52 19 L63 5','art-success-line');
    } else if (kind === 'parcel') {
      path('M13 18 L36 6 L62 18 V47 L36 60 L13 47 Z','art-soft-fill');
      path('M13 18 L36 30 L62 18 M36 30 V60 M25 12 L49 24 V38','art-outline');
      if(value.loaded)rect(20,31,10,13,2,'art-solid');
    } else if (kind === 'memory') {
      rect(8,16,30,42,5,'art-soft-fill');rect(32,6,30,42,5,value.copied?'art-warn':'art-solid');
      path('M13 27 H29 M13 34 H29 M13 41 H24','art-outline');
      path('M38 16 H55 M38 23 H55 M38 30 H50','art-light');
      if(value.copied)path('M48 51 L52 55 L62 45','art-success-line');
    } else if (kind === 'document') {
      path('M17 5 H46 L59 18 V59 H17 Z','art-soft-fill');
      path('M46 5 V19 H59 M25 29 H50 M25 37 H50 M25 45 H44','art-outline');
      if(value.built)path('M40 51 L47 58 L64 39','art-success-line');
    } else if (kind === 'cloud') {
      path('M16 48 C-1 47 2 25 18 25 C18 3 52 1 57 24 C76 24 79 48 59 48 Z','art-soft-fill');
      path('M20 32 H50 L44 26 M50 32 L44 38 M50 56 H20 L26 50 M20 56 L26 62','art-outline');
    } else if (kind === 'flow') {
      circle(36,31,25,'art-soft-fill');
      rect(22,17,28,28,7,value.empty?'art-paper':'art-solid');
      if(value.value != null)el('text',{'class':'art-count',x:36,y:36,'text-anchor':'middle'},g).textContent=value.value;
      if(value.empty)path('M29 31 H43','art-outline');
      path('M1 31 H8 M64 31 H71 M66 26 L71 31 L66 36','art-outline');
    } else if (kind === 'code') {
      rect(4,7,64,48,7,'art-solid');path('M5 18 H67','art-light');
      [12,19,26].forEach(function(x){circle(x,12,1.7,'art-light-fill');});
      path('M27 27 L18 35 L27 43 M45 27 L54 35 L45 43','art-light');
      if(value.built)path('M45 51 L51 57 L66 43','art-success-line');
    } else if (kind === 'player') {
      rect(4,6,64,45,7,'art-solid');rect(8,10,56,37,4,'art-soft-fill');
      if(value.playing)path('M29 20 V38 M43 20 V38','art-outline');else path('M29 18 L47 29 L29 40 Z','art-solid');
      path('M10 59 H62','art-outline');circle(value.playing?46:19,59,4,'art-solid');
    } else if (kind === 'lock') {
      path('M21 28 V19 C21 0 53 0 53 19 V28','art-outline');rect(12,26,50,34,8,'art-solid');circle(37,41,4,'art-light-fill');path('M37 44 V51','art-light');
    } else if (kind === 'key') {
      circle(22,25,15,'art-soft-fill');circle(22,25,5,'art-paper');path('M36 32 L61 57 M49 45 L56 38 M57 53 L64 46','art-outline');
    } else if (kind === 'inspect') {
      circle(29,26,21,'art-soft-fill');path('M45 42 L65 62','art-outline');path('M16 29 H22 L27 20 L32 34 L40 24','art-outline');
    } else if (kind === 'graph') {
      path('M36 20 V33 M14 33 H58 M14 33 V45 M58 33 V45','art-outline');rect(22,3,28,18,5,'art-solid');rect(1,44,27,18,5,'art-soft-fill');rect(45,44,27,18,5,'art-soft-fill');
    } else if (kind === 'frame') {
      rect(4,7,64,49,7,'art-paper');circle(22,22,6,'art-solid');path('M6 49 L26 31 L39 43 L49 30 L66 49','art-soft-fill');
    } else if (kind === 'stack') {
      path('M8 7 V60 H64 V7','art-outline');
      var slots=value.items==null?['','','']:value.items.slice(0,3);
      slots.forEach(function(item,i){var y=46-(slots.length-i-1)*14;rect(16,y,40,12,3,'art-soft-fill');if(item!=='')el('text',{'class':'art-item',x:36,y:y+10,'text-anchor':'middle'},g).textContent=item;});
      path('M36 1 V12 M30 7 L36 13 L42 7','art-outline');
    } else if (kind === 'signal') {
      circle(36,31,26,'art-soft-fill');path('M39 8 L22 34 H35 L31 55 L52 27 H38 Z','art-solid');
    } else {
      circle(36,31,25,'art-soft-fill');path('M36 10 V29 L17 48 M36 29 L55 48','art-outline');
      [ [36,10],[17,48],[55,48] ].forEach(function(p){circle(p[0],p[1],7,'art-solid');});
    }
    if(value.badge != null)count(value.badge);
    if(status === 'is-warn') { circle(63,51,9,'art-warn'); path('M63 46 V51 M63 55 V55.5','art-light'); }
    else if(status === 'is-done' && kind !== 'memory') { circle(63,51,9,'art-success');path('M58 51 L62 55 L68 47','art-light'); }
  }

  function lines(text, value, width, x, y, leading) {
    while(text.firstChild)text.removeChild(text.firstChild);
    text.setAttribute('x',x);text.setAttribute('y',y);
    var words=String(value || '').split(/\s+/), row='', rows=[];
    words.forEach(function(word){
      var test=row?row+' '+word:word;
      text.textContent=test;
      if(text.getComputedTextLength()>width && row){rows.push(row);row=word;}else row=test;
      text.textContent=row;
      while(text.getComputedTextLength()>width && row.length>1){
        var part=row;
        while(part.length>1){text.textContent=part;if(text.getComputedTextLength()<=width)break;part=part.slice(0,-1);}
        rows.push(part);row=row.slice(part.length);text.textContent=row;
      }
    });
    if(row)rows.push(row);text.textContent='';
    rows.forEach(function(row,i){el('tspan',{x:x,y:y+i*leading},text).textContent=row+(i<rows.length-1?' ':'');});
  }
  // The same original vector objects also illustrate the existing HTML state diagrams.
  function Actor(parent, data) {
    var svg=el('svg',{'class':'stepper-art actor-'+data.role,viewBox:'0 0 80 72','aria-hidden':'true',focusable:'false'},null);
    var group=el('g',{'class':'pb-art',transform:'translate(4 4)'},svg);
    parent.insertBefore(svg,parent.firstChild);
    return {element:svg,paint:function(state,value){
      var status=state==='done'?'is-done':state==='warn'||state==='error'?'is-warn':'';
      illustrate(group,data.kind,Object.assign({},value || {},state==='ghost'?{visible:false}:{}),status);
    }};
  }
  var uid = 0;
  // Smallest text in each layout, in drawing units (kept in step with bundle.css), and the smallest size it may render at.
  // A layout is used only if, at the scale it would render, handwritten labels stay >= 15px and other text >= 12px.
  var TEXT = { wide: { hand: 17, sans: 13 }, narrow: { hand: 19, sans: 15 } }, MIN = { hand: 15, sans: 12 };
  function needScale(key) { return Math.max(MIN.hand / TEXT[key].hand, MIN.sans / TEXT[key].sans); }
  function pickLayout(root, data) {
    if (!data.layouts) data.layouts = autoLayouts(data);
    // Cross-process/lane scenes keep their authored topology. A local scroll
    // viewport protects legibility without turning side-by-side owners into a list.
    if(root.dataset.pbFlow === 'scene')return 'wide';
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
    if(svg.closest('[data-pb-flow="scene"]'))svg.style.minWidth=Math.ceil(L.size[0]*needScale('wide'))+'px';
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
    var ref = { id: id, L: L, edges: {}, nodes: {}, illustrated: !!data.illustrated };
    var gE = el('g', {}, svg);
    Object.keys(L.edges).forEach(function (k) { ref.edges[k] = el('path', { 'class': 'pb-edge', d: L.edges[k], 'marker-end': 'url(#' + id + 'hrest)' }, gE); });
    var gN = el('g', {}, svg);
    data.nodes.forEach(function (n) {
      var p = L.nodes[n.id], portrait=!!n.art && p.w<180, base='pb-node'+(n.art?' has-art actor-'+n.art.role+(portrait?' portrait':''):''), g = el('g', { 'class': base }, gN);
      el('rect', { x: p.x, y: p.y, width: p.w, height: p.h, rx: n.art?16:10, filter: n.art?null:'url(#' + id + 'r)' }, g);
      var title=el('text', { 'class': 't', x: p.x + 14, y: p.y + 27 }, g);
      var rec = { g: g, base:base, sub: el('text', { 'class': 's', x: p.x + 14, y: p.y + 47 }, g), chips: {}, dots: [] };
      if(n.art){
        rec.art=n.art;
        rec.picture=el('g',{'class':'pb-art','aria-hidden':'true',transform:'translate('+(portrait?p.x+(p.w-72)/2:p.x+12)+' '+(portrait?p.y+8:p.y+(p.h-64)/2)+')'},g);
        rec.tx=portrait?p.x+p.w/2:p.x+96;rec.tw=portrait?p.w-20:p.w-108;rec.sy=portrait?p.y+132:p.y+75;
        if(portrait){title.setAttribute('text-anchor','middle');rec.sub.setAttribute('text-anchor','middle');}
        lines(title,n.label,rec.tw,rec.tx,portrait?p.y+88:p.y+27,21);
      }else title.textContent=n.label;
      if (n.chips) {
        var cw = portrait?p.w-24:Math.min(88, (p.w - 36) / 2);
        n.chips.forEach(function (c, i) {
          var cg = el('g', { 'class': 'pb-chip' }, g), cx = p.x + (portrait?12:14+i*(cw+8)), cy=n.art?(portrait?p.y+p.h-52+i*25:p.y+p.h-32):p.y+56;
          el('rect', { x: cx, y: cy, width: cw, height: 22, rx: 11 }, cg);
          rec.chips[c] = { g: cg, t: el('text', { x: cx + cw / 2, y: cy+16 }, cg) };
        });
      }
      if (n.queue && !n.art) for (var i = 0; i < 3; i++) rec.dots.push(el('circle', { 'class': 'pb-q', cx: p.x + 22 + i * 16, cy: p.y + p.h - 18, r: 6, opacity: 0 }, g));
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
      n.g.setAttribute('class', n.base+' '+v[0]);
      if(n.art){
        lines(n.sub,v[1],n.tw,n.tx,n.sy,17);
        var picture=(state.visuals || {})[id] || {};
        if(n.art.kind==='queue' && picture.count == null && n.art.queue)picture=Object.assign({},picture,{count:state.queue || 0});
        illustrate(n.picture,n.art.kind,picture,v[0]);
      }else n.sub.textContent = v[1];
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
  function packet(ref, tone, label, kind, value) {
    var g = el('g', { 'class': 'pb-pk ' + tone, opacity: 0 }, ref.packets);
    if(ref.illustrated){
      g.classList.add('is-object');
      el('rect',{x:-15,y:-11,width:30,height:22,rx:5,'class':'payload-body'},g);
      if(kind==='rows') { [-5,1,7].forEach(function(y){el('path',{d:'M-9 '+y+' H9','class':'payload-mark'},g);}); }
      else if(kind==='signal')el('path',{d:'M2 -8 L-5 1 H1 L-1 8 L7 -2 H1 Z','class':'payload-fill'},g);
      else if(kind==='frame')el('path',{d:'M-4 -6 L7 0 L-4 6 Z','class':'payload-fill'},g);
      else if(kind==='page')el('path',{d:'M-7 -7 H5 L9 -3 V8 H-7 Z M5 -7 V-3 H9','class':'payload-mark'},g);
      else el('path',{d:'M-13 -8 L0 2 L13 -8','class':'payload-mark'},g);
      if(tone==='back')el('path',{d:'M10 -14 L16 -8 L10 -2 L4 -8 Z','class':'return-cue'},g);
    }else if (tone === 'back') el('path', { d: 'M0 -7 L7 0 L0 7 L-7 0 z' }, g); else el('circle', { r: 6.5 }, g);
    if (label) {
      var pk = ref.L.pk || { dx: 0, dy: -12, anchor: 'middle' };
      el('text', { x: pk.dx, y: pk.dy, 'text-anchor': pk.anchor }, g).textContent = label;
    }
    return g;
  }
  function Payload(parent, tone, kind) {
    var svg=el('svg',{viewBox:'-18 -15 36 30','aria-hidden':'true',focusable:'false'},parent);
    packet({packets:svg,illustrated:true},tone,null,kind).setAttribute('opacity',1);
  }
  function place(ref, g, key, k) {
    var path = ref.edges[key], len = path.getTotalLength();
    var e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2, pt = path.getPointAtLength(e * len);
    g.setAttribute('transform', 'translate(' + pt.x + ' ' + pt.y + ')');
    g.setAttribute('opacity', k < .1 ? k * 10 : k > .9 ? (1 - k) * 10 : 1);
    // Edge lanes may run near the drawing's border. Keep the label readable inside the SVG as its packet moves.
    var label = g.querySelector('text');
    if (label) {
      var bounds = label.getBBox(), shift = Math.max(8 - pt.x - bounds.x, Math.min(0, ref.L.size[0] - 8 - pt.x - bounds.x - bounds.width));
      if (shift) label.setAttribute('x', Number(label.getAttribute('x')) + shift);
    }
  }
  function observeResize(root, callback) {
    var queued = false;
    function schedule() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; callback(); });
    }
    if (window.ResizeObserver) new ResizeObserver(schedule).observe(root); else window.addEventListener('resize', schedule);
  }
  function watch(root, onVisible, onResize) {
    var io = window.IntersectionObserver ? new IntersectionObserver(function (es) { es.forEach(function (e) { onVisible(e.isIntersecting); }); }) : null;
    if (io) io.observe(root);
    observeResize(root, onResize);
  }

  // At most one diagram moves at a time. Loops register in document order; the first visible one that may move plays on
  // its own, the rest stay still with a Play button. Pressing Play on any diagram, or stepping a scene, takes the turn.
  var loops = [], stepped = [], owner = null;
  function eligible(c) { return !document.hidden && c.visible && !c.userPaused && (!motion.reduced() || c.userPlayed); }
  function allowed(c) {
    if (owner) return owner === c && eligible(c);
    for (var i = 0; i < loops.length; i++) if (eligible(loops[i])) return loops[i] === c;
    return false;
  }
  function syncLoops() { loops.forEach(function (c) { c.sync(); }); }
  function claim(c) {
    if (owner === c) return;
    owner = c;
    stepped.forEach(function (other) { if (other !== c) other.stop(); });
    syncLoops();
  }
  function release(c) { if (owner === c) { owner = null; syncLoops(); } }
  function registerSteps(stop) {
    var controller = { stop: stop };
    stepped.push(controller);
    return { claim: function () { claim(controller); }, release: function () { release(controller); } };
  }
  function pauseAll() {
    stepped.forEach(function (c) { c.stop(); });
    loops.forEach(function (c) { c.userPaused = true; c.userPlayed = false; });
    syncLoops();
  }
  motion.subscribe(function (r) { if (r) loops.forEach(function (c) { c.userPlayed = false; }); syncLoops(); });
  document.addEventListener('visibilitychange', function () { if (document.hidden) pauseAll(); });

  // FlowDiagram: streams loop on their edges while running; the still version shows order markers instead.
  function FlowDiagram(root, data) {
    var svg = root.querySelector('svg'), btn = root.querySelector('[data-toggle]');
    var ref, key, raf = 0, live = [];
    var me = { visible: true, userPaused: false, userPlayed: false, sync: function () { if (ref) sync(); } };
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
    build(); // throws on invalid data, before this diagram joins the turn-taking or gets any listeners
    loops.push(me);
    btn.addEventListener('click', function () {
      if (running()) { me.userPaused = true; me.userPlayed = false; } else { me.userPaused = false; me.userPlayed = true; }
      claim(me); syncLoops(); // pausing keeps the turn, so pausing one diagram never starts another
    });
    watch(root, function (v) {
      if (v === me.visible) return;
      me.visible = v;
      if (!v && owner === me) owner = null;
      syncLoops();
    }, function () { if (pickLayout(root, data) !== key) build(); });
    syncLoops();
  }

  // FlowScene: one system stepped through; packets land and change state. Pause or leaving the screen finishes the step at once.
  function FlowScene(root, data) {
    var svg = root.querySelector('svg'), countEl = root.querySelector('.pb-count'), capEl = root.querySelector('.pb-caption p'),
      bar = root.querySelector('.pb-progress i'), list = root.querySelector('.pb-steps ol');
    var btn = {}; root.querySelectorAll('[data-act]').forEach(function (b) { btn[b.dataset.act] = b; });
    var mode = Object.keys(data.modes)[0], idx = 0, token = 0, flying = false, playing = false, timer = 0, ref, key;
    var turn;
    // Keep the live explanation and its controls together; optional help and the
    // full transcript share one disclosure instead of competing with the scene.
    var interaction = document.createElement('div'); interaction.className = 'pb-interaction';
    var caption = root.querySelector('.pb-caption'), progress = root.querySelector('.pb-progress'), controls = root.querySelector('.pb-controls');
    caption.before(interaction); interaction.append(caption, progress, controls);
    root.querySelector('.pb-paper').before(interaction);
    var mapHint=document.createElement('p');mapHint.className='sequence-scroll-hint';mapHint.textContent='Follow the labelled arrowheads and process boundaries. Swipe the diagram sideways on a narrow screen; the labels keep their reading size.';root.querySelector('.pb-paper').after(mapHint);
    btn.prev.textContent = 'Previous'; btn.next.textContent = 'Next'; btn.reset.textContent = 'Reset';
    var guide = root.querySelector('.pb-steps');
    guide.classList.add('pb-guide');
    guide.querySelector('summary').textContent = 'Help & step transcript';
    var help=document.createElement('p');help.textContent='Use Next to follow cause and effect, Previous to compare states' + (data.illustrated ? ', or choose a numbered step. ' : '. ') + 'Reset returns to the first step. Play follows the sequence; Pause finishes the current step. With reduced motion, use the step controls.';
    guide.insertBefore(help, list);
    if(data.illustrated){
      root.classList.add('is-illustrated');
      var legend=document.createElement('div');legend.className='pb-legend';
      [['client','Devices'],['runtime','Execution'],['storage','Stored data'],['queue','Queued work']].forEach(function(pair){var item=document.createElement('span');item.className='actor-'+pair[0];item.textContent=pair[1];legend.appendChild(item);});guide.insertBefore(legend,list);
      var direction=document.createElement('p');direction.textContent='Long dashes show forward transfers; dotted paths and a diamond mark returns. Amber marks a warning. The caption names the actual object or signal being transferred.';guide.insertBefore(direction,list);
    }
    function track() { return data.modes[mode]; }
    function stateAt(k) {
      var s = JSON.parse(JSON.stringify(track().initial));
      for (var i = 0; i <= k; i++) {
        var set = track().steps[i].set || {};
        if (set.nodes) for (var id in set.nodes) s.nodes[id] = set.nodes[id];
        if (set.chips) for (var c in set.chips) s.chips[c] = set.chips[c];
        if (set.queue != null) s.queue = set.queue;
        if (set.visuals) { s.visuals=s.visuals || {}; for(var v in set.visuals)s.visuals[v]=Object.assign({},s.visuals[v] || {},set.visuals[v]); }
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
      Object.keys(ref.nodes).forEach(function (id) { ref.nodes[id].g.classList.remove('pulse'); });
      paint(ref, stateAt(idx), [], true); edgesFor(track().steps[idx], false);
    }
    function ui() {
      var n = track().steps.length;
      countEl.textContent = 'Step ' + (idx + 1) + ' of ' + n;
      capEl.innerHTML = track().steps[idx].caption;
      bar.style.width = ((idx + 1) / n * 100) + '%';
      btn.prev.disabled = idx === 0; btn.next.disabled = idx === n - 1;
      btn.play.textContent = playing || flying ? 'Pause' : 'Play';
      btn.play.setAttribute('aria-pressed', playing || flying ? 'true' : 'false');
      btn.play.setAttribute('aria-label', playing || flying ? 'Pause playback' : (idx === n - 1 ? 'Play from the first step' : 'Play sequence'));
      btn.play.disabled = motion.reduced();
      root.querySelectorAll('[data-step]').forEach(function(b){if(Number(b.dataset.step)===idx)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
    }
    function fly(p, my) {
      return new Promise(function (done) {
        var g = packet(ref, p.tone, p.label, p.kind), t0 = null;
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
      flying = true; root.classList.add('is-moving'); ui();
      return step.packets.reduce(function (pr, p) {
        return pr.then(function (ok) { return ok && my === token ? fly(p, my) : false; });
      }, Promise.resolve(true)).then(function (ok) {
        if (!ok || my !== token) return false;
        flying = false; root.classList.remove('is-moving');
        paint(ref, stateAt(i), changed, false); edgesFor(step, false); ui();
        return true;
      });
    }
    function stop() { playing = false; clearTimeout(timer); timer = 0; settle(); ui(); }
    function loop() {
      if (!playing) return;
      if (idx >= track().steps.length - 1) { stop(); return; }
      go(idx + 1, true).then(function (ok) { if (ok && playing) timer = setTimeout(loop, 2600); });
    }
    btn.next.addEventListener('click', function () { stop(); turn.claim(); if (idx < track().steps.length - 1) go(idx + 1, true); });
    btn.prev.addEventListener('click', function () { stop(); if (idx > 0) go(idx - 1, false); });
    btn.reset.addEventListener('click', function () { stop(); go(0, false); });
    btn.play.addEventListener('click', function () {
      if (playing || flying) { stop(); return; }
      if (motion.reduced()) return;
      playing = true; turn.claim();
      if (idx >= track().steps.length - 1) go(0, false);
      ui(); timer = setTimeout(loop, 400);
    });
    root.querySelectorAll('[data-mode]').forEach(function (b) {
      b.addEventListener('click', function () {
        stop(); mode = b.dataset.mode; idx = 0;
        root.querySelectorAll('[data-mode]').forEach(function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); });
        fillList(); go(0, false);
      });
    });
    function fillList() {
      list.innerHTML = '';
      track().steps.forEach(function (s) { var li = document.createElement('li'); li.innerHTML = s.caption; list.appendChild(li); });
      if(data.illustrated){
        var nav=root.querySelector('.pb-step-nav');
        if(!nav){nav=document.createElement('nav');nav.className='pb-step-nav';nav.setAttribute('aria-label','Scene steps');root.querySelector('.pb-progress').insertAdjacentElement('afterend',nav);}
        nav.innerHTML='';
        track().steps.forEach(function(s,i){var b=document.createElement('button');b.type='button';b.dataset.step=i;b.textContent=i+1;b.setAttribute('aria-label','Go to step '+(i+1));b.addEventListener('click',function(){stop();turn.claim();go(i,false);});nav.appendChild(b);});
      }
    }
    function build() { key = pickLayout(root, data); ref = draw(svg, data, key); settle(); }
    key = pickLayout(root, data); ref = draw(svg, data, key);
    turn = registerSteps(stop);
    motion.subscribe(function (r) { if (r) stop(); else ui(); });
    watch(root, function (v) { if (!v) { stop(); turn.release(); } }, function () { if (pickLayout(root, data) !== key) { stop(); build(); } });
    fillList(); go(0, false);
  }

  function WideDiagram(root) {
    var box = root.querySelector('.pb-wide') || root; // the root may be its own scroll box (the reader's Mermaid figures)
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
    observeResize(box, sync);
    sync();
  }

  // ReadingSheet owns overflow expansion for allcurrent and future lessons.
  function ReadingSheet(scope) {
    var reading=scope.querySelector('.reading-content');
    if(!reading || reading.__pbLayout)return;reading.__pbLayout=true;
    var pending;
    function schedule(){cancelAnimationFrame(pending);pending=requestAnimationFrame(function(){
      var candidates=Array.from(reading.querySelectorAll('.code-card,table')).filter(function(n){return !n.closest('.blend,.pb-figure,.relationship-map,.source-diagram,.original-diagram,li');});
      candidates.forEach(function(n){n.classList.remove('content-bleed');});
      if(!matchMedia('(min-width:641px)').matches)return;
      var wide=candidates.filter(function(n){var c=n.matches('.code-card')?n.querySelector('pre'):n;return n.getClientRects().length && c && c.scrollWidth>c.clientWidth+2;});
      wide.forEach(function(n){n.classList.add('content-bleed');});
    });}
    addEventListener('resize',schedule,{passive:true});addEventListener('load',schedule,{once:true});
    if(document.fonts){document.fonts.ready.then(schedule);document.fonts.addEventListener('loadingdone',schedule);}
    var observer=new MutationObserver(schedule);observer.observe(document.documentElement,{attributes:true});observer.observe(document.body,{attributes:true});
    scope.addEventListener('change',schedule);scope.addEventListener('input',schedule);
    scope.addEventListener('click',function(e){if(e.target.closest('[role=tab]'))schedule();});schedule();
  }
  function mountAll(scope) {
    ReadingSheet(scope || document);
    (scope || document).querySelectorAll('[data-pb-wide]').forEach(function (root) { if (!root.__pb) { root.__pb = true; WideDiagram(root); } });
    (scope || document).querySelectorAll('[data-pb-flow]').forEach(function (root) {
      if (root.__pb) return; root.__pb = true;
      try {
        var data = JSON.parse(root.querySelector('script[type="application/json"]').textContent);
        (root.dataset.pbFlow === 'scene' ? FlowScene : FlowDiagram)(root, data);
      } catch (e) { // one broken diagram must not stop or block the others; show its description instead
        root.classList.add('pb-error');
        root.querySelectorAll('button').forEach(function (b) { b.disabled = true; });
        var svg = root.querySelector('svg'), note = document.createElement('p');
        note.className = 'pb-fallback';
        note.textContent = 'This diagram could not be drawn. ' + ((svg && svg.getAttribute('aria-label')) || '');
        var paper = root.querySelector('.pb-paper');
        if (paper && paper.parentNode) paper.parentNode.insertBefore(note, paper.nextSibling); else root.appendChild(note);
        if (window.console) console.error('Playbook diagram failed to mount:', e.message, root);
      }
    });
  }
  window.Playbook = { motion: motion, registerSteps: registerSteps, pauseAll: pauseAll, observeResize: observeResize, Actor: Actor, Payload: Payload, FlowDiagram: FlowDiagram, FlowScene: FlowScene, WideDiagram: WideDiagram, mountAll: mountAll };
})();
