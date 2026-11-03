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
        key=(row['path'],row['figure'])
        if key in found:raise ValueError('Duplicate static figure model: '+str(key))
        found[key]=row
    return found

def content(source):
    tree=Parser(source).root
    nodes=[e for e in tree.walk() if 'node' in e.classes()]
    return tree,nodes

def as_map(row,source):
    tree,elements=content(source);nodes=[]
    for i,(el,role) in enumerate(zip(elements,row['roles']),1):
        title=next((e for e in el.walk() if e.tag=='strong'),None)
        details=[e.text() for e in el.children if isinstance(e,Element) and e is not title]
        n={'id':str(i),'role':role,'title':title.text() if title else el.text(),'detail':' '.join(details)}
        if 'is-key' in el.classes():n['key']=True
        if el.attrs.get('data-state'):n['state']=el.attrs['data-state']
        nodes.append(n)
    key=hashlib.sha256(('static:'+row['path']+':'+str(row['figure'])+':'+row['source_sha256']).encode()).hexdigest()[:16]
    result={'path':row['path'],'diagram':key,'kind':'map','number':row['figure'],
            'figure_label':'Visual '+str(row['figure']),'title':row['title'],
            'caption':next(e.text() for e in tree.walk() if e.tag=='figcaption'),
            'nodes':nodes,'edges':[{'from':str(a),'to':str(b),'label':label} for a,b,label in row['edges']],
            'sources':row['sources'],'node_descriptions':True}
    if row.get('groups'):result['groups']=[{'id':'group'+str(i),'label':g['label'],'nodes':[str(n) for n in g['nodes']]} for i,g in enumerate(row['groups'],1)]
    return result

def render(path,text):
    rows=load();path=path.removesuffix('.md');number=0
    def replace(match):
        nonlocal number
        number+=1;source=match[0];row=rows.get((path,number))
        if row is None:
            if os.environ.get('WEBSITE_PENDING_FIGURES')=='1':return source
            raise ValueError(f'{path}: missing static figure model {number}')
        if hashlib.sha256(source.encode()).hexdigest()!=row['source_sha256']:
            raise ValueError(f'{path}: static figure {number} changed; review its presentation model')
        tree,nodes=content(source)
        if len(nodes)!=len(row['roles']) or any(r not in ROLES for r in row['roles']):
            raise ValueError(f'{path}: static figure {number} needs one valid role per node')
        if row['kind']=='map':
            model=as_map(row,source);fm.check(model)
            return fm.render(model,'','teaching')[0]
        if row['kind'] not in {'comparison','timeline'}:raise ValueError('Unknown static figure kind')
        root=next(e for e in tree.walk() if e.tag=='figure');root.add_class('pb-static')
        for el,role in zip(nodes,row['roles']):el.add_class('actor-'+role)
        if not nodes:
            if row.get('role') not in ROLES:raise ValueError('Static chart needs a declared role')
            root.add_class('actor-'+row['role'])
        used=list(dict.fromkeys(row['roles'] or [row['role']]))
        legend='<div class="fm-legend">'+''.join('<span class="actor-'+r+'">'+ROLES[r]+'</span>' for r in used)+'</div>'
        caption=next(e for e in root.walk() if e.tag=='figcaption')
        caption.children.insert(0,'<strong>Visual '+str(number)+'.</strong> ')
        caption_at=root.children.index(caption)
        root.children.insert(caption_at,legend)
        root.children.insert(0,'<p class="fm-heading">'+escape(row['title'])+'</p>')
        return tree.html()
    return FIGURE.sub(replace,text)
