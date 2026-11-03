"""Resolve shared FlowScene layout tokens; topic content supplies only semantics."""
from pathlib import Path
import copy,json
WEB=Path(__file__).resolve().parents[1]
def resolve(data):
    if 'layout' not in data:
        return data
    result=copy.deepcopy(data)
    tokens=json.loads((WEB/'design-system/tokens.json').read_text())
    presets=tokens['sceneLayouts']
    result['layouts']=copy.deepcopy(presets[result['layout']])
    result['lossMarker']=copy.deepcopy(tokens['sceneMarkers']['loss'])
    result['responsive']=True
    edges={e['id']:e for e in result['edges']}
    for layout in result['layouts'].values():
        if set(layout['nodes'])!={n['id'] for n in result['nodes']}:
            raise ValueError('FlowScene preset actors do not match scene')
        if set(edges)-set(layout['edges']):
            raise ValueError('FlowScene preset routes do not match declared edges')
        layout['edges']={key:value for key,value in layout['edges'].items() if key in edges}
        layout['labels']=[label for label in layout.get('labels',[]) if label['edge'] in edges]
        for region in layout.get('regions',[]):
            region['label']=result['owners'][region.pop('owner')]
        for label in layout.get('labels',[]):
            label['text']=edges[label.pop('edge')]['label']
    return result
