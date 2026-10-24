#!/usr/bin/env python3
"""Render the original Kotlin chapters without shortening their content."""
from pathlib import Path
from html import escape, unescape
from urllib.parse import urlsplit, unquote, quote
import argparse, hashlib, json, os, re, shlex, shutil, subprocess, sys
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'website'
OUT = WEB / 'dist'
CACHE = WEB / '.cache'
SOURCE_ROOT = 'https://github.com/swarnsingh/android-staff-engineer-playbook/blob/main/'
MD = MarkdownIt('commonmark', {'html': True}).enable(['table', 'strikethrough'])
FILES = sorted((ROOT/'kotlin').rglob('*.md'))
PATHS = {p.relative_to(ROOT).as_posix() for p in FILES} | {'kotlin.md'}
# Site prefix, so the same build works at a domain root or under a project path.
BASE = '/' + os.environ.get('SITE_BASE', '/').strip('/') + '/' if os.environ.get('SITE_BASE', '/').strip('/') else '/'
MERMAID_RENDERER = os.environ.get('MERMAID_RENDERER', 'npx --yes @mermaid-js/mermaid-cli@11.16.0')
# Original chapters are never edited. Corrections are a website-only overlay and are
# applied only after the owner approves them (status "approved").
ALL_CORRECTIONS = []
for path in sorted((WEB/'content').glob('corrections-*.json')):
    ALL_CORRECTIONS.extend(json.loads(path.read_text()))
APPROVED_CORRECTIONS = [fix for fix in ALL_CORRECTIONS if fix.get('status') == 'approved']


def route(path):
    return BASE + 'kotlin/' if path == 'kotlin.md' else BASE + path.removesuffix('.md') + '/'


def slug(text):
    text = re.sub(r'<[^>]+>', '', text.strip().lower())
    text = re.sub(r'[`*_~]', '', text)
    text = ''.join(c for c in text if c.isalnum() or c in ' -_')
    return re.sub(r'\s', '-', text)


def clean(text):
    # Keep code spans verbatim (they may contain generics such as `List<Dog>`); strip markup elsewhere.
    parts = re.split(r'(`[^`]*`)', text)
    return ''.join(p[1:-1] if p.startswith('`') and p.endswith('`') and len(p) > 1 else re.sub(r'<[^>]*>|[*_~]', '', p) for p in parts).strip()


def title(path):
    return clean(re.search(r'^# (.+)', path.read_text(), re.M).group(1))


def corrected(source, path):
    applied = []
    for fix in APPROVED_CORRECTIONS:
        if fix['path'] != path: continue
        if source.count(fix['old']) != 1:
            raise ValueError(f"Correction no longer matches exactly once: {path}: {fix['reason']}")
        source = source.replace(fix['old'], fix['new'], 1)
        applied.append(fix)
    return source, applied


def link_rules(path):
    def link_open(tokens, idx, options, env):
        token = tokens[idx]
        href = token.attrGet('href') or ''
        if href.startswith(('https:', 'http:')):
            token.attrSet('target','_blank'); token.attrSet('rel','noreferrer')
        elif not href.startswith(('#', 'mailto:')):
            parts = urlsplit(href)
            target = (ROOT/path).parent.joinpath(unquote(parts.path)).resolve()
            if target.is_relative_to(ROOT):
                relative = target.relative_to(ROOT).as_posix()
                suffix = ('#'+parts.fragment) if parts.fragment else ''
                if relative in PATHS:
                    token.attrSet('href', route(relative)+suffix)
                else:
                    token.attrSet('href', SOURCE_ROOT+quote(relative)+suffix)
                    token.attrSet('target','_blank'); token.attrSet('rel','noreferrer')
        return MD.renderer.renderToken(tokens, idx, options, env)
    MD.renderer.rules['link_open'] = link_open


