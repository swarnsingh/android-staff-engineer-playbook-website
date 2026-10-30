#!/usr/bin/env python3
"""Render the original chapters of each lesson tree without shortening their content."""
from pathlib import Path
from html import escape, unescape
from urllib.parse import urlsplit, unquote, quote
import argparse, hashlib, json, os, re, shlex, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'website'
OUT = WEB / 'dist'
CACHE = WEB / '.cache'
SOURCE_ROOT = 'https://github.com/swarnsingh/android-staff-engineer-playbook-website/blob/main/'
MD = MarkdownIt('commonmark', {'html': True}).enable(['table', 'strikethrough'])
sys.path.insert(0, str(Path(__file__).resolve().parent))
import figure_maps
import walkthrough
# Designed figures that replace rendered Mermaid pictures, keyed by original diagram hash.
FIGURES = figure_maps.load()
FIGURES_USED = set()
# Topic trees rendered as lessons, in site order. `phases` lists the guided-reading phases a pilot
# renders (None renders the whole tree); chapters outside them keep linking to GitHub. `pilot`, when
# present, narrows those phases to the listed chapters (a local prototype, never a publishable tree).
TREES = {
    'engineering-fundamentals': {'title': 'Engineering Fundamentals', 'phases': None},
    'computer-science': {'title': 'Computer Science', 'phases': None},
    'platform-engineering': {'title': 'Platform Engineering', 'phases': None},
    'kotlin': {'title': 'Kotlin', 'phases': None},
    'android': {'title': 'Android', 'phases': [1, 2, 3, 4, 5, 6, 7, 8, 9]},
    'mobile-system-design': {'title': 'Mobile System Design', 'phases': [1, 2, 3, 4], 'pilot': [
        'mobile-system-design/design-framework.md', 'mobile-system-design/non-functional-requirements.md',
        'mobile-system-design/performance.md', 'mobile-system-design/accessibility.md',
        'mobile-system-design/localization-and-internationalization.md', 'mobile-system-design/security-and-privacy.md',
        'mobile-system-design/versioning-and-backward-compatibility.md', 'mobile-system-design/app-startup.md',
        'mobile-system-design/authentication.md', 'mobile-system-design/deep-links-and-universal-links.md',
        'mobile-system-design/push-notifications.md', 'mobile-system-design/feature-flags-and-remote-config.md',
        'mobile-system-design/telemetry-sdk.md', 'mobile-system-design/analytics-sdk.md',
        'mobile-system-design/image-loading.md', 'mobile-system-design/file-downloader.md',
        'mobile-system-design/caching-library.md', 'mobile-system-design/pagination.md',
        'mobile-system-design/typeahead-autocomplete-search.md', 'mobile-system-design/search.md',
        'mobile-system-design/notification-system.md', 'mobile-system-design/offline-sync.md']},
}


def phases(slug):
    """[(phase heading, chapter paths)] from the `### Phase …` lists of a tree's guided reading sequence."""
    if slug == 'engineering-fundamentals':
        sequence=(ROOT/f'{slug}.md').read_text().split('## Guided Reading Sequence',1)[1].split('**Next:**',1)[0]
        paths=re.findall(r'\]\((engineering-fundamentals/[^)#]+\.md)\)',sequence)
        return [('Phase 1 — Core vocabulary',paths[:5]),('Phase 2 — State and coordination',paths[5:9]),('Phase 3 — Production failure behavior',paths[9:])]
    if slug == 'computer-science':
        sequence=(ROOT/f'{slug}.md').read_text().split('## Guided Reading Sequence',1)[1].split('**Next:**',1)[0]
        paths=re.findall(r'\]\((computer-science/[^)#]+\.md)\)',sequence)
        return [('Phase 1 — Data structures',paths[:7]),('Phase 2 — Algorithms',paths[7:11]),('Phase 3 — Systems',paths[11:])]
    if slug == 'platform-engineering':
        sequence=(ROOT/f'{slug}.md').read_text().split('## Guided Reading Sequence',1)[1].split('**Next:**',1)[0]
        paths=re.findall(r'\]\((platform-engineering/[^)#]+\.md)\)',sequence)
        return [('Phase 1 — Paved roads and shared UI',paths[:2]),('Phase 2 — Distribution and guardrails',paths[2:5]),('Phase 3 — Build feedback',paths[5:])]
    result = []
    for block in re.split(r'^### ', (ROOT/f'{slug}.md').read_text(), flags=re.M)[1:]:
        heading, _, body = block.partition('\n')
        chapters = []
        # Links with an #anchor point into another chapter's section; they do not list that chapter here.
        for target in re.findall(r'\]\(([^)#]+\.md)\)', body.split('\n## ')[0]):
            if target.startswith(slug + '/') and target not in chapters: chapters.append(target)
        if chapters and heading.startswith('Phase'): result.append((heading.strip(), chapters))
    return result


ORDER, SECTION = {}, {}
for _slug, _tree in TREES.items():
    ORDER[_slug] = []
    for _heading, _chapters in phases(_slug):
        if _tree['phases'] is None or int(re.match(r'Phase (\d+)', _heading)[1]) in _tree['phases']:
            ORDER[_slug] += [p for p in _chapters if p not in ORDER[_slug]]
            for p in _chapters: SECTION.setdefault(p, _heading)  # the first phase listing a chapter owns it
    if _tree.get('pilot'): ORDER[_slug] = [p for p in ORDER[_slug] if p in _tree['pilot']]
    # A chapter's first phase owns it; the rendered reading sequence must not return to an earlier group.
    _phase_positions = {heading: index for index, (heading, _) in enumerate(phases(_slug))}
    _group_numbers = [_phase_positions[SECTION[p]] for p in ORDER[_slug]]
    if _group_numbers != sorted(_group_numbers):
        raise ValueError(f'{_slug} reading phases are not contiguous')
    if _tree['phases'] is None and set(ORDER[_slug]) != {p.relative_to(ROOT).as_posix() for p in (ROOT/_slug).rglob('*.md')}:
        raise ValueError(f'{_slug} reading sequence does not cover every chapter')
PAGES = [p for slug in TREES for p in [f'{slug}.md'] + ORDER[slug]]
PATHS = set(PAGES)
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
    return BASE + path.removesuffix('.md') + '/'


def slug_heading(heading):
    return slug(heading)


def tree_of(path):
    return path.split('/')[0].removesuffix('.md')


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


def corrected(source, path, mark=False):
    """Apply approved corrections. Returns the corrected source and, per fix, the line it landed on.

    With mark=True, a single-line fix outside code (except table rows) is wrapped in <mark class="correction-mark">, so the
    corrected words are visible where they stand. The reader uses unmarked corrected prose
    and keeps the detailed change inventory in its optional footer history.
    """
    applied = []
    for fix in APPROVED_CORRECTIONS:
        if fix['path'] != path: continue
        if source.count(fix['old']) != 1:
            raise ValueError(f"Correction no longer matches exactly once: {path}: {fix['reason']}")
        at = source.index(fix['old'])
        line_start = source.rfind('\n', 0, at) + 1
        in_fence = len(re.findall(r'^\s*(```|~~~)', source[:at], re.M)) % 2 == 1
        in_span = source[line_start:at].count('`') % 2 == 1
        line_end = source.find('\n', at)
        current_line = source[line_start:line_end if line_end >= 0 else len(source)]
        in_table_row = current_line.lstrip().startswith('|')
        new = fix['new']
        if mark and '\n' not in fix['old'] + new and not in_fence and not in_span and not in_table_row:
            # At the start of a line, keep the block syntax (list marker, heading, quote) outside the mark;
            # table rows and indented lines stay unmarked and rely on the section note.
            prefix = '' if at > line_start else re.match(r'(?:[-*+] |\d+\.\s+|> ?|#{1,6} )?', new).group(0)
            body = new[len(prefix):]
            if body.strip() and not (at == line_start and re.match(r'\s|\|', new)):
                new = prefix + f'<mark class="correction-mark" title="Corrected on this website">{body}</mark>'
        source = source[:at] + new + source[at + len(fix['old']):]
        shift = len(new) - len(fix['old'])
        for earlier in applied:  # keep earlier fixes pointing at their own text
            if earlier['at'] > at: earlier['at'] += shift
        applied.append({**fix, 'at': at})
    for fix in applied:
        fix['line'] = source.count('\n', 0, fix['at'])
    return source, applied


