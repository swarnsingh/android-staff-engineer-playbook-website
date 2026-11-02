"""Resolve shared FlowScene layout tokens; topic content supplies only semantics."""
from pathlib import Path
import copy,json
WEB=Path(__file__).resolve().parents[1]
def resolve(data):
    if 'layout' not in data:
        return data
    result=copy.deepcopy(data)
    presets=json.loads((WEB/'design-system/tokens.json').read_text())['sceneLayouts']
    result['layouts']=copy.deepcopy(presets[result['layout']])
    result['responsive']=True
    edges={e['id']:e for e in result['edges']}
    for layout in result['layouts'].values():
        if set(layout['nodes'])!={n['id'] for n in result['nodes']}:
            raise ValueError('FlowScene preset actors do not match scene')
        for region in layout.get('regions',[]):
            region['label']=result['owners'][region.pop('owner')]
        for label in layout.get('labels',[]):
            label['text']=edges[label.pop('edge')]['label']
    return result
