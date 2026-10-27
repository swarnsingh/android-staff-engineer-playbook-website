"""Render website/design-system component previews as standalone pages for local review.

The published design system compiles tokens.json into CSS variables for each preview.
This script does the same locally: one page per component per theme, plus an index.
Usage: python3 website/tools/build_design_system_preview.py  (writes website/.cache/design-system-preview/)
"""
import json, pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'design-system'
OUT = pathlib.Path(__file__).resolve().parents[1] / '.cache' / 'design-system-preview'
tokens = json.loads((ROOT / 'tokens.json').read_text())
themes = [t['id'] for t in tokens['color']['themes']]

def css(theme):
    first = themes[0]
    val = lambda v: v if isinstance(v, str) else v.get(theme, v[first])
    out = [f"--{c['name']}:{val(c['value'])};" for c in tokens['color']['tokens']]
    for family in ('spacing', 'radius', 'layout'):
        out += [f"--{x['name']}:{x['value']};" for x in tokens[family]['tokens']]
    out += [f"--{x['name']}:{val(x['value'])};" for x in tokens['shadow']['tokens']]
    out += [f"--font-{k}:{v};" for k, v in tokens['type']['families'].items()]
    out += [f"--font-prose:var(--font-{tokens['type']['prose']['default']});"]
    return ':root{' + ''.join(out) + '}'

def font_faces():
    faces = []
    for f in tokens['type'].get('fonts', []):
        faces.append(f"@font-face{{font-family:\"{f['family']}\";src:url(\"{f['file']}\") format(\"woff2\");"
                     f"font-weight:{f.get('weight', '400')};font-style:{f.get('style', 'normal')};font-display:swap}}")
    return ''.join(faces)

def shared(name):
    path = ROOT / 'components' / name
    return path.read_text() if path.exists() else ''

OUT.mkdir(parents=True, exist_ok=True)
if (ROOT / 'fonts').exists():
    shutil.copytree(ROOT / 'fonts', OUT / 'fonts', dirs_exist_ok=True)
links = []
for comp in sorted(p.name for p in (ROOT / 'components').iterdir() if p.is_dir() and (p / 'preview.html').exists()):
    body = (ROOT / 'components' / comp / 'preview.html').read_text()
    row = []
    for theme in themes:
        name = f'{comp}-{theme}.html'
        (OUT / name).write_text(f'<!doctype html><html lang="en" data-theme="{theme}"><head><meta charset="utf-8">'
                                f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{comp} · {theme}</title>'
                                f'<style>{font_faces()}{css(theme)}body{{margin:0}}{shared("bundle.css")}</style>'
                                f'<script>{shared("bundle.js")}</script></head><body>{body}</body></html>')
        row.append(f'<a href="{name}">{theme}</a>')
    links.append(f'<li><strong>{comp}</strong>: ' + ' · '.join(row) + '</li>')
(OUT / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Playbook Design System previews</title>'
                                '<body style="font:16px/1.6 system-ui;margin:2rem"><h1>Playbook Design System previews</h1><ul>'
                                + ''.join(links) + '</ul><p>Tokens and guidelines: website/design-system/README.md</p></body>')
print(f'{len(links)} components x {len(themes)} themes -> {OUT}')