def correction_note(fixes):
    """Optional editorial history; corrected lesson prose reads without review annotations."""
    if not fixes: return ''
    items = ''.join(
        f'<li data-correction-id="{escape(fix["id"])}"><p>{escape(fix["reason"])}</p><details><summary>Changed wording</summary><p>Current wording</p><pre>{escape(fix["new"])}</pre><p>Original wording</p><pre>{escape(fix["old"])}</pre></details>'
        + (f'<p>Sources: ' + ', '.join(f'<a href="{escape(url)}" target="_blank" rel="noreferrer">{escape(urlsplit(url).netloc)}</a>' for url in fix['sources']) + '</p>' if fix.get('sources') else '')
        + '</li>' for fix in fixes)
    count=len(fixes)
    return f'<details class="technical-correction-history"><summary>Technical correction history · {count} {"update" if count==1 else "updates"}</summary><ol>{items}</ol></details>'


def added(kind, html):
    """Label website-only material, so readers can tell it from the original chapter."""
    label = BLEND_LABELS[kind]
    return f'<div class="blend" data-kind="{kind}">' + (f'<span class="blend-label">{label}</span>' if label else '') + html + '</div>'


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
    ('MECHANISM', 'How it really works', 'How the mechanism works, step by step.'),
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
                'check': 'Check yourself', 'deeper': 'Under the hood', 'staff': 'Staff lens', 'try': 'Try it', 'review': 'Under review', 'bridge': '',
                'tryfirst': 'Try first', 'pushback': 'Interviewer pushes back', 'recap': 'Interview recap · added by this site'}


def load_blend(path):
    """Read website/content/blend/<chapter>.blend: Markdown fragments placed by markers.

    <!-- @opening -->                      replaces the generic intro with a problem-first story
    <!-- @before Heading :: kind -->       inserted before that H2 section
    <!-- @after Heading :: kind -->        appended inside that H2 section
    <!-- @diagram <hash> -->               designed redraw shown instead of that Mermaid diagram
    <!-- @part Heading :: KEY -->          force the part a section belongs to
    Headings are matched on their visible text (backticks and emphasis removed).
    """
    # Kotlin blends predate other trees and sit at the top level; other trees use a folder per tree.
    folder = WEB / 'content/blend' if tree_of(path) == 'kotlin' else WEB / 'content/blend' / tree_of(path)
    # Full chapter paths prevent collisions such as data-and-di/dependency-injection
    # and kotlin-multiplatform/ecosystem/dependency-injection. Retain legacy locations.
    scoped = WEB / 'content/blend' / Path(path).with_suffix('.blend')
    file = scoped if scoped.exists() else folder / (Path(path).stem + '.blend')
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


def timeline_labels(html):
    """Keep long teaching-timeline labels readable without changing proportional bars."""
    def track(match):
        labels = re.findall(r'<span\b[^>]*class="mark(?:\s[^"]*)?"[^>]*>(.*?)</span>', match.group(2), re.S)
        if not labels or all(len(clean(unescape(label))) <= 2 for label in labels):
            return match.group(0)
        index = 0
        def mark(item):
            nonlocal index
            index += 1
            return item.group(1)[:-1] + f' data-label-index="{index}" aria-hidden="true">' + item.group(2) + '</span>'
        bars = re.sub(r'(<span\b[^>]*class="mark(?:\s[^"]*)?"[^>]*>)(.*?)</span>', mark, match.group(2), flags=re.S)
        legend = '<ol class="timeline-legend">' + ''.join('<li>'+label+'</li>' for label in labels) + '</ol>'
        return '<div class="timeline-lane-body">' + match.group(1) + bars + '</div>' + legend + '</div>'
    return re.sub(r'(<div\b[^>]*class="track"[^>]*>)(.*?)</div>', track, html, flags=re.S)


def steps_as_text(html):
    """Print every animation step as a numbered list, so no step depends on motion or JavaScript."""
    def add(match):
        steps = json.loads(match.group(2))
        items = ''.join(f'<li>{"<strong>"+escape(s["label"])+".</strong> " if s.get("label") else ""}{escape(s.get("caption",""))}</li>' for s in steps)
        return match.group(1) + match.group(2) + match.group(3) + f'<details class="steps-text"><summary>Read every step as text</summary><ol>{items}</ol></details>'
    html = re.sub(r'(<script type="application/json" class="steps">)(.*?)(</script>)', add, html, flags=re.S)
    def scene_text(match):
        fragment = match.group(0)
        data = json.loads(re.search(r'<script type="application/json">(.*?)</script>', fragment, re.S)[1])
        modes = list(data['modes'].values())
        items = ''.join('<li>'+s['caption']+'</li>' for s in modes[0]['steps'])
        fragment = fragment.replace('<ol></ol>', '<ol>'+items+'</ol>', 1)
        # Alternate tracks also remain readable when JavaScript is unavailable.
        if len(modes) > 1:
            alternate = ''.join('<ol>'+''.join('<li>'+s['caption']+'</li>' for s in mode['steps'])+'</ol>' for mode in modes[1:])
            fragment = fragment.replace('</section>', '<noscript><p>Alternate track:</p>'+alternate+'</noscript></section>')
        return fragment
    return re.sub(r'<section\b[^>]*data-pb-flow="scene"[^>]*>.*?</section>', scene_text, html, flags=re.S)


def component_parameters(html):
    """Declared lesson parameters (data-at/data-len) become the timeline component's variables."""
    def mark(m):
        at, length = m.group(2), m.group(3)
        return m.group(1) + f' style="--at:{at}' + (f';--len:{length}' if length else '') + '"'
    return re.sub(r'(<[a-z][^<>]*?)\sdata-at="([^"]+)"(?:\s+data-len="([^"]+)")?', mark, html)


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
    return added(kind, steps_as_text(timeline_labels(component_parameters(html))))


def is_question_section(heading):
    """Explicit practice sections; a mechanism heading containing 'question' stays in Content."""
    name = re.sub(r'^\d+\.\s*', '', clean(heading)).casefold()
    return name in {'probing questions', 'answer key', 'q&a', 'questions and answers'} or name.endswith(('review checklist', 'review questions'))


