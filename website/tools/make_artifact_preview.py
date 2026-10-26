"""Copy website/dist into a preview folder whose links are all relative, for a multi-file artifact.

Artifact files are served from relative paths, and directory URLs do not resolve to index.html,
so every root-absolute href/src becomes ../-relative and every directory link names index.html.
"""
import pathlib, re, shutil, sys

src = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2])
if out.exists(): shutil.rmtree(out)
shutil.copytree(src, out, ignore=shutil.ignore_patterns('*.mmd', 'diagram-sources'))

def fix_url(u, prefix):
    path, _, rest = u.partition('?')
    path, hashsep, frag = path.partition('#')
    if path == '' or path.endswith('/'): path += 'index.html'
    return prefix + path.lstrip('/') + (hashsep + frag if hashsep else '') + ('?' + rest if rest else '')

for page in out.rglob('*.html'):
    depth = len(page.relative_to(out).parts) - 1
    prefix = '../' * depth
    s = page.read_text()
    s = re.sub(r'(\b(?:href|src)=")(/(?!/)[^"]*)"', lambda m: m.group(1) + fix_url(m.group(2), prefix) + '"', s)
    s = re.sub(r'data-base="/"', f'data-base="{prefix or "./"}"', s)
    page.write_text(s)

for css in out.glob('*.css'):
    s = css.read_text()
    css.write_text(re.sub(r'url\((["\']?)/(?!/)', r'url(\1', s))

app = out / 'app.js'; s = app.read_text()
s = s.replace(".replace(/\\.md$/,'/')", ".replace(/\\.md$/,'/index.html')").replace("topic.slug+'/'", "topic.slug+'/index.html'")
app.write_text(s)

left = [str(p.relative_to(out)) for p in out.rglob('*.html') if re.search(r'(?:href|src)="/(?!/)', p.read_text())]
print(sum(1 for p in out.rglob('*') if p.is_file()), 'files;', len(left), 'pages with root links left')
