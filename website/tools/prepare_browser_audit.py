#!/usr/bin/env python3
"""Copy a built site into a disposable, instrumented browser QA directory."""
from pathlib import Path
from html.parser import HTMLParser
import argparse, hashlib, json, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]


class SourceNode:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, SourceNode): yield from child.walk()

    def text(self):
        # Presentation labels cannot establish that an original answer survived.
        if self.tag in {'script','style'} or set(self.attrs.get('class','').split()) & {'blend','correction-note','code-header','qa-answer-label'}: return ''
        return ''.join(child.text() if isinstance(child, SourceNode) else child for child in self.children)


class SourceHTML(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = SourceNode(); self.stack = [self.root]; self.feed(html)

    def handle_starttag(self, tag, attrs):
        node=SourceNode(tag,attrs);self.stack[-1].children.append(node)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}: self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1,0,-1):
            if self.stack[index].tag==tag:
                self.stack=self.stack[:index];break

    def handle_data(self, value): self.stack[-1].children.append(value)


def source_pair_manifest(output, pages):
    """Read unpaired static HTML, independently of the runtime pairing metadata.

    The static build has already checked its source units. Exclude presentation
    chrome so copying code or simplifying a header cannot alter answer identity.
    """
    import re
    digest=lambda node:hashlib.sha256(re.sub(r'\s+',' ',node.text()).strip().encode()).hexdigest()
    manifest={}
    for page in pages:
        dom=SourceHTML((output/page['url'].strip('/')/'index.html').read_text())
        sections={node.attrs.get('id'):node for node in dom.root.walk() if node.tag=='section'}
        if 'section-probing-questions' not in sections or 'section-answer-key' not in sections: continue
        lists=[]
        for key in ['section-probing-questions','section-answer-key']:
            lists.append(next((node for node in sections[key].children if isinstance(node,SourceNode) and node.tag=='ol'),None))
        if not all(lists):raise ValueError('Missing original question/answer list: '+page['source'])
        questions,answers=([node for node in group.children if isinstance(node,SourceNode) and node.tag=='li'] for group in lists)
        first=int(lists[0].attrs.get('start','1'))
        if len(questions)!=len(answers) or first!=int(lists[1].attrs.get('start','1')):raise ValueError('Question/answer numbering mismatch: '+page['source'])
        manifest[page['source']]=[{'number':first+index,'question_sha256':digest(question),'answer_sha256':digest(answer)} for index,(question,answer) in enumerate(zip(questions,answers))]
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--tree', choices=['all','kotlin','android','engineering-fundamentals','computer-science','platform-engineering'], default='all')
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
    version = hashlib.sha256((audit+(ROOT/'website/tools/browser_audit_runner.js').read_text()+(ROOT/'website/blend.js').read_text()+(ROOT/'website/design-system/components/bundle.js').read_text()).encode()).hexdigest()[:12]
    (fx/'audit.js').write_text('window.__inspectOriginalContent = '+audit+';\n')
    shutil.copy2(ROOT/'website/tools/browser_audit_runner.js',fx/'run.js')
    pages = json.loads((output/'coverage/pages.json').read_text())
    pairs = source_pair_manifest(output,pages)
    (output/'coverage/qa-pairs.json').write_text(json.dumps(pairs,separators=(',',':'))+'\n')
    targets = [p['url'] for p in pages if args.tree == 'all' or p['source'].startswith(args.tree+'/') or p['source']==args.tree+'.md']
    for page in output.rglob('index.html'):
        page.write_text(page.read_text().replace('<head>', '<head><script>window.__qaErrors=[];addEventListener(\"error\",e=>{if(e.message)window.__qaErrors.push(e.message)});addEventListener(\"unhandledrejection\",e=>window.__qaErrors.push(String(e.reason)));</script>').replace('</body>',f'<script src="/fx/audit.js?v={version}"></script></body>'))
    harness = '<!doctype html><meta charset="utf-8"><title>Reader browser audit</title><h1>Reader browser audit</h1><p>Disposable QA copy. Checks source preservation, image readiness, animations and layout widths with 22px handwritten text.</p><button id="start">Start audit</button><pre id="qa-results">Not started</pre><script src="/fx/run.js"></script><script>document.getElementById("start").onclick=()=>window.__runAudit('+json.dumps(targets)+');</script>'
    (output/'audit.html').write_text(harness.replace('/fx/run.js',f'/fx/run.js?v={version}'))
    # A self-contained real-runtime fixture keeps simultaneous controllers visible.
    import re
    scene = re.search(r'<section class="pb-figure" data-pb-flow="scene".*?</section>', (ROOT/'website/content/blend/android/retrofit-and-okhttp.blend').read_text(), re.S)[0]
    illustrated_stepper = re.search(r'<figure class="stepper".*?</figure>', (ROOT/'website/content/blend/channels-and-select.blend').read_text(), re.S)[0]
    second_scene = re.search(r'<section class="pb-figure" data-pb-flow="scene".*?</section>', (ROOT/'website/content/blend/android/workmanager.blend').read_text(), re.S)[0]
    def legacy(extra='', transfer=True):
        data = [{'caption':'A owns the request','add':['a','b'],'state':{'a':'active'}}, {'caption':'Deliver to B','state':{'a':'done','b':'active'}}]
        if transfer: data[1]['handoff']={'from':'a','to':'b'}
        return '<figure class="stepper" '+extra+'><div class="stage viz-flow"><div class="node" data-el="a">A</div><div class="node" data-el="b">B</div></div><script type="application/json" class="steps">'+json.dumps(data)+'</script></figure>'
    loop_data = {'nodes':[{'id':'a','label':'Sender'},{'id':'b','label':'Receiver'}], 'edges':[{'id':'ab','from':'a','to':'b'}], 'streams':[{'edge':'ab','tone':'fwd'}], 'state':{'nodes':{}}}
    loop = '<section class="pb-figure" data-pb-flow="loop"><div class="pb-paper"><svg class="pb-svg"></svg></div><button data-toggle>Play</button><script type="application/json">'+json.dumps(loop_data)+'</script></section>'
    fixture = '<!doctype html><meta charset="utf-8"><title>Reader motion regressions</title>'+''.join('<link rel="stylesheet" href="/'+f+'">' for f in ['styles.css','blend.css','tokens.css','theme.css','flow.css'])
    fixture += '<style>body{padding:12px}#cases{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.pb-paper{height:65px;overflow:hidden}.pb-caption{min-height:0;height:54px;overflow:hidden}.pb-sub{display:none}.pb-figure{padding:8px}.stepper{margin:0;padding:8px}.stepper-caption{min-height:0}#motion-results{white-space:pre-wrap}</style>'
    fixture += '<button id="motion-start">Start motion regressions</button><div id="cases">'+scene+second_scene+loop+legacy()+legacy(transfer=False)+legacy('data-no-handoff')+illustrated_stepper+'</div><pre id="motion-results">Not started</pre>'
    fixture += '<script src="/flow.js"></script><script src="/blend.js"></script><script src="/fx/motion.js"></script><script>document.getElementById("motion-start").onclick=runMotionAudit</script>'
    fixture=re.sub(r'((?:src|href)="/[^"?]+\.(?:js|css))"',lambda m:m[1]+'?v='+version+'"',fixture)
    (output/'motion-fixture.html').write_text(fixture)
    shutil.copy2(ROOT/'website/tools/motion_audit_runner.js',fx/'motion.js')
    shutil.copy2(ROOT/'website/tools/binder_audit_runner.js',fx/'binder.js')
    (output/'binder-audit.html').write_text('<!doctype html><title>Binder reading matrix</title><button id="binder-start">Start Binder matrix</button><pre id="binder-results">Not started</pre><iframe id="binder-frame" style="width:1440px;height:900px;position:fixed;left:0;top:150px;opacity:.01;pointer-events:none"></iframe><script src="/fx/binder.js"></script><script>document.getElementById("binder-start").onclick=runBinderAudit</script>')
    shutil.copy2(ROOT/'website/tools/refinement_audit_runner.js',fx/'refinement.js')
    (output/'refinement-audit.html').write_text('<!doctype html><title>Reader refinement checks</title><button id="refinement-start">Start refinement checks</button><pre id="refinement-results">Not started</pre><iframe style="width:390px;height:900px;position:fixed;left:0;top:150px;opacity:.01;pointer-events:none"></iframe><script src="/fx/refinement.js"></script><script>document.getElementById("refinement-start").onclick=runRefinementAudit</script>')
    shutil.copy2(ROOT/'website/tools/ux_audit_runner.js',fx/'ux.js')
    (output/'ux-audit.html').write_text('<!doctype html><title>Reader UX checks</title><button id="ux-start">Start UX checks</button><pre id="ux-results">Not started</pre><iframe style="width:390px;height:900px;position:fixed;left:0;top:150px;opacity:.01;pointer-events:none"></iframe><script src="/fx/ux.js"></script><script>document.getElementById("ux-start").onclick=runUXAudit</script>')
    shutil.copy2(ROOT/'website/tools/qa_fixture_runner.js',fx/'qa-fixtures.js')
    subprocess.run([sys.executable,str(ROOT/'website/scripts/make_browser_fixtures.py'),str(output/'fixtures')],check=True)
    (output/'qa-fixtures.html').write_text('<!doctype html><title>Question answer preservation regressions</title><button id="qa-fixture-start">Start Q&amp;A regressions</button><pre id="qa-fixture-results">Not started</pre><iframe style="width:390px;height:900px;position:fixed;left:0;top:150px;opacity:.01;pointer-events:none"></iframe><script src="/fx/qa-fixtures.js"></script><script>document.getElementById("qa-fixture-start").onclick=runQAFixtures</script>')
    export_script = "<button id=\"export-results\">Download results</button><script>document.getElementById('export-results').onclick=()=>{const out=document.querySelector('pre');const a=document.createElement('a');a.download=location.pathname.split('/').pop().replace('.html','.json');a.href=URL.createObjectURL(new Blob([out.textContent],{type:'application/json'}));a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};</script>"
    for name in ['audit.html','motion-fixture.html','binder-audit.html','refinement-audit.html','ux-audit.html','qa-fixtures.html']:
        page=output/name
        page.write_text(page.read_text()+export_script)
    print(f'{len(targets)} pages prepared in {output}. Serve this directory; open /audit.html and press Start audit.')


if __name__ == '__main__':
    main()
