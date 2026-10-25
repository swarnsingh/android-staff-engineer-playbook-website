#!/usr/bin/env python3
"""Copy a built site into a disposable, instrumented browser QA directory."""
from pathlib import Path
import argparse, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--tree', choices=['all','kotlin','android'], default='all')
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or output == ROOT/'website/dist' or output in ROOT.parents:
        raise SystemExit('Choose a disposable output directory distinct from the source and built site.')
    if output.exists():
        if not (output/'.playbook-browser-qa').exists():
            raise SystemExit('Refusing to overwrite a directory not created by this QA tool.')
        shutil.rmtree(output)
    shutil.copytree(ROOT/'website/dist', output)
    (output/'.playbook-browser-qa').write_text('Disposable browser audit copy. Never deploy.\n')
    fx = output/'fx';fx.mkdir(exist_ok=True)
    audit = (ROOT/'website/scripts/browser_preservation.js').read_text()
    version = hashlib.sha256((audit+(ROOT/'website/tools/browser_audit_runner.js').read_text()).encode()).hexdigest()[:12]
    (fx/'audit.js').write_text('window.__inspectOriginalContent = '+audit+';\n')
    shutil.copy2(ROOT/'website/tools/browser_audit_runner.js',fx/'run.js')
    pages = json.loads((output/'coverage/pages.json').read_text())
    targets = [p['url'] for p in pages if args.tree == 'all' or p['source'].startswith(args.tree+'/') or p['source']==args.tree+'.md']
    for page in output.rglob('index.html'):
        page.write_text(page.read_text().replace('</body>',f'<script src="/fx/audit.js?v={version}"></script></body>'))
    harness = '<!doctype html><meta charset="utf-8"><title>Reader browser audit</title><h1>Reader browser audit</h1><p>Disposable QA copy. Checks source preservation, image readiness, animations and layout widths with 22px handwritten text.</p><button id="start">Start audit</button><pre id="qa-results">Not started</pre><script src="/fx/run.js"></script><script>document.getElementById("start").onclick=()=>window.__runAudit('+json.dumps(targets)+');</script>'
    (output/'audit.html').write_text(harness.replace('/fx/run.js',f'/fx/run.js?v={version}'))
    print(f'{len(targets)} pages prepared in {output}. Serve this directory; open /audit.html and press Start audit.')


if __name__ == '__main__':
    main()
