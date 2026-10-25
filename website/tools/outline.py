import sys,hashlib,pathlib
sys.path.insert(0,'website/scripts')
import build
from markdown_it import MarkdownIt
MD=MarkdownIt('commonmark',{'html':True}).enable(['table','strikethrough'])
n=int(sys.argv[1])
for h,ps in build.phases('android'):
    if not h.startswith(f'Phase {n}'): continue
    for p in ps:
        toks=MD.parse(pathlib.Path(p).read_text()); heads=[]; out=[]
        for i,t in enumerate(toks):
            if t.type=='heading_open' and t.tag=='h2': heads.append(build.clean(toks[i+1].content))
            if t.type=='fence' and t.info.strip()=='mermaid': out.append(f'mermaid {hashlib.sha256(t.content.encode()).hexdigest()[:16]} in [{heads[-1] if heads else "-"}]')
        print(f'== {p} ({len(pathlib.Path(p).read_text().split())}w)\n  H2: '+' | '.join(heads)+('\n  '+'\n  '.join(out) if out else ''))