def render_chapter(path, raw, is_course=False):
    source, fixes = corrected(raw, path, mark=False)
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
    # Interview walkthrough (system-design chapters): derived from the numbered H2 headings, or None.
    steps = None if is_course else walkthrough.plan(path, [(clean(h), a) for _, h, a in sections])
    step_of = {s['anchor']: s for s in steps or []}
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
            provenance="teaching" if env.get("blend") else "original"
            original=f'<img data-{provenance}-diagram="{key}" src="{BASE}diagrams/{key}.svg" alt="{escape(env.get("heading","Concept relationships"))}" loading="eager">'
            source=f'<details class="diagram-source"><summary>Read diagram source</summary><pre tabindex="0"><code data-{provenance}-diagram-source="{key}">{escape(token.content)}</code></pre></details>'
            if key in FIGURES:
                # Designed figure from the shared FigureMap component; no Mermaid picture is shown.
                FIGURES_USED.add(key)
                figure,preserved=figure_maps.render(FIGURES[key],token.content,provenance)
                # A teaching-layer diagram is already inside its labelled addition.
                return figure if provenance=='teaching' else wrap('visual', figure, env) + preserved
            if ('diagram', key) in blend:
                # A designed redraw leads; the chapter's own diagram stays one tap away.
                used.add(('diagram', key))
                # Rulebook §20: the original stays as preserved Mermaid source text, never a rendered Mermaid picture.
                return wrap('visual', blend[('diagram', key)], env) + f'<details class="original-diagram"><summary>Original diagram from the chapter</summary><pre tabindex="0"><code data-{provenance}-diagram-source="{key}">{escape(token.content)}</code></pre></details>'
            return f'<figure class="source-diagram">{original}<figcaption>Concept relationships from this section.</figcaption>{source}</figure>'
        if env.get('blend'):
            label, note = {'kotlin':'Kotlin','java':'Java','text':'Output'}.get(language,language), 'Added example'
        else:
            label={'kotlin':'Kotlin','java':'Java','groovy':'Gradle / Groovy','kts':'Gradle / Kotlin','text':'Illustrative output'}.get(language,language)
            note=''
        return f'<div class="code-card"><div class="code-header"><span>{escape(label)}{f'<small>{note}</small>' if note else ''}</span><button class="code-button" data-copy="{code_id}">Copy code</button></div><pre tabindex="0" aria-label="{escape(label)} example"><code id="{code_id}" class="highlight language-{escape(language)}">{escape(token.content)}</code></pre></div>\n'
    MD.renderer.rules['fence']=fence
    env={'prefix':slug(path),'code_index':0}
    initial=tokens[:sections[0][0]] if sections else tokens
    # H1 is represented by the page hero; all other opening content stays intact.
    if initial and initial[0].type=='heading_open' and initial[0].tag=='h1': initial=initial[3:]
    opening=MD.renderer.render(initial,MD.options,env)
    def band(number, index):
        key, title_text, promise = PARTS[index]
        return f'<div class="part-band" data-part-band="{key}"><span class="part-number">PART {number}</span><span class="part-name">{title_text}</span><p class="part-promise">{promise}</p></div>'
    # The opening story always belongs to the first part of the chapter. A walkthrough is paced by
    # its interview timeline instead of story parts.
    first_band = walkthrough.timeline(steps) if steps else '' if is_course else band(1, 0)
    if ('opening', '') in blend:
        used.add(('opening', ''))
        body=first_band+f'<section class="lesson-section lesson-start" id="problem"><h2>Start here</h2>{wrap("story", blend[("opening","")], env)}<div class="original-opening">{opening}</div></section>'
    else:
        desc=intro(path)
        # A walkthrough's hero already carries this description; do not repeat it above the chapter's opening.
        lead='' if steps else f'<p>{escape(desc)}</p>'
        body=first_band+f'<section class="lesson-section lesson-start" id="problem"><span class="eyebrow">START WITH THE NEED</span><h2>Why this topic matters</h2>{lead}<div class="original-opening">{opening}</div></section>'
    if path.endswith('/coroutines.md'):
        body += '<section class="lesson-section" id="experiment">' + added('try', '<h2>Watch independent waits overlap</h2><p>A profile needs a name and an avatar. Waiting for one request before starting the other adds avoidable waiting. Run the example, switch <code>concurrent</code> from <code>true</code> to <code>false</code>, and compare the start messages.</p>' + (WEB/'content/coroutine-experiment.html').read_text() + '<p>In Playground output, <code>main @coroutine#2</code> means thread <code>main</code>, coroutine #2. Different coroutine numbers can share the same thread.</p>') + '</section>'
    part_index = 0
    bands = 1
    for j,(start,heading,anchor) in enumerate(sections):
        end=sections[j+1][0] if j+1<len(sections) else len(tokens)
        name=clean(heading)
        env['heading']=name
        rendered=MD.renderer.render(tokens[start:end],MD.options,env)
        qa=' data-question' if is_question_section(heading) else ''
        # Parts only move forward, so the story reads as one progression.
        wanted = PART_KEYS.index(blend[('part', name)]) if ('part', name) in blend else classify_part(name)
        if ('part', name) in blend: used.add(('part', name))
        if wanted > part_index and not is_course and not steps:
            part_index = wanted
            bands += 1
            body += band(bands, part_index)
        part = PARTS[part_index][0]
        before = ''.join(wrap(kind, html, env) for key, html in blend.items() if len(key) == 3 and key[0] == 'before' and key[1] == name for kind in [key[2]])
        after = ''.join(wrap(kind, html, env) for key, html in blend.items() if len(key) == 3 and key[0] == 'after' and key[1] == name for kind in [key[2]])
        used.update(k for k in blend if k[:2] in (('before', name), ('after', name)))
        step = step_of.get(anchor)
        if step:
            if step['role'] in walkthrough.TRY_FIRST: before = walkthrough.try_first(step['role']) + before
            if step['role'] == 'tradeoffs': rendered = walkthrough.decision_cards(rendered)
            if step['role'] == 'followups': rendered = walkthrough.pushbacks(rendered)
        interview = f' data-interview-step="{step["number"]}"' if step else ''
        body += before + f'<section class="lesson-section" id="section-{anchor}" data-part="{part}" data-source-order="{j+1}"{interview}{qa}>{rendered}{after}</section>'
        if path.endswith('/coroutines.md') and heading=='How `suspend` Works (Mental Model + Mechanism)':
            body += added('deeper', (WEB/'content/coroutine-internals.html').read_text())
        if path.endswith('/coroutines.md') and heading=='Exception Handling Patterns':
            body += added('guide', (WEB/'content/coroutine-policies.html').read_text())
        if path.endswith('/coroutines.md') and heading=='Job Hierarchy and Cancellation':
            figure=(WEB/'content/coroutine-model.html').read_text()
            body += '<section class="lesson-section" id="ownership">' + added('visual', '<h2>See the ownership and failure policy</h2><p>The Android UI owner starts the profile load. The model assumes main-safe requests and shows an illustrative sequence, not measured Android frames or a captured runtime trace.</p><p>In the failure scenario, the outer UI boundary catches the expected <code>IOException</code> and sets an error state. Cancellation is allowed to propagate.</p>'+owner_code()+figure) + '</section>'
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
    report={'layout':'walkthrough' if steps else 'chapter','pacing':walkthrough.pacing(steps) if steps else '','source':path,'source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'source_words':len(raw.split()),'headings':headings,'original_sections':len(sections),'code_blocks':len(codes),'diagrams':diagram_count[0],'corrections':len(fixes),'source_content':'Full corrected Markdown token stream rendered; no section or code-block selection.'}
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
'kotlin':'Start with values and functions, then connect types, compiler transformations, asynchronous work and runtime behaviour. Follow the guided phases or open a chapter directly.',
# Other trees are keyed by path, because chapter names repeat across trees.
'android.md':'Start with the lifecycle the system imposes on every screen, then decide who owns state and data, how the UI renders it, where work runs, and how you verify and measure the result. Follow the guided phases or open a chapter directly.',
'android/architecture/activity.md':'The system can stop or destroy your screen at any moment: on rotation, when another app comes forward, or to reclaim memory. Learn what an Activity is in that contract, which callbacks you can rely on, and what must not live inside it.',
'android/architecture/fragment.md':'Many production screens are still built from Fragments, which add a second, shorter-lived view lifecycle inside their host. Learn where that split causes leaks and stale UI, and how Fragments fit a Compose-first codebase.',
'android/architecture/viewmodel.md':'Rotation recreates the Activity, but the user expects loaded data to stay. A ViewModel keeps screen state across configuration changes; know exactly what it survives, what it does not, and who owns its work.',
'android/architecture/savedstatehandle.md':'A ViewModel is lost when the system kills a backgrounded process. SavedStateHandle keeps small, critical screen inputs in saved instance state, so the screen can rebuild after process death.',
'android/architecture/process-death-and-state-restoration.md':'Android kills background processes to free memory, and the user returns expecting the same screen. Learn what the system restores, what you must restore, and how to test that path deliberately.',
'android/architecture/navigation.md':'A flow of screens must survive Back, deep links, rotation and process death while passing each destination only what it needs. Learn how the back stack is modelled and what belongs in navigation arguments.',
'android/architecture/mvvm-vs-mvi.md':'Two screens with the same features can behave very differently under concurrent events and failures. Compare how MVVM and MVI shape state, events and tests before choosing one for a team.',
'android/architecture/state-management.md':'Duplicated or ambiguously owned state shows stale data and races between updates. Give each piece of screen state one owner, one source of truth and one direction of flow.',
'android/architecture/modularization-strategies.md':'As an app and its team grow, build times, ownership and accidental coupling grow with them. Learn how to split modules by feature and layer, and what each boundary costs.',
'android/data-and-di/repository-source-of-truth.md':'When the network, the database and the UI each hold a copy, users see stale screens and lose offline edits. Decide which copy is the truth for each kind of data, then build the read path, durable writes and merge rules around it.',
'android/data-and-di/room.md':'A database outlives every version of the code that writes to it. Learn how Room checks SQL at build time, keeps queries live as tables change, and migrates schemas without losing users\' data.',
'android/data-and-di/datastore.md':'Settings stored with SharedPreferences can block the main thread in places you never wrote disk code. Learn how DataStore makes reads and writes asynchronous and transactional, and how to migrate safely.',
'android/data-and-di/room-vs-datastore.md':'Both Room and DataStore persist data with Flow reads and suspend writes, but one rewrites a whole document on every change. Choose by the shape of the data, then plan migrations, encryption and backup.',
'android/data-and-di/storage-and-content-sharing.md':'Access to a file your app does not own is a permission attached to a URI, and it can expire before your background work runs. Pick the right storage primitive and keep its grant valid for as long as you need it.',
'android/data-and-di/paging.md':'Infinite lists show duplicates, reset on rotation and go blank offline when pages are loaded by hand. Learn how Paging 3 loads pages, survives configuration changes and pages from a database the network fills.',
'android/data-and-di/dependency-injection.md':'Classes that build their own collaborators are slow to test and share nothing by accident or by design. Learn how dependency injection and Hilt decide how each dependency is built, shared and released.',
'android/data-and-di/components.md':'A Hilt scope is a promise about which container holds an instance, and each container lives for one Android lifetime. Map the standard components to those lifetimes and learn how a request finds its binding.',
'android/data-and-di/scopes.md':'A singleton says nothing about when its background work stops. Separate Hilt scopes, which decide how many instances exist, from coroutine scopes, which decide when work is cancelled.',
'android/data-and-di/hilt-vs-koin-vs-manual-di.md':'Every app does dependency injection; the choice is when the graph is checked, what it costs to build and where it can run. Compare manual DI, Hilt and Koin on those trade-offs.',
'android/compose/compose-runtime.md':'Compose has no virtual DOM to diff. Follow how the compiler and runtime record what each composable emitted, so you can predict what re-runs after a state change and what is skipped.',
'android/compose/snapshot-system.md':'Every mutableStateOf keeps versioned records read through snapshots. Learn how Compose tracks reads, publishes several writes at once, and bridges state to coroutines.',
'android/compose/recomposition-and-state.md':'Nothing redraws because a variable changed; it redraws because observable state that a composable read was written. Build that model, then use it for hoisting, lists and loops.',
'android/compose/stability.md':'Whether Compose can skip a child depends on how it compares arguments. Learn what is inferred stable, what the annotations promise, and why instance reuse matters under strong skipping.',
'android/compose/modifiers-and-layout.md':'A Modifier chain is an ordered list of wrappers, not a set of attributes. Read it in the right direction and backgrounds, ripples, clipping and margins all follow from one rule.',
'android/compose/custom-layout-measurement.md':'A custom layout is a contract: measure each child once, choose a size within the constraints, then place children. Learn when to write one and how to keep each clause.',
'android/compose/side-effects.md':'A composable may run many times, be skipped or be abandoned. Give every effect on the outside world an owner that defines when it starts, restarts and is cleaned up.',
'android/compose/compose-navigation.md':'Navigation Compose 2 keeps the back stack inside a controller; Navigation 3 makes it app-owned state. Compare the two lines, choose one, and migrate without breaking deep links or ViewModel lifetimes.',
'android/compose/adaptive-compose-large-screens.md':'Large screens rarely need different features; they need the same product state in a different arrangement that can change at any moment. Separate state from layout across windows, folds and input modes.',
'android/compose/form-factors-matrix.md':'Wear OS, TV, cars and widgets each have their own UI toolkit and rules, and only the layers below the UI carry over. Decide which surfaces to build with a cost model, not a wish list.',
'android/compose/compose-accessibility.md':'Accessibility services see a semantics tree, not pixels. Make every element say what it is, what state it has and what it can do, then test it with real assistive technology.',
'android/compose/view-interop-and-migration.md':'Most apps move to Compose over years, with Views and Compose embedded in each other. Learn both interop directions, what every seam costs, and a migration order that keeps features shipping.',
'android/compose/compose-performance-tooling.md':'Compose performance work starts with measurement, not techniques. Reproduce the journey in a release-like build, find the phase that costs time, fix it, and guard it with a benchmark.',
'android/architecture/structured-concurrency.md':'Background work that nothing owns keeps running after its screen is gone. Give every coroutine a parent and every parent a lifetime, so cancellation flows down and failure flows up.',
'android/architecture/flow.md':'A Flow runs its producer once per collector, which is wrong for an expensive source many screens share. Keep sources cold, share them once in the ViewModel, and collect with lifecycle awareness.',
'android/concurrency/coroutines-under-the-hood.md':'A suspend function does not hold a thread while it waits. Follow the compiler-generated state machine to see where locals live, where execution resumes, and why thread-confined state is lost.',
'android/concurrency/threads-and-looper.md':'Everything on the main thread is a message taken from one queue by one loop. Learn how Looper, MessageQueue and Handler fit together, why blocking the loop freezes the app, and how queued work outlives its owner.',
'android/concurrency/shared-flow-and-state-flow.md':'StateFlow, SharedFlow and Channel make different promises about values nobody is collecting and what new collectors receive. Match the contract to the job, especially for effects the user must not miss.',
'android/concurrency/synchronization-and-mutex.md':'Shared mutable state needs a rule for who may touch it and when. Match atomics, locks, Mutex and confinement to the problems each actually solves, without blocking threads coroutines depend on.',
'android/concurrency/services.md':'A Service is not a thread but a declaration to the system that the process is doing work that matters. Learn the three kinds, the main-thread trap, foreground service types, and when WorkManager fits better.',
'android/concurrency/workmanager.md':'Some work must happen eventually, even across process death and reboots. Follow a WorkManager request from enqueue to success, with constraints, retries and backoff.',
'android/concurrency/battery-optimizations.md':'Android defers background work when a device is idle and rations it by how recently each app was used. Learn how Doze and App Standby Buckets behave, and which narrow exits fit work that cannot wait.',
'android/networking-and-security/retrofit-and-okhttp.md':"A request that works in a demo breaks once authentication, retries and response bodies interact. Separate Retrofit's declarative interface from OkHttp's transport, then decide who owns each policy and resource.",
'android/networking-and-security/ktor-vs-retrofit.md':'Retrofit and Ktor can both fetch the same JSON; they differ in where the code can run and how the pipeline is extended. Choose by the boundary you are sharing and what you must operate, not by fashion.',
'android/networking-and-security/graphql.md':"One screen needing data from five REST endpoints tempts a team towards GraphQL, which moves the shape of every response into the client's query. Learn what that buys, how caching and partial errors change, and what the server must now protect.",
'android/networking-and-security/networkcallback-metered-vpn-captive-portal.md':'"Connected" does not mean your request will succeed: the network may be metered, behind a VPN or trapped by a captive portal. Treat connectivity signals as hints, and let real request outcomes drive retries.',
'android/networking-and-security/security-and-keystore.md':'A secret stored in app files can be copied off a rooted or backed-up device. Learn how Android Keystore keeps key material out of your process, what hardware backing promises, and what it cannot protect.',
'android/networking-and-security/device-connectivity-and-location.md':'A BLE scan or location request that works on the desk can drain the battery, lose its connection or be stopped by the system in the field. Design when access starts, when it stops and what survives process death.',
'android/data-and-di/health-connect.md':"Health data comes from many apps and devices, and the user decides who may read or write each kind. Learn how Health Connect's shared schema, permissions and change tokens let apps exchange records without owning them.",
'android/networking-and-security/webview-and-hybrid.md':"Embedded web pages run someone else's code with access to whatever your app exposes to it, next to your users' sessions. Decide when WebView, Custom Tabs or native screens fit, and how to keep the JavaScript bridge and navigation from becoming an attack surface.",
'android/media/media3-player-architecture.md':'Feed autoplay, full-screen video, background audio and downloads all compete for limited codecs, audio focus, memory and battery. Design a single Media3 player stack that every surface shares, with a session the system can control.',
'android/media/camerax-capture-architecture.md':'Camera code that works on one phone fails on hundreds of others with different sensors and quirks. Learn how CameraX use cases bind to a lifecycle, when Camera2 is worth its cost, and how to test across devices.',
'android/testing/testing-strategy.md':'A test suite that takes an hour or fails at random stops protecting releases and starts slowing them down. Decide what each tier of tests is worth, where it runs in CI and who owns flakiness.',
'android/testing/unit-testing.md':'Fast tests are only useful if they exercise the real logic with time and threads under control. Learn how to isolate a unit, fake its collaborators and drive coroutines with a test scheduler.',
'android/testing/ui-testing.md':'UI tests that sleep, guess at timing or match pixels become the flakiest part of a build. Learn how Compose and Espresso tests synchronise with the app, find elements by semantics and stay trustworthy at scale.',
'android/performance/startup.md':'A spinner appears quickly, but the user is still waiting for the content they came for. Choose the finish line that matters, measure cold, warm and hot starts against it, then cut work from the critical path.',
'android/performance/jank.md':'A scroll stutters even with no network request running. Find out which part of one late frame took too long: app code on the main thread, a wait on another thread, or rendering further downstream.',
'android/performance/rendering.md':'The main thread can finish its work and the frame still arrives late. Follow a frame from recorded drawing commands through the RenderThread and buffer queue to the display.',
'android/performance/anrs.md':'When an app stops responding, the main thread is usually waiting on something: slow I/O, a binder call, heavy work, or a lock whose owner is itself stuck. Learn what the system times out, how to read the traces, and how to follow the wait to its cause.',
'android/performance/memory-management-and-leaks.md':'Every screen the user closes should become garbage, yet a forgotten listener can keep each one alive. Treat memory growth as an ownership problem: who registered a reference, and who promised to remove it?',
'android/performance/native-memory-bitmaps.md':"An image feed can be killed on a small device while the Kotlin heap looks normal, because pixels and graphics buffers live elsewhere. Account for the whole process's memory and size bitmaps for the view that shows them.",
'android/performance/app-size-and-r8.md':'A feature works in development and fails only in the release build, while each new SDK makes the download bigger. Learn what R8 keeps, removes and renames, and how to measure the bytes users actually receive.',
'android/performance/baseline-profiles.md':'A freshly installed app is slower on its first journeys than after repeated use. Baseline Profiles tell the runtime which code to compile ahead of time; learn how to generate, ship and verify them.',
'android/performance/macrobenchmark-and-perfetto.md':'A red benchmark only matters if the experiment was fair: the same content, device and compilation state. Learn how Macrobenchmark measures real journeys and how Perfetto traces explain the result.',
'android/performance/battery-power-profiling.md':'The app sits idle on screen and the battery keeps draining. Find the work that continues after useful activity ends, such as retry loops, location sessions and wake locks, and measure its cost.',
'android/performance/network-radio-wakeups.md':'Many tiny requests can cost more battery than one large one, because each can keep the radio in a high-power state for longer. Set a freshness requirement for every request, then batch, defer or push what can wait.',
'android/performance/thermal-low-end-device-strategy.md':'An app that is smooth for the first minute slows as the device heats up, and low-end phones start with less headroom. Adapt quality and work to the budget the device can sustain, not the one it has at launch.',
'android/observability/logging.md':'A disabled debug log can still build its expensive message, and a forgotten log can leak personal data. Decide what each log costs to construct, which sink receives it, and what must never be written.',
'android/observability/crash-monitoring.md':'A new release brings a crash cluster with minified stacks from one group of devices. Connect each report to the exact build, its mapping files and an owner, and decide when to halt the rollout.',
'android/observability/mobile-apm-and-rum.md':"In an illustrative case, the backend says checkout took 200 milliseconds while the user waited three seconds. Measure from the user's interaction to the visible result, and connect client timings to server traces.",
'android/kotlin-multiplatform/kmp-decision-matrix.md':'Two native apps implement the same business rule and slowly drift apart. Decide whether Kotlin Multiplatform is worth its build, tooling and team costs, and which code to share first.',
'android/kotlin-multiplatform/foundations/overview-and-k1-vs-k2.md':'Kotlin is one language compiled by one frontend into very different targets: JVM bytecode, native binaries and JavaScript. Learn how that pipeline works and what the K2 compiler changed for multiplatform code.',
'android/kotlin-multiplatform/shared-domain-boundaries.md':'The best shared code is plain domain logic with explicit platform edges; the worst hides Android and iOS differences until production. Decide what to share and where each boundary should sit.',
'android/kotlin-multiplatform/foundations/architecture-and-module-boundaries.md':'Sharing only logic and sharing the whole UI lead to different project shapes, iOS workflows and CI costs. Choose a paradigm, then set module boundaries both platform teams can live with.',
'android/kotlin-multiplatform/tooling/build-system-and-source-sets.md':'A KMP build compiles the same module for several targets, each seeing a different set of source files and dependencies. Learn how source-set hierarchies and published variants decide what code each target gets.',
'android/kotlin-multiplatform/ecosystem/libraries-ecosystem.md':'A dependency usable on Android may have no variant for iOS, and common code can call only what every target supports. Check library support per target before choosing, and plan for the gaps.',
'android/kotlin-multiplatform/ecosystem/networking-with-ktor.md':"Shared networking needs one API in common code and a different HTTP engine on each platform. Learn how Ktor's client pipeline separates the two, and where engine differences still reach your code.",
'android/kotlin-multiplatform/ecosystem/persistence.md':'Moving a database into shared code means choosing a library that works on every target and migrating data users already have. Compare Room, SQLDelight and key-value stores for multiplatform use.',
'android/kotlin-multiplatform/ecosystem/dependency-injection.md':'Hilt builds Android graphs well but does not run on iOS. Decide how shared code receives its dependencies, and which DI approach each platform uses around it.',
'android/kotlin-multiplatform/ui-sharing/compose-multiplatform.md':'Sharing UI saves the most code and carries the most risk, because users expect each platform to look and behave natively. Learn what Compose Multiplatform shares, how it renders on iOS, and where native screens still fit.',
'android/kotlin-multiplatform/ui-sharing/resource-sharing.md':'Strings, images and fonts need to be packaged differently for each platform yet referenced once from shared code. Learn how Compose Multiplatform resources are generated, packaged and loaded.',
'android/kotlin-multiplatform/production/concurrency-and-memory.md':'Kotlin/Native once froze objects shared between threads, and old code still carries that history. Learn how the current memory model and garbage collector work, and how coroutines cross into Swift.',
'android/kotlin-multiplatform/tooling/swift-interop.md':'iOS developers meet shared code only through its exported API, so awkward names, lossy generics and unmanaged Flows make it expensive to adopt. Design the Swift-facing surface deliberately.',
'android/kotlin-multiplatform/tooling/ios-distribution.md':'An iOS team needs a predictable framework it can reproduce and debug, not just Kotlin that compiles. Choose how the framework is built, packaged and versioned, and what ships with each release.',
'android/kotlin-multiplatform/binary-compatibility-api-evolution.md':'A change that is harmless for Android consumers can break Swift callers or persisted data. Name each consumer and its compatibility promise, then gate every published artifact separately.',
'android/kotlin-multiplatform/production/testing-and-mocking.md':'Shared code can pass on the JVM and fail on iOS, because runtimes, schedulers and platform adapters differ. Decide which tests run on which targets and how to replace platform dependencies in them.',
'android/kotlin-multiplatform/kmp-observability-crash-symbolication.md':'A crash inside shared Kotlin code on iOS can arrive as an unreadable native stack. Make shared failures traceable across platforms, with symbols, logs and metrics tied to each release.',
'android/kotlin-multiplatform/production/ci-cd-for-kmp.md':'Apple frameworks can only be linked and tested on macOS, which makes multiplatform pipelines slower and more expensive. Decide what runs on each change, what is cached, and how releases stay reproducible.',
'android/kotlin-multiplatform/production/adoption-and-migration.md':'Rewriting two apps at once is rarely an option. Introduce shared code behind existing boundaries one slice at a time, keep each step reversible, and define when the old path can be removed.',
'android/build-tooling/gradle-and-build-systems.md':'You change one line and wait a minute before anything compiles. Learn how Gradle configures a task graph from plugins, decides what to run, and where an incremental build actually spends its time.',
'android/build-tooling/multi-module.md':"A private change in one feature turns other teams' builds red when module boundaries are wrong. Learn a standard module taxonomy and how API, implementation and test modules limit how far an edit spreads.",
'android/build-tooling/convention-plugins.md':'Fifty copied build files drift apart until no two modules are configured alike. Move shared build logic into small, tested convention plugins that every module applies by ID.',
'android/build-tooling/ksp.md':'Much of the code your app runs is generated at build time by annotation processors. Learn how KSP reads Kotlin symbols directly, why it replaces kapt, and how incremental processing decides what to regenerate.',
'android/os-internals/intent-resolution-and-manifest.md':'Every intent that reaches your app is input from outside, and every manifest entry is part of your public surface. Learn how Android matches intents to components and what your code must still check.',
'android/os-internals/broadcast-receivers.md':'A broadcast receiver can start your process for one short callback, then let it be killed. Learn how receivers are delivered, how long they live, and how to hand lasting work to an owner that survives.',
'android/os-internals/content-providers-and-contentresolver.md':'Another app cannot read a path into your private storage. Learn how content providers, URIs and temporary grants share exactly one piece of data, and why providers run before Application.onCreate().',
'android/os-internals/permissions-and-app-ops.md':'Holding a permission and being allowed to use a sensor right now are different questions. Learn the permission categories, the runtime flow, and how to design features that handle denial and degraded access.',
'android/os-internals/activitymanager-process-lifecycle.md':"Your app's task can stay in Recents after the process holding its memory has been killed. Learn how Android ranks and kills processes, and which owners restore state when the user returns.",
'android/os-internals/package-manager-installation-classloading.md':'An install can succeed while a class the app needs is missing until a user reaches it. Learn what PackageManager records at install, how classes load lazily, and how splits and R8 change that.',
'android/os-internals/the-binder.md':"A method call that looks local can wait on another process's busy thread. Learn how Binder carries calls between processes, what limits apply, and how to design cross-process contracts.",
'android/os-internals/the-zygote.md':'Every app needs the same framework, so Android prepares it once and copies the process. Learn how the Zygote preloads, forks and shares memory, and why a fast fork does not mean a ready app.',
'android/os-internals/art-and-dalvik.md':'The same build can run faster days after install with no code change. Learn how ART mixes interpretation, JIT and profile-guided AOT compilation, and how to measure performance fairly.'}


