"""Build the standalone review page; never includes local books or transcripts."""
from pathlib import Path
import re, json, subprocess
from html import escape
B=Path(__file__).resolve().parent
html=(B/'index.html').read_text()
scene=json.loads(subprocess.check_output(['node','-e',"process.stdout.write(JSON.stringify(require('./lesson-model.js').scenes.success))"],cwd=B,text=True))
rows=''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in [f"{i+1}. {step['time']}",step['name'],step['avatar'],step['parent'],step['caption']])+'</tr>' for i,step in enumerate(scene['steps']))
html=re.sub(r'(<tbody id="step-table">).*?(</tbody>)',lambda m:m[1]+rows+m[2],html,flags=re.S)
html=re.sub(r'(<caption id="step-table-caption">).*?(</caption>)',lambda m:m[1]+escape(scene['description'])+m[2],html,flags=re.S)
html=re.sub(r'(<p id="model-caption" aria-live="polite">).*?(</p>)',lambda m:m[1]+escape(scene['steps'][0]['caption'])+m[2],html,flags=re.S)
html=re.sub(r'(<code id="model-code">).*?(</code>)',lambda m:m[1]+escape('\n'.join(scene['code']))+m[2],html,flags=re.S)
(B/'index.html').write_text(html)
html=html.replace('<link rel="stylesheet" href="styles.css">','<style>\n'+(B/'styles.css').read_text()+'\n</style>')
scripts=[]
for name in ['nav-data.js','lesson-model.js','app.js']:
    html=html.replace(f'<script defer src="{name}"></script>','')
    scripts.append('<script>\n'+(B/name).read_text().replace('</script','<\\/script')+'\n</script>')
html=html.replace('</body>','\n'+ '\n'.join(scripts)+'\n</body>')
(B/'reader-draft.html').write_text(html)
assert not re.search(r'<script[^>]*src="(?:app|nav-data|lesson-model)\.js"',html)
print('Standalone review page built:',len(html),'characters')
