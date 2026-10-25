#!/usr/bin/env python3
"""Create disposable browser-audit fixtures; serve the output and inspect cases.json."""
from pathlib import Path
import argparse, json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    first = '<p>First original paragraph.</p>'
    repeated = '<p>Repeated original paragraph.</p>'
    body = first + repeated + repeated
    cases = {
        'visible': (body, '', 'pass'),
        'template': (body.replace(first, f'<template>{first}</template>'), '', 'fail'),
        'noscript': (body.replace(first, f'<noscript>{first}</noscript>'), '', 'fail'),
        'removed': (body.replace(first, ''), '', 'fail'),
        'reordered': (repeated + first + repeated, '', 'fail'),
        'repeat-removed': (first + repeated, '', 'fail'),
        'stylesheet': (body.replace(first, '<p class="hidden">First original paragraph.</p>'), '.hidden{display:none}', 'fail'),
        'opacity-dot-zero': (body.replace(first, f'<div style="opacity:.0">{first}</div>'), '', 'fail'),
        'inherited-opacity': (f'<div style="opacity:0">{body}</div>', '', 'fail'),
        'nearly-transparent': (body.replace(first, f'<div style="opacity:.01">{first}</div>'), '', 'fail'),
        'transparent-color': (body.replace(first, '<p style="color:transparent">First original paragraph.</p>'), '', 'fail'),
        'filter-opacity': (body.replace(first, f'<div style="filter:opacity(0)">{first}</div>'), '', 'fail'),
        'clip-path': (body.replace(first, f'<div style="clip-path:inset(100%)">{first}</div>'), '', 'fail'),
        'offscreen': (body.replace(first, f'<div style="position:absolute;left:-99999px">{first}</div>'), '', 'fail'),
        'text-indent': (body.replace(first, f'<div style="text-indent:-9999px;overflow:hidden;width:300px">{first}</div>'), '', 'fail'),
        'disguised-disclosure': (body.replace(first, f'<details class="original-diagram"><summary>Original diagram from the chapter</summary>{first}</details>'), '', 'fail'),
        'labelled-copy-cannot-replace-original': (body.replace(first, f'<div class="blend">{first}</div>'), '', 'fail'),
        # Occlusion is deliberately outside the automatic audit's guarantee.
        'overlay-limitation': (body + '<div class="blend overlay">Overlay</div>', '.overlay{position:fixed;inset:0;background:white;z-index:99999}', 'limitation'),
        'broken-lazy-diagram': (body + '<div style="margin-top:20000px"><img data-original-diagram="fixture-diagram" src="missing-diagram.svg" loading="lazy"><details class="diagram-source"><summary>Read diagram source</summary><pre><code data-original-diagram-source="fixture-diagram">graph TD; A--&gt;B\n</code></pre></details></div>', '', 'fail'),
    }
    units = [{'kind':'heading','text':'Fixture'}, {'kind':'text','text':'First original paragraph.'}, *[{'kind':'text','text':'Repeated original paragraph.'}]*2]
    report = []
    for name, (content, css, expected) in cases.items():
        html = '<!doctype html><html><head><meta charset="utf-8"><title>Audit fixture</title><style>'+css+'</style></head><body data-source="fixture"><main><div class="lesson-hero"><h1>Fixture</h1></div><section id="panel-content"><article><section id="section-fixture">'+content+'</section></article></section></main></body></html>'
        (out/(name+'.html')).write_text(html)
        case_units = units + ([{'kind':'diagram','text':'graph TD; A-->B'}] if name == 'broken-lazy-diagram' else [])
        report.append({'name':name,'file':name+'.html','expected':expected,'units':case_units,'diagrams':{'fixture-diagram':'graph TD; A-->B\n'} if name == 'broken-lazy-diagram' else {}})
    (out/'cases.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'{len(report)} browser fixtures: {out}')


if __name__ == '__main__':
    main()
