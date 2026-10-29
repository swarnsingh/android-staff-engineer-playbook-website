#!/usr/bin/env python3
"""One entry point for routine website work, with short summaries instead of long logs.

    python3 website/tools/dev.py build              # local build; skips only the publication gate
    python3 website/tools/dev.py figures            # check every FigureMap model; list all problems
    python3 website/tools/dev.py frames             # in Chrome: figures framed, nothing scrolls, labels fit (after build)
    python3 website/tools/dev.py audit NAME         # run the six browser audits into website/reviews/NAME/
    python3 website/tools/dev.py gate NAME          # point the gate at reviews/NAME, refresh fingerprints, real build
    python3 website/tools/dev.py ci                 # unit tests, docs check and browser-script syntax, as CI runs them

Full output goes to website/.cache/logs/; only a summary is printed. Use the Python
environment that has website/requirements.txt installed (set PYTHON to override).
"""
from pathlib import Path
import collections, glob, json, os, socket, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'website'
LOGS = WEB / '.cache/logs'
PY = os.environ.get('PYTHON', sys.executable)
PROJECT_BASE = '/android-staff-engineer-playbook-website/'


def run(name, cmd, env=None, cwd=ROOT):
    """Run a step, keep its full log on disk and return (ok, last lines)."""
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f'{name}.log'
    result = subprocess.run(cmd, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True)
    log.write_text(result.stdout + result.stderr)
    lines = [l for l in (result.stdout + result.stderr).splitlines() if l.strip() and not l.strip().startswith('ok ')]
    return result.returncode == 0, lines, log


def report(name, ok, lines, log, keep=3):
    print(f'{"PASS" if ok else "FAIL"}  {name}')
    for line in ((lines[-keep:] if keep else []) if ok else lines[-12:]):
        print('      ' + line[:200])
    if not ok:
        print(f'      full log: {log.relative_to(ROOT)}')
    return ok


def build(base='/'):
    """The iteration build: every check except the fingerprint gate, which needs fresh audit evidence."""
    code = ('import sys,runpy;sys.path.insert(0,"website/scripts");import check_completion;'
            'check_completion.check=lambda *a,**k:None;sys.argv=["build.py"];'
            'runpy.run_path("website/scripts/build.py",run_name="__main__")')
    return report('build (gate skipped)', *run('build', [PY, '-c', code], {'SITE_BASE': base}))


def figures():
    sys.path.insert(0, str(WEB / 'scripts'))
    import figure_maps as fm
    problems, count = [], 0
    for source in sorted((WEB / 'content/diagram-models/figures').glob('*.json')):
        for row in json.loads(source.read_text()):
            count += 1
            try:
                fm.check(row)
                fm.render(row, 'source', 'original')
            except Exception as error:
                problems.append(f'{source.name} {row.get("path")} {row.get("diagram")}: {error}')
    print(f'{"PASS" if not problems else "FAIL"}  figures: {count} models, {len(problems)} problems')
    for p in problems:
        print('      ' + p[:220])
    return not problems


def puppeteer_dir():
    found = os.environ.get('PUPPETEER_DIR') or next(iter(sorted(glob.glob(str(Path.home() / '.npm/_npx/*/node_modules/puppeteer')))), None)
    if not found:
        sys.exit('No puppeteer found. Run `npx --yes puppeteer browsers install chrome-headless-shell` once, or set PUPPETEER_DIR.')
    return found


def summarize(folder):
    ok = True
    browser = json.loads((folder / 'browser.json').read_text())
    bad = [p for p in browser['pages'] if not p['ok']]
    reasons = collections.Counter()
    for p in bad:
        for m in p['preservation']['problems']:
            reasons[m[:100]] += 1
        for s in p.get('sceneChecks', []) + p.get('illustratedChecks', []):
            if not s.get('ok'):
                reasons['scene: ' + str(s.get('problems'))[:100]] += 1
        for layout in p.get('layouts', []):
            if layout.get('overflow') or layout.get('clipped') or layout.get('smallLabels'):
                reasons[f'layout at {layout.get("width")}px {layout.get("view")}'] += 1
        if p.get('runtimeErrors'):
            reasons['runtime error'] += 1
    code = [c for p in browser['pages'] for c in p.get('codeChecks', [])]
    pairs = [c for p in browser['pages'] for v in p['preservation']['views'] for c in v.get('pairChecks', [])]
    print(f'{"PASS" if not bad else "FAIL"}  browser: {len(browser["pages"]) - len(bad)}/{len(browser["pages"])} pages; '
          f'code {sum(c["ok"] for c in code)}/{len(code)}; Q&A pairs {sum(c["ok"] for c in pairs)}/{len(pairs)}')
    for reason, n in reasons.most_common(8):
        print(f'      {n} × {reason}')
    ok &= not bad
    for name in ['binder', 'motion', 'refinement', 'ux', 'qa-tampering']:
        r = json.loads((folder / f'{name}.json').read_text())
        checks = r.get('checks') or r.get('results') or []
        failed = [c for c in checks if not c.get('ok', True)] + list(r.get('problems') or [])
        print(f'{"PASS" if r.get("done") and not failed else "FAIL"}  {name}: {len(checks) - len(failed)}/{len(checks)}')
        ok &= bool(r.get('done')) and not failed
    return ok


