"""Validate the explicit object choices for every HTML state step-through."""
from pathlib import Path
from html.parser import HTMLParser
import json, re

WEB=Path(__file__).resolve().parents[1]
KINDS=set('phone screen server worker queue database clock parcel memory document cloud flow code player gate lock key inspect graph frame stack signal'.split())
ROLES={'client','runtime','storage','queue'}

class Nodes(HTMLParser):
    def __init__(self):
        super().__init__();self.nodes=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'node' in attrs.get('class','').split():
            self.nodes.append({'id':attrs.get('data-el'),'kind':attrs.get('data-art'),'role':attrs.get('data-art-role')})

def check():
    records=json.loads((WEB/'content/illustrated-stepper-coverage.json').read_text())['figures']
    expected={(row['path'],row['figure']):row['nodes'] for row in records}
    found={}
    for source in (WEB/'content/blend').rglob('*.blend'):
        for i,figure in enumerate(re.findall(r'<figure class="stepper".*?</figure>',source.read_text(),re.S)):
            key=(source.relative_to(WEB/'content/blend').with_suffix('').as_posix(),i)
            if 'data-illustrated' not in figure.split('>',1)[0]:raise ValueError(f'Unillustrated step-through: {key}')
            parser=Nodes();parser.feed(figure)
            for node in parser.nodes:
                if node['kind'] not in KINDS or node['role'] not in ROLES:raise ValueError(f'Invalid actor: {key} {node}')
            found[key]=parser.nodes
    if found!=expected:raise ValueError('Illustrated step-through coverage differs from its explicit actor manifest')
    print(f'Illustration coverage: {len(found)} step-throughs, {sum(len(nodes) for nodes in found.values())} explicit objects verified.')

if __name__=='__main__':check()
