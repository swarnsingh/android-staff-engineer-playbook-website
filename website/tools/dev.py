#!/usr/bin/env python3
"""One entry point for routine website work, with short summaries instead of long logs.

    python3 website/tools/dev.py build [--pending]  # local build; skips only the publication gate (--pending: allow unfinished figures)
    python3 website/tools/dev.py figures            # check every FigureMap model; list all problems
    python3 website/tools/dev.py frames             # in Chrome: figures framed, nothing scrolls, labels fit (after build)
    python3 website/tools/dev.py frames-phone       # automated 375px frames and labelled local scrolling
    python3 website/tools/dev.py readiness          # in Chrome: audit startup and controlled resource failures (after build)
    python3 website/tools/dev.py audit NAME         # run the six browser audits into website/reviews/NAME/
    python3 website/tools/dev.py gate NAME          # point the gate at reviews/NAME, refresh fingerprints, real build
    python3 website/tools/dev.py ci                 # unit tests, docs check and browser-script syntax, as CI runs them

Full output goes to website/.cache/logs/; only a summary is printed. Use the Python
environment that has website/requirements.txt installed (set PYTHON to override).
"""
from pathlib import Path
import glob, json, os, socket, subprocess, sys, time, traceback

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
    import static_figures as sf
    static_count=0
    for row in sf.load().values():
        static_count+=1
        try:
            source=sf.source_for(row)
            sf.validate(row,source)
            if row['kind']=='map':
                model=sf.as_map(row,source)
                fm.check(model)
                fm.render(model,'','teaching')
        except Exception as error:
            problems.append(f"static {row['path']} #{row['figure']}: {error}")
    print(f'{"PASS" if not problems else "FAIL"}  figures: {count} original models + {static_count} teaching models, {len(problems)} problems')
    for p in problems:
        print('      ' + p[:220])
    return not problems


def puppeteer_dir():
    found = os.environ.get('PUPPETEER_DIR') or next(iter(sorted(glob.glob(str(Path.home() / '.npm/_npx/*/node_modules/puppeteer')))), None)
    if not found:
        sys.exit('No puppeteer found. Run `npx --yes puppeteer browsers install chrome-headless-shell` once, or set PUPPETEER_DIR.')
    return found


def summarize(folder):
    """Summarize complete or partial evidence without hiding the original failure."""
    ok = True
    for name in ['browser', 'binder', 'motion', 'refinement', 'ux', 'qa-tampering']:
        source = folder / f'{name}.json'
        try:
            result = json.loads(source.read_text())
            if not isinstance(result, dict):
                raise ValueError('expected a result object')
            key = 'pages' if name == 'browser' else 'results' if name == 'motion' else 'checks'
            checks = result.get(key)
            if not isinstance(checks, list) or not checks or any(not isinstance(c, dict) for c in checks):
                raise ValueError(f'missing or empty {key} results; {result.get("error") or "audit incomplete"}')
            failed = [c for c in checks if c.get('ok') is not True]
            problems = result.get('problems') or []
            if not isinstance(problems, list):
                raise ValueError('expected a problems list')
            clean = (result.get('done') is True and result.get('ok', True) is True
                     and not result.get('error') and not failed and not problems)
            counts = f'{len(checks) - len(failed)}/{len(checks)}'
            if name == 'browser':
                code = [c for page in checks for c in page.get('codeChecks', [])]
                pairs = [c for page in checks for view in (page.get('preservation') or {}).get('views', [])
                         for c in view.get('pairChecks', [])]
                missing = [page for page in checks if page.get('ok') is True
                           and not isinstance(page.get('preservation'), dict)]
                clean &= not missing
                counts += (f' pages; code {sum(c.get("ok") is True for c in code)}/{len(code)}; '
                           f'Q&A pairs {sum(c.get("ok") is True for c in pairs)}/{len(pairs)}')
                print(f'{"PASS" if clean else "FAIL"}  browser: {counts}')
                for page in failed[:8]:
                    details = [str(page['error'])] if page.get('error') else []
                    details += list((page.get('preservation') or {}).get('problems', []))
                    details += [str(error) for error in page.get('runtimeErrors') or []]
                    for scene in (page.get('sceneChecks') or []) + (page.get('illustratedChecks') or []):
                        if scene.get('ok') is not True:
                            details.append('scene: ' + str(scene.get('problems')))
                    for layout in page.get('layouts') or []:
                        if layout.get('overflow') or layout.get('clipped') or layout.get('smallLabels'):
                            details.append(f'layout at {layout.get("width")}px {layout.get("view")}')
                    if not details:
                        details = ['page checks failed; see browser.json for scene/layout/code details']
                    print(f'      {page.get("href", "unknown page")}: ' + '; '.join(details))
                for page in missing[:8]:
                    print(f'      {page.get("href", "unknown page")}: missing preservation results')
            else:
                print(f'{"PASS" if clean else "FAIL"}  {name}: {counts}')
                for check in failed[:8]:
                    print(f'      {check.get("name", "check")}: '
                          f'{check.get("error") or check.get("problems") or check.get("errors") or "failed"}')
            if result.get('done') is not True:
                print('      audit incomplete')
            if result.get('error'):
                print('      ' + str(result['error']))
            for problem in problems[:8]:
                print('      ' + str(problem))
            ok &= bool(clean)
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
            print(f'FAIL  {name}: {source.name}: {error}')
            ok = False
    return ok


