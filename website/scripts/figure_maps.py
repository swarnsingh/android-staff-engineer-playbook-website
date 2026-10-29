"""Designed figures that replace Mermaid diagrams (design-system component: FigureMap).

A model in content/diagram-models/figures/*.json replaces the rendered Mermaid
picture of one diagram, bound by the diagram source's hash. An original chapter
diagram keeps its Mermaid source on the page as preserved text. This module only
lays out geometry, checks it and emits design-system classes; colours, type and
patterns come from tokens.json through design-system/components/bundle.css.
"""
from pathlib import Path
from html import escape
import json, math

WEB = Path(__file__).resolve().parents[1]
ROLES = {'client': 'Devices and clients', 'runtime': 'Execution', 'storage': 'Stored data',
         'queue': 'Queued work', 'neutral': 'Sources and structure'}
CARD_W, MARGIN, GRID = 220, 20, (260, 120)
# Conservative glyph widths (px) for the faces bundle.css assigns; used to reject clipped labels.
GLYPH = {'title': 8.7, 'detail': 7.9, 'label': 7.3, 'note': 7.9}
LINE = 18


def width(text, kind):
    return len(text) * GLYPH[kind]


def lines(value):
    return value if isinstance(value, list) else ([value] if value else [])


def load():
    """Every figure model, keyed by the hash of the diagram it redraws."""
    found = {}
    for source in sorted((WEB / 'content/diagram-models/figures').glob('*.json')):
        for row in json.loads(source.read_text()):
            check(row)
            if row['diagram'] in found:
                raise ValueError(f'Two figures redraw diagram {row["diagram"]}')
            found[row['diagram']] = row
    return found


def check(row):
    key = row.get('diagram', '?')
    for field in ('path', 'diagram', 'kind', 'number', 'title', 'caption', 'sources'):
        if not row.get(field):
            raise ValueError(f'Figure {key}: missing {field}')
    if any(not u.startswith('https://') for u in row['sources']):
        raise ValueError(f'Figure {key}: sources must be https URLs')
    actors = row['nodes'] if row['kind'] == 'map' else row.get('participants', [])
    if row['kind'] not in ('map', 'sequence'):
        raise ValueError(f'Figure {key}: unknown kind {row["kind"]}')
    ids = [n['id'] for n in actors]
    if len(ids) != len(set(ids)):
        raise ValueError(f'Figure {key}: duplicate actor IDs')
    for n in actors:
        if n.get('shape') in ('start', 'end'):
            continue
        if n.get('role') not in ROLES or not n.get('title'):
            raise ValueError(f'Figure {key}: {n["id"]} needs a title and a known role')
        if 'x' not in n and 'col' not in n:
            continue  # auto_layout sizes these cards and checks them itself
        room = n.get('w', CARD_W) - 28
        if any(width(t, 'title') > room for t in lines(n['title'])) or any(width(d, 'detail') > room for d in lines(n.get('detail'))):
            raise ValueError(f'Figure {key}: label of {n["id"]} would be clipped; widen the card or shorten it')
    if row['kind'] == 'map':
        owners = [m for g in row.get('groups', []) for m in g['nodes']]
        if len(owners) != len(set(owners)) or not set(owners) <= set(ids):
            raise ValueError(f'Figure {key}: every boundary member needs one owner and a real actor')
        for e in row.get('edges', []):
            if e['from'] not in ids or e['to'] not in ids or not e.get('label'):
                raise ValueError(f'Figure {key}: invalid relationship {e}')
    else:
        for event in row['events']:
            for e in event if isinstance(event, list) else [event]:
                used = (e['over'] if isinstance(e.get('over'), list) else [e.get('over')]) + [e.get('at'), e.get('from'), e.get('to')]
                if any(u is not None and u not in ids for u in used):
                    raise ValueError(f'Figure {key}: event names an unknown participant {e}')