def audit(name):
    """Full build with diagrams, an instrumented QA copy, then all six audits headlessly (about 5 minutes)."""
    folder = WEB / 'reviews' / name
    if not build('/'):
        return False
    qa = WEB / '.cache/browser-qa'
    if not report('prepare QA copy', *run('prepare', [PY, 'website/tools/prepare_browser_audit.py', str(qa)])):
        return False
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    server = subprocess.Popen([PY, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', str(qa)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        ok, lines, log = run('audit', ['node', str(WEB / 'tools/run_audits.mjs'), puppeteer_dir(), f'http://127.0.0.1:{port}/', str(folder)])
        report('six browser audits', ok, lines, log, keep=6)
    finally:
        server.terminate()
    kotlin = sorted((WEB / 'reviews').glob('*/kotlin-validation.json'), key=lambda p: p.stat().st_mtime)
    if not (folder / 'kotlin-validation.json').exists() and kotlin:
        # Kotlin fragment evidence carries over; the gate re-verifies its hashes against current content.
        (folder / 'kotlin-validation.json').write_text(kotlin[-1].read_text())
    print(f'      evidence: {folder.relative_to(ROOT)}  (add REPORT.md before running `gate {name}`)')
    return summarize(folder)


def gate(name):
    folder = WEB / 'reviews' / name
    if not (folder / 'REPORT.md').exists():
        sys.exit(f'{folder.relative_to(ROOT)}/REPORT.md is missing: write the evidence report first.')
    code = ('import json,sys;sys.path.insert(0,"website/scripts");import check_completion;'
            'p="website/reviews/completion/validation.json";d=json.load(open(p));'
            f'd["ux_review"]="website/reviews/{name}/REPORT.md";d["ux_review_date"]="{time.strftime("%Y-%m-%d")}";'
            'd["fingerprints"]=check_completion.fingerprints();'
            'open(p,"w").write(json.dumps(d,indent=2,ensure_ascii=False)+"\\n")')
    if not report('refresh fingerprints', *run('fingerprints', [PY, '-c', code])):
        return False
    return report('real build with publication gate', *run('gate-build', [PY, 'website/scripts/build.py'], {'SITE_BASE': PROJECT_BASE}))


def frames():
    """Real-browser layout check of every built chapter page at desktop width."""
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    server = subprocess.Popen([PY, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', str(WEB / 'dist')],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        ok, lines, log = run('frames', ['node', str(WEB / 'tools/frame_check.mjs'), puppeteer_dir(), f'http://127.0.0.1:{port}/', str(WEB / 'dist/nav-data.js')])
    finally:
        server.terminate()
    result = json.loads(lines[-1]) if ok and lines else None
    clean = bool(result) and not result['kinds']
    print(f'{"PASS" if clean else "FAIL"}  frames: ' + (f'{result["pages"]} pages, {result["figs"]} figures, {result["maps"]} maps, {result["labels"]} labels; problems {result["kinds"] or "none"}' if result else f'see {log.relative_to(ROOT)}'))
    for line in (result or {}).get('sample', []):
        print('      ' + line)
    return clean


def ci():
    ok = report('website unit tests', *run('tests-website', [PY, '-m', 'unittest', 'discover', '-s', 'website/scripts', '-p', 'test_*.py']))
    ok &= report('docs unit tests', *run('tests-docs', [PY, '-m', 'unittest', 'discover', '--start-directory', 'scripts', '--pattern', 'test_*.py']))
    ok &= report('docs check', *run('docs', [PY, 'scripts/check_docs.py']), keep=0)
    scripts = ['website/scripts/browser_preservation.js', 'website/app.js', 'website/blend.js',
               'website/design-system/components/bundle.js', *sorted(str(p.relative_to(ROOT)) for p in (WEB / 'tools').glob('*.js'))]
    bad = [s for s in scripts if subprocess.run(['node', '--check', s], cwd=ROOT, capture_output=True).returncode]
    print(f'{"PASS" if not bad else "FAIL"}  browser-script syntax: {len(scripts) - len(bad)}/{len(scripts)}' + ('' if not bad else f' failing {bad}'))
    return ok and not bad


if __name__ == '__main__':
    command, args = (sys.argv[1] if len(sys.argv) > 1 else ''), sys.argv[2:]
    actions = {'build': lambda: build(), 'figures': figures, 'frames': frames, 'ci': ci,
               'audit': lambda: audit(args[0]) if args else sys.exit('usage: dev.py audit REVIEW-FOLDER-NAME'),
               'gate': lambda: gate(args[0]) if args else sys.exit('usage: dev.py gate REVIEW-FOLDER-NAME')}
    if command not in actions:
        sys.exit(__doc__)
    sys.exit(0 if actions[command]() else 1)