# The story every chapter moves through. Sections are mapped to a part by their heading;
# a blend file can override the mapping with `<!-- @part Heading :: KEY -->`.
PARTS = [
    ('BEGINNING', 'The problem and the idea', 'Why this exists, and the picture to keep in mind.'),
    ('MECHANISM', 'How it really works', 'What the compiler and runtime actually do.'),
    ('PRODUCTION', 'In real apps', 'Patterns, trade-offs and the ways it fails.'),
    ('STAFF', 'Staff-level judgement', 'Decisions, reviews and the misconceptions to correct.'),
    ('PRACTICE', 'Practise', 'Questions with worked answers.'),
    ('DEEPER', 'Go deeper', 'Sources and next steps.'),
]
PART_KEYS = [key for key, _, _ in PARTS]
PART_WORDS = [
    ('DEEPER', ['further reading', 'references']),
    ('PRACTICE', ['probing question', 'answer key', 'review checklist', 'review question', 'interview']),
    ('STAFF', ['staff', 'misconception']),
    ('PRODUCTION', ['production', 'android example', 'android pattern', 'real android', 'tradeoff', 'trade-off',
                    'failure mode', 'performance', 'reliability', 'security', 'observability', 'pitfall',
                    'android failure', 'testing', 'where they earn', 'migration', 'when to reach', 'right choice',
                    'wrong choice', 'sdk and public', 'lifecycle collection', 'common failure']),
    ('BEGINNING', ['overview', 'why it', 'why this', 'historical context', 'first principles', 'mental model',
                   'big idea', 'debugging model']),
]


def classify_part(heading):
    lower = heading.lower()
    for key, words in PART_WORDS:
        if any(word in lower for word in words):
            return PART_KEYS.index(key)
    return PART_KEYS.index('MECHANISM')


BLEND_LABELS = {'story': 'Start here', 'guide': 'In plain words', 'visual': 'See it', 'animation': 'Step through it',
                'check': 'Check yourself', 'deeper': 'Under the hood', 'staff': 'Staff lens', 'try': 'Try it', 'bridge': ''}


def load_blend(path):
    """Read website/content/blend/<chapter>.blend: Markdown fragments placed by markers.

    <!-- @opening -->                      replaces the generic intro with a problem-first story
    <!-- @before Heading :: kind -->       inserted before that H2 section
    <!-- @after Heading :: kind -->        appended inside that H2 section
    <!-- @diagram <hash> -->               designed redraw shown instead of that Mermaid diagram
    <!-- @part Heading :: KEY -->          force the part a section belongs to
    Headings are matched on their visible text (backticks and emphasis removed).
    """
    file = WEB / 'content/blend' / (Path(path).stem + '.blend')
    if not file.exists():
        return {}
    pieces = re.split(r'<!--\s*@(opening|before|after|diagram|part)\b(.*?)-->', file.read_text(), flags=re.S)
    blend = {}
    for i in range(1, len(pieces), 3):
        marker, argument, content = pieces[i], pieces[i + 1].strip(), pieces[i + 2].strip()
        target, _, kind = (part.strip() for part in argument.partition('::'))
        if marker == 'opening':
            key = ('opening', '')
        elif marker == 'diagram':
            key = ('diagram', target)
        elif marker == 'part':
            if kind not in PART_KEYS:
                raise ValueError(f'{file.name}: unknown part {kind!r}')
            blend[('part', target)] = kind
            continue
        else:
            if kind not in BLEND_LABELS:
                raise ValueError(f'{file.name}: unknown kind {kind!r} for {target!r}')
            key = (marker, target, kind)
            if key in blend:  # several inserts of one kind at one place stay in order
                content = blend[key] + '\n\n' + content
        blend[key] = content
    return blend


def steps_as_text(html):
    """Print every animation step as a numbered list, so no step depends on motion or JavaScript."""
    def add(match):
        steps = json.loads(match.group(2))
        items = ''.join(f'<li>{"<strong>"+escape(s["label"])+".</strong> " if s.get("label") else ""}{escape(s.get("caption",""))}</li>' for s in steps)
        return match.group(1) + match.group(2) + match.group(3) + f'<details class="steps-text"><summary>Read every step as text</summary><ol>{items}</ol></details>'
    return re.sub(r'(<script type="application/json" class="steps">)(.*?)(</script>)', add, html, flags=re.S)


