"""Interview-walkthrough layout for system-design chapters (website/design-system/components/InterviewWalkthrough).

Everything is derived from the chapter's own numbered H2 headings, their `(~N min)` hints, its trade-off
tables and its `> **Q: …**` follow-ups. Original text is never moved, hidden or retyped: tables and
follow-ups keep their markup and gain only attributes and a labelled added tag. A chapter uses this layout
only when website/content/walkthrough-layout.json lists it and its headings match; otherwise the build
renders the normal chapter layout.
"""
from pathlib import Path
from html import escape, unescape
import json, re

WEB = Path(__file__).resolve().parents[1]
MANIFEST = WEB / 'content/walkthrough-layout.json'
# Headings arrive with emphasis markers removed, so "(~5 min)" reads "(5 min)"; accept both.
NUMBERED = re.compile(r'^(\d+)\.\s+(.+?)(?:\s*\(~?\s*(\d+)\s*min\))?\s*$')
# Section roles, matched on the heading text after its number; the first match wins.
ROLES = [('requirements', r'\brequirements?\b'), ('clarifying', r'\bclarif'), ('api', r'\bapi\b'),
         ('tradeoffs', r'\btrade-?offs?\b'), ('followups', r'\bfollow-?up')]
# Try-first prompts go before these sections, in this order.
TRY_FIRST = ('requirements', 'clarifying', 'api')
MIN_SECTIONS = 8


def manifest():
    return json.loads(MANIFEST.read_text())


def listed(path):
    return any(g['layout'] == 'walkthrough' and path in g['chapters'] for g in manifest()['groups'])


def plan(path, names):
    """Steps for a listed chapter, or None when its headings do not follow the numbered interview template.

    `names` are the chapter's H2 headings (markup removed) with their anchors, in order.
    """
    if not listed(path):
        return None
    steps = []
    for name, anchor in names:
        match = NUMBERED.match(name)
        if not match:
            continue  # unnumbered extras keep their place and are simply not interview steps
        number, title, minutes = int(match[1]), match[2].strip(), match[3]
        role = next((key for key, pattern in ROLES if re.search(pattern, title, re.I)), None)
        if role and any(s['role'] == role for s in steps):
            role = None
        steps.append({'number': number, 'title': title, 'minutes': int(minutes) if minutes else None,
                      'anchor': anchor, 'name': name, 'role': role})
    numbers = [s['number'] for s in steps]
    if len(steps) < MIN_SECTIONS or numbers != list(range(1, len(steps) + 1)):
        return None
    if not any(s['minutes'] for s in steps) or not any(s['role'] == 'requirements' for s in steps):
        return None
    return steps


def timeline(steps):
    """The interview timeline: a proportional bar of the timed steps, then every step as a linked list."""
    timed = [s for s in steps if s['minutes']]
    # The minutes are a declared component parameter (like the teaching timeline's data-at), applied as a CSS variable.
    bar = ''.join(f'<li data-step="{s["number"]}" style="--minutes:{s["minutes"]}"><span>{s["number"]}</span></li>' for s in timed)
    items = ''.join(
        f'<li data-step="{s["number"]}"><a href="#section-{s["anchor"]}"><span class="wt-number">{s["number"]}</span>'
        f'<span class="wt-title">{escape(s["title"])}</span>'
        f'<span class="wt-time">{"~" + str(s["minutes"]) + " min" if s["minutes"] else "No time hint"}</span></a></li>'
        for s in steps)
    return ('<nav class="wt-timeline" id="interview-timeline" aria-labelledby="wt-heading">'
            '<p class="wt-heading" id="wt-heading">Interview timeline</p>'
            f'<p class="wt-note">Built from the chapter\'s {len(steps)} numbered sections. Time hints come from its headings; '
            'they are guidance for pacing, not a schedule.</p>'
            f'<ol class="wt-steps">{items}</ol></nav>'
            # The bar is a pacing picture only; the list above is the accessible version.
            f'<div class="wt-progress" aria-hidden="true"><ol class="wt-bar">{bar}</ol>'
            '<p class="wt-now"><span class="wt-now-label">Now</span> <span class="wt-now-text"></span></p></div>')


def try_first(role):
    """Added practice prompt before an answer section. The chapter's answer below stays fully visible."""
    entry = manifest()['try_first'][role]
    covers = ''.join(f'<li>{escape(c)}</li>' for c in entry['covers'])
    return (f'<div class="blend" data-kind="tryfirst" data-role="{role}"><span class="blend-label">Try first</span>'
            f'<p class="tf-question">{escape(entry["question"])}</p><p>{escape(entry["prompt"])}</p>'
            f'<details class="tf-hints"><summary>What a strong answer covers</summary><ul>{covers}</ul></details>'
            '<p class="tf-next">Then compare with the chapter\'s answer below.</p></div>')


def _cells(row):
    return re.findall(r'<(t[hd])([^>]*)>(.*?)</t[hd]>', row, re.S)


def decision_cards(html):
    """Trade-off tables become decision cards: same table, same cells, labelled for a card layout."""
    def text(cell):
        return re.sub(r'<[^>]+>', '', unescape(cell)).strip()

    def table(match):
        head = re.search(r'<thead>(.*?)</thead>', match[0], re.S)
        body = re.search(r'<tbody>(.*?)</tbody>', match[0], re.S)
        if not head or not body:
            return match[0]
        labels = [text(c[2]) for c in _cells(head[1])]
        verdict = next((i for i, l in enumerate(labels) if l.lower() in ('verdict', 'use when')), None)

        bold = lambda r: r.lstrip().startswith('<td>') and r.lstrip()[4:].lstrip().startswith('<strong>')
        rows_html = re.findall(r'<tr>(.*?)</tr>', body[1], re.S)
        # The chapter marks its choice in bold when only one option is bold (some tables bold every option),
        # or with a verdict that starts "Pick".
        single_bold = sum(map(bold, rows_html)) == 1

        def row(r):
            cells = re.findall(r'<td([^>]*)>(.*?)</td>', r[1], re.S)
            chosen = bool(cells) and ((single_bold and bold(r[1]))
                                      or (verdict is not None and verdict < len(cells) and text(cells[verdict][1]).lower().startswith('pick')))
            out = []
            for i, (attrs, content) in enumerate(cells):
                kind = 'option' if i == 0 else ('verdict' if i == verdict else 'detail')
                label = labels[i] if i < len(labels) else ''
                out.append(f'<td{attrs} role="cell" data-label="{escape(label)}" data-cell="{kind}">{content}</td>')
            return f'<tr role="row"{" data-chosen" if chosen else ""}>' + '\n'.join(out) + '</tr>'

        header = re.sub(r'<th([^>]*)>', r'<th\1 role="columnheader">', head[0]).replace('<tr>', '<tr role="row">')
        rows = re.sub(r'<tr>(.*?)</tr>', row, body[1], flags=re.S)
        return f'<table class="decision-cards" role="table" data-columns="{len(labels)}">{header}<tbody>{rows}</tbody></table>'
    return re.sub(r'<table>.*?</table>', table, html, flags=re.S)


PUSHBACK_TAG = ('<div class="blend" data-kind="pushback"><span class="blend-label">Interviewer pushes back</span>'
                '<span class="pushback-hint">Answer aloud first, then read the chapter\'s reply.</span></div>')


def pushbacks(html):
    """`> **Q: …**` follow-ups become pushback checks. The question and its original answer stay visible."""
    return re.sub(r'<blockquote>(\s*<p><strong>Q:)', lambda m: '<blockquote class="pushback">' + PUSHBACK_TAG + m[1], html)