def intro(path):
    extras={}
    for name in ('engineering-fundamentals','computer-science','platform-engineering','mobile-system-design'):
        extras.update(json.loads((WEB/f'content/{name}.json').read_text()))
    return extras.get(path) or INTRO.get(path) or INTRO[Path(path).stem]


def render_diagrams():
    """Render each Mermaid source to diagrams/<hash>.svg, reusing a local cache."""
    cache=CACHE/'diagrams'; cache.mkdir(parents=True,exist_ok=True)
    config=ROOT/'.github/puppeteer-config.json'
    def render(source):
        cached=cache/(source.stem+'.svg')
        if not cached.exists():
            command=shlex.split(MERMAID_RENDERER)+['-i',str(source),'-o',str(cached),'-b','transparent']
            if config.exists(): command+=['-p',str(config)]
            result=subprocess.run(command,capture_output=True,text=True)
            if result.returncode: raise RuntimeError(f"Mermaid render failed: {source.name}\n{result.stderr}")
        shutil.copy2(cached,OUT/'diagrams'/cached.name)
    with ThreadPoolExecutor(max_workers=3) as workers:
        list(workers.map(render,sorted((OUT/'diagram-sources').glob('*.mmd'))))


DESIGN=WEB/'design-system'
# The site's names for design-system tokens, so existing styles take the new palette unchanged.
TOKEN_ALIASES={'bg':'sheet','surface':'sheet-sunken','hero':'accent-soft','text':'ink','muted':'ink-muted','line':'line',
               'accent':'accent','on-accent':'on-accent','accent-soft':'accent-soft','warning':'warn','code':'code-bg','code-text':'code-ink'}
