#!/usr/bin/env python3
"""Fail if any part of an original chapter is missing, moved, hidden or mixed with unlabelled text.

The original chapter is every heading, paragraph, list item, table row, code block, raw HTML
block and diagram source in its Markdown. On the built page, original text lives only in the
opening (`.original-opening`) and the chapter sections (`section#section-…`). Inside those,
website-only material is always wrapped and labelled (`.blend`, `.correction-note`, code-card
headers, part bands), and the check reads around it. It then requires that:

- every original unit appears, in the original order, as often as it does in the Markdown;
- no original unit is hidden (`hidden`, `aria-hidden`, `display:none`, `.sr-only`) or folded
  into a `<details>`, except actual Mermaid source inside the build's diagram disclosures;
- no other text appears in the original areas, apart from a few fixed interface strings.

Text changed by an approved correction is checked in its corrected form. These are static
HTML checks: CSS visibility is checked independently by browser_preservation.js in a rendered
browser. The static gate does not claim to evaluate a browser CSS cascade.
"""
from pathlib import Path
from html import unescape
from html.parser import HTMLParser
import json, re, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402  (reuses the build's parser, routes and correction overlay)

MD = build.MD
BOUNDARY = '\x00'
BLOCK = {'address', 'article', 'aside', 'blockquote', 'br', 'dd', 'details', 'div', 'dl', 'dt', 'figcaption',
         'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'li', 'ol', 'p', 'pre', 'section', 'summary',
         'table', 'tbody', 'thead', 'tfoot', 'tr', 'ul'}
VOID = {'area', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
ADDED = {'blend', 'correction-note', 'code-header', 'part-band', 'steps-text'}
DISCLOSURES = {'original-diagram', 'diagram-source'}
# Interface text the build places among the original blocks.
CHROME = {'Copy code', 'Read diagram source', 'Original diagram from the chapter',
          'Concept relationships from this section.'}


def normalise(html):
    text = unescape(re.sub(r'<[^>]+>', ' ', html)).replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def units(source):
    """Yield (kind, text) for every block-level unit of a Markdown document, in order."""
    tokens = MD.parse(source)
    row = None
    for i, token in enumerate(tokens):
        if token.type == 'tr_open':
            row = []
        elif token.type == 'tr_close':
            yield 'table row', ' '.join(cell for cell in row if cell)
            row = None
        elif token.type == 'inline':
            text = normalise(MD.renderer.renderInline(token.children, MD.options, {}))
            if row is not None:
                row.append(text)
            elif text:
                kind = 'heading' if tokens[i - 1].type == 'heading_open' else 'text'
                yield kind, text
        elif token.type in ('fence', 'code_block'):
            yield ('diagram' if token.type == 'fence' and token.info.strip() == 'mermaid' else 'code'), token.content.rstrip('\n')
        elif token.type == 'html_block' and normalise(token.content):
            yield 'html', normalise(token.content)


class Page(HTMLParser):
    """Flatten the Content panel into the text of its original areas, with block boundaries."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.size = [], 0
        self.concealed = []          # (start, end) spans of original-area text a reader cannot see
        self.codes = []              # (text, concealed) for every <pre><code> in the original areas
        self.stack, self.code = [], None
        self.headings, self.heading = [], None

    def top(self):
        return self.stack[-1] if self.stack else {'tag': '', 'zone': False, 'added': False, 'concealed': False, 'hidden': False, 'details': []}

    def emit(self, text, concealed=False):
        if concealed and text.strip(BOUNDARY + ' '):
            self.concealed.append((self.size, self.size + len(text)))
        self.parts.append(text)
        self.size += len(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get('class') or '').split())
        style = re.sub(r'\s+', '', a.get('style') or '').lower()
        parent = self.top()
        if tag in BLOCK:
            self.emit(BOUNDARY)
        elif tag in ('td', 'th'):
            self.emit(' ')
        if tag in VOID:
            return
        details = list(parent['details'])
        if tag == 'summary' and parent['tag'] == 'details':
            details = details[:-1]  # the summary is outside its own disclosure's folded body
        hidden = (parent['hidden'] or 'hidden' in a or a.get('aria-hidden') == 'true'
                  or 'sr-only' in classes or 'display:none' in style or 'visibility:hidden' in style
                  or bool(re.search(r'(?:^|;)opacity:0(?:\.0+)?%?(?:!important)?(?:;|$)', style)))
        if tag == 'details':
            details.append(classes)
        self.stack.append({
            'tag': tag, 'hidden': hidden, 'details': details,
            'concealed': hidden or bool(details),
            'zone': parent['zone'] or 'original-opening' in classes or (tag == 'section' and (a.get('id') or '').startswith('section-')),
            'added': parent['added'] or bool(classes & ADDED),
        })
        if re.fullmatch(r'h[1-6]', tag) and self.top()['zone'] and not self.top()['added']:
            self.heading = (self.size, tag)
        if tag == 'code' and parent['tag'] == 'pre' and self.top()['zone'] and not self.top()['added']:
            self.code = []

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            element = self.stack.pop()
            if element['tag'] == 'code' and self.code is not None:
                self.codes.append((''.join(self.code), element['hidden'], element['details']))
                self.code = None
            if element['tag'] == tag:
                if re.fullmatch(r'h[1-6]', tag) and self.heading is not None:
                    start, level = self.heading
                    self.headings.append((start, self.size, level))
                    self.heading = None
                break
        if tag in BLOCK:
            self.emit(BOUNDARY)

    def handle_data(self, data):
        if self.code is not None:
            self.code.append(data)
        element = self.top()
        if element['zone'] and not element['added']:
            self.emit(re.sub(r'\s+', ' ', data.replace('\xa0', ' ')), element['concealed'])

    def text(self):
        return ''.join(self.parts)


def pattern(unit, anchored):
    # Markup boundaries add or drop spaces ("( `val` ," renders as "(val,"), so spacing is free; characters are not.
    body = r'[ \x00]*'.join(re.escape(word) for word in unit.split(' '))
    return re.compile((r'(?<=\x00)[ ]*' if anchored else '') + body)


def content_panel(page):
    match = re.search(r'<section id="panel-content".*?(?=<section id="panel-qa")', page, re.S)
    if not match:
        raise ValueError('page has no Content panel')
    return match.group(0)


def verify(path, panel):
    """Return (problems, units checked) for one page's Content panel."""
    raw = (build.ROOT / path).read_text()
    source, _ = build.corrected(raw, path)
    page = Page()
    page.feed(panel)
    page.close()
    text = page.text()
    covered = bytearray(len(text))
    problems, position, code_index, checked = [], 0, 0, 0
    page_title = build.title(build.ROOT / path)
    heading_levels = iter(token.tag for token in MD.parse(source) if token.type == 'heading_open')

    def is_concealed(start, end):
        return any(start < c_end and c_start < end for c_start, c_end in page.concealed)

    for kind, unit in units(source):
        checked += 1
        if kind == 'heading':
            level = next(heading_levels)
        if kind == 'heading' and build.clean(unit) == page_title and checked == 1:
            continue  # the H1 is shown as the page title
        if kind in ('code', 'diagram'):
            found = next((i for i in range(code_index, len(page.codes)) if page.codes[i][0].rstrip('\n') == unit), None)
            label = unit.splitlines()[0][:80] if unit else '(empty)'
            if found is None:
                moved = any(block[0].rstrip('\n') == unit for block in page.codes)
                problems.append(('out of order' if moved else 'missing', kind, label))
                continue
            _, hidden, disclosures = page.codes[found]
            permitted_diagram = kind == 'diagram' and all(classes & DISCLOSURES for classes in disclosures)
            if hidden or (disclosures and not permitted_diagram):
                problems.append(('hidden', kind, label))
            code_index = found + 1
            # The code's text is also in the flat text; claim it there so it is not reported as extra.
            match = pattern(re.sub(r'\s+', ' ', unit).strip(), False).search(text, position) if unit.strip() else None
            if match:
                covered[match.start():match.end()] = b'\x01' * (match.end() - match.start())
                position = match.end()
            continue
        regex = pattern(unit, anchored=kind != 'html')
        match = regex.search(text, position)
        if not match:
            problems.append(('out of order' if regex.search(text) else 'missing', kind, unit))
            continue
        if kind == 'heading' and not any(start <= match.start() and match.end() <= end and tag == level for start, end, tag in page.headings):
            problems.append(('structure', kind, unit))
        if is_concealed(match.start(), match.end()):
            problems.append(('hidden', kind, unit))
        covered[match.start():match.end()] = b'\x01' * (match.end() - match.start())
        position = match.end()

    # Anything left in the original areas must be interface text, not unlabelled additions.
    leftover = ''.join(BOUNDARY if covered[i] else ch for i, ch in enumerate(text))
    for piece in leftover.split(BOUNDARY):
        piece = piece.strip()
        if piece and piece not in CHROME:
            problems.append(('unlabelled', 'text', piece))
    return problems, checked


def check(path):
    page_file = build.OUT / build.route(path)[len(build.BASE):].strip('/') / 'index.html'
    html = page_file.read_text()
    problems, checked = verify(path, content_panel(html))
    titles = re.findall(r'<h1\b[^>]*>(.*?)</h1>', html, re.S)
    if len(titles) != 1 or normalise(titles[0]) != build.title(build.ROOT / path):
        problems.append(('structure', 'heading', 'The original H1 must appear once as the page title'))
    return problems, checked


def self_test():
    """The checker must catch reordering, loss of a repeated unit, hiding, relabelling and unlabelled text."""
    def panel_of(path):
        page_file = build.OUT / build.route(path)[len(build.BASE):].strip('/') / 'index.html'
        return content_panel(page_file.read_text())
    path = 'kotlin/language-core/variables.md'
    panel = panel_of(path)
    paragraphs = re.findall(r'<p>(?:(?!</p>).)+</p>', panel.split('id="section-', 1)[1], re.S)
    first, second = paragraphs[2], paragraphs[3]
    cases = {
        'swapped paragraphs': panel.replace(first, '\x02', 1).replace(second, first, 1).replace('\x02', second, 1),
        'hidden paragraph': panel.replace(first, f'<div hidden>{first}</div>', 1),
        'paragraph folded into details': panel.replace(first, f'<details><summary>More</summary>{first}</details>', 1),
        'paragraph relabelled as added': panel.replace(first, f'<div class="blend">{first}</div>', 1),
        'unlabelled addition': panel.replace(first, first + '<p>An added claim with no label.</p>', 1),
        'removed paragraph': panel.replace(first, '', 1),
        'prose folded with diagram class': panel.replace(first, f'<details class="original-diagram"><summary>Original diagram from the chapter</summary>{first}</details>', 1),
        'transparent paragraph': panel.replace(first, f'<div style="opacity: 0">{first}</div>', 1),
        'heading demoted to paragraph': panel.replace('<h2 id="overview">Overview</h2>', '<p id="overview">Overview</p>', 1),
        'heading level changed': panel.replace('<h2 id="overview">Overview</h2>', '<h3 id="overview">Overview</h3>', 1),
    }
    # "Staff-level guidance:" appears twice in this chapter; dropping the second must be caught.
    repeated_path = 'kotlin/version-updates/kotlin-2-4-update.md'
    repeated = panel_of(repeated_path)
    last = [m for m in re.finditer(r'<p>(?:(?!</p>).)*Staff-level guidance:(?:(?!</p>).)*</p>', repeated, re.S)][-1]
    checks = [(path, name, broken) for name, broken in cases.items()]
    checks.append((repeated_path, 'second of two equal paragraphs removed', repeated[:last.start()] + repeated[last.end():]))
    for page_path, name, broken in checks:
        if broken == panel_of(page_path):
            raise AssertionError(f'preservation self-test: {name} did not alter the fixture')
        problems, _ = verify(page_path, broken)
        if not problems:
            raise AssertionError(f'preservation self-test: {name} was not detected')


def main():
    self_test()
    order = ['kotlin.md'] + sorted(p for p in build.PATHS if p != 'kotlin.md')
    total_problems = total_checked = 0
    report = {}
    for path in order:
        problems, checked = check(path)
        total_checked += checked
        report[path] = [{'problem': p, 'kind': k, 'text': t} for p, k, t in problems]
        total_problems += len(problems)
        status = 'ok' if not problems else f'{len(problems)} PROBLEMS'
        print(f'{status:>12}  {path}')
        for problem, kind, unit in problems[:5]:
            print(f'              - {problem} {kind}: {unit[:110]}')
    (build.OUT / 'coverage').mkdir(parents=True, exist_ok=True)
    (build.OUT / 'coverage/preservation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Preservation: {len(order)} pages, {total_checked} original units checked in order, {total_problems} problems.')
    return 1 if total_problems else 0


if __name__ == '__main__':
    sys.exit(main())
