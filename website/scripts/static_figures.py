"""Explicit presentation models for the reader's older teaching figures.

The source HTML is hash-bound. Roles and relationships are authored content;
layout, borders, legends and typography belong to shared components.
"""
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
import hashlib,json,os,re
import figure_maps as fm
WEB=Path(__file__).resolve().parents[1]
SOURCE=WEB/'content/static-figures.json'
FIGURE=re.compile(r'<figure class="viz".*?</figure>',re.S)
ROLES=fm.ROLES
SEEN=set()
class Element:
    def __init__(self,tag='',attrs=(),start='',parent=None):
        self.tag,self.attrs,self.start,self.parent=tag,dict(attrs),start,parent
        self.children=[]
    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child,Element):yield from child.walk()
    def text(self):
        return re.sub(r'\s+',' ',unescape(''.join(c.text() if isinstance(c,Element) else c for c in self.children))).strip()
    def html(self):
        if not self.tag:return ''.join(c.html() if isinstance(c,Element) else c for c in self.children)
        tail='' if self.tag in {'br','img','input','hr','meta','link','source','wbr'} else '</'+self.tag+'>'
        return self.start+''.join(c.html() if isinstance(c,Element) else c for c in self.children)+tail
    def classes(self):return self.attrs.get('class','').split()
    def add_class(self,value):
        self.start=re.sub(r'class="([^"]*)"',lambda m:'class="'+m[1]+' '+value+'"',self.start,count=1)
        self.attrs['class']=self.attrs.get('class','')+' '+value
class Parser(HTMLParser):
    def __init__(self,source):
        super().__init__(convert_charrefs=False);self.root=Element();self.stack=[self.root];self.feed(source)
    def handle_starttag(self,tag,attrs):
        e=Element(tag,attrs,self.get_starttag_text(),self.stack[-1]);self.stack[-1].children.append(e)
        if tag not in {'br','img','input','hr','meta','link','source','wbr'}:self.stack.append(e)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self,text):self.stack[-1].children.append(text)
    def handle_entityref(self,name):self.handle_data('&'+name+';')
    def handle_charref(self,name):self.handle_data('&#'+name+';')
    def handle_comment(self,text):self.handle_data('<!--'+text+'-->')
def load():
    rows=json.loads(SOURCE.read_text()) if SOURCE.exists() else []
    found={}
    for row in rows:
        allowed={'path','figure','source_sha256','title','roles','role','kind','sources','edges','groups','reading','keep_nodes'}
        if set(row)-allowed:raise ValueError('Static models carry content only: '+str(set(row)-allowed))
        if not row.get('title') or not row.get('sources') or any(not u.startswith('https://') for u in row['sources']):
            raise ValueError('Static figure needs a title and source links')
        if any(set(group)!={'label','nodes'} for group in row.get('groups',[])):
            raise ValueError('Static boundaries declare a label and members only')
        key=(row['path'],row['figure'])
        if key in found:raise ValueError('Duplicate static figure model: '+str(key))
        found[key]=row
    return found

def content(source):
    tree=Parser(source).root
    nodes=[e for e in tree.walk() if 'node' in e.classes()]
    return tree,nodes

def figure_key(row):
    return hashlib.sha256(('static:'+row['path']+':'+str(row['figure'])+':'+row['source_sha256']).encode()).hexdigest()[:16]

def describe(el):
    title=next((e for e in el.walk() if e.tag=='strong'),None)
    def own(e):
        if e is title:return ''
        bits=[]
        for child in e.children:
            if isinstance(child,Element):
                if 'node' in child.classes():continue
                bits.append(own(child))
                if child.tag in {'div','p','small','pre'}:bits.append(' ')
            else:bits.append(child)
        return ''.join(bits)
    detail=re.sub(r'\s+',' ',unescape(own(el))).strip()
    return (title.text(),detail) if title else (detail,'')

