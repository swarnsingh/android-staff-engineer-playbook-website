"""Regenerate the Android rows of the progress table and the Android scope sentences from build.py."""
import sys, re, json, glob
from pathlib import Path
sys.path.insert(0, 'website/scripts')
import build
p = Path('website/README.md'); s = p.read_text()
phases = build.TREES['android']['phases']
rows = ['| `android.md` (learning path) | `android/android.blend` | Blended (phase map) |']
for heading, paths in build.phases('android'):
    n = int(re.match(r'Phase (\d+)', heading)[1])
    if n in phases:
        for path in paths:
            stem = Path(path).stem
            rows.append(f'| {path.removeprefix("android/").removesuffix(".md")} | `android/{stem}.blend` | Blended |')
pending = [int(re.match(r'Phase (\d+)', h)[1]) for h, _ in build.phases('android') if int(re.match(r'Phase (\d+)', h)[1]) not in phases]
if pending:
    rows.append(f'| Android phases {", ".join(map(str, pending))} | — | Not rendered yet; links open GitHub |')
s = re.sub(r'\| `android\.md` \(learning path\).*?(?=\n\nUpdate this table)', '\n'.join(rows), s, flags=re.S)
chapters = len(build.ORDER['android'])
done = ', '.join(map(str, phases))
s = re.sub(r'and the Android pilot \(`android\.md` plus the [^)]*\) render as pages\.|and the Android tree \(`android\.md` plus [^)]*\) render as pages\.',
           f'and the Android tree (`android.md` plus {chapters} chapters, phases {done}) render as pages.', s)
p.write_text(s)
print('android chapters', chapters, 'phases', done, 'pending', pending)
