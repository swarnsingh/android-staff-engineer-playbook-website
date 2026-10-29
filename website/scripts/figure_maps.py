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
        room = n.get('w', CARD_W) - 28
        if width(n['title'], 'title') > room or any(width(d, 'detail') > room for d in lines(n.get('detail'))):
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
                used = [e.get('over'), e.get('at'), e.get('from'), e.get('to')]
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
    return n.get('h', 30 + LINE * (1 + len(lines(n.get('detail')))))


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
    rows = [('fm-title', n['title'])] + [('fm-detail', d) for d in lines(n.get('detail'))]
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


def render_map(row, key):
    c = Canvas(key)
    gx, gy = row.get('grid', GRID)
    nodes = {}
    for n in row['nodes']:
        m = dict(n)
        m['w'] = 24 if n.get('shape') in ('start', 'end') else n.get('w', row.get('card_w', CARD_W))
        m['h'] = card_height(n)
        m['x'] = n['x'] if 'x' in n else n['col'] * gx
        m['y'] = n['y'] if 'y' in n else n['row'] * gy
        nodes[n['id']] = m
    for g in row.get('groups', []):
        members = [nodes[m] for m in g['nodes']]
        x0 = min(m['x'] for m in members) - 24
        y0 = min(m['y'] for m in members) - 52
        x1 = max(m['x'] + m['w'] for m in members) + 24
        y1 = max(m['y'] + m['h'] for m in members) + 24
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
    for p in row['participants']:
        card(c, dict(p, x=lanes[p['id']] - CARD_W / 2, y=0, w=CARD_W, h=card_height(p)))
    head = max(card_height(p) for p in row['participants'])
    y, number, body = head + 44, 0, []
    for event in row['events']:
        tallest = 0
        for e in event if isinstance(event, list) else [event]:
            if 'over' in e:
                w = width(e['text'], 'note') + 32
                x = lanes[e['over']] - w / 2
                body.append(f'<g class="fm-note actor-{e.get("role", "storage")}"><rect x="{x:.1f}" y="{y-17}" width="{w:.1f}" height="34" rx="9"/>'
                            f'<text x="{lanes[e["over"]]}" y="{y}" dominant-baseline="central">{escape(e["text"])}</text></g>')
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
                    items.append(f'{names[e["over"]]} — {e["text"]}')
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