def as_map(row,source):
    tree,elements=content(source);nodes=[]
    descriptions={i:describe(el) for i,el in enumerate(elements,1)}
    active=set(row.get('keep_nodes',range(1,len(elements)+1)))
    if not active <= set(descriptions):raise ValueError('Unknown retained card')
    labelled={label['card'] for a,b,label in row['edges'] if isinstance(label,dict)}
    if any(set(label)!={'card'} for a,b,label in row['edges'] if isinstance(label,dict)):
        raise ValueError('An edge annotation names exactly one source card')
    if active|labelled!=set(descriptions):raise ValueError('Every source card must remain a card or an explicit edge annotation')
    for i,(el,role) in enumerate(zip(elements,row['roles']),1):
        if i not in row.get('keep_nodes',range(1,len(elements)+1)):continue
        title,detail=descriptions[i]
        n={'id':str(i),'role':role,'title':title,'detail':detail}
        if 'is-key' in el.classes():n['key']=True
        if el.attrs.get('data-state'):n['state']=el.attrs['data-state']
        nodes.append(n)
    key=figure_key(row)
    result={'path':row['path'],'diagram':key,'kind':'map','number':row['figure'],
            'figure_label':'Visual '+str(row['figure']),'title':row['title'],
            'caption':next(e.text() for e in tree.walk() if e.tag=='figcaption'),
            'nodes':nodes,'edges':[{'from':str(a),'to':str(b),'label':' — '.join(filter(None,descriptions[label['card']])) if isinstance(label,dict) else label} for a,b,label in row['edges']],
            'sources':row['sources'],'node_descriptions':True}
    if row.get('groups'):result['groups']=[{'id':'group'+str(i),'label':g['label'],'nodes':[str(n) for n in g['nodes']]} for i,g in enumerate(row['groups'],1)]
    if row.get('reading'):result['reading']=row['reading']
    return result

def validate(row,source):
    label=f"{row['path']}: static figure {row['figure']}"
    if hashlib.sha256(source.encode()).hexdigest()!=row['source_sha256']:
        raise ValueError(label+' changed; review its presentation model')
    tree,nodes=content(source)
    if len(nodes)!=len(row['roles']) or any(r not in ROLES for r in row['roles']):
        raise ValueError(label+' needs one valid role per node')
    if row['kind'] not in {'map','comparison','timeline'}:raise ValueError(label+': unknown kind')
    if row['kind']!='map' and any(set(e.classes())&{'arrow','down'} for e in tree.walk()):
        raise ValueError(label+': relationships need explicit endpoints and labelled arrows')
    if row['kind']!='map' and not nodes and row.get('role') not in ROLES:
        raise ValueError(label+': chart needs a declared role')
    return tree,nodes


def source_for(row):
    # The build owns legacy/scoped blend resolution, including category subfolders.
    from build import blend_file
    source=blend_file(row['path']+'.md')
    figures=list(FIGURE.finditer(source.read_text()))
    if not 0 < row['figure'] <= len(figures):
        raise ValueError(f"{row['path']}: missing source figure {row['figure']}")
    return figures[row['figure']-1][0]


def source_notes(row):
    links=''.join('<li><a href="'+escape(url,quote=True)+'" target="_blank" rel="noreferrer">'+escape(url.split('/')[2]+': '+url.rstrip('/').split('/')[-1])+'</a></li>' for url in row['sources'])
    return '<details class="fm-sources"><summary>Figure sources</summary><ul>'+links+'</ul></details>'


def render(path,text):
    rows=load();path=path.removesuffix('.md');number=0
    def replace(match):
        nonlocal number
        number+=1;source=match[0];row=rows.get((path,number))
        if row is None:
            if os.environ.get('WEBSITE_PENDING_FIGURES')=='1':return source
            raise ValueError(f'{path}: missing static figure model {number}')
        SEEN.add((path,number))
        tree,nodes=validate(row,source)
        if row['kind']=='map':
            model=as_map(row,source);fm.check(model)
            return fm.render(model,'','teaching')[0]
        root=next(e for e in tree.walk() if e.tag=='figure');root.add_class('pb-static')
        root.start=root.start[:-1]+' data-static-figure="'+figure_key(row)+'" data-static-kind="'+row['kind']+'">'
        for el,role in zip(nodes,row['roles']):el.add_class('actor-'+role)
        for el in nodes:
            if el.attrs.get('data-state') in {'error','warn'}:
                el.children.insert(0,'<span class="static-status">Warning</span>')
        if not nodes:
            if row.get('role') not in ROLES:raise ValueError('Static chart needs a declared role')
            root.add_class('actor-'+row['role'])
        used=list(dict.fromkeys(row['roles'] or [row['role']]))
        legend='<div class="fm-legend">'+''.join('<span class="actor-'+r+'">'+ROLES[r]+'</span>' for r in used)+(('<em>'+escape(row['reading'])+'</em>') if row.get('reading') else '')+'</div>'
        caption=next(e for e in root.walk() if e.tag=='figcaption')
        caption.children.insert(0,'<strong>Visual '+str(number)+'.</strong> ')
        caption_at=root.children.index(caption)
        root.children.insert(caption_at,legend)
        root.children.insert(0,'<p class="fm-heading">'+escape(row['title'])+'</p>')
        root.children.append(source_notes(row))
        return tree.html()
    return FIGURE.sub(replace,text)

def begin():SEEN.clear()

def check_coverage():
    unused=set(load())-SEEN
    if unused:raise ValueError('Unused static figure models: '+str(sorted(unused)))
    print(f'Static teaching figures: {len(SEEN)} hash-bound presentation models checked.')
