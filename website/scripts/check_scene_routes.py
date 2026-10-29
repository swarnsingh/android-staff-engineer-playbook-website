"""Sample authored SVG paths to catch transfers routed through actors."""
import re,json
from pathlib import Path
def check():
 issues=[];scenes=0
 for p in (Path(__file__).resolve().parents[1]/'content/blend').rglob('*.blend'):
  for m in re.finditer(r'<section class="pb-figure" data-pb-flow="scene".*?<script type="application/json">(.*?)</script>',p.read_text(),re.S):
   scenes+=1;data=json.loads(m[1])
   for name,L in data['layouts'].items():
    for edge,path in L['edges'].items():
     pieces=re.findall(r'([MLCQHV])([^MLCQHV]+)',path);start=(0,0)
     for cmd,numbers in pieces:
      v=[float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',numbers)];x0,y0=start
      if cmd=='M':start=tuple(v);continue
      end=tuple(v[-2:]) if cmd not in 'HV' else ((v[0],y0) if cmd=='H' else (x0,v[0]))
      for i in range(1,40):
       t=i/40;u=1-t
       if cmd=='C':x=u**3*x0+3*u*u*t*v[0]+3*u*t*t*v[2]+t**3*v[4];y=u**3*y0+3*u*u*t*v[1]+3*u*t*t*v[3]+t**3*v[5]
       elif cmd=='Q':x=u*u*x0+2*u*t*v[0]+t*t*v[2];y=u*u*y0+2*u*t*v[1]+t*t*v[3]
       else:x=x0+(end[0]-x0)*t;y=y0+(end[1]-y0)*t
       for id,r in L['nodes'].items():
        if r['x']+3<x<r['x']+r['w']-3 and r['y']+3<y<r['y']+r['h']-3:issues.append((p.stem,name,edge,id))
      start=end
 print(f"Scene routes: all {scenes} wide/narrow layouts avoid actor interiors.") if not issues else print(sorted(set(issues)))
 assert scenes and not issues

if __name__=="__main__":check()
