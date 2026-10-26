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
        page.write_text(page.read_text().replace('<head>', '<head><script>window.__qaErrors=[];addEventListener(\"error\",e=>{if(e.message)window.__qaErrors.push(e.message)});addEventListener(\"unhandledrejection\",e=>window.__qaErrors.push(String(e.reason)));</script>').replace('</body>',f'<script src="/fx/audit.js?v={version}"></script></body>'))
    harness = '<!doctype html><meta charset="utf-8"><title>Reader browser audit</title><h1>Reader browser audit</h1><p>Disposable QA copy. Checks source preservation, image readiness, animations and layout widths with 22px handwritten text.</p><button id="start">Start audit</button><pre id="qa-results">Not started</pre><script src="/fx/run.js"></script><script>document.getElementById("start").onclick=()=>window.__runAudit('+json.dumps(targets)+');</script>'
    (output/'audit.html').write_text(harness.replace('/fx/run.js',f'/fx/run.js?v={version}'))
    # A self-contained real-runtime fixture keeps simultaneous controllers visible.
    import re
    scene = re.search(r'<section class="pb-figure" data-pb-flow="scene".*?</section>', (ROOT/'website/content/blend/android/retrofit-and-okhttp.blend').read_text(), re.S)[0]
    second_scene = re.search(r'<section class="pb-figure" data-pb-flow="scene".*?</section>', (ROOT/'website/content/blend/android/workmanager.blend').read_text(), re.S)[0]
    def legacy(extra='', transfer=True):
        data = [{'caption':'A owns the request','add':['a','b'],'state':{'a':'active'}}, {'caption':'Deliver to B','state':{'a':'done','b':'active'}}]
        if transfer: data[1]['handoff']={'from':'a','to':'b'}
        return '<figure class="stepper" '+extra+'><div class="stage viz-flow"><div class="node" data-el="a">A</div><div class="node" data-el="b">B</div></div><script type="application/json" class="steps">'+json.dumps(data)+'</script></figure>'
    loop_data = {'nodes':[{'id':'a','label':'Sender'},{'id':'b','label':'Receiver'}], 'edges':[{'id':'ab','from':'a','to':'b'}], 'streams':[{'edge':'ab','tone':'fwd'}], 'state':{'nodes':{}}}
    loop = '<section class="pb-figure" data-pb-flow="loop"><div class="pb-paper"><svg class="pb-svg"></svg></div><button data-toggle>Play</button><script type="application/json">'+json.dumps(loop_data)+'</script></section>'
    fixture = '<!doctype html><meta charset="utf-8"><title>Reader motion regressions</title>'+''.join('<link rel="stylesheet" href="/'+f+'">' for f in ['styles.css','blend.css','tokens.css','theme.css','flow.css'])
    fixture += '<style>body{padding:12px}#cases{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.pb-paper{height:65px;overflow:hidden}.pb-caption{min-height:0;height:54px;overflow:hidden}.pb-sub{display:none}.pb-figure{padding:8px}.stepper{margin:0;padding:8px}.stepper-caption{min-height:0}#motion-results{white-space:pre-wrap}</style>'
    fixture += '<button id="motion-start">Start motion regressions</button><div id="cases">'+scene+second_scene+loop+legacy()+legacy(transfer=False)+legacy('data-no-handoff')+'</div><pre id="motion-results">Not started</pre>'
    fixture += '<script src="/flow.js"></script><script src="/blend.js"></script><script src="/fx/motion.js"></script><script>document.getElementById("motion-start").onclick=runMotionAudit</script>'
    (output/'motion-fixture.html').write_text(fixture)
    shutil.copy2(ROOT/'website/tools/motion_audit_runner.js',fx/'motion.js')
    shutil.copy2(ROOT/'website/tools/binder_audit_runner.js',fx/'binder.js')
    (output/'binder-audit.html').write_text('<!doctype html><title>Binder reading matrix</title><button id="binder-start">Start Binder matrix</button><pre id="binder-results">Not started</pre><iframe id="binder-frame" style="width:1440px;height:900px;position:fixed;left:0;top:150px;opacity:.01;pointer-events:none"></iframe><script src="/fx/binder.js"></script><script>document.getElementById("binder-start").onclick=runBinderAudit</script>')
    export_script = "<button id=\"export-results\">Download results</button><script>document.getElementById('export-results').onclick=()=>{const out=document.querySelector('pre');const a=document.createElement('a');a.download=location.pathname.split('/').pop().replace('.html','.json');a.href=URL.createObjectURL(new Blob([out.textContent],{type:'application/json'}));a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};</script>"
    for name in ['audit.html','motion-fixture.html','binder-audit.html']:
        page=output/name
        page.write_text(page.read_text()+export_script)
    print(f'{len(targets)} pages prepared in {output}. Serve this directory; open /audit.html and press Start audit.')


if __name__ == '__main__':
    main()
