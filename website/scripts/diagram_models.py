"""Authored relationship maps: never infer a transfer from activation or DOM order."""
from pathlib import Path
from html import escape, unescape
import hashlib, json, re
from html.parser import HTMLParser

WEB=Path(__file__).resolve().parents[1]

class Actors(HTMLParser):
    def __init__(self):
        super().__init__();self.nodes=[];self.current=None;self.strong=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'node' in a.get('class','').split() and a.get('data-el'):
            self.current={'id':a['data-el'],'label':'','role':a.get('data-art-role','runtime')};self.nodes.append(self.current)
        if tag=='strong' and self.current and not self.current['label']:self.strong=True
    def handle_endtag(self,tag):
        if tag=='strong':self.strong=False
    def handle_data(self,text):
        if self.strong and self.current:self.current['label']+=text

def models():
    rows=[]
    for source in sorted((WEB/'content/diagram-models').glob('*.json')):
        rows+=json.loads(source.read_text())
    found={}
    for row in rows:
        key=(row['path'],row['figure'])
        if key in found:raise ValueError(f'Duplicate relationship map: {key}')
        found[key]=row
    return found

def check():
    authored=models()
    coverage=json.loads((WEB/'content/illustrated-stepper-coverage.json').read_text())['figures']
    expected={(r['path'],r['figure']):r for r in coverage}
    if set(authored)!=set(expected):raise ValueError(f'Relationship coverage: missing={set(expected)-set(authored)}, extra={set(authored)-set(expected)}')
    for key,row in authored.items():
        if row.get('renderer','map') not in {'map','ownership'}:raise ValueError(f'Unknown diagram renderer: {key}')
        if row.get('renderer')=='ownership' and key!=('android/viewmodel',0):raise ValueError(f'Ownership component is not configured for {key}')
        nodes={n['id'] for n in expected[key]['nodes']};groups=row.get('groups',[]);ids={g['id'] for g in groups}
        if len(ids)!=len(groups) or nodes&ids:raise ValueError(f'Group IDs collide: {key}')
        members=[]
        for g in groups:
            if not g.get('label') or not set(g['nodes'])<=nodes:raise ValueError(f'Invalid boundary: {key} {g}')
            if g.get('parent') and g['parent'] not in ids:raise ValueError(f'Unknown parent boundary: {key}')
            trail={g['id']};parent=g.get('parent')
            while parent:
                if parent in trail:raise ValueError(f'Cyclic ownership: {key}')
                trail.add(parent);parent=next(x for x in groups if x['id']==parent).get('parent')
            members+=g['nodes']
        if len(members)!=len(set(members)):raise ValueError(f'An actor has two owners: {key}')
        for edge in row.get('edges',[]):
            if edge['from'] not in nodes or edge['to'] not in nodes or not edge.get('label'):raise ValueError(f'Invalid relationship: {key} {edge}')
        if not row.get('problem') or not row.get('reading') or not row.get('sources'):raise ValueError(f'Missing explanation or official source: {key}')
        if any(not u.startswith('https://') for u in row['sources']):raise ValueError(f'Invalid source URL: {key}')
    return authored

def label(text):
    # Mermaid quoted labels use entities for quotes and syntax punctuation.
    return escape(unescape(text),quote=True).replace('\n','<br/>')

def graph(row,nodes):
    out=['%%{init: {"theme":"base","htmlLabels":false,"themeVariables":{"fontSize":"17px","fontFamily":"Arial"},"flowchart":{"htmlLabels":false,"curve":"linear","rankSpacing":65,"nodeSpacing":40,"padding":18}}}%%','flowchart TB']
    names={n['id']:'actor'+str(i) for i,n in enumerate(nodes)}
    groupnames={g['id']:'boundary'+str(i) for i,g in enumerate(row.get('groups',[]))}
    groups=row.get('groups',[]);owned={n for g in groups for n in g['nodes']};byid={n['id']:n for n in nodes}
    def actor(n):
        text=str(next(i for i,a in enumerate(nodes,1) if a['id']==n['id']))+' · '+row.get('labels',{}).get(n['id'],n['label'] or n['id'])
        out.append(f'  {names[n["id"]]}["{label(text)}"]:::{n["role"]}')
    def boundary(g):
        out.append(f'  subgraph {groupnames[g["id"]]}["{label(g["label"])}"]')
        for nid in g['nodes']:actor(byid[nid])
        for child in groups:
            if child.get('parent')==g['id']:boundary(child)
        out.append('  end')
    for g in groups:
        if not g.get('parent'):boundary(g)
    for n in nodes:
        if n['id'] not in owned:actor(n)
    for index,e in enumerate(row.get('edges',[]),1):
        out.append(f'  {names[e["from"]]} -->|"{index}. {label(e["label"])}"| {names[e["to"]]}')
    return '\n'.join(out)+'\n'