class Canvas:
    def __init__(self, key):
        self.key, self.parts, self.boxes, self.pills, self.segments = key, [], [], [], []
        self.box = [10**9, 10**9, -10**9, -10**9]

    def grow(self, x0, y0, x1, y1):
        b = self.box
        self.box = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]

    def add(self, markup, *bounds):
        self.parts.append(markup)
        if bounds:
            self.grow(*bounds)

    def verify(self):
        """Reject the layouts that make a figure misleading: covered labels and lines through cards."""
        def overlap(a, b, pad=2):
            return a[0] < b[2] - pad and b[0] < a[2] - pad and a[1] < b[3] - pad and b[1] < a[3] - pad
        for i, p in enumerate(self.pills):
            for q in self.pills[i + 1:]:
                if overlap(p[1], q[1]):
                    raise ValueError(f'Figure {self.key}: labels "{p[0]}" and "{q[0]}" overlap')
            for name, b in self.boxes:
                if overlap(p[1], b):
                    raise ValueError(f'Figure {self.key}: label "{p[0]}" covers card {name}')
        for (x0, y0), (x1, y1), ends in self.segments:
            for name, (bx0, by0, bx1, by1) in self.boxes:
                if name in ends:
                    continue
                # Sample the segment; cards are rectangles and segments are short.
                steps = max(2, int(math.hypot(x1 - x0, y1 - y0) / 4))
                for s in range(1, steps):
                    x, y = x0 + (x1 - x0) * s / steps, y0 + (y1 - y0) * s / steps
                    if bx0 + 1 < x < bx1 - 1 and by0 + 1 < y < by1 - 1:
                        raise ValueError(f'Figure {self.key}: a line passes through card {name}')

    def svg(self, prefix, title, desc):
        self.verify()
        x0, y0, x1, y1 = self.box
        x0, y0, x1, y1 = x0 - MARGIN, y0 - MARGIN, x1 + MARGIN, y1 + MARGIN
        w, h = x1 - x0, y1 - y0
        marker = (f'<defs><marker id="{prefix}-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" '
                  f'markerHeight="8" orient="auto-start-reverse"><path class="fm-arrowhead" d="M1 1L9 5L1 9z"/></marker></defs>')
        return (f'<svg class="fm-svg" viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" '
                f'style="min-width:{w:.0f}px;max-width:{w:.0f}px" role="img" aria-labelledby="{prefix}-t {prefix}-d">'
                f'<title id="{prefix}-t">{escape(title)}</title><desc id="{prefix}-d">{escape(desc)}</desc>'
                + marker + ''.join(self.parts) + '</svg>')


def card_height(n):
    if n.get('shape') in ('start', 'end'):
        return 24
    return n.get('h', 30 + LINE * (len(lines(n['title'])) + len(lines(n.get('detail')))))


def card(c, n):
    x, y, w, h, role = n['x'], n['y'], n['w'], n['h'], n.get('role', 'neutral')
    if n.get('shape') == 'start':
        c.add(f'<circle class="fm-start" cx="{x+12}" cy="{y+12}" r="10"/>', x, y, x + 24, y + 24)
        c.boxes.append((n['id'], (x, y, x + 24, y + 24)))
        return
    if n.get('shape') == 'end':
        c.add(f'<g class="fm-end"><circle cx="{x+12}" cy="{y+12}" r="11"/><circle cx="{x+12}" cy="{y+12}" r="6"/></g>',
              x, y, x + 24, y + 24)
        c.boxes.append((n['id'], (x, y, x + 24, y + 24)))
        return
    cls = f'fm-node actor-{role}' + (' is-key' if n.get('key') else '')
    inner = (f'<rect class="fm-card-inner" x="{x+4}" y="{y+4}" width="{w-8}" height="{h-8}" rx="8"/>'
             if role == 'storage' else '')
    rows = [('fm-title', t) for t in lines(n['title'])] + [('fm-detail', d) for d in lines(n.get('detail'))]
    top = y + h / 2 - (len(rows) - 1) * LINE / 2 - (2 if len(rows) > 1 else 0)
    texts = ''.join(f'<text class="{cls_}" x="{x+w/2}" y="{top + i*LINE + (4 if i else 0):.1f}" dominant-baseline="central">{escape(t)}</text>'
                    for i, (cls_, t) in enumerate(rows))
    c.add(f'<g class="{cls}"><rect class="fm-card" x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>{inner}{texts}</g>',
          x, y, x + w, y + h)
    c.boxes.append((n['id'], (x, y, x + w, y + h)))


def pill(c, x, y, number, label):
    """A numbered relationship label centred at (x, y), on the sheet colour above the line."""
    rows = lines(label)
    w = 30 + max(width(r, 'label') for r in rows) + 12
    h = 26 + LINE * (len(rows) - 1)
    left, top = x - w / 2, y - h / 2
    texts = ''.join(f'<text class="l" x="{left+28:.1f}" y="{top + 13 + i*LINE:.1f}" dominant-baseline="central">{escape(r)}</text>'
                    for i, r in enumerate(rows))
    c.add(f'<g class="fm-pill"><rect x="{left:.1f}" y="{top:.1f}" width="{w:.1f}" height="{h}" rx="13"/>'
          f'<circle cx="{left+14:.1f}" cy="{top+13:.1f}" r="9"/><text class="n" x="{left+14:.1f}" y="{top+13:.1f}" dominant-baseline="central">{number}</text>'
          f'{texts}</g>', left, top, left + w, top + h)
    c.pills.append((' '.join(rows), (left, top, left + w, top + h)))


