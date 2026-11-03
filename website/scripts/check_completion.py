#!/usr/bin/env python3
"""Prevent publication of an incomplete or unvalidated retained review backlog."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,argparse
import build
ROOT=build.ROOT;REVIEW=ROOT/'website/reviews/completion'
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def fingerprints():
 files=['website/scripts/check_fundamentals_kotlin.py','website/tests/FundamentalsRegression.kt','website/content/engineering-fundamentals.json','website/content/corrections-engineering-fundamentals.json','website/content/corrections-computer-science.json','source-snapshot.json','website/content/observability.json','website/content/corrections-zz-observability-source-sync.json','website/scripts/check_scene_routes.py','website/scripts/scene_data.py','website/content/distributed-systems.json','website/content/release-engineering.json','website/content/security.json','website/content/backend-for-mobile.json','website/content/corrections-z-completion.json','website/reviews/completion/source-sync.json',
  'website/scripts/build.py','website/scripts/diagram_models.py','website/scripts/figure_maps.py','website/sequence.css','website/scripts/check_completion.py','website/scripts/check_preservation.py',
  'website/scripts/generate_android_validation.py','website/scripts/browser_preservation.js',
  'website/tools/qa_fixture_runner.js','website/styles.css','website/blend.css',
  'website/theme.css','website/learning-path.css','website/navigation.css','website/app.js','website/blend.js',
  'website/templates/reader.html','website/templates/home.html','website/design-system/tokens.json',
  'website/design-system/gallery.html','website/design-system/components/bundle.css',
  'website/design-system/components/bundle.js','website/tools/browser_audit_runner.js',
  'website/tools/ux_audit_runner.js','website/tools/prepare_browser_audit.py']
 files += ['website/content/code-pairs.json','website/content/code-kotlin-only.json','website/scripts/check_cs_code.py']
 files += [str(f.relative_to(ROOT)) for f in (ROOT/'website/content/blend').rglob('*.blend')]
 files += [str(f.relative_to(ROOT)) for f in (ROOT/'website/content/diagram-models').glob('*.json')]
 files += [str(f.relative_to(ROOT)) for f in (ROOT/'website/content/diagram-models/figures').glob('*.json')]
 files += [str(f.relative_to(ROOT)) for f in (ROOT/'website/content/components').glob('*.html')]
 result={f:digest((ROOT/f).read_text()) for f in sorted(files)}
 for tree in build.TREES:
  for file in sorted([ROOT/(tree+'.md'),*(ROOT/tree).rglob('*.md')]):
   path=str(file.relative_to(ROOT));result['corrected:'+path]=digest(build.corrected(file.read_text(),path)[0])
 return result
def audit_tree(href):
 # Classify by the top-level route, not any nested directory with the same name.
 prefix=build.BASE if href.startswith(build.BASE) else '/'
 return href.removeprefix(prefix).strip('/').split('/')[0]

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
 core=[r for r in build.APPROVED_CORRECTIONS if r['path'].split('/')[0] in {'kotlin','android'}]
 canonical_ids={r['id'] for r in rows}
 assert len([r for r in core if r['id'] in canonical_ids])==743, 'Canonical inventory must be applied exactly once'
 sync=json.loads((ROOT/'website/content/corrections-zz-observability-source-sync.json').read_text())
 expected_paths={'android/networking-and-security/retrofit-and-okhttp.md','android/performance/anrs.md','android/performance/memory-management-and-leaks.md'}
 assert len(sync)==3 and {r['path'] for r in sync}==expected_paths, 'Merged PR #72 sync scope changed'
 auth_sync=json.loads((ROOT/'website/content/corrections-zz-auth-source-sync.json').read_text())
 assert len(auth_sync)==1 and {r['path'] for r in auth_sync}=={'android/networking-and-security/ktor-vs-retrofit.md'}, 'Merged PR #74 sync scope changed'
 assert len(core)==747 and len({r['id'] for r in core})==747, 'Unexpected or duplicate Kotlin/Android corrections'
 assert {r['id'] for r in core}==canonical_ids|{r['id'] for r in sync}|{r['id'] for r in auth_sync}
 for fix in sync:
  assert fix['status']=='approved' and fix['source_pr']==72 and fix.get('approval') and fix.get('sources')
  assert fix['source_commit']=='7666569cf77db7616d43f05cf041c438cb947035'
  assert digest(fix['new'])==fix['source_sha256']
  assert digest(build.corrected((ROOT/fix['path']).read_text(),fix['path'])[0])==fix['source_sha256'], ('Merged-source replay mismatch',fix['path'])
 for fix in auth_sync:
  assert fix['status']=='approved' and fix['source_pr']==74 and fix.get('approval') and fix.get('sources')
  assert fix['source_commit']=='8e152a8ead842de3c7f20ac6f88118d5b3e70fc6'
  assert digest(fix['new'])==fix['source_sha256']
  assert digest(build.corrected((ROOT/fix['path']).read_text(),fix['path'])[0])==fix['source_sha256'], ('Merged-source replay mismatch',fix['path'])
 fundamentals=[r for r in build.APPROVED_CORRECTIONS if r['path'].startswith('engineering-fundamentals/')]
 assert fundamentals and len({r['id'] for r in fundamentals})==len(fundamentals)
 assert all(r.get('sources') and r.get('validation') for r in fundamentals)
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
 # Content-completion evidence remains the baseline. Shared-reader changes also
 # require their own current browser evidence rather than reusing that old run.
 # The latest shared-reader review names its own evidence folder; it must cover the current inputs.
 assert proof.get('ux_review') and (ROOT/proof['ux_review']).exists(),'Missing reader UX verification'
 ux=(ROOT/proof['ux_review']).parent
 # Binder matrix: 4 themes x every reading font x 2 sizes x 7 widths x 2 views.
 binder_checks=4*len(json.loads((ROOT/'website/design-system/tokens.json').read_text())['type']['prose']['options'])*2*7*2
 browser=json.loads((ux/'browser.json').read_text())
 assert browser['done'] and {p['href'].removeprefix(build.BASE if p['href'].startswith(build.BASE) else '/').strip('/') for p in browser['pages']}=={p.removesuffix('.md') for p in build.PAGES} and all(p['ok'] for p in browser['pages'])
 code_checks=[c for p in browser['pages'] for c in p.get('codeChecks',[])]
 assert code_checks and all(c['ok'] for c in code_checks),'Code readability or contrast regression'
 pairs=[c for p in browser['pages'] for v in p['preservation']['views'] for c in v.get('pairChecks',[])]
 core_pairs=[c for p in browser['pages'] if audit_tree(p['href']) in {'kotlin','android'} for v in p['preservation']['views'] for c in v.get('pairChecks',[])]
 fundamentals_pairs=[c for p in browser['pages'] if audit_tree(p['href'])=='engineering-fundamentals' for v in p['preservation']['views'] for c in v.get('pairChecks',[])]
 delivery_pairs=[c for p in browser['pages'] if audit_tree(p['href'])=='distributed-systems' for v in p['preservation']['views'] for c in v.get('pairChecks',[])]
 # The exact chapter inventory fixes the full tree's original question/answer count.
 assert len(delivery_pairs)==92 and all(c['ok'] for c in delivery_pairs),'Distributed Systems original Q&A pairing failed'
 topic_pairs=[c for p in browser['pages'] if audit_tree(p['href'])=='backend-for-mobile' for v in p['preservation']['views'] for c in v.get('pairChecks',[])]
 assert len(topic_pairs)==72 and all(c['ok'] for c in topic_pairs), 'Backend for Mobile original Q&A pairing failed'
 topic_pairs=[c for p in browser['pages'] if audit_tree(p['href'])=='security' for v in p['preservation']['views'] for c in v.get('pairChecks',[])]
 assert len(topic_pairs)==8 and all(c['ok'] for c in topic_pairs), 'Security original Q&A pairing failed'
 topic_pairs=[c for p in browser['pages'] if audit_tree(p['href'])=='release-engineering' for v in p['preservation']['views'] for c in v.get('pairChecks',[])]
 assert len(topic_pairs)==10 and all(c['ok'] for c in topic_pairs), 'Release Engineering original Q&A pairing failed'
 # Kotlin/Android and Fundamentals counts are fixed; newer trees add pairs that must all pass.
 assert len(core_pairs)==928 and len(fundamentals_pairs)==130 and all(c['ok'] for c in pairs),'Question/answer pairing failed'
 kotlin=json.loads((ux/'kotlin-validation.json').read_text())
 assert kotlin['status']=='passed' and kotlin['checks']['assertions']==27
 assert kotlin['fixture_sha256']==digest((ROOT/'website/tests/FundamentalsRegression.kt').read_text())
 assert len(kotlin['fragments'])==5
 for needle,expected_hash in kotlin['fragments'].items():
  fragments=[block for path in build.ORDER['engineering-fundamentals'] for block in re.findall(r'```kotlin\n(.*?)\n```',build.corrected((ROOT/path).read_text(),path)[0],re.S) if needle in block]
  assert len(fragments)==1 and digest(fragments[0])==expected_hash,('compiled fragment changed',needle)
 fixtures=json.loads((ux/'qa-tampering.json').read_text())
 assert fixtures['done'] and fixtures['ok'] and len(fixtures['checks'])==31 and all(c['ok'] for c in fixtures['checks']),'QA preservation negative fixtures failed'
 assert len({c['id'] for c in code_checks if c['inList']})>=45,'Nested-list code examples not checked'
 for name in ['binder','motion','refinement','ux']:
  result=json.loads((ux/(name+'.json')).read_text());assert result['done'],name+' UX audit incomplete'
  if name=='binder':assert len(result['checks'])==binder_checks and not result['problems']
  elif name=='motion':assert len(result['results'])==13 and all(c['ok'] for c in result['results'])
  else:assert result['ok'] and len(result['checks'])>=(222 if name=='ux' else 69) and all(c['ok'] for c in result['checks'])
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