def enhance(article,path,out,base,authored):
    slug=path.removesuffix('.md')
    if slug.startswith('kotlin/'):slug=slug.removeprefix('kotlin/')
    # Blend names deliberately differ from original source chapter directories.
    coverage=json.loads((WEB/'content/illustrated-stepper-coverage.json').read_text())['figures']
    source=next((r['path'] for r in coverage if r['path']==slug),None)
    if not source:
        candidates=[r['path'] for r in coverage if r['path'].split('/')[-1]==Path(path).stem and r['path'].startswith('android/')==path.startswith('android/')]
        if candidates:source=candidates[0]
    number=0
    def figure(match):
        nonlocal number
        number+=1
        parser=Actors();parser.feed(match[0]);nodes=parser.nodes
        actual=tuple(n['id'] for n in nodes)
        # Inserts are rendered beside their target sections, which can differ
        # from their authoring-file order. Bind by explicit actor identity.
        candidates=[(r['path'],r['figure']) for r in coverage if r['path']==source and tuple(n['id'] for n in r['nodes'])==actual]
        if len(candidates)!=1:raise ValueError(f'Ambiguous/missing relationship map for {path}: {actual}')
        key=candidates[0];row=authored[key]
        if row.get('renderer')=='ownership':
            component=(WEB/'content/components/viewmodel-ownership.html').read_text()
            return '<figure class="stepper has-ownership" data-illustrated>'+component+'</figure>'
        mmd=graph(row,nodes);digest=hashlib.sha256(mmd.encode()).hexdigest()[:16]
        (out/'diagram-sources'/f'{digest}.mmd').write_text(mmd)
        problems='<div class="sequence-intro"><p class="sequence-problem"><strong>The problem.</strong> '+escape(row['problem'])+'</p><p class="sequence-reading">'+escape(row['reading'])+'</p></div>'
        hint='Follow the labelled arrowheads.' if row.get('edges') else 'Compare the labelled alternatives; no flow between them is implied.'
        map_html=f'<div class="relationship-map" data-map="{digest}" role="region" aria-label="Labelled relationships; scroll sideways when needed" tabindex="0"><!--relationship-svg:{digest}--></div><p class="sequence-scroll-hint">{hint} Boundaries group related objects; they are not extra steps. Swipe the diagram sideways when needed.</p>'
        data='<script type="application/json" class="relationship-model">'+json.dumps({**row,'actors':nodes},ensure_ascii=False).replace('</','<\\/')+'</script>'
        links='<details class="relationship-sources"><summary>Diagram sources</summary><ul>'+''.join('<li><a href="'+escape(u)+'" target="_blank" rel="noreferrer">'+escape(u.split('/')[2])+': '+escape(u.split('/')[-1] or 'documentation')+'</a></li>' for u in row['sources'])+'</ul></details>'
        result=match[0].replace('<figure class="stepper"','<figure class="stepper has-relationships"',1)
        result=re.sub(r'(<div class="stage\b)',lambda m:problems+map_html+m[1],result,count=1)
        return result.replace('</figure>',data+links+'</figure>')
    return re.sub(r'<figure class="stepper".*?</figure>',figure,article,flags=re.S)

def inline(out):
    """Inline trusted build-produced SVG so the site's themes can style its text and edges."""
    cache={}
    def embed(match):
        digest=match[1]
        if digest not in cache:
            svg=(out/'diagrams'/f'{digest}.svg').read_text()
            svg=re.sub(r'<style\b[^>]*>.*?</style>','',svg,flags=re.S)
            # Each diagram needs unique marker/label IDs even in a gallery of several.
            ids=re.findall(r'\bid="([^"]+)"',svg)
            for id in sorted(ids,key=len,reverse=True):
                svg=svg.replace('id="'+id+'"','id="rel-'+digest+'-'+id+'"').replace('url(#'+id+')','url(#rel-'+digest+'-'+id+')').replace('href="#'+id+'"','href="#rel-'+digest+'-'+id+'"')
            svg=svg.replace('<svg ','<svg class="relationship-svg" ',1)
            # Preserve the authored font size: local scrolling, never unreadably shrinking.
            size=re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+)',svg)
            if size:svg=re.sub(r'style="[^"]*"','',svg,count=1).replace('<svg ',f'<svg style="width:{float(size[1]):.1f}px;min-width:{float(size[1]):.1f}px" ',1)
            cache[digest]=svg
        return cache[digest]
    for file in out.rglob('*.html'):
        value=file.read_text()
        if '<!--relationship-svg:' in value:file.write_text(re.sub(r'<!--relationship-svg:([a-f0-9]+)-->',embed,value))