def anchors(a, b, e):
    """Where an edge leaves its source card and enters its target card, by route."""
    acx, acy = a['x'] + a['w'] / 2 + e.get('from_dx', 0), a['y'] + a['h'] / 2
    bcx, bcy = b['x'] + b['w'] / 2 + e.get('to_dx', 0), b['y'] + b['h'] / 2
    down, right = bcy > acy, bcx > acx
    top = lambda n: n['y']
    bottom = lambda n: n['y'] + n['h']
    route = e.get('route', 'straight')
    if route == 'straight' and not e.get('from_dx') and not e.get('to_dx'):
        # Cards that share a band of height or width get an orthogonal line through that band.
        lo, hi = max(a['y'], b['y']), min(a['y'] + a['h'], b['y'] + b['h'])
        if hi - lo > 16 and (a['x'] + a['w'] <= b['x'] or b['x'] + b['w'] <= a['x']):
            y = (lo + hi) / 2
            return [(a['x'] + a['w'] if right else a['x'], y), (b['x'] if right else b['x'] + b['w'], y)], route
        lo, hi = max(a['x'], b['x']), min(a['x'] + a['w'], b['x'] + b['w'])
        if hi - lo > 16 and (a['y'] + a['h'] <= b['y'] or b['y'] + b['h'] <= a['y']):
            x = (lo + hi) / 2
            return [(x, bottom(a) if down else top(a)), (x, top(b) if down else bottom(b))], route
    if a is b:
        x, off = a['x'] + a['w'], e.get('off', 46)
        return [(x, acy - 12), (x + off, acy - 12), (x + off, acy + 12), (x, acy + 12)], 'loop'
    if route == 'straight' and abs(acy - bcy) < 1:
        return [(a['x'] + a['w'] if right else a['x'], acy), (b['x'] if right else b['x'] + b['w'], bcy)], route
    if route in ('straight', 'curve'):
        if route == 'curve' and abs(acy - bcy) < 1:
            return [(a['x'] + a['w'] if right else a['x'], acy), (b['x'] if right else b['x'] + b['w'], bcy)], route
        return [(acx, bottom(a) if down else top(a)), (bcx, top(b) if down else bottom(b))], route
    if route == 'side':
        return [(a['x'] + a['w'] if right else a['x'], acy), (b['x'] if right else b['x'] + b['w'], bcy)], route
    if route == 'hv':
        return [(a['x'] + a['w'] if right else a['x'], acy), (bcx, acy), (bcx, top(b) if down else bottom(b))], route
    if route == 'vh':
        return [(acx, bottom(a) if down else top(a)), (acx, bcy), (b['x'] if right else b['x'] + b['w'], bcy)], route
    if route == 'vhv':
        mid = e.get('mid', (bottom(a) + top(b)) / 2 if down else (bottom(b) + top(a)) / 2)
        return [(acx, bottom(a) if down else top(a)), (acx, mid), (bcx, mid), (bcx, top(b) if down else bottom(b))], route
    if route == 'around':
        if e.get('side', 'right') == 'right':
            x = max(a['x'] + a['w'], b['x'] + b['w']) + e.get('off', 60)
            return [(a['x'] + a['w'], acy), (x, acy), (x, bcy), (b['x'] + b['w'], bcy)], route
        x = min(a['x'], b['x']) - e.get('off', 60)
        return [(a['x'], acy), (x, acy), (x, bcy), (b['x'], bcy)], route
    raise ValueError(f'unknown route {route}')


def wrap_label(text, limit=22):
    """Long relationship labels become short lines, so pills fit between columns."""
    if isinstance(text, list):
        return text
    rows, cur = [], ''
    words = []
    for word in text.split():
        # Paths and package names have no spaces: break them after '/', '-' or '.'.
        while len(word) > limit:
            cut = max(word.rfind(sep, 0, limit) for sep in '/-.')
            cut = cut + 1 if cut > 0 else limit
            words.append(word[:cut])
            word = word[cut:]
        words.append(word)
    for word in words:
        if cur and len(cur) + 1 + len(word) > limit:
            rows.append(cur)
            cur = word
        else:
            cur = (cur + ' ' + word).strip()
    rows.append(cur)
    return rows if len(rows) > 1 else rows[0]


def pill_size(label):
    rows = lines(label)
    return 30 + max(width(r, 'label') for r in rows) + 12, 26 + LINE * (len(rows) - 1)