THEME_SELECTORS={'light':':root','dark':'html[data-theme=dark]','sepia':'html[data-theme=sepia]','contrast':'html[data-theme=contrast]'}

def design_tokens_css():
    """Compile website/design-system/tokens.json into the site's custom properties and @font-face rules."""
    tokens=json.loads((DESIGN/'tokens.json').read_text())
    themes=[t['id'] for t in tokens['color']['themes']]
    value=lambda v,theme: v if isinstance(v,str) else v.get(theme,v[themes[0]])
    out=['/* Generated by build.py from website/design-system/tokens.json. Do not edit. */']
    for f in tokens['type'].get('fonts',[]):
        out.append(f'@font-face{{font-family:"{f["family"]}";src:url("fonts/{Path(f["file"]).name}") format("woff2");'
                   f'font-weight:{f.get("weight","400")};font-style:{f.get("style","normal")};font-display:swap}}')
    # Metric-matched local fallbacks: text keeps its line breaks while a web font is still loading.
    for f in tokens['type'].get('fallbacks',{}).get('faces',[]):
        out.append(f'@font-face{{font-family:"{f["family"]}";src:'+','.join(f'local("{name}")' for name in f['local'])+
                   f';size-adjust:{f["sizeAdjust"]};ascent-override:{f["ascentOverride"]};descent-override:{f["descentOverride"]};line-gap-override:{f["lineGapOverride"]}}}')
    for theme in themes:
        props=[f'--{c["name"]}:{value(c["value"],theme)}' for c in tokens['color']['tokens']]
        props+=[f'--{x["name"]}:{value(x["value"],theme)}' for x in tokens['shadow']['tokens']]
        # A token alias to itself creates a CSS variable cycle and invalidates the real colour.
        props+=[f'--{old}:var(--{new})' for old,new in TOKEN_ALIASES.items() if old != new]
        if theme==themes[0]:
            for family in ('spacing','radius','layout','figure','uitype'): props+=[f'--{x["name"]}:{x["value"]}' for x in tokens[family]['tokens']]
            props+=[f'--font-{k}:{v}' for k,v in tokens['type']['families'].items()]
            prose=tokens['type']['prose']; body=prose['metrics']
            props+=[f'--font-prose:var(--font-{reader_font(prose,prose["default"])["family"]})','--reader-font:var(--font-prose)',
                    f'--prose-leading:{body["lineHeight"]}',f'--prose-weight:{body["weight"]}',f'--prose-spacing:{body["paragraphSpacing"]}',f'--prose-x-height:{body["xHeight"]}',
                    f'--measure-prose:{reader_font(prose,prose["default"])["measure"]}']
            code=tokens['type']['code']; props+=[f'--code-size:{code["size"]}',f'--code-leading:{code["lineHeight"]}',f'--code-inline:{code["inline"]}']
        out.append(THEME_SELECTORS[theme]+'{'+';'.join(props)+'}')
    # The reader's font choice swaps one token; every prose rule reads --font-prose.
    prose=tokens['type']['prose']
    out+=[f'html[data-reader-font={o["id"]}]{{--font-prose:var(--font-{o["family"]});--measure-prose:{o["measure"]}}}' for o in prose['options'] if o['id']!=prose['default']]
    return '\n'.join(out)+'\n'