def audit(name):
    """Full build with diagrams, an instrumented QA copy, then all six audits headlessly (about 5 minutes)."""
    folder = WEB / 'reviews' / name
    if not build('/'):
        return False
    qa = WEB / '.cache/browser-qa'
    if not report('prepare QA copy', *run('prepare', [PY, 'website/tools/prepare_browser_audit.py', str(qa)])):
        return False
    folder.mkdir(parents=True, exist_ok=True)
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
    try:
        summary_ok = summarize(folder)
    except Exception as error:
        # Keep a formatter bug from replacing the runner's original diagnostics.
        LOGS.mkdir(parents=True, exist_ok=True)
        summary_log = LOGS / 'audit-summary.log'
        summary_log.write_text(traceback.format_exc())
        print(f'FAIL  audit summary: {error}; full log: {summary_log.relative_to(ROOT)}')
        return False
    return ok and summary_ok


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


def frames(width=1440):
    """Real-browser layout check of every built chapter page at the requested viewport width."""
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    server = subprocess.Popen([PY, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', str(WEB / 'dist')],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        ok, lines, log = run('frames' if width==1440 else 'frames-phone', ['node', str(WEB / 'tools/frame_check.mjs'), puppeteer_dir(), f'http://127.0.0.1:{port}/', str(WEB / 'dist/nav-data.js'),str(width)])
    finally:
        server.terminate()
    result = json.loads(lines[-1]) if ok and lines else None
    clean = bool(result) and not result['kinds']
    print(f'{"PASS" if clean else "FAIL"}  frames ({width}px): ' + (f'{result["pages"]} pages, {result["figs"]} figures, {result["maps"]} maps, {result["labels"]} labels; static {result.get("staticFigures",0)} figures/{result.get("staticCards",0)} cards; problems {result["kinds"] or "none"}' if result else f'see {log.relative_to(ROOT)}'))
    if result and width < 1024:
        local = result.get('scrolling', {})
        print(f'      local scrolls ({width}px): {local.get("figures", 0)} figures, {local.get("maps", 0)} relationship maps, {local.get("scenes", 0)} scenes')
    for line in (result or {}).get('sample', []):
        print('      ' + line)
    return clean


def readiness():
    """Exercise real audit startup with intact and deliberately broken inputs."""
    qa = WEB / '.cache/readiness-qa'
    if not report('prepare readiness fixtures', *run('readiness-prepare', [PY, 'website/tools/prepare_browser_audit.py', str(qa)])):
        return False
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    server = subprocess.Popen([PY, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', str(qa)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        return report('audit readiness fault injection', *run('readiness', ['node', str(WEB / 'tools/check_audit_readiness.mjs'),
                      puppeteer_dir(), f'http://127.0.0.1:{port}/', str(WEB / '.cache/audit-readiness.json')]))
    finally:
        server.terminate()


def ci():
    ok = report('website unit tests', *run('tests-website', [PY, '-m', 'unittest', 'discover', '-s', 'website/scripts', '-p', 'test_*.py']))
    ok &= report('Computer Science Java compilation and behaviour', *run('cs-code', [PY, 'website/scripts/check_cs_code.py']))
    ok &= report('docs unit tests', *run('tests-docs', [PY, '-m', 'unittest', 'discover', '--start-directory', 'scripts', '--pattern', 'test_*.py']))
    ok &= report('docs check', *run('docs', [PY, 'scripts/check_docs.py']), keep=0)
    scripts = ['website/scripts/browser_preservation.js', 'website/app.js', 'website/blend.js',
               'website/design-system/components/bundle.js', *sorted(str(p.relative_to(ROOT)) for pattern in ('*.js', '*.mjs') for p in (WEB / 'tools').glob(pattern))]
    bad = [s for s in scripts if subprocess.run(['node', '--check', s], cwd=ROOT, capture_output=True).returncode]
    print(f'{"PASS" if not bad else "FAIL"}  browser-script syntax: {len(scripts) - len(bad)}/{len(scripts)}' + ('' if not bad else f' failing {bad}'))
    return ok and not bad


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command, args = (argv[0] if argv else ''), argv[1:]
    if command == 'build' and '--pending' in args:
        os.environ['WEBSITE_PENDING_FIGURES'] = '1'  # local only: other chapters' figures may still be missing
    actions = {'build': lambda: build(), 'figures': figures, 'frames': frames, 'frames-phone': lambda: frames(375), 'readiness': readiness, 'ci': ci,
               'audit': lambda: audit(args[0]) if args else sys.exit('usage: dev.py audit REVIEW-FOLDER-NAME'),
               'gate': lambda: gate(args[0]) if args else sys.exit('usage: dev.py gate REVIEW-FOLDER-NAME')}
    if command not in actions:
        sys.exit(__doc__)
    return 0 if actions[command]() else 1


if __name__ == '__main__':
    sys.exit(main())