def auto_layout(row, key):
    """Place a model without coordinates: one column per owner boundary, rows in relationship order.

    Routes avoid other cards and each label is placed where it covers no card, boundary label
    or earlier label. A model that cannot be placed cleanly fails the build rather than
    publishing a misleading figure.
    """
    row = json.loads(json.dumps(row))
    nodes, groups, edges = row['nodes'], row.get('groups', []), row.get('edges', [])
    byid = {n['id']: n for n in nodes}
    parent = {g['id']: g.get('parent') for g in groups}
    root = lambda gid: gid if not parent.get(gid) else root(parent[gid])
    owner = {m: g['id'] for g in groups for m in g['nodes']}
    columns = []
    for n in nodes:
        k = root(owner[n['id']]) if n['id'] in owner else None
        if k not in columns:
            columns.append(k)
        n['_col'] = columns.index(k)
    # Longest-path rank over the relationships, ignoring edges that close a cycle.
    state, back = {}, set()
    def visit(u):
        state[u] = 1
        for i, e in enumerate(edges):
            if e['from'] == u:
                v = e['to']
                if v == u or state.get(v) == 1:
                    back.add(i)
                elif v not in state:
                    visit(v)
        state[u] = 2
    for n in nodes:
        if n['id'] not in state:
            visit(n['id'])
    rank = {n['id']: 0 for n in nodes}
    for _ in nodes:
        for i, e in enumerate(edges):
            if i not in back and rank[e['to']] < rank[e['from']] + 1:
                rank[e['to']] = rank[e['from']] + 1
    for c in range(len(columns)):
        last = -1
        for n in sorted((n for n in nodes if n['_col'] == c), key=lambda n: (rank[n['id']], nodes.index(n))):
            n['_row'] = max(rank[n['id']], last + 1)
            last = n['_row']
    used = sorted({n['_row'] for n in nodes})
    for n in nodes:
        n['_row'] = used.index(n['_row'])
    for n in nodes:
        if any(width(t, 'title') + 28 > 330 for t in lines(n['title'])):
            n['title'] = [part for t in lines(n['title']) for part in lines(wrap_label(t, 32))]
        if any(width(d, 'detail') + 28 > 330 for d in lines(n.get('detail'))):
            n['detail'] = [part for d in lines(n['detail']) for part in lines(wrap_label(d, 36))]
    if row.get('layout') in ('layers', 'snake'):
        place_flow(row, nodes, rank)
    else:
        # Column widths fit their longest title, detail or boundary label.
        labels = {g['id']: g['label'] for g in groups}
        for n in nodes:
            if width(n['title'], 'title') + 28 > 330:
                n['title'] = wrap_label(n['title'], 32)
        colw = []
        for c, k in enumerate(columns):
            need = [width(t, 'title') + 28 for n in nodes if n['_col'] == c for t in lines(n['title'])]
            need += [width(d, 'detail') + 28 for n in nodes if n['_col'] == c for d in lines(n.get('detail'))]
            cards_need = min(330, math.ceil(max(need)))
            boundary_need = max([len(labels[g]) * 8.6 + 36 - 48 + 2 for g in labels if root(g) == k], default=0)
            colw.append(math.ceil(max(200, cards_need, boundary_need)))
        gap_x, gap_y = row.get('gap_x', 230), row.get('gap_y', 96)
        # Columns that would make the figure wider than its frame continue on a band below.
        band, xs, x = [0] * len(columns), [0] * len(columns), 0
        for c in range(len(columns)):
            if c and x + colw[c] > row.get('max_w', 900):
                band[c], x = band[c - 1] + 1, 0
            elif c:
                band[c] = band[c - 1]
            xs[c], x = x, x + colw[c] + gap_x
        rows_per_band = max(n['_row'] for n in nodes) + 1
        for n in nodes:
            n['_row'] += band[n['_col']] * rows_per_band
        used = sorted({n['_row'] for n in nodes})
        for n in nodes:
            n['_row'] = used.index(n['_row'])
        heights = {}
        for n in nodes:
            heights[n['_row']] = max(heights.get(n['_row'], 0), card_height(n))
        nested_first = {}
        for g in groups:
            if g.get('parent'):
                first = min((byid[m]['_row'] for m in g['nodes']), default=None)
                if first is not None:
                    nested_first[first] = True
        ys, y = {}, 0
        band_of_row = {n['_row']: band[n['_col']] for n in nodes}
        for r in range(len(used)):
            y += 44 if nested_first.get(r) and r else 0
            y += 60 if r and band_of_row[r] != band_of_row[r - 1] else 0
            ys[r] = y
            y += heights[r] + gap_y
        for n in nodes:
            n['w'], n['x'], n['y'] = colw[n['_col']], xs[n['_col']], ys[n['_row']]
    geo = {n['id']: dict(n, h=card_height(n)) for n in nodes}
    cards = [(n['id'], (g['x'], g['y'], g['x'] + g['w'], g['y'] + g['h'])) for n, g in ((n, geo[n['id']]) for n in nodes)]
    obstacles = []
    for g in groups:
        x0, y0, _, _ = group_box(g, geo, groups)
        obstacles.append((x0 + 10, y0 + 10, x0 + 24 + len(g['label']) * 8.6, y0 + 42))

    def hits_card(pts, ends):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            steps = max(2, int(math.hypot(x1 - x0, y1 - y0) / 4))
            for s in range(1, steps):
                x, y = x0 + (x1 - x0) * s / steps, y0 + (y1 - y0) * s / steps
                for name, (bx0, by0, bx1, by1) in cards:
                    if name not in ends and bx0 - 6 < x < bx1 + 6 and by0 - 6 < y < by1 + 6:
                        return True
        return False

    def free(rect):
        def over(a, b, pad=4):
            return a[0] < b[2] + pad and b[0] < a[2] + pad and a[1] < b[3] + pad and b[1] < a[3] + pad
        return not any(over(rect, b) for _, b in cards) and not any(over(rect, o) for o in obstacles)

    seen, buses, drawn = {}, set(), []
    if row.get('layout') == 'layers':
        # Several edges from one parent with the same label share a bus and one label.
        count = {}
        for e in edges:
            count[(e['from'], str(e['label']))] = count.get((e['from'], str(e['label'])), 0) + 1
        for e in edges:
            if count[(e['from'], str(e['label']))] > 2 and 'bus' not in e:
                e['bus'] = e['from'] + ':' + str(e['label'])
    for i, e in enumerate(edges):
        e['label'] = wrap_label(e['label'])
        a, b = geo[e['from']], geo[e['to']]
        pair = frozenset((e['from'], e['to']))
        twin = seen.get(pair, 0)
        seen[pair] = twin + 1
        if a is b:
            options = [{}]
        elif twin:
            options = [{'route': 'curve', 'bend': 70 * (1 if twin % 2 else -1)}, {'route': 'around', 'side': 'right', 'off': 60 * twin}]
        elif a['_col'] == b['_col'] or a['_row'] == b['_row']:
            options = [{'route': 'straight'}]
        elif row.get('layout') == 'layers':
            # Turn in the gap just above the target's row, so the line never crosses an earlier row.
            above = b['y'] - row.get('gap_y', 116) / 2 if b['y'] > a['y'] else None
            options = ([{'route': 'vhv', 'mid': above}] if above else []) + [{'route': 'vhv'}, {'route': 'straight'}, {'route': 'vh'}, {'route': 'hv'}]
        else:
            options = [{'route': 'vh'}, {'route': 'hv'}, {'route': 'vhv'}, {'route': 'straight'}]
        if a is not b:
            options += [{'route': 'around', 'side': side, 'off': off} for off in (70, 120, 180) for side in ('right', 'left')]
            options += [{'route': 'curve', 'bend': bend} for bend in (70, -70, 120, -120)]
        def crossings(pts):
            count = 0
            for (p1, p2) in zip(pts, pts[1:]):
                for (q1, q2) in drawn:
                    d = (p2[0]-p1[0]) * (q2[1]-q1[1]) - (p2[1]-p1[1]) * (q2[0]-q1[0])
                    if abs(d) < 1e-9:
                        continue
                    t = ((q1[0]-p1[0]) * (q2[1]-q1[1]) - (q1[1]-p1[1]) * (q2[0]-q1[0])) / d
                    u = ((q1[0]-p1[0]) * (p2[1]-p1[1]) - (q1[1]-p1[1]) * (p2[0]-p1[0])) / d
                    if 0.02 < t < 0.98 and 0.02 < u < 0.98:
                        count += 1
            return count
        # Every clean option is scored; fewer crossings, then fewer bends and less length win.
        candidates = []
        for rank_, option in enumerate(options):
            trial = dict(e, **option)
            pts, kind = anchors(a, b, trial)
            if kind not in ('curve', 'loop') and hits_card(pts, {e['from'], e['to']}):
                continue
            w, h = pill_size(e['label'])
            found = None
            if e.get('bus') in buses or kind == 'loop':
                found = (option, None)
            elif kind == 'curve':
                (sx, sy), (tx, ty) = pts
                length = math.hypot(tx - sx, ty - sy) or 1
                bend = option['bend']
                x = (sx + tx) / 2 + -(ty - sy) / length * bend / 2
                y = (sy + ty) / 2 + (tx - sx) / length * bend / 2
                rect = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
                if free(rect):
                    found = (option, rect)
            else:
                order = sorted(range(len(pts) - 1), key=lambda s_: -math.hypot(pts[s_+1][0]-pts[s_][0], pts[s_+1][1]-pts[s_][1]))
                for s_ in order:
                    for t in (.5, .35, .65, .25, .75, .15, .85):
                        (sx, sy), (tx, ty) = pts[s_], pts[s_ + 1]
                        x, y = sx + (tx - sx) * t, sy + (ty - sy) * t
                        rect = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
                        if free(rect):
                            found = (dict(option, at=s_, t=t), rect)
                            break
                    if found:
                        break
            if found:
                straight_pts = pts if kind not in ('curve', 'loop') else [pts[0], pts[-1]]
                length = sum(math.hypot(q[0]-p_[0], q[1]-p_[1]) for p_, q in zip(straight_pts, straight_pts[1:]))
                score = crossings(straight_pts) * 1000 + (len(straight_pts) - 2) * 60 + length / 10 + rank_ * 5 + (400 if kind == 'curve' else 0)
                candidates.append((score, found, straight_pts))
        placed = None
        if candidates:
            score, placed, chosen = min(candidates, key=lambda c: c[0])
            drawn.extend(zip(chosen, chosen[1:]))
        if not placed:
            raise ValueError(f'Figure {key}: no clean route and label position for {e["from"]} → {e["to"]}')
        option, rect = placed
        e.update(option)
        if e.get('bus'):
            buses.add(e['bus'])
        if rect:
            obstacles.append(rect)
    for n in nodes:
        n.pop('_col'); n.pop('_row')
    return row