def reader_font(prose,font_id):
    return next(o for o in prose['options'] if o['id']==font_id)

def reader_font_markup():
    """Reading-font options and the head bootstrap, both from tokens.json, so the panel and the CSS cannot drift."""
    tokens=json.loads((DESIGN/'tokens.json').read_text()); prose=tokens['type']['prose']
    options=''.join(f'<option value="{o["id"]}" data-legacy="{" ".join(o["legacy"])}" data-description="{escape(o["description"])}">{escape(o["label"])}</option>' for o in prose['options'])
    preload=[f for f in tokens['type']['fonts'] if f.get('preload')]
    files={o['id']:BASE+'fonts/'+Path(o['file']).name for o in prose['options'] if o.get('file')}
    legacy={old:o['id'] for o in prose['options'] for old in o['legacy']}
    # Runs before first paint: applies a saved choice (mapping legacy IDs) and preloads only that prose font.
    script=('<script>(()=>{let p={};try{p=JSON.parse(localStorage.getItem("playbook-reader-v1"))||{}}catch{}'
            f'const files={json.dumps(files)},legacy={json.dumps(legacy)},ids={json.dumps([o["id"] for o in prose["options"]])};'
            f'let f=legacy[p.font]||p.font;if(!ids.includes(f))f={json.dumps(prose["default"])};'
            'document.documentElement.dataset.readerFont=f;'
            'if(files[f]){const l=document.createElement("link");l.rel="preload";l.as="font";l.type="font/woff2";l.crossOrigin="anonymous";l.href=files[f];document.head.append(l)}})()</script>')
    head=''.join(f'<link rel="preload" href="{BASE}fonts/{Path(f["file"]).name}" as="font" type="font/woff2" crossorigin>' for f in preload)+script
    return options,head

def design_gallery(asset_version):
    """Use real lesson sections and shared assets; do not maintain a second scene demo."""
    tokens=json.loads((DESIGN/'tokens.json').read_text())
    names=['canvas','sheet','ink','accent','scene-client','scene-runtime','scene-storage','scene-queue']
    swatches=''.join('<div class="swatch" style="--colour:var(--'+escape(name)+')"><i aria-hidden="true"></i><code>'+escape(name)+'</code></div>' for name in names)
    samples=[]
    for name,label in [('room','Data changes become a new screen state'),('the-binder','Compare blocking and one-way calls'),('the-zygote','A child writes its own memory page'),('flow','A value survives its collector')]:
        source=(WEB/'content/blend/android'/f'{name}.blend').read_text()
        scene=re.search(r'<section class="pb-figure" data-pb-flow="scene".*?</section>',source,re.S)
        if not scene: raise ValueError('Gallery scene missing: '+name)
        samples.append('<section class="demo"><h3>'+label+'</h3>'+scene[0]+'</section>')
    for name,label in [('sync-vs-async','Separate a task from its executing thread'),('queues','Follow an acknowledgement lost after processing'),('backpressure','Compare suspension with dropping pending work'),('time-and-clocks','Follow causality across a message')]:
        source=(WEB/'content/blend/engineering-fundamentals'/f'{name}.blend').read_text()
        scene=re.search(r'<section class="pb-figure" data-pb-flow="scene".*?</section>',source,re.S)
        if not scene: raise ValueError('Fundamentals gallery scene missing: '+name)
        samples.append('<section class="demo"><h3>'+label+'</h3>'+scene[0]+'</section>')
    for name,label in [('channels-and-select','Compare four channel capacities'),('bytecode','Watch an operand stack change'),('android/viewmodel','Follow a retained state owner')]:
        import diagram_models
        source=(WEB/'content/blend'/f'{name}.blend').read_text()
        scene=re.search(r'<figure class="stepper(?: [^"]*)?".*?</figure>',source,re.S)
        if not scene: raise ValueError('Gallery illustrated stepper missing: '+name)
        sample=diagram_models.enhance(steps_as_text(scene[0]),name+'.md',OUT,BASE,diagram_models.models())
        samples.append('<section class="demo"><h3>'+label+'</h3>'+sample+'</section>')
    page_walkthrough=walkthrough_gallery()
    prose=tokens['type']['prose']
    fonts=''.join(f'<figure class="specimen" style="--specimen:var(--font-{o["family"]});--measure-prose:{o["measure"]}"><figcaption><strong>{escape(o["label"])}</strong> · {escape(o["description"])}</figcaption>'
                  '<p>A suspended call gives its thread back. When the result arrives, the coroutine resumes where it stopped, with its state intact.</p></figure>' for o in prose['options'])
    page=(DESIGN/'gallery.html').read_text().replace('{{swatches}}',swatches).replace('{{fonts}}',fonts).replace('{{scenes}}',''.join(samples)).replace('{{walkthrough}}',page_walkthrough)
    for asset in ('styles.css','blend.css','theme.css','tokens.css','flow.css','sequence.css','flow.js','blend.js'):page=page.replace('"/'+asset+'"','"'+BASE+asset+'?v='+asset_version+'"')
    page=page.replace('href="/android/"','href="'+route('android.md')+'"')
    destination=OUT/'design-system';destination.mkdir(exist_ok=True)
    (destination/'index.html').write_text(page)

