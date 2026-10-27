#!/usr/bin/env python3
"""Prevent publication of an incomplete or unvalidated retained review backlog."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,argparse
import build
ROOT=build.ROOT;REVIEW=ROOT/'website/reviews/completion'
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def fingerprints():
 files=['website/content/corrections-z-completion.json','website/reviews/completion/source-sync.json','website/scripts/build.py','website/scripts/check_completion.py','website/scripts/generate_android_validation.py','website/theme.css','website/app.js','website/blend.js','website/design-system/components/bundle.js']
 files += [str(f.relative_to(ROOT)) for f in (ROOT/'website/content/blend').rglob('*.blend')]
 result={f:digest((ROOT/f).read_text()) for f in sorted(files)}
 for tree in ['kotlin','android']:
  for file in sorted([ROOT/(tree+'.md'),*(ROOT/tree).rglob('*.md')]):
   path=str(file.relative_to(ROOT));result['corrected:'+path]=digest(build.corrected(file.read_text(),path)[0])
 return result
def check(source_root=None):
 ledger=json.loads((REVIEW/'backlog.json').read_text());entries=ledger['entries'];ids=[e['id'] for e in entries]
 assert len(ids)==len(set(ids)) and len(ids)==515,'Retained review inventory changed: reconcile scope explicitly'
 assert sum(i.startswith('kotlin:') for i in ids)==295
 assert sum(i.startswith('android:') for i in ids)==206
 allowed={'verified-fix','verified-no-change','already-applied'}
 for entry in entries:
  assert entry['status'] in allowed,(entry['id'],entry['status'])
  assert entry.get('primary_sources'),('missing primary evidence',entry['id'])
 rows=json.loads((ROOT/'website/content/corrections-z-completion.json').read_text())
 assert len(rows)==743 and len({r['id'] for r in rows})==743
 assert len(build.APPROVED_CORRECTIONS)==743, 'Canonical inventory must be applied exactly once'
 assert all(r['status']=='approved' and r.get('sources') and 'pending' not in r.get('validation','').lower() for r in rows)
 for file in (ROOT/'website/content/blend').rglob('*.blend'):
  assert not re.search(r'<!--\s*@[^>]*:: review\s*-->',file.read_text()),('resolved review notice remains',file)
 proof=json.loads((REVIEW/'validation.json').read_text())
 assert proof['fingerprints']==fingerprints(),'Build/lesson inputs changed after the recorded audit'
 for name in ['browser','binder','motion','refinement']:
  r=json.loads((REVIEW/(name+'.json')).read_text());assert r['done'],name+' incomplete'
  if name=='browser':
   assert len(r['pages'])==125 and all(p['ok'] for p in r['pages'])
  elif name=='binder':assert len(r['checks'])==448 and not r['problems']
  elif name=='motion':assert len(r['results'])==13 and all(c['ok'] for c in r['results'])
  else:assert len(r['checks'])==69 and all(c['ok'] for c in r['checks'])
 assert proof['android_runtime_tests']==22 and proof['android_failures']==0 and proof['instrumentation_compilation']=='passed'
 assert proof['gradle_plugin_probe']=='passed'
 focused=json.loads((REVIEW/'merged-sync-browser.json').read_text())
 assert focused['done'] and all(p['ok'] for p in focused['pages'])
 deltas=json.loads((REVIEW/'render-deltas.json').read_text())['files']
 assert {p['href'].strip('/')+'/index.html' for p in focused['pages']}==set(deltas)
 if source_root:
  for path in {r['path'] for r in build.APPROVED_CORRECTIONS}:
   actual=(Path(source_root)/path).read_text().split('\n### Official verification references\n',1)[0].rstrip()
   expected=build.corrected((ROOT/path).read_text(),path)[0].rstrip()
   assert actual==expected,('source/website divergence',path)
 print(f'Completion: {len(entries)} review entries closed; {len(rows)} canonical exact replacements; '+str(dict(Counter(e['status'] for e in entries)))+'.')
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root');args=parser.parse_args();check(args.source_root)