def place_flow(row, nodes, rank):
    """Layered rows for trees and fan-outs, or a wrapped snake for long pipelines."""
    w = max(180, min(330, math.ceil(max([width(t, 'title') + 28 for n in nodes for t in lines(n['title'])] +
                                        [width(d, 'detail') + 28 for n in nodes for d in lines(n.get('detail'))]))))
    max_w = row.get('max_w', 900)
    if row['layout'] == 'snake':
        gap_x, gap_y = row.get('gap_x', 190), row.get('gap_y', 90)
        per = max(1, int((max_w + gap_x) // (w + gap_x)))
        ordered = sorted(nodes, key=lambda n: (rank[n['id']], nodes.index(n)))
        rows = [ordered[i:i + per] for i in range(0, len(ordered), per)]
        slots = []
        for r, members in enumerate(rows):
            for i, n in enumerate(members):
                slots.append((n, r, i if r % 2 == 0 else per - 1 - i))
    else:
        gap_x, gap_y = row.get('gap_x', 60), row.get('gap_y', 116)
        per = max(1, int((max_w + gap_x) // (w + gap_x)))
        rows, place = [], {}
        for k in sorted(set(rank.values())):
            members = [n for n in nodes if rank[n['id']] == k]
            parents = lambda n: [place[e['from']] for e in row.get('edges', []) if e['to'] == n['id'] and e['from'] in place]
            members.sort(key=lambda n: (sum(parents(n)) / len(parents(n)) if parents(n) else 1e9, nodes.index(n)))
            for i in range(0, len(members), per):
                chunk = members[i:i + per]
                rows.append(chunk)
                for j, n in enumerate(chunk):
                    place[n['id']] = j - (len(chunk) - 1) / 2
        slots = []
        for r, members in enumerate(rows):
            for i, n in enumerate(members):
                slots.append((n, r, i - (len(members) - 1) / 2 + (per - 1) / 2))
    heights = {}
    for n, r, _ in slots:
        heights[r] = max(heights.get(r, 0), card_height(n))
    ys, y = {}, 0
    for r in sorted(heights):
        ys[r] = y
        y += heights[r] + gap_y
    for n, r, slot in slots:
        n['w'], n['x'], n['y'] = w, round(slot * (w + gap_x)), ys[r]
        n['_col'], n['_row'] = n['x'], r


def group_box(g, nodes, groups):
    """A boundary encloses its own members and every nested boundary."""
    members = [nodes[m] for m in g['nodes']]
    boxes = [(m['x'] - 24, m['y'] - 52, m['x'] + m['w'] + 24, m['y'] + m['h'] + 24) for m in members]
    for child in groups:
        if child.get('parent') == g['id']:
            cx0, cy0, cx1, cy1 = group_box(child, nodes, groups)
            boxes.append((cx0 - 14, cy0 - 44, cx1 + 14, cy1 + 14))
    return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)


def render_map(row, key):
    c = Canvas(key)
    if not all('x' in n or 'col' in n for n in row['nodes']):
        row = auto_layout(row, key)
    gx, gy = row.get('grid', GRID)
    nodes = {}
    for n in row['nodes']:
        m = dict(n)
        m['w'] = 24 if n.get('shape') in ('start', 'end') else n.get('w', row.get('card_w', CARD_W))
        m['h'] = card_height(n)
        m['x'] = n['x'] if 'x' in n else n['col'] * gx
        m['y'] = n['y'] if 'y' in n else n['row'] * gy
        nodes[n['id']] = m
    depth = lambda g: 0 if not g.get('parent') else 1 + depth(next(x for x in row['groups'] if x['id'] == g['parent']))
    def owned(g):
        return set(g['nodes']).union(*[owned(x) for x in row['groups'] if x.get('parent') == g['id']])
    for g in sorted(row.get('groups', []), key=depth):
        x0, y0, x1, y1 = group_box(g, nodes, row['groups'])
        # A boundary must not appear to own a card that it does not contain.
        for nid, m in nodes.items():
            if nid not in owned(g) and m['x'] < x1 and x0 < m['x'] + m['w'] and m['y'] < y1 and y0 < m['y'] + m['h']:
                raise ValueError(f'Figure {key}: boundary "{g["label"]}" overlaps card {nid}, which it does not own')
        if len(g['label']) * 8.6 > x1 - x0 - 36:
            raise ValueError(f'Figure {key}: boundary label "{g["label"]}" is wider than its boundary')
        c.add(f'<g class="fm-group"><rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="18"/>'
              f'<text x="{x0+18}" y="{y0+26}" dominant-baseline="central">{escape(g["label"])}</text></g>', x0, y0, x1, y1)
    edges, pills, numbers = [], [], {}
    for e in row.get('edges', []):
        a, b = nodes[e['from']], nodes[e['to']]
        pts, kind = anchors(a, b, e)
        # Stop the line short of the card so the arrowhead touches the border.
        (px, py), (qx, qy) = pts[-2], pts[-1]
        d_ = math.hypot(qx - px, qy - py) or 1
        pts[-1] = (qx - (qx - px) / d_ * 2, qy - (qy - py) / d_ * 2)
        cls = 'fm-edge' + (' is-dashed' if e.get('style') == 'dashed' else '')
        start = f' marker-start="url(#{key}-head)"' if e.get('both') else ''
        if kind == 'curve':
            (sx, sy), (tx, ty) = pts
            length = math.hypot(tx - sx, ty - sy) or 1
            nx, ny = -(ty - sy) / length, (tx - sx) / length
            bend = e.get('bend', 60)
            cx_, cy_ = (sx + tx) / 2 + nx * bend, (sy + ty) / 2 + ny * bend
            path = f'M{sx:.1f} {sy:.1f} Q{cx_:.1f} {cy_:.1f} {tx:.1f} {ty:.1f}'
            label_at = ((sx + 2 * cx_ + tx) / 4, (sy + 2 * cy_ + ty) / 4)
            c.grow(min(sx, tx, cx_), min(sy, ty, cy_), max(sx, tx, cx_), max(sy, ty, cy_))
        else:
            path = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
            for i in range(len(pts) - 1):
                c.segments.append((pts[i], pts[i + 1], {e['from'], e['to']}))
            for x, y in pts:
                c.grow(x, y, x, y)
            if kind == 'loop':
                label_at = (pts[1][0] + 6, (pts[1][1] + pts[2][1]) / 2)
            else:
                seg = e.get('at')
                if seg is None:
                    seg = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]))
                t = e.get('t', .5)
                (sx, sy), (tx, ty) = pts[seg], pts[seg + 1]
                label_at = (sx + (tx - sx) * t, sy + (ty - sy) * t)
        edges.append(f'<path class="{cls}" d="{path}"{start} marker-end="url(#{key}-head)"/>')
        # Edges on one shared bus carry one number and one visible label.
        bus = e.get('bus')
        if bus in numbers:
            continue
        number = len(numbers) + 1
        numbers[bus or id(e)] = number
        if kind == 'loop':
            w = 30 + max(width(r, 'label') for r in lines(e['label'])) + 12
            label_at = (label_at[0] + w / 2, label_at[1])
        pills.append((label_at, number, e['label']))
    c.parts.extend(edges)
    for n in row['nodes']:
        card(c, nodes[n['id']])
    for (x, y), number, label in pills:
        pill(c, x, y, number, label)
    return c