def walkthrough_gallery():
    """InterviewWalkthrough samples generated from Offline Sync by the same functions the lesson uses."""
    path='mobile-system-design/offline-sync.md'
    source=(ROOT/path).read_text(); tokens=MD.parse(source); names=[]; counts={}
    for i,token in enumerate(tokens):
        if token.type=='heading_open' and token.tag=='h2':
            heading=tokens[i+1].content; base=slug(heading); n=counts.get(base,0); counts[base]=n+1
            names.append((clean(heading),base if not n else f'{base}-{n}'))
    steps=walkthrough.plan(path,names)
    if not steps: raise ValueError('Gallery walkthrough sample missing: '+path)
    table=re.search(r'^### Sync strategy\n\n(\|.*?)\n\n',source,re.S|re.M)
    question=re.search(r'^(> \*\*Q:.*?)\n\n',source,re.S|re.M)
    if not table or not question: raise ValueError('Gallery walkthrough sample text missing: '+path)
    parts=[walkthrough.timeline(steps),walkthrough.try_first('clarifying'),walkthrough.decision_cards(MD.render(table[1])),walkthrough.pushbacks(MD.render(question[1]))]
    return '<section class="demo"><div class="reading-content">'+''.join(parts)+'</div></section>'

SHARED_CSS=['styles.css','blend.css','theme.css','sequence.css','learning-path.css','navigation.css','design-system/components/bundle.css']


def check_design_boundary():
    """Rulebook §20: topics contribute content only; every value lives in tokens and shared components."""
    problems=[]
    for f in sorted([*(WEB/'content').rglob('*.blend'),*(WEB/'content').rglob('*.html')]):
        text=f.read_text()
        if re.search(r'<[a-zA-Z][^<>]*\sstyle\s*=',text) or re.search(r'<style\b',text):
            problems.append(f'{f.relative_to(WEB)}: inline style in lesson content (use a declared component parameter)')
    for name in SHARED_CSS:
        css=re.sub(r'/\*.*?\*/','',(WEB/name).read_text(),flags=re.S)
        for decl in re.findall(r'[{;]\s*([a-z-]+\s*:[^;{}]*)',css):
            if re.search(r'#[0-9a-fA-F]{3,8}\b',decl):
                problems.append(f'{name}: hard-coded colour in "{decl.strip()[:60]}" (add a colour token)')
            m=re.match(r'font(-size)?\s*:\s*(.*)',decl.strip())
            if m and re.search(r'(?<![\d./])\d+(\.\d+)?px(?!\s*\))', m.group(2).split('/')[0]):
                problems.append(f'{name}: raw font size in "{decl.strip()[:60]}" (use a type token)')
    if problems: raise ValueError('Design-system boundary:\n  '+'\n  '.join(problems))


