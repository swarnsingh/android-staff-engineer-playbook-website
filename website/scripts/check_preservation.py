#!/usr/bin/env python3
"""Fail if any part of an original chapter is missing from its built Content tab.

Every heading, paragraph, list item, table row, code block and diagram source in
the original Markdown must appear on the chapter's page, and headings must keep
their original order. Text changed by an approved correction is checked in its
corrected form, so a correction can never remove content silently.
"""
from pathlib import Path
from html import unescape
import json, re, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402  (reuses the build's parser, routes and correction overlay)

MD = build.MD


def normalise(html):
    text = unescape(re.sub(r'<[^>]+>', ' ', html)).replace(' ', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def units(source):
    """Yield (kind, text) for every block-level unit of a Markdown document."""
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
            yield 'code', token.content.rstrip('\n')
        elif token.type == 'html_block' and normalise(token.content):
            yield 'html', normalise(token.content)


def content_panel(page):
    match = re.search(r'<section id="panel-content".*?(?=<section id="panel-qa")', page, re.S)
    if not match:
        raise ValueError('page has no Content panel')
    return match.group(0)


def check(path):
    raw = (build.ROOT / path).read_text()
    source, _ = build.corrected(raw, path)
    page_file = build.OUT / build.route(path)[len(build.BASE):].strip('/') / 'index.html'
    panel = content_panel(page_file.read_text())
    text = normalise(panel)
    code = {unescape(re.sub(r'<[^>]+>', '', c)).rstrip('\n') for c in re.findall(r'<code[^>]*>(.*?)</code>', panel, re.S)}
    missing, position, checked = [], 0, 0
    for kind, unit in units(source):
        checked += 1
        if kind == 'heading':
            if build.clean(unit) == build.title(build.ROOT / path):
                continue  # the H1 is shown as the page title
            found = text.find(unit, position)
            if found < 0:
                missing.append((kind, unit))
            else:
                position = found  # headings must appear in their original order
        elif kind == 'code':
            if unit not in code:
                missing.append((kind, unit.splitlines()[0][:80] if unit else '(empty)'))
        elif unit not in text:
            missing.append((kind, unit))
    return missing, checked


def main():
    order = ['kotlin.md'] + sorted(p for p in build.PATHS if p != 'kotlin.md')
    total_missing = total_checked = 0
    report = {}
    for path in order:
        missing, checked = check(path)
        total_checked += checked
        report[path] = [{'kind': k, 'text': t} for k, t in missing]
        total_missing += len(missing)
        status = 'ok' if not missing else f'{len(missing)} MISSING'
        print(f'{status:>12}  {path}')
        for kind, unit in missing[:5]:
            print(f'              - {kind}: {unit[:110]}')
    (build.OUT / 'coverage').mkdir(parents=True, exist_ok=True)
    (build.OUT / 'coverage/preservation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Preservation: {len(order)} pages, {total_checked} original units checked, {total_missing} missing.')
    return 1 if total_missing else 0


if __name__ == '__main__':
    sys.exit(main())