def render_sequence(row, key):
    c = Canvas(key)
    gap = row.get('lane_gap', 420)
    lanes = {p['id']: 20 + CARD_W / 2 + i * gap for i, p in enumerate(row['participants'])}
    participants = []
    for p in row['participants']:
        p = dict(p)
        if any(width(t, 'title') + 28 > CARD_W for t in lines(p['title'])):
            p['title'] = [part for t in lines(p['title']) for part in lines(wrap_label(t, 20))]
        participants.append(p)
    row = dict(row, participants=participants)
    for p in participants:
        card(c, dict(p, x=lanes[p['id']] - CARD_W / 2, y=0, w=CARD_W, h=card_height(p)))
    head = max(card_height(p) for p in participants)
    y, number, body = head + 44, 0, []
    for event in row['events']:
        tallest = 0
        for e in event if isinstance(event, list) else [event]:
            if 'over' in e:
                w = width(e['text'], 'note') + 32
                over = e['over'] if isinstance(e['over'], list) else [e['over']]
                centre = sum(lanes[o] for o in over) / len(over)
                x = centre - w / 2
                body.append(f'<g class="fm-note actor-{e.get("role", "storage")}"><rect x="{x:.1f}" y="{y-17}" width="{w:.1f}" height="34" rx="9"/>'
                            f'<text x="{centre}" y="{y}" dominant-baseline="central">{escape(e["text"])}</text></g>')
                c.grow(x, y - 17, x + w, y + 17)
                tallest = max(tallest, 34)
            elif 'at' in e:
                number += 1
                lx = lanes[e['at']]
                body.append(f'<path class="fm-edge" d="M{lx} {y-14} C{lx+70} {y-18} {lx+70} {y+18} {lx+4} {y+16}" marker-end="url(#{key}-head)"/>')
                c.grow(lx, y - 18, lx + 60, y + 18)
                pill_x = lx + 74 + (30 + width(e['label'], 'label') + 12) / 2
                body.append(('pill', pill_x, y, number, e['label']))
                tallest = max(tallest, 40)
            else:
                number += 1
                x0, x1 = lanes[e['from']], lanes[e['to']]
                step = 6 if x1 > x0 else -6
                dashed = ' is-dashed' if e.get('style') == 'dashed' else ''
                body.append(f'<path class="fm-edge{dashed}" d="M{x0+step} {y+8} L{x1-step} {y+8}" marker-end="url(#{key}-head)"/>')
                body.append(('pill', (x0 + x1) / 2, y - 12, number, e['label']))
                tallest = max(tallest, 48)
        y += tallest + 26
    end = y - 10
    lifelines = [f'<line class="fm-lifeline" x1="{lanes[p["id"]]}" y1="{card_height(p)+2}" x2="{lanes[p["id"]]}" y2="{end}"/>'
                 for p in row['participants']]
    c.grow(0, 0, 0, end)
    c.parts = lifelines + c.parts
    for part in body:
        if isinstance(part, tuple):
            pill(c, *part[1:])
        else:
            c.add(part)
    # Sequence pills sit on lifelines by design; only check them against each other.
    c.boxes = []
    return c


