"""Utilities for applying reviewed completion patches to both existing checkouts.

Authoring utility, not part of the website runtime. Each patch must match once;
source citations and the named backlog entries remain mandatory review evidence.
"""
from pathlib import Path
import hashlib,json,re,sys
import build
class CompletionPatches:
 def __init__(self,source_root):
  self.root=build.ROOT;self.source=Path(source_root);self.file=self.root/'website/content/corrections-z-completion.json';self.rows=json.loads(self.file.read_text());self.ledger_path=self.root/'website/reviews/completion/backlog.json';self.ledger=json.loads(self.ledger_path.read_text());self.touched={}
 def text(self,path):
  return self.touched.get(path,build.corrected((self.root/path).read_text(),path)[0])
 def add(self,path,old,new,reason,sources,findings):
  text=self.text(path)
  assert text.count(old)==1,(path,old[:130],text.count(old))
  assert old!=new
  target=self.source/path;original=target.read_text();assert original.count(old)==1,('source mismatch',path,old[:130])
  target.write_text(original.replace(old,new,1));after=text.replace(old,new,1);self.touched[path]=after
  row={'id':'completion:'+str(len(self.rows)+1),'path':path,'old':old,'new':new,'reason':reason,'sources':sources if isinstance(sources,list) else [sources],'status':'approved','findings':findings,'approval':'Owner requested full backlog closure and final review after completion, 2026-10-27.','validation':'Completion gate pending; do not publish a partial completion.'};self.rows.append(row)
  blend=self.root/'website/content/blend'/('android/' if path.startswith('android/') else '')/(Path(path).stem+'.blend')
  if blend.exists():
   s=blend.read_text();a=re.findall(r'```mermaid\n(.*?)```',text,re.S);b=re.findall(r'```mermaid\n(.*?)```',after,re.S)
   if len(a)==len(b):
    for x,y in zip(a,b):
     if x!=y:s=s.replace('@diagram '+hashlib.sha256(x.encode()).hexdigest()[:16],'@diagram '+hashlib.sha256(y.encode()).hexdigest()[:16])
   aa=re.findall(r'^## (.+)$',old,re.M);bb=re.findall(r'^## (.+)$',new,re.M)
   if len(aa)==len(bb):
    for x,y in zip(aa,bb):
     s=s.replace('@before '+build.clean(x)+' ::','@before '+build.clean(y)+' ::').replace('@after '+build.clean(x)+' ::','@after '+build.clean(y)+' ::')
   blend.write_text(s)
  for e in self.ledger['entries']:
   if e['id'] in findings:
    e['status']='implemented-pending-validation';e.setdefault('patches',[]).append(row['id']);e['primary_sources']=sorted(set(e.get('primary_sources',[])+row['sources']))
  return row
 def line(self,path,needle,new,reason,sources,findings):
  lines=[l for l in self.text(path).splitlines() if needle in l];assert len(lines)==1,(path,needle,len(lines));return self.add(path,lines[0],new,reason,sources,findings)
 def close_existing(self,ids,reason,sources):
  for e in self.ledger['entries']:
   if e['id'] in ids:e.update(status='already-applied',disposition=reason,primary_sources=sources)
 def save(self):
  self.file.write_text(json.dumps(self.rows,ensure_ascii=False,indent=2)+'\n');self.ledger_path.write_text(json.dumps(self.ledger,ensure_ascii=False,indent=2)+'\n')
