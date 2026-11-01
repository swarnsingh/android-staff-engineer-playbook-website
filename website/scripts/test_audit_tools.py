"""Audit failures must remain diagnosable and produce failing command exit codes."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
DEV_PATH = ROOT / 'website/tools/dev.py'
spec = importlib.util.spec_from_file_location('website_dev', DEV_PATH)
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)
NAMES = ('browser', 'binder', 'motion', 'refinement', 'ux', 'qa-tampering')


def evidence():
    rows = {name: {'done': True, 'ok': True, 'checks': [{'name': 'fixture', 'ok': True}]}
            for name in NAMES}
    rows['browser'] = {'done': True, 'pages': [{
        'href': '/lesson/', 'ok': True,
        'preservation': {'problems': [], 'views': [{'pairChecks': [{'ok': True}]}]},
        'codeChecks': [{'ok': True}],
    }]}
    rows['motion'] = {'done': True, 'ok': True, 'results': [{'name': 'motion', 'ok': True}]}
    return rows


class AuditSummaryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.rows = evidence()
        self.write()

    def write(self):
        for name, result in self.rows.items():
            (self.folder / f'{name}.json').write_text(json.dumps(result))

    def summary(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            ok = dev.summarize(self.folder)
        return ok, output.getvalue()

    def test_success(self):
        ok, output = self.summary()
        self.assertTrue(ok)
        self.assertIn('Q&A pairs 1/1', output)
        self.assertNotIn('FAIL', output)

    def test_early_page_failure_keeps_original_error_without_preservation(self):
        self.rows['browser']['pages'].append({
            'href': '/engineering-fundamentals/', 'ok': False,
            'error': 'Error: Page readiness timed out',
        })
        self.write()
        ok, output = self.summary()
        self.assertFalse(ok)
        self.assertIn('browser: 1/2 pages', output)
        self.assertIn('/engineering-fundamentals/: Error: Page readiness timed out', output)
        self.assertIn('PASS  qa-tampering', output)

    def test_runtime_error_keeps_its_text(self):
        self.rows['browser']['pages'] = [{
            'href': '/lesson/', 'ok': False, 'runtimeErrors': ['TypeError: null click'],
        }]
        self.write()
        self.assertIn('TypeError: null click', self.summary()[1])

    def test_scene_and_layout_diagnostics_remain_visible(self):
        page = self.rows['browser']['pages'][0]
        page.update(ok=False, sceneChecks=[{'ok': False, 'problems': ['node clipped']}],
                    layouts=[{'width': 390, 'view': 'qa', 'overflow': True}])
        self.write()
        ok, output = self.summary()
        self.assertFalse(ok)
        self.assertIn('node clipped', output)
        self.assertIn('layout at 390px qa', output)

    def test_missing_file_is_failure_and_other_audits_are_summarized(self):
        (self.folder / 'browser.json').unlink()
        ok, output = self.summary()
        self.assertFalse(ok)
        self.assertIn('browser.json', output)
        self.assertIn('PASS  qa-tampering', output)

    def test_invalid_json_is_failure(self):
        (self.folder / 'browser.json').write_text('{broken')
        self.assertFalse(self.summary()[0])

    def test_incomplete_empty_and_top_level_errors_fail(self):
        for change in ({'done': False}, {'pages': []}, {'error': 'manifest fetch failed'}, {'ok': False}):
            with self.subTest(change=change):
                self.rows = evidence()
                self.rows['browser'].update(change)
                self.write()
                self.assertFalse(self.summary()[0])

    def test_successful_page_missing_preservation_fails_closed(self):
        del self.rows['browser']['pages'][0]['preservation']
        self.write()
        ok, output = self.summary()
        self.assertFalse(ok)
        self.assertIn('missing preservation', output)

    def test_auxiliary_failed_check_overrides_top_level_success(self):
        self.rows['binder']['checks'][0]['ok'] = False
        self.rows['binder']['checks'][0]['problems'] = ['binder overflow']
        self.write()
        ok, output = self.summary()
        self.assertFalse(ok)
        self.assertIn('binder overflow', output)

    def test_auxiliary_top_level_failure_overrides_passing_checks(self):
        self.rows['motion']['ok'] = False
        self.write()
        self.assertFalse(self.summary()[0])

    def test_auxiliary_problems_are_not_hidden(self):
        self.rows['binder']['problems'] = ['unexpected extra panel']
        self.write()
        ok, output = self.summary()
        self.assertFalse(ok)
        self.assertIn('unexpected extra panel', output)


class AuditCommandTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patches = [patch.object(dev, 'ROOT', self.root),
                        patch.object(dev, 'WEB', self.root / 'website'),
                        patch.object(dev, 'LOGS', self.root / 'website/.cache/logs'),
                        patch.object(dev, 'build', return_value=True),
                        patch.object(dev, 'puppeteer_dir', return_value='/fake/puppeteer'),
                        patch.object(dev.time, 'sleep')]
        self.mocks = [p.start() for p in self.patches]
        self.addCleanup(lambda: [p.stop() for p in reversed(self.patches)])
        self.folder = dev.WEB / 'reviews/test'
        self.folder.mkdir(parents=True)
        for name, result in evidence().items():
            (self.folder / f'{name}.json').write_text(json.dumps(result))

    def invoke(self, runner_ok=True, summary=None):
        log = dev.LOGS / 'audit.log'
        def run(name, *args, **kwargs):
            return (runner_ok if name == 'audit' else True), ['original runner diagnostic'], log
        output = io.StringIO()
        with patch.object(dev, 'run', side_effect=run), patch.object(dev.subprocess, 'Popen') as server, contextlib.redirect_stdout(output):
            if summary is None:
                status = dev.main(['audit', 'test'])
            else:
                with patch.object(dev, 'summarize', side_effect=summary):
                    status = dev.main(['audit', 'test'])
        server.return_value.terminate.assert_called_once()
        return status, output.getvalue()

    def test_success_returns_zero(self):
        self.assertEqual(self.invoke()[0], 0)

    def test_runner_failure_cannot_be_overridden_by_old_passing_json(self):
        status, output = self.invoke(runner_ok=False)
        self.assertEqual(status, 1)
        self.assertIn('original runner diagnostic', output)

    def test_early_page_failure_returns_nonzero(self):
        (self.folder / 'browser.json').write_text(json.dumps({
            'done': True, 'pages': [{'href': '/bad/', 'ok': False, 'error': 'readiness timeout'}],
        }))
        status, output = self.invoke()
        self.assertEqual(status, 1)
        self.assertIn('/bad/: readiness timeout', output)

    def test_summary_crash_keeps_runner_error_and_writes_traceback(self):
        status, output = self.invoke(runner_ok=False, summary=RuntimeError('summary exploded'))
        self.assertEqual(status, 1)
        self.assertIn('original runner diagnostic', output)
        self.assertIn('summary exploded', output)
        self.assertIn('RuntimeError: summary exploded', (dev.LOGS / 'audit-summary.log').read_text())

    def test_cli_propagates_failure_exit_status(self):
        code = (f'import importlib.util,sys; s=importlib.util.spec_from_file_location("dev",{str(DEV_PATH)!r});'
                'd=importlib.util.module_from_spec(s);s.loader.exec_module(d);'
                'd.audit=lambda _:False;sys.exit(d.main(["audit","test"]))')
        self.assertEqual(subprocess.run([sys.executable, '-c', code], capture_output=True).returncode, 1)


class NodeAuditRunnerTest(unittest.TestCase):
    """Run the actual Node CLI with deterministic browser-boundary fakes."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.pptr = self.folder / 'puppeteer'
        self.pptr.mkdir()
        (self.pptr / 'package.json').write_text('{"main":"index.cjs"}')
        (self.pptr / 'index.cjs').write_text(r'''
const fs = require('fs');
const config = JSON.parse(process.env.AUDIT_FIXTURE);
let clock = 0;
Date.now = () => clock;
global.setTimeout = fn => { queueMicrotask(fn); return 0; };
function record(message) { fs.appendFileSync(process.env.AUDIT_EVENTS, message + '\n'); }
exports.launch = async () => {
  if (config.launchError) throw Error(config.launchError);
  return {
    newPage: async () => {
      let entry;
      return {
        setViewport: async () => {},
        goto: async url => {
          entry = config.entries[new URL(url).pathname.slice(1)];
          if (entry.gotoError) throw Error(entry.gotoError);
        },
        click: async () => { if (entry.timeout) clock += 21 * 60 * 1000; },
        $eval: async () => JSON.stringify(entry.result),
        close: async () => { record('page closed'); if (entry.closeError) throw Error(entry.closeError); },
      };
    },
    close: async () => { record('browser closed'); if (config.closeError) throw Error(config.closeError); },
  };
};
''')
        self.out = self.folder / 'evidence'
        self.events = self.folder / 'events'

    def run_runner(self, result=None, selected=('browser.json',), **entry):
        entries = {'audit.html': {'result': result or evidence()['browser'], **entry},
                   'binder-audit.html': {'result': evidence()['binder']}}
        config = {'entries': entries}
        for key in ('launchError', 'closeError'):
            if key in entry:
                config[key] = entry[key]
        return subprocess.run(['node', str(ROOT / 'website/tools/run_audits.mjs'), str(self.pptr),
                               'http://fixture/', str(self.out), *selected], capture_output=True, text=True,
                              env={**os.environ, 'AUDIT_FIXTURE': json.dumps(config), 'AUDIT_EVENTS': str(self.events)}, timeout=15)

    def test_success_and_browser_closed(self):
        result = self.run_runner()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('browser closed', self.events.read_text())

    def test_early_failed_page_returns_nonzero_and_keeps_error(self):
        row = {'done': True, 'pages': [{'ok': False, 'href': '/bad/', 'error': 'null click'}]}
        result = self.run_runner(row)
        self.assertEqual(result.returncode, 1)
        self.assertIn('/bad/: null click', result.stderr)
        self.assertEqual(json.loads((self.out / 'browser.json').read_text()), row)

    def test_failed_check_is_failure_even_if_top_level_ok(self):
        row = {'done': True, 'ok': True, 'checks': [{'ok': False}]}
        self.assertEqual(self.run_runner(row).returncode, 1)

    def test_top_level_error_is_failure_even_with_passing_pages(self):
        row = evidence()['browser']
        row['error'] = 'manifest failed'
        self.assertEqual(self.run_runner(row).returncode, 1)

    def test_timeout_replaces_old_success_with_failure(self):
        self.out.mkdir()
        (self.out / 'browser.json').write_text(json.dumps(evidence()['browser']))
        result = self.run_runner(timeout=True)
        self.assertEqual(result.returncode, 1)
        row = json.loads((self.out / 'browser.json').read_text())
        self.assertFalse(row['done'])
        self.assertIn('TIMEOUT', row['error'])

    def test_navigation_error_is_recorded_and_next_audit_runs(self):
        result = self.run_runner(gotoError='navigation failed', selected=('browser.json', 'binder.json'))
        self.assertEqual(result.returncode, 1)
        self.assertIn('navigation failed', (self.out / 'browser.json').read_text())
        self.assertTrue(json.loads((self.out / 'binder.json').read_text())['done'])
        self.assertIn('browser closed', self.events.read_text())

    def test_launch_failure_removes_old_success_files(self):
        self.out.mkdir()
        for name in ('browser', 'binder'):
            (self.out / f'{name}.json').write_text(json.dumps(evidence()[name]))
        result = self.run_runner(launchError='Chrome could not start', selected=('browser.json', 'binder.json'))
        self.assertEqual(result.returncode, 1)
        self.assertIn('Chrome could not start', result.stderr)
        self.assertFalse((self.out / 'browser.json').exists())
        self.assertFalse((self.out / 'binder.json').exists())

    def test_close_failure_still_returns_nonzero(self):
        result = self.run_runner(closeError='browser close failed')
        self.assertEqual(result.returncode, 1)
        self.assertIn('browser close failed', result.stderr)
        self.assertIn('browser closed', self.events.read_text())

    def test_unknown_selection_cannot_pass_without_running_anything(self):
        self.assertEqual(self.run_runner(selected=('unknown.json',)).returncode, 1)

    def test_empty_result_cannot_pass(self):
        self.assertEqual(self.run_runner({'done': True, 'pages': []}).returncode, 1)


if __name__ == '__main__':
    unittest.main()
