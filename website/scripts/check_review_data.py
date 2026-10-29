#!/usr/bin/env python3
"""Check triage totals, exact proposed replacements, and the read-only Kotlin and Android snapshot."""
from collections import Counter
from pathlib import Path
import hashlib, json, re

ROOT = Path(__file__).resolve().parents[2]
VERDICTS = ('Approve', 'Approve with edit', 'Reject')


def check():
    review = ROOT/'website/reviews'
    triage = (review/'corrections-triage.md').read_text()
    totals, ids, edited = Counter(), set(), set()
    for chapter in re.split(r'^## ', triage, flags=re.M)[1:]:
        rows = re.findall(r'^\| ([A-Z]+\d+)(?: \(new\))? \| (.+)$', chapter, re.M)
        if not rows:
            continue
        actual = Counter()
        for row_id, row in rows:
            if row_id in ids:
                raise ValueError(f'Duplicate triage ID: {row_id}')
            ids.add(row_id)
            verdict = re.search(r'\| (Approve with edit|Approve|Reject) \|', '| '+row)
            if not verdict:
                raise ValueError(f'Unknown verdict: {row_id}')
            actual[verdict[1]] += 1
            if verdict[1] == 'Approve with edit': edited.add(row_id)
        summary = re.search(r'^\*\*Summary:\*\* (.+)', chapter, re.M)
        if not summary:
            raise ValueError('Missing chapter summary: '+chapter.splitlines()[0])
        declared = Counter()
        for label, expression in [('Approve',r'(\d+) approve(?! with)'),('Approve with edit',r'(\d+) approve with edit'),('Reject',r'(\d+) reject')]:
            match = re.search(expression, summary[1])
            declared[label] = int(match[1]) if match else 0
        if actual != declared:
            raise ValueError(f'Summary mismatch in {chapter.splitlines()[0]}: {dict(actual)} != {dict(declared)}')
        totals.update(actual)
    for label in VERDICTS:
        count = re.search(r'^\| '+re.escape(label)+r' \| (\d+)',triage,re.M)
        if not count or int(count[1]) != totals[label]:
            raise ValueError('Overview mismatch: '+label)
    total = re.search(r'^\| \*\*Total\*\* \| \*\*(\d+)\*\*',triage,re.M)
    if not total or int(total[1]) != sum(totals.values()):
        raise ValueError('Triage total mismatch')
    proposals = json.loads((review/'corrections-with-edits.json').read_text())
    if {fix['id'] for fix in proposals} != edited:
        raise ValueError('Amended proposal IDs differ from the triage')
    prose = (review/'corrections-with-edits.md').read_text()
    occupied = {}
    for fix in proposals:
        raw = (ROOT/fix['path']).read_text()
        if raw.count(fix['old']) != 1:
            raise ValueError('Original must occur once: '+fix['id'])
        start = raw.index(fix['old']);end = start+len(fix['old'])
        for earlier_start, earlier_end in occupied.setdefault(fix['path'],[]):
            if start < earlier_end and earlier_start < end:
                raise ValueError('Overlapping proposal: '+fix['id'])
        occupied[fix['path']].append((start,end))
        if fix['old'].strip() not in prose or fix['new'].strip() not in prose:
            raise ValueError('Markdown/JSON wording differs: '+fix['id'])
    snapshot = json.loads((ROOT/'source-snapshot.json').read_text())
    verified = 0
    for tree in ('kotlin', 'android', 'engineering-fundamentals', 'computer-science'):
        hashes = snapshot[tree+'_sha256']
        actual_paths = {tree+'.md'} | {str(p.relative_to(ROOT)) for p in (ROOT/tree).rglob('*.md')}
        if actual_paths != set(hashes):
            raise ValueError(tree+' snapshot file set changed')
        for path, digest in hashes.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
                raise ValueError('Read-only source changed: '+path)
        verified += len(hashes)
    print(f'Review data: {sum(totals.values())} triage rows, {len(edited)} amended IDs / {len(proposals)} replacements, {verified} source hashes verified.')
    return totals


if __name__ == '__main__':
    check()