def build(skip_diagrams=False):
    check_design_boundary()
    import diagram_models
    relationship_models=diagram_models.check()
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    for directory in ['diagram-sources','diagrams','coverage']:(OUT/directory).mkdir(exist_ok=True)
    # Generate catalog from checked-in tree indexes, using guided order rather than filenames.
    # Each chapter carries its guided-reading phase, so wide trees group into sub-sections.
    catalog=json.loads((WEB/'nav-data.js').read_text().split('=',1)[1].strip().rstrip(';'))
    for tree in catalog:
        tree_index=ROOT/(tree['slug']+'.md')
        if not tree_index.exists():continue
        tree_order=[]
        section={}
        phase_groups=phases(tree['slug'])
        for heading,paths in phase_groups:
            for p in paths:
                if p not in tree_order: tree_order.append(p)
                section.setdefault(p,heading)
        # Section cross-references do not claim a chapter's place in the Topics menu either.
        for target in re.findall(r'\]\(([^)#]+\.md)\)',tree_index.read_text()):
            if target.startswith(tree['slug']+'/') and target not in tree_order:tree_order.append(target)
        actual=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/tree['slug']).rglob('*.md'))
        tree_order += [p for p in actual if p not in tree_order]
        phase_positions={heading:index for index,(heading,_) in enumerate(phase_groups)}
        catalog_positions=[phase_positions[section[p]] for p in tree_order if p in section]
        if catalog_positions != sorted(catalog_positions):
            raise ValueError(f'{tree["slug"]} Topics phases are not contiguous')
        tree['chapters']=[{'title':title(ROOT/p),'path':p,'section':section.get(p,'More chapters'),'rendered':p in PATHS} for p in tree_order]
    (OUT/'nav-data.js').write_text('window.PLAYBOOK_CATALOG = '+json.dumps(catalog,ensure_ascii=False)+';\n')
    # Include the generated catalog in the asset version. A newly rendered tree must
    # not reuse a cached catalog that still sends its chapters to GitHub.
    tokens_css=design_tokens_css().encode()
    asset_inputs=['styles.css','blend.css','sequence.css','theme.css','learning-path.css','navigation.css','app.js','blend.js','coroutines.js','lesson-model.js','design-system/components/bundle.css','design-system/components/bundle.js']
    asset_version=hashlib.sha256(tokens_css+b''.join((WEB/n).read_bytes() for n in asset_inputs)+(OUT/'nav-data.js').read_bytes()).hexdigest()[:10]
    font_options,font_head=reader_font_markup()
    template=(WEB/'templates/reader.html').read_text().replace('{{font_head}}',font_head).replace('{{font_options}}',font_options).replace('{{base}}',BASE).replace('{{asset_version}}',asset_version)
    reports=[]
    for path in PAGES:
        slug=tree_of(path); order=ORDER[slug]; is_index=path==f'{slug}.md'
        raw=(ROOT/path).read_text(); article,outline,report=render_chapter(path,raw,is_index)
        article=diagram_models.enhance(article,path,OUT,BASE,relationship_models)
        name=title(ROOT/path)
        category='Learning path' if is_index else SECTION[path]
        navigation=''
        if path in order:
            i=order.index(path); links=[]
            if i: links.append(f'<a href="{route(order[i-1])}"><small>Previous lesson</small>← {escape(title(ROOT/order[i-1]))}</a>')
            if i+1<len(order):links.append(f'<a href="{route(order[i+1])}"><small>Next lesson</small>{escape(title(ROOT/order[i+1]))} →</a>')
            else: links.append(f'<a href="{route(slug+".md")}"><small>Review the path</small>Explore {escape(TREES[slug]["title"])} phases →</a>')
            navigation='<nav class="chapter-navigation" id="continue-learning" aria-label="Continue learning">'+''.join(links)+'</nav>'
        scripts=f'<script defer src="{BASE}lesson-model.js?v={asset_version}"></script><script defer src="{BASE}coroutines.js?v={asset_version}"></script>' if path.endswith('/coroutines.md') else ''
        tree=TREES[slug]['title']
        page_kind='learning-path' if is_index else 'lesson'
        has_qa=not is_index and bool(re.search(r'\bdata-question\b|data-kind="check"',article))
        has_playground=path.endswith('/coroutines.md')
        page_fixes=[fix for fix in APPROVED_CORRECTIONS if fix['path']==path]
        has_resources=not is_index and (bool(page_fixes) or bool(re.search(r'<a\b[^>]*target="_blank"',article)))
        controls=[('content','Content')]
        if has_qa: controls.append(('qa','Q&A'))
        if has_playground: controls.append(('playground','Playground'))
        if has_resources: controls.append(('resources','Resources'))
        tabs='' if is_index else '<div class="lesson-tabs" role="tablist" aria-label="Lesson views">'+''.join(
            f'<button id="tab-{view}" role="tab" aria-selected="{str(view=="content").lower()}" aria-controls="panel-{view}" tabindex="{0 if view=="content" else -1}">{label}</button>' for view,label in controls)+'</div>'
        qa_panel='<section id="panel-qa" role="tabpanel" aria-labelledby="tab-qa" tabindex="0" hidden><div class="panel-intro"><span class="eyebrow">RETRIEVE AND REASON</span><h2>Questions & answers</h2><p>Practice questions, answers and review checklists for this chapter. Added checkpoints are labelled separately.</p></div><div id="practice-questions"></div><button class="secondary-button" data-open-tab="content">Return to your reading position</button></section>' if has_qa else ''
        playground='<section id="panel-playground" role="tabpanel" aria-labelledby="tab-playground" tabindex="0" hidden><div class="panel-intro"><span class="eyebrow">LEARN THROUGH CODE</span><h2>Experiment with overlapping waits</h2><p>Edit and run the coroutine example beside its explanation. Compare sequential and concurrent requests, then inspect the output.</p><button class="primary-button" data-go="experiment">Go to the example →</button></div></section>' if has_playground else ''
        resources='<section id="panel-resources" role="tabpanel" aria-labelledby="tab-resources" tabindex="0" hidden><div class="panel-intro"><span class="eyebrow">CONTRACTS AND DEEPER ROUTES</span><h2>Follow the source trail.</h2><p>Sources are cited where each mechanism is explained. This view gathers the same reading routes.</p></div><div id="resource-links"></div><button class="secondary-button" data-go="continue-learning">Continue learning →</button></section>' if has_resources else ''
        path_overview=''
        if is_index:
            groups=[(heading,[p for p in order if SECTION[p]==heading]) for heading,_ in phases(slug)]
            groups=[(heading,paths) for heading,paths in groups if paths]
            hero=f'<div class="lesson-hero path-hero"><span class="eyebrow">{escape(tree.upper())} / LEARNING PATH</span><h1>{escape(name)}</h1><p>{escape(intro(path))}</p><ul class="path-facts" aria-label="Learning path summary"><li>{len(groups)} phases</li><li>{len(order)} chapters</li><li>Beginner to Staff</li></ul><div class="path-actions"><a class="primary-button" href="{route(order[0])}">Start with {escape(title(ROOT/order[0]))} →</a><a class="secondary-button" href="#path-phases">Choose a phase</a></div></div>'
            cards=[]
            for index,(heading,paths) in enumerate(groups,1):
                label=re.sub(r'^Phase \d+\s*[—–-]\s*','',heading)
                target=route(paths[0]) if slug=='engineering-fundamentals' else '#'+slug_heading(heading)
                action='Start this phase' if slug=='engineering-fundamentals' else 'View sequence'
                cards.append(f'<li><a href="{target}"><span class="phase-number">Phase {index}</span><strong>{escape(label)}</strong><span class="phase-count">{len(paths)} {"chapter" if len(paths)==1 else "chapters"} · {action} →</span></a></li>')
            path_overview='<section class="path-overview" id="path-phases" aria-labelledby="path-phases-title"><h2 id="path-phases-title">Choose your next phase</h2><p>Follow the phases in order, or use the checkpoints in the full sequence below to find your starting point.</p><ol class="path-phase-grid">'+''.join(cards)+'</ol></section>'
        elif report['layout']=='walkthrough':
            hero=f'<div class="lesson-hero"><span class="eyebrow">{escape(tree.upper())} · INTERVIEW WALKTHROUGH</span><h1>{escape(name)}</h1><p>{escape(intro(path))}</p><div class="lesson-meta"><span id="reading-time" data-pacing>{escape(report['pacing'])}</span><button id="bookmark" class="text-button" aria-pressed="false">☆ Save lesson</button></div></div>'
        else:
            hero=f'<div class="lesson-hero"><span class="eyebrow">{escape(tree.upper())} · BEGINNER TO STAFF</span><h1>{escape(name)}</h1><p>{escape(intro(path))}</p><div class="lesson-meta"><span id="reading-time">Read at your pace · experiments extra</span><button id="bookmark" class="text-button" aria-pressed="false">☆ Save lesson</button></div></div>'
        values={'title':escape(name),'description':escape(intro(path)),'tree_title':escape(tree),'tree_route':route(f'{slug}.md'),'tree_eyebrow':escape(tree.upper()),'article':article,'outline':outline,'source':path,'source_url':SOURCE_ROOT+path,'category':escape(category),'chapter_navigation':navigation,'lesson_scripts':scripts,'playground_panel':playground,'page_kind':page_kind,'page_label':'learning path' if is_index else 'lesson','page_hero':hero,'page_tabs':tabs,'path_overview':path_overview,'qa_panel':qa_panel,'resources_panel':resources,'correction_history':correction_note(page_fixes),'outline_label':'ON THIS PATH' if is_index else 'ON THIS PAGE','content_semantics':'role="region" aria-label="Learning path"' if is_index else 'role="tabpanel" aria-labelledby="tab-content"'}
        html=template
        for key,value in values.items():html=html.replace('{{'+key+'}}',value)
        if re.search(r'\{\{[a-z_]+\}\}',html):raise ValueError('Unexpanded page template')
        destination=OUT/route(path)[len(BASE):].strip('/')/'index.html';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(html)
        report['url']=route(path);reports.append(report)
        if path=='kotlin.md':(OUT/'index.html').write_text(html)
    home=(WEB/'templates/home.html').read_text().replace('{{base}}',BASE).replace('{{version}}',asset_version).replace('{{android_count}}',str(len(ORDER['android']))).replace('{{kotlin_count}}',str(len(ORDER['kotlin']))).replace('{{fundamentals_count}}',str(len(ORDER['engineering-fundamentals'])))
    (OUT/'index.html').write_text(home)
    (OUT/'.nojekyll').touch()
    for name in ['styles.css','blend.css','sequence.css','theme.css','learning-path.css','navigation.css','app.js','blend.js','coroutines.js','lesson-model.js']:
        shutil.copy2(WEB/name,OUT/name)
    # The design system is the source for tokens, the diagram runtime and the self-hosted fonts.
    (OUT/'tokens.css').write_bytes(tokens_css)
    shutil.copy2(DESIGN/'components/bundle.css',OUT/'flow.css')
    shutil.copy2(DESIGN/'components/bundle.js',OUT/'flow.js')
    shutil.copytree(WEB/'fonts',OUT/'fonts')
    for font in (DESIGN/'fonts').glob('*.woff2'): shutil.copy2(font,OUT/'fonts'/font.name)
    # Each bundled family travels with its SIL Open Font License and provenance.
    shutil.copytree(DESIGN/'fonts/licenses',OUT/'fonts/licenses'); shutil.copy2(DESIGN/'fonts/README.md',OUT/'fonts/README.md')
    design_gallery(asset_version)
    # Rulebook §20 "Designed visuals only": no page may show a rendered Mermaid picture.
    mermaid_pages=sorted(str(f.relative_to(OUT)) for f in OUT.rglob('*.html') if re.search(r'<img data-(original|teaching)-diagram=',f.read_text()))
    if mermaid_pages:
        # Local work in progress only (dev.py build --pending); the gate and CI never set this.
        if os.environ.get('WEBSITE_PENDING_FIGURES')=='1': print(f'PENDING figures (not publishable): {len(mermaid_pages)} pages still show Mermaid')
        else: raise ValueError(f'Rendered Mermaid pictures remain (add FigureMap models): {mermaid_pages}')
    if set(FIGURES)-FIGURES_USED: raise ValueError(f'Figure models without a matching original diagram: {sorted(set(FIGURES)-FIGURES_USED)}')
    (OUT/'coverage/pages.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
    (OUT/'coverage/diagram-sources.json').write_text(json.dumps({p.stem:p.read_text() for p in sorted((OUT/'diagram-sources').glob('*.mmd'))},ensure_ascii=False,indent=2)+'\n')
    shutil.copy2(WEB/'content/illustrated-stepper-coverage.json',OUT/'coverage/illustrated-steppers.json')
    (OUT/'coverage/corrections.json').write_text(json.dumps(APPROVED_CORRECTIONS,ensure_ascii=False,indent=2)+'\n')
    trees='; '.join(f'{TREES[s]["title"]}: {len(ORDER[s])} chapters + learning path' for s in TREES)
    print(f'Rendered {trees}; {sum(r["original_sections"] for r in reports)} source sections; {sum(r["code_blocks"] for r in reports)} code/diagram blocks; {len(APPROVED_CORRECTIONS)} of {len(ALL_CORRECTIONS)} proposed corrections approved and applied.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-diagrams',action='store_true',help='do not render Mermaid diagrams to SVG')
    args=parser.parse_args()
    import check_review_data
    check_review_data.check()
    import check_completion
    check_completion.check()
    import check_illustrated_coverage
    check_illustrated_coverage.check()
    import check_scene_routes
    check_scene_routes.check()
    build(args.skip_diagrams)
    # Never publish a build that dropped original content.
    import check_preservation
    sys.exit(check_preservation.main())