def wrap(kind, markdown, env):
    """Render an added fragment and label it, so readers can tell it from the original text."""
    # A blank line would end a raw HTML block early; keep blank lines inside figures as newlines.
    def keep_blank_lines(match):
        text = match.group(0)
        while '\n\n' in text:
            text = text.replace('\n\n', '\n&#10;')
        return text
    markdown = re.sub(r'<figure\b.*?</figure>', keep_blank_lines, markdown, flags=re.S)
    env['blend'] = True
    try:
        html = MD.render(markdown, env)
    finally:
        env['blend'] = False
    label = BLEND_LABELS[kind]
    label_html = f'<span class="blend-label">{label}</span>' if label else ''
    return f'<div class="blend" data-kind="{kind}">{label_html}{steps_as_text(html)}</div>'


def render_chapter(path, raw, is_course=False):
    source, fixes = corrected(raw, path)
    tokens = MD.parse(source)
    counts = {}; sections = []; headings = []; codes = []
    for i, token in enumerate(tokens):
        if token.type == 'heading_open':
            heading = tokens[i+1].content
            base = slug(heading); n = counts.get(base,0); counts[base] = n+1
            anchor = base if not n else f'{base}-{n}'
            token.attrSet('id', anchor)
            if token.tag != 'h1': headings.append({'level':int(token.tag[1]),'text':heading,'id':anchor})
            if token.tag == 'h2': sections.append((i,heading,anchor))
        if token.type == 'fence': codes.append({'language':token.info,'text':token.content})
    link_rules(path)
    blend = load_blend(path)
    used = set()
    diagram_count = [0]
    def fence(tokens, idx, options, env):
        token=tokens[idx]; language=token.info.split()[0] if token.info.strip() else 'text'
        code_id = env['prefix'] + '-code-' + str(env['code_index']); env['code_index'] += 1
        if language == 'mermaid':
            key=hashlib.sha256(token.content.encode()).hexdigest()[:16]
            diagram_count[0]+=1
            (OUT/'diagram-sources'/f'{key}.mmd').write_text(token.content)
            original=f'<img src="{BASE}diagrams/{key}.svg" alt="{escape(env.get("heading","Concept relationships"))}" loading="lazy">'
            source=f'<details><summary>Read diagram source</summary><pre tabindex="0"><code>{escape(token.content)}</code></pre></details>'
            if ('diagram', key) in blend:
                # A designed redraw leads; the chapter's own diagram stays one tap away.
                used.add(('diagram', key))
                return wrap('visual', blend[('diagram', key)], env) + f'<details class="original-diagram"><summary>Original diagram from the chapter</summary>{original}{source}</details>'
            return f'<figure class="source-diagram">{original}<figcaption>Concept relationships from this section.</figcaption>{source}</figure>'
        if env.get('blend'):
            label, note = {'kotlin':'Kotlin','java':'Java','text':'Output'}.get(language,language), 'Added example'
        else:
            label={'kotlin':'Kotlin','java':'Java','groovy':'Gradle / Groovy','kts':'Gradle / Kotlin','text':'Illustrative output'}.get(language,language)
            note='Chapter example · surrounding text defines its assumptions'
        return f'<div class="code-card"><div class="code-header"><span>{escape(label)}<small>{note}</small></span><button class="code-button" data-copy="{code_id}">Copy code</button></div><pre tabindex="0" aria-label="{escape(label)} example"><code id="{code_id}" class="highlight language-{escape(language)}">{escape(token.content)}</code></pre></div>\n'
    MD.renderer.rules['fence']=fence
    env={'prefix':slug(path),'code_index':0}
    initial=tokens[:sections[0][0]] if sections else tokens
    # H1 is represented by the page hero; all other opening content stays intact.
    if initial and initial[0].type=='heading_open' and initial[0].tag=='h1': initial=initial[3:]
    opening=MD.renderer.render(initial,MD.options,env)
    def band(number, index):
        key, title_text, promise = PARTS[index]
        return f'<div class="part-band" data-part-band="{key}"><span class="part-number">PART {number}</span><span class="part-name">{title_text}</span><p class="part-promise">{promise}</p></div>'
    # The opening story always belongs to the first part of the chapter.
    first_band = '' if is_course else band(1, 0)
    if ('opening', '') in blend:
        used.add(('opening', ''))
        body=first_band+f'<section class="lesson-section lesson-start" id="problem"><h2>Start here</h2>{wrap("story", blend[("opening","")], env)}<div class="original-opening">{opening}</div></section>'
    else:
        desc=INTRO.get(Path(path).stem, 'Follow the concepts, examples, failure modes and design decisions in this chapter.')
        body=first_band+f'<section class="lesson-section lesson-start" id="problem"><span class="eyebrow">START WITH THE NEED</span><h2>Why this topic matters</h2><p>{escape(desc)}</p><div class="original-opening">{opening}</div></section>'
    if path.endswith('/coroutines.md'):
        body += '<section class="lesson-section" id="experiment"><span class="eyebrow">TRY THE IDEA</span><h2>Watch independent waits overlap</h2><p>A profile needs a name and an avatar. Waiting for one request before starting the other adds avoidable waiting. Run the example, switch <code>concurrent</code> from <code>true</code> to <code>false</code>, and compare the start messages.</p>' + (WEB/'content/coroutine-experiment.html').read_text() + '<p>In Playground output, <code>main @coroutine#2</code> means thread <code>main</code>, coroutine #2. Different coroutine numbers can share the same thread.</p></section>'
    part_index = 0
    bands = 1
    for j,(start,heading,anchor) in enumerate(sections):
        end=sections[j+1][0] if j+1<len(sections) else len(tokens)
        name=clean(heading)
        env['heading']=name
        rendered=MD.renderer.render(tokens[start:end],MD.options,env)
        qa=' data-question' if any(s in heading.lower() for s in ['answer key','probing question','review checklist','review questions']) else ''
        # Parts only move forward, so the story reads as one progression.
        wanted = PART_KEYS.index(blend[('part', name)]) if ('part', name) in blend else classify_part(name)
        if ('part', name) in blend: used.add(('part', name))
        if wanted > part_index and not is_course:
            part_index = wanted
            bands += 1
            body += band(bands, part_index)
        part = PARTS[part_index][0]
        before = ''.join(wrap(kind, html, env) for key, html in blend.items() if len(key) == 3 and key[0] == 'before' and key[1] == name for kind in [key[2]])
        after = ''.join(wrap(kind, html, env) for key, html in blend.items() if len(key) == 3 and key[0] == 'after' and key[1] == name for kind in [key[2]])
        used.update(k for k in blend if k[:2] in (('before', name), ('after', name)))
        body += before + f'<section class="lesson-section" id="section-{anchor}" data-part="{part}"{qa}>{rendered}{after}</section>'
        if path.endswith('/coroutines.md') and heading=='How `suspend` Works (Mental Model + Mechanism)':
            body += (WEB/'content/coroutine-internals.html').read_text()
        if path.endswith('/coroutines.md') and heading=='Exception Handling Patterns':
            body += (WEB/'content/coroutine-policies.html').read_text()
        if path.endswith('/coroutines.md') and heading=='Job Hierarchy and Cancellation':
            figure=(WEB/'content/coroutine-model.html').read_text()
            body += '<section class="lesson-section" id="ownership"><h2>See the ownership and failure policy</h2><p>The Android UI owner starts the profile load. The model assumes main-safe requests and shows an illustrative sequence, not measured Android frames or a captured runtime trace.</p><p>In the failure scenario, the outer UI boundary catches the expected <code>IOException</code> and sets an error state. Cancellation is allowed to propagate.</p>'+owner_code()+figure+'</section>'
    body += '<section class="lesson-section" id="continue-learning"><span class="eyebrow">CONNECT THE IDEAS</span><h2>Continue your Kotlin learning path</h2><p>The chapter above presents the original explanations, code examples, questions and answers in full. Use the learning path to connect this topic to the next one.</p><a class="secondary-button" href="'+BASE+'kotlin/">Explore all Kotlin chapters →</a></section>'
    unused = set(blend) - used
    if unused:
        raise ValueError(f'{path}: blend inserts target headings or diagrams that do not exist: {sorted(unused)}')
    # Outline is generated from exactly the displayed H2 headings, grouped by part.
    outline=[]
    for match in re.finditer(r'<div class="part-band" data-part-band="[^"]+"><span class="part-number">[^<]*</span><span class="part-name">([^<]*)</span>|<h2(?: id="([^"]+)")?>(.*?)</h2>',body,re.S):
        if match[1]:
            outline.append(f'<span class="outline-part">{match[1]}</span>')
            continue
        anchor=match[2]
        if not anchor:
            before=body[:match.start()]
            anchor=re.findall(r'<section[^>]* id="([^"]+)"',before)[-1]
        outline.append(f'<a href="#{anchor}">{escape(unescape(clean(match[3])))}</a>')
    rendered_text = re.sub('<[^>]+>',' ',body)
    source_headings=[t.content for i,t in enumerate(tokens) if t.type=='inline' and i>0 and tokens[i-1].type=='heading_open' and tokens[i-1].tag!='h1']
    report={'source':path,'source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'source_words':len(raw.split()),'headings':headings,'original_sections':len(sections),'code_blocks':len(codes),'diagrams':diagram_count[0],'corrections':len(fixes),'source_content':'Full corrected Markdown token stream rendered; no section or code-block selection.'}
    return body, ''.join(outline), report


def owner_code():
    code='''fun onProfileRequested() {
    viewModelScope.launch {
        state.value = ProfileUiState.Loading
        try {
            state.value = ProfileUiState.Content(loadProfile())
        } catch (error: IOException) {
            state.value = ProfileUiState.Error(error)
        }
    }
}'''
    return '<div class="code-card"><div class="code-header"><span>Android UI boundary<small>Application fragment · ProfileUiState and loadProfile supplied by the app</small></span><button class="code-button" data-copy="owner-code">Copy code</button></div><pre tabindex="0"><code id="owner-code" class="highlight">'+escape(code)+'</code></pre></div>'


INTRO = {
'variables':'A screen’s state changes over time. Before choosing val, var, lazy or lateinit, decide who can change the value, when it exists, and whether several callers can see it at once.',
'null-safety':'A profile photo, cached response or Java API value can be absent. Make that possibility visible in the type, then handle it where the application can choose a sensible outcome.',
'functions':'A growing codebase needs operations that callers can understand and safely combine. Start with parameters and results, then follow function types, higher-order functions and their runtime costs.',
'extensions':'You want a readable API around a type you do not own. Extensions help organise the call site; understanding how they are resolved prevents surprising behaviour when types or imports change.',
'data-classes':'Passing a record between layers creates questions about equality, copying and mutation. Data classes supply useful operations, but the generated behaviour depends on where each property is declared.',
'value-classes':'Two values may share a primitive representation while meaning different things. Value classes help express that distinction; their boxing and Java boundaries still need deliberate design.',
'sealed-classes':'A loading screen can be loading, showing content or showing an error. Model those alternatives explicitly, then make callers handle the permitted cases as the API evolves.',
'delegation':'Several components need the same behaviour without sharing one inheritance tree. Delegation moves that behaviour into a collaborator; property delegation applies the idea to access and storage.',
'generics':'A collection or API should work with many types without giving up type checking. Follow the constraints that make reuse safe, then examine what remains after JVM type erasure.',
'variance':'A producer of Dogs can often stand in for a producer of Animals, while a consumer needs the opposite relationship. Separate reading from writing before choosing in, out or a projection.',
'inline-functions':'A small higher-order function can create call and allocation costs. Inlining changes where its body lives, with consequences for control flow, visibility, code size and public API evolution.',
'reified-types':'A generic parser sometimes needs to ask which type the caller requested. Reified parameters carry type information into an inline call site, within the limits of erased nested types.',
'coroutines':'A profile screen needs network results while still responding to input. Follow how suspension releases a waiting thread, how independent requests overlap, who owns the work, and how failure reaches the UI.',
'channels-and-select':'A producer can generate work faster than a consumer handles it. Choose an explicit handoff, capacity and owner before deciding whether to wait, queue or drop values.',
'flow-operators-and-backpressure':'A stream can outpace its collector or keep obsolete work alive. Follow the default sequential pipeline, then decide when buffering, dropping, cancellation or parallel collection is appropriate.',
'callbackflow-and-bridging-callbacks':'A callback keeps delivering values until someone unregisters it. Connect registration and cleanup to collection so cancellation releases the listener and its resources.',
'coroutines-debugging-and-profiling':'A spinner is stuck, work survives navigation, or a failure appears far from its cause. Reconstruct ownership, dispatcher execution and suspension before choosing the diagnostic tool.',
'test-dispatchers-virtual-time':'A retry should happen after a delay and a cancelled request should clean up. Test those contracts with controlled scheduling rather than waiting for wall-clock time.',
'memory-model':'Two threads can observe the same shared data differently unless the program establishes a visibility and ordering contract. Begin with ownership and happens-before relationships, then examine runtime memory costs.',
'jvm-interop':'Your Kotlin API may be called from Java or exposed through JVM tooling. Inspect what callers actually see: signatures, nullability, properties, wildcards, defaults and binary compatibility.',
'bytecode':'Readable Kotlin can hide allocations, generated methods and dispatch. Connect source constructs to JVM output before making a performance or compatibility claim.',
'kotlin-2-4-update':'A compiler upgrade changes language and platform capabilities. Separate stable concepts from release-specific changes, and verify compatibility before changing a production build.',
'kotlin':'Start with values and functions, then connect types, compiler transformations, asynchronous work and runtime behaviour. Follow the guided phases or open a chapter directly.'}


def render_diagrams():
    """Render each Mermaid source to diagrams/<hash>.svg, reusing a local cache."""
    cache=CACHE/'diagrams'; cache.mkdir(parents=True,exist_ok=True)
    config=ROOT/'.github/puppeteer-config.json'
    for source in sorted((OUT/'diagram-sources').glob('*.mmd')):
        cached=cache/(source.stem+'.svg')
        if not cached.exists():
            command=shlex.split(MERMAID_RENDERER)+['-i',str(source),'-o',str(cached),'-b','transparent']
            if config.exists(): command+=['-p',str(config)]
            subprocess.run(command,check=True,capture_output=True,text=True)
        shutil.copy2(cached,OUT/'diagrams'/cached.name)


def build(skip_diagrams=False):
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    for directory in ['diagram-sources','diagrams','coverage']:(OUT/directory).mkdir(exist_ok=True)
    template=(WEB/'templates/reader.html').read_text().replace('{{base}}',BASE)
    index=(ROOT/'kotlin.md').read_text()
    order=[]
    for relative in re.findall(r'\]\((kotlin/[^)#]+\.md)\)',index):
        if relative not in order: order.append(relative)
    if set(order)!=PATHS-{'kotlin.md'}: raise ValueError('Kotlin reading sequence does not cover every chapter')
    # Generate catalog from checked-in tree indexes, using guided order rather than filenames.
    catalog=json.loads((WEB/'nav-data.js').read_text().split('=',1)[1].strip().rstrip(';'))
    for tree in catalog:
        tree_index=ROOT/(tree['slug']+'.md')
        if not tree_index.exists():continue
        tree_order=[]
        for target in re.findall(r'\]\(([^)#]+\.md)(?:#[^)]*)?\)',tree_index.read_text()):
            if target.startswith(tree['slug']+'/') and target not in tree_order:tree_order.append(target)
        actual=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/tree['slug']).rglob('*.md'))
        tree_order += [p for p in actual if p not in tree_order]
        tree['chapters']=[{'title':title(ROOT/p),'path':p} for p in tree_order]
    (OUT/'nav-data.js').write_text('window.PLAYBOOK_CATALOG = '+json.dumps(catalog,ensure_ascii=False)+';\n')
    reports=[]
    for path in ['kotlin.md']+order:
        raw=(ROOT/path).read_text(); article,outline,report=render_chapter(path,raw,path=='kotlin.md')
        name=title(ROOT/path)
        category='Learning path' if path=='kotlin.md' else Path(path).parent.name.replace('-',' ').title()
        navigation=''
        if path in order:
            i=order.index(path); links=[]
            if i: links.append(f'<a href="{route(order[i-1])}">← {escape(title(ROOT/order[i-1]))}</a>')
            if i+1<len(order):links.append(f'<a href="{route(order[i+1])}">{escape(title(ROOT/order[i+1]))} →</a>')
            navigation='<nav class="chapter-navigation" aria-label="Chapter navigation">'+''.join(links)+'</nav>'
        scripts=f'<script defer src="{BASE}lesson-model.js"></script><script defer src="{BASE}coroutines.js"></script>' if path.endswith('/coroutines.md') else ''
        playground='<section id="panel-playground" role="tabpanel" aria-labelledby="tab-playground" tabindex="0" hidden><div class="panel-intro"><span class="eyebrow">LEARN THROUGH CODE</span><h2>Keep the example with its explanation.</h2><p>Code blocks throughout Content can be copied. Application fragments depend on the surrounding app types, imports and libraries; they are not presented as standalone programs.</p>'
        if path.endswith('/coroutines.md'): playground+='<p>The runnable console example demonstrates overlapping waits. Return to Content to edit and run it beside the explanation.</p><button class="primary-button" data-go="experiment">Go to the example →</button>'
        else: playground+='<p>Use a Kotlin/JVM project or an Android project as indicated by each example. Read the assumptions and expected behaviour before running or changing a block.</p><button class="primary-button" data-open-tab="content">Return to Content</button>'
        playground+='</div></section>'
        values={'title':escape(name),'description':escape(INTRO[Path(path).stem]),'article':article,'outline':outline,'source':path,'source_url':SOURCE_ROOT+path,'category':escape(category),'chapter_navigation':navigation,'lesson_scripts':scripts,'playground_panel':playground}
        html=template
        for key,value in values.items():html=html.replace('{{'+key+'}}',value)
        if re.search(r'\{\{[a-z_]+\}\}',html):raise ValueError('Unexpanded page template')
        destination=OUT/route(path)[len(BASE):].strip('/')/'index.html';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(html)
        report['url']=route(path);reports.append(report)
        if path=='kotlin.md':(OUT/'index.html').write_text(html)
    for name in ['styles.css','blend.css','app.js','blend.js','coroutines.js','lesson-model.js']:
        shutil.copy2(WEB/name,OUT/name)
    if not skip_diagrams: render_diagrams()
    (OUT/'coverage/kotlin.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
    (OUT/'coverage/corrections.json').write_text(json.dumps(APPROVED_CORRECTIONS,ensure_ascii=False,indent=2)+'\n')
    print(f'Rendered {len(order)} Kotlin chapters + learning path; {sum(r["original_sections"] for r in reports)} source sections; {sum(r["code_blocks"] for r in reports)} code/diagram blocks; {len(APPROVED_CORRECTIONS)} of {len(ALL_CORRECTIONS)} proposed corrections approved and applied.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-diagrams',action='store_true',help='do not render Mermaid diagrams to SVG')
    args=parser.parse_args()
    build(args.skip_diagrams)
    # Never publish a build that dropped original content.
    import check_preservation
    sys.exit(check_preservation.main())