def transcript(row):
    """The figure's relationships or steps as plain text, so nothing depends on seeing the drawing."""
    names = {n['id']: n.get('title') or ('Start' if n.get('shape') == 'start' else 'End')
             for n in row.get('nodes', row.get('participants', []))}
    items = []
    if row['kind'] == 'map':
        for e in row.get('edges', []):
            arrow = ' ↔ ' if e.get('both') else ' → '
            items.append(f'{names[e["from"]]}{arrow}{names[e["to"]]}: {" ".join(lines(e["label"]))}')
    else:
        for event in row['events']:
            for e in event if isinstance(event, list) else [event]:
                if 'over' in e:
                    over = e['over'] if isinstance(e['over'], list) else [e['over']]
                    items.append(f'{" and ".join(names[o] for o in over)} — {e["text"]}')
                elif 'at' in e:
                    items.append(f'{names[e["at"]]}: {e["label"]}')
                else:
                    items.append(f'{names[e["from"]]} → {names[e["to"]]}: {e["label"]}')
    return ''.join(f'<li>{escape(i)}</li>' for i in items)


def render(row, source, provenance='original'):
    """The designed figure; for an original diagram, also its preserved Mermaid source."""
    prefix = 'fm-' + row['diagram']
    canvas = render_map(row, row['diagram']) if row['kind'] == 'map' else render_sequence(row, row['diagram'])
    used = []
    for item in row.get('nodes', row.get('participants', [])):
        if item.get('shape') not in ('start', 'end') and item['role'] not in used:
            used.append(item['role'])
    if row['kind'] == 'sequence':
        for ev in row['events']:
            for e in ev if isinstance(ev, list) else [ev]:
                if 'over' in e and e.get('role', 'storage') not in used:
                    used.append(e.get('role', 'storage'))
    legend = ''.join(f'<span class="actor-{r}">{ROLES[r]}</span>' for r in used)
    reading = row.get('reading') or ('Numbers follow time from top to bottom.' if row['kind'] == 'sequence'
                                     else 'Numbered arrows name relationships, not time steps.')
    sources = ''.join(f'<li><a href="{escape(u)}" target="_blank" rel="noreferrer">{escape(u.split("/")[2])}: '
                      f'{escape(u.rstrip("/").split("/")[-1] or "documentation")}</a></li>' for u in row['sources'])
    figure = (f'<figure class="fm-figure" data-figure="{row["diagram"]}" data-pb-wide>'
              f'<p class="fm-heading">{escape(row["title"])}</p>'
              # The shared WideDiagram component adds scroll semantics and edge fades only when it overflows.
              f'<div class="pb-widewrap"><div class="fm-scroll pb-wide" data-label="Figure {row["number"]}">'
              + canvas.svg(prefix, row['title'], row['caption']) + '</div></div>'
              f'<div class="fm-legend">{legend}<em>{escape(reading)}</em></div>'
              f'<figcaption><strong>Figure {row["number"]}.</strong> {escape(row["caption"])}</figcaption>'
              f'<details class="fm-sources"><summary>Read the figure as text</summary><ol>{transcript(row)}</ol>'
              f'<p>Sources</p><ul>{sources}</ul></details></figure>')
    if provenance != 'original':
        return figure, ''
    original = (f'<details class="original-diagram"><summary>Original diagram from the chapter</summary>'
                f'<pre tabindex="0"><code data-{provenance}-diagram-source="{row["diagram"]}">{escape(source)}</code></pre></details>')
    return figure, original
