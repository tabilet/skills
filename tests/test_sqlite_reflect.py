import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
from unittest import mock

import test_harness as h

CLI = Path(__file__).resolve().parents[1] / 'harness/tabilet_audit_host.py'
sys.path.insert(0, str(CLI.parent))
import tabilet_audit as audit  # noqa: E402
import tabilet_reflect as reflect  # noqa: E402


class ReflectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = h.make_repo(self.base / 'project')

    def command(self, *arguments, data=None, ok=True):
        env = {k: v for k, v in os.environ.items()
               if k not in ('TABILET_AUDIT_CAPTURE', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY')}
        result = subprocess.run([sys.executable, '-B', str(CLI), *map(str, arguments)],
                                input=json.dumps(data) if data is not None else None,
                                text=True, capture_output=True, env=env, cwd=self.repo)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return json.loads(result.stdout) if ok else result.stderr

    def record_completed_task(self, run_id='fast', result='completed', enable=True):
        if enable:
            self.command('audit', 'enable', self.repo)
        started = self.command('audit', 'begin', self.repo, 'next', '--run-id', run_id)
        self.command('audit', 'event', data={
            'schema': 'tabilet.audit.event/v1', 'event_id': 'e-' + run_id, 'run_id': run_id,
            'workspace_id': started['workspace_id'], 'operation': 'next', 'event_type': 'task_transition',
            'subject': {'milestone_id': 'M01', 'task_label': 'Implement feature',
                        'old_state': 'pending', 'new_state': 'completed'},
            'details': {'schema': 'tabilet.audit.details/v1', 'capture_source': 'agent', 'fidelity': 'summarized'}})
        self.command('audit', 'finish', run_id, result)

    def write_downstream_project(self):
        memory = self.repo / 'tabilet/memory-bank'
        (memory / 'milestone.md').write_text(
            '# Milestone\n\n## M01 - Delivery\n\nFirst.\n\n## M02 - Search\n\nSEARCH-SPEC run the whole suite.\n\n'
            '## M03 - Billing\n\nBILLING-SPEC unlisted.\n\n## M04 - Docs\n\nDOCS-SPEC done already.\n')
        for ident, state in (('M02', '[ ]'), ('M03', '[ ]'), ('M04', '[+]')):
            (memory / f'status-{ident}.md').write_text(
                '# Status\n\n| Item | State | Notes |\n|---|---|---|\n'
                f'| Build {ident} | {h.marker(state)} | note |\n')
        (memory / 'suggested.txt').write_text(
            'STATUS_ORDER: M01 -> M02 -> M03 -> M04\n\nDOWNSTREAM_IMPACTS:\nM01 -> M02, M04, M09\n\nCOMMIT_POLICY: task\n')

    def test_project_selected_by_flag_or_cwd_without_positional(self):
        self.command('audit', 'enable', self.repo)
        for arguments in (('--project', self.repo, 'reflect', '--dry-run'), ('reflect', '--dry-run')):
            self.assertTrue(self.command(*arguments)['dry_run'])

    def test_check_needs_no_project_data(self):
        result = self.command('reflect', '--check')
        self.assertEqual(result['available'], True)
        self.assertIsInstance(result['backends'], list)
        self.assertEqual(result['min_model_milestone_sec'], 150)

    def test_check_lists_the_backends_reflection_could_use(self):
        with mock.patch.dict(os.environ, {'PATH': '', 'GEMINI_API_KEY': 'k'}, clear=True):
            self.assertEqual(reflect.available_backends(), ['rest:gemini'])
        only = {'PATH': str(self.base / 'bin')}
        self.fake_cli('true\n')
        with mock.patch.dict(os.environ, only, clear=True):
            self.assertEqual(reflect.available_backends(), ['cli:claude'])

    def test_default_proposal_must_be_git_ignored(self):
        self.record_completed_task()
        ignore = self.repo / 'tabilet/.gitignore'
        ignore.write_text('/audit.sqlite3*\n')
        with self.assertRaisesRegex(audit.AuditError, 'not Git-ignored'):
            reflect.reflect_command(str(self.repo), milestone_id='M01')
        self.command('audit', 'enable', self.repo)
        result = reflect.reflect_command(str(self.repo), milestone_id='M01')
        self.assertTrue(Path(result['output_file']).is_file())
        self.assertEqual(h.run('git', 'status', '--porcelain', '--', 'tabilet/memory-bank', cwd=self.repo).stdout, '')

    def test_fast_baseline_matches_completed_tasks(self):
        self.record_completed_task()
        telemetry = self.command('reflect', self.repo, '--dry-run')['telemetry']
        self.assertEqual([r['task_label'] for r in telemetry['contrastive_fast_baselines']], ['Implement feature'])

    def test_linked_worktree_reads_its_own_memory_bank_and_shares_the_database(self):
        subprocess.run(['git', 'worktree', 'add', '-q', str(self.base / 'lease'), '-b', 'lease'],
                       cwd=self.repo, check=True)
        root, database = reflect.resolve_project_db(self.base / 'lease')
        self.assertEqual(root, (self.base / 'lease').resolve())
        self.assertEqual(database, audit.default_database_path(project_root=self.repo))

    def test_output_paths_are_contained(self):
        self.record_completed_task()
        self.assertIn('inside the project', self.command('reflect', self.repo, '--output', '../escape.md', ok=False))
        self.assertIn('--output is required', self.command('reflect', self.repo, '--format', 'trajectories', ok=False))
        tracked = 'tabilet/memory-bank/trajectories.json'
        self.assertIn('Git-ignored', self.command('reflect', self.repo, '--format', 'trajectories',
                                                   '--output', tracked, ok=False))
        outside = self.base / 'out' / 'trajectories.json'
        self.command('reflect', self.repo, '--format', 'trajectories', '--output', outside)
        self.assertTrue(outside.is_file())

    def test_no_backend_report_is_labelled_and_proposes_no_edits(self):
        self.record_completed_task()
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch('shutil.which', return_value=None):
            proposal, source = reflect.invoke_improver_llm(
                reflect.extract_telemetry(self.repo), self.repo)
        self.assertEqual(source, 'heuristic')
        self.assertIn('No model analysed', proposal)
        self.assertNotIn('--timeout', proposal)

    def test_configured_backend_failure_is_an_error_not_a_template(self):
        self.record_completed_task()
        telemetry = reflect.extract_telemetry(self.repo)
        error = urllib.error.HTTPError('https://api.anthropic.com', 404, 'not found', {}, None)
        with mock.patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'secret-key'}, clear=True), \
                mock.patch('shutil.which', return_value=None), \
                mock.patch('urllib.request.urlopen', side_effect=error):
            with self.assertRaises(audit.AuditError) as raised:
                reflect.invoke_improver_llm(telemetry, self.repo)
        self.assertIn('HTTP 404', str(raised.exception))
        self.assertNotIn('secret-key', str(raised.exception))

    def test_gemini_key_travels_in_a_header_not_the_url(self):
        captured = []

        def fake(request, timeout=None):
            captured.append(request)
            raise urllib.error.URLError('stop')
        with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'secret-key'}, clear=True), \
                mock.patch('urllib.request.urlopen', side_effect=fake):
            with self.assertRaises(urllib.error.URLError):
                reflect._call_rest_fallback('prompt', 'gemini')
        self.assertNotIn('secret-key', captured[0].full_url)
        self.assertEqual(captured[0].get_header('X-goog-api-key'), 'secret-key')

    def test_downstream_ids_come_from_impacts_then_strict_order(self):
        self.write_downstream_project()
        self.assertEqual(reflect.suggested_downstream(self.repo, 'M01'), ['M02', 'M04', 'M09'])
        (self.repo / 'tabilet/memory-bank/suggested.txt').write_text(
            'STATUS_ORDER: M01 -> M02? -> M03 -> M04 -> M05\n')
        self.assertEqual(reflect.suggested_downstream(self.repo, 'M01'), ['M02', 'M03', 'M04'])
        self.assertEqual(reflect.suggested_downstream(self.repo, None), [])

    def test_inline_downstream_impacts_are_honoured(self):
        suggested = self.repo / 'tabilet/memory-bank/suggested.txt'
        suggested.write_text('STATUS_ORDER: M01 -> M02 -> M03\n\nDOWNSTREAM_IMPACTS: none\n\nCOMMIT_POLICY: task\n')
        self.assertEqual(reflect.suggested_downstream(self.repo, 'M01'), [])
        suggested.write_text('STATUS_ORDER: M01 -> M02 -> M03\n\nDOWNSTREAM_IMPACTS: M01 -> M03\n\nCOMMIT_POLICY: task\n')
        self.assertEqual(reflect.suggested_downstream(self.repo, 'M01'), ['M03'])

    def test_quiet_milestone_feeds_nothing_downstream(self):
        self.write_downstream_project()
        self.record_completed_task()
        telemetry = reflect.extract_telemetry(self.repo, 'M01')
        self.assertEqual(telemetry['downstream']['gate'], 'closed')
        self.assertEqual(telemetry['downstream']['milestones'], [])
        prompt = reflect.build_reflection_prompt(telemetry, self.repo)
        self.assertIn('closed (no significant finding', prompt)
        self.assertNotIn('SEARCH-SPEC', prompt)

    def test_significant_finding_feeds_only_listed_live_milestones(self):
        self.write_downstream_project()
        self.record_completed_task('first', 'failed')
        self.record_completed_task('second', 'completed', enable=False)
        telemetry = reflect.extract_telemetry(self.repo, 'M01')
        down = telemetry['downstream']
        self.assertEqual(down['gate'], 'open')
        self.assertEqual([m['id'] for m in down['milestones']], ['M02'])
        self.assertEqual({m['id']: m['reason'] for m in down['skipped']},
                         {'M04': 'no pending or in-progress rows', 'M09': 'no active status file (missing or retired)'})
        prompt = reflect.build_reflection_prompt(telemetry, self.repo)
        self.assertIn('SEARCH-SPEC', prompt)
        self.assertNotIn('BILLING-SPEC', prompt)
        self.assertNotIn('DOCS-SPEC', prompt)
        self.assertIn('No downstream changes.', prompt)

    def test_failed_run_with_an_unattributed_terminal_event_still_counts_for_its_milestone(self):
        self.command('audit', 'enable', self.repo)
        started = self.command('audit', 'begin', self.repo, 'next', '--run-id', 'broken')
        for index, (event_type, subject) in enumerate((
                ('task_observed', {'milestone_id': 'M01', 'task_label': 'Implement feature', 'old_state': 'in_progress'}),
                ('run_failed', {}))):
            self.command('audit', 'event', data={
                'schema': 'tabilet.audit.event/v1', 'event_id': f'broken-{index}', 'run_id': 'broken',
                'workspace_id': started['workspace_id'], 'operation': 'next', 'event_type': event_type,
                'subject': subject, 'details': {'schema': 'tabilet.audit.details/v1', 'capture_source': 'agent',
                            'fidelity': 'summarized', 'reason': 'model made no commit'}})
        self.command('audit', 'finish', 'broken', 'failed')
        telemetry = reflect.extract_telemetry(self.repo, 'M01')
        self.assertEqual([(r['run_id'], r['task_label']) for r in telemetry['friction_runs']], [('broken', 'Implement feature')])
        self.assertEqual(telemetry['downstream']['reasons'], ['run broken ended failed'])
        self.assertEqual(reflect.extract_telemetry(self.repo, 'M02')['friction_runs'], [])

    def test_no_milestone_means_no_downstream_feeding(self):
        self.write_downstream_project()
        self.record_completed_task('first', 'failed')
        telemetry = reflect.extract_telemetry(self.repo)
        self.assertEqual(telemetry['downstream']['gate'], 'closed')
        self.assertEqual(telemetry['downstream']['milestones'], [])

    def test_model_budget_is_a_capped_share_of_milestone_time(self):
        self.assertEqual(reflect.model_budget_sec(1000, 10), 100)
        self.assertEqual(reflect.model_budget_sec(5000, 10), reflect.MODEL_TIMEOUT_CAP_SEC)
        self.assertEqual(reflect.model_budget_sec(0, 10), 0)

    def test_short_milestone_skips_the_model_entirely(self):
        self.record_completed_task()
        with mock.patch.object(reflect, 'invoke_improver_llm', side_effect=AssertionError('model called')):
            result = reflect.reflect_command(str(self.repo), milestone_id='M01')
        self.assertEqual(result['proposal_source'], 'heuristic')
        self.assertIn('model skipped', result['budget_note'])
        self.assertTrue(Path(result['output_file']).is_file())

    def test_budget_overrun_degrades_to_the_model_free_report(self):
        self.record_completed_task()
        with mock.patch.object(reflect, 'model_budget_sec', return_value=60), \
                mock.patch.object(reflect, 'invoke_improver_llm', side_effect=reflect.BudgetExceeded('slow')):
            result = reflect.reflect_command(str(self.repo), milestone_id='M01')
        self.assertEqual(result['proposal_source'], 'heuristic')
        self.assertIn('slow', result['budget_note'])

    def fake_cli(self, body):
        bin_dir = self.base / 'bin'
        bin_dir.mkdir(exist_ok=True)
        script = bin_dir / 'claude'
        script.write_text('#!/bin/sh\n' + body)
        script.chmod(0o755)
        return {'PATH': f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"}

    def test_backend_timeouts_count_as_budget_not_failure(self):
        self.record_completed_task()
        telemetry = reflect.extract_telemetry(self.repo)
        # The CLI leaves a helper holding the output pipe open; the whole group must die on time.
        env = self.fake_cli('sleep 30 &\nsleep 30\n')
        started = time.monotonic()
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(reflect.BudgetExceeded):
                reflect.invoke_improver_llm(telemetry, self.repo, backend='claude', timeout_sec=1)
        self.assertLess(time.monotonic() - started, 10)

    def test_cli_backend_runs_outside_the_project(self):
        self.record_completed_task()
        telemetry = reflect.extract_telemetry(self.repo)
        with mock.patch.dict(os.environ, self.fake_cli('cat >/dev/null\npwd\n'), clear=True):
            text, source = reflect.invoke_improver_llm(telemetry, self.repo, backend='claude', timeout_sec=10)
        self.assertEqual(source, 'cli:claude')
        self.assertNotEqual(Path(text).resolve(), self.repo.resolve())
        self.assertFalse(Path(text).exists(), 'the scratch directory is removed afterwards')

    def test_probes_are_opt_in_and_never_use_a_shell(self):
        marker = self.repo / 'pwned'
        proposal = (f"```probe-commands\npython3 -m unittest --help\ntouch {marker}; echo hi\nrm -rf x\n"
                    f"sh -c 'touch {marker}'\nenv touch {marker}\nfind . -name x -delete\n```\n")
        off = reflect.probe_proposed_commands(proposal, self.repo)
        self.assertEqual({r['status'] for r in off}, {'SKIPPED'})
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual({r['status'] for r in reflect.probe_proposed_commands(proposal, self.repo, enabled=True)},
                             {'SKIPPED'})
        with mock.patch.dict(os.environ, {'ALLOW_UNSANDBOXED_SHELL': '1'}):
            on = reflect.probe_proposed_commands(proposal, self.repo, enabled=True)
        self.assertEqual([r['status'] for r in on], ['PASSED', 'SKIPPED', 'SKIPPED', 'SKIPPED', 'SKIPPED', 'SKIPPED'])
        self.assertFalse(marker.exists())

    def test_probe_timeout_kills_the_process_group(self):
        (self.repo / 'test_slow.py').write_text('import time\nimport unittest\n\n\nclass Slow(unittest.TestCase):\n'
                                                '    def test_sleep(self):\n        time.sleep(30)\n')
        proposal = "```probe-commands\npython3 -m unittest test_slow\n```\n"
        with mock.patch.dict(os.environ, {'ALLOW_UNSANDBOXED_SHELL': '1'}):
            result = reflect.probe_proposed_commands(proposal, self.repo, timeout_sec=1, enabled=True)
        self.assertEqual(result[0]['status'], 'TIMEOUT')

    def test_extract_coverage_evidence_various_runners(self):
        # Unittest
        cov = reflect.extract_coverage_evidence("Ran 5 tests in 0.012s\n\nOK")
        self.assertEqual(cov["tests_run"], 5)
        self.assertTrue(cov["has_coverage"])
        self.assertEqual(cov["summary"], "Ran 5 tests")

        cov_zero = reflect.extract_coverage_evidence("Ran 0 tests in 0.000s\n\nOK")
        self.assertEqual(cov_zero["tests_run"], 0)
        self.assertFalse(cov_zero["has_coverage"])

        # Pytest
        cov_pytest = reflect.extract_coverage_evidence("= 12 passed, 2 failed in 0.35s =")
        self.assertEqual(cov_pytest["tests_run"], 14)
        self.assertTrue(cov_pytest["has_coverage"])
        self.assertIn("12 passed, 2 failed", cov_pytest["summary"])

        cov_pytest_zero = reflect.extract_coverage_evidence("collected 0 items\n\n= no tests ran in 0.01s =")
        self.assertEqual(cov_pytest_zero["tests_run"], 0)
        self.assertFalse(cov_pytest_zero["has_coverage"])

        # Jest / Vitest
        cov_jest = reflect.extract_coverage_evidence("Tests: 8 passed, 8 total\nTime: 1.2s")
        self.assertEqual(cov_jest["tests_run"], 8)
        self.assertTrue(cov_jest["has_coverage"])

        cov_jest_zero = reflect.extract_coverage_evidence("Tests: 0 passed, 0 total\nTime: 0.1s")
        self.assertEqual(cov_jest_zero["tests_run"], 0)
        self.assertFalse(cov_jest_zero["has_coverage"])

        # Mocha
        cov_mocha = reflect.extract_coverage_evidence("  22 passing (450ms)")
        self.assertEqual(cov_mocha["tests_run"], 22)
        self.assertTrue(cov_mocha["has_coverage"])

        # Cargo test
        cov_cargo = reflect.extract_coverage_evidence("test result: ok. 14 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out")
        self.assertEqual(cov_cargo["tests_run"], 14)
        self.assertTrue(cov_cargo["has_coverage"])

        cov_cargo_zero = reflect.extract_coverage_evidence("test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 14 filtered out")
        self.assertEqual(cov_cargo_zero["tests_run"], 0)
        self.assertFalse(cov_cargo_zero["has_coverage"])

        # Go test
        cov_go = reflect.extract_coverage_evidence("PASS\nok  \texample/pkg\t0.014s")
        self.assertTrue(cov_go["has_coverage"])

        cov_go_zero = reflect.extract_coverage_evidence("?   \texample/empty\t[no test files]")
        self.assertFalse(cov_go_zero["has_coverage"])

        # Unrecognised
        cov_none = reflect.extract_coverage_evidence("random tool output without test statistics")
        self.assertIsNone(cov_none["has_coverage"])
        self.assertIsNone(cov_none["tests_run"])

    def test_probe_proposed_commands_detects_zero_coverage(self):
        (self.repo / 'test_real.py').write_text(
            'import unittest\n\nclass Real(unittest.TestCase):\n    def test_ok(self):\n        pass\n'
        )
        proposal = (
            "```probe-commands\n"
            "python3 -m unittest test_real\n"
            "python3 -m unittest -k nonexistent\n"
            "```\n"
        )
        with mock.patch.dict(os.environ, {'ALLOW_UNSANDBOXED_SHELL': '1'}):
            results = reflect.probe_proposed_commands(proposal, self.repo, enabled=True)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['status'], 'PASSED')
        self.assertTrue(results[0]['coverage']['has_coverage'])
        self.assertEqual(results[0]['coverage']['tests_run'], 1)
        self.assertIsNotNone(results[0]['duration_sec'])

        self.assertEqual(results[1]['status'], 'ZERO_COVERAGE')
        self.assertFalse(results[1]['coverage']['has_coverage'])
        self.assertEqual(results[1]['coverage']['tests_run'], 0)

    @staticmethod
    def probe(command, tests=None, seconds=1.0, status='PASSED', has_coverage=True):
        coverage = {'tests_run': tests, 'has_coverage': has_coverage if tests != 0 else False,
                    'summary': None if tests is None else f'Ran {tests} tests'}
        return {'command': command, 'status': status, 'exit_code': 0, 'duration_sec': seconds,
                'coverage': coverage, 'output_snippet': ''}

    def test_a_subset_is_a_fast_tier_never_the_recommended_profile(self):
        report = reflect.format_compose_report('## Proposed\n', [
            self.probe('python3 -m unittest discover tests', 50, 1.25),
            self.probe('python3 -m unittest tests/test_fast.py', 10, 0.35),
            self.probe('python3 -m unittest -k nonexistent', 0, 0.05, status='ZERO_COVERAGE'),
        ])
        self.assertIn('| Proposed Command | Probe Status | Avg Duration | Coverage Evidence | Output Snippet |', report)
        self.assertNotIn('Recommended Test Profile:', report)
        self.assertIn('**Fast tier only:** `python3 -m unittest tests/test_fast.py` runs 10 of the baseline\'s 50 tests (20%)', report)
        self.assertIn('does not replace the baseline', report)
        self.assertIn('WARNING:** One or more proposed commands executed 0 tests', report)

    def test_a_faster_candidate_with_at_least_the_baseline_tests_is_recommended(self):
        report = reflect.format_compose_report('## Proposed\n', [
            self.probe('make test', 50, 4.0), self.probe('pytest -n 4', 52, 1.5), self.probe('pytest tests/unit', 12, 0.4)])
        self.assertIn('**Recommended Test Profile:** `pytest -n 4` runs 52 tests', report)
        self.assertIn('**Fast tier only:** `pytest tests/unit` runs 12 of the baseline\'s 50 tests', report)

    def test_a_slower_candidate_is_not_recommended(self):
        report = reflect.format_compose_report('## Proposed\n', [self.probe('make test', 50, 1.0), self.probe('pytest', 50, 3.0)])
        self.assertNotIn('Recommended Test Profile:', report)
        self.assertIn('No verified candidate is faster than the baseline', report)

    def test_output_without_a_test_count_is_never_recommended(self):
        report = reflect.format_compose_report('## Proposed\n', [
            self.probe('pytest', 50, 3.0), self.probe('make test', None, 0.01, has_coverage=None)])
        self.assertNotIn('Recommended Test Profile:', report)
        self.assertIn('`make test` passed, but its output reported no test count', report)

    def test_a_baseline_that_was_not_measured_blocks_every_recommendation(self):
        timeout = {**self.probe('make test', None, 15.0, status='TIMEOUT', has_coverage=None)}
        report = reflect.format_compose_report('## Proposed\n', [timeout, self.probe('pytest tests/unit', 10, 0.4)])
        self.assertNotIn('Recommended Test Profile:', report)
        self.assertNotIn('Fast tier only', report)
        self.assertIn('was not measured: it timed out at the probe limit', report)
        self.assertIn('WARNING:** One or more proposed commands failed, timed out or were unstable', report)

    def test_a_command_that_fails_its_repeat_run_is_unstable_not_passed(self):
        (self.repo / 'test_flaky.py').write_text(
            'import os\nimport unittest\n\n\nclass Flaky(unittest.TestCase):\n    def test_once(self):\n'
            '        if os.path.exists("seen"):\n            self.fail("second run")\n        open("seen", "w").close()\n')
        proposal = '```probe-commands\npython3 -m unittest test_flaky\n```\n'
        with mock.patch.dict(os.environ, {'ALLOW_UNSANDBOXED_SHELL': '1'}):
            [result] = reflect.probe_proposed_commands(proposal, self.repo, enabled=True)
        self.assertEqual(result['status'], 'UNSTABLE')
        self.assertIn('failed with exit', result['output_snippet'])
        self.assertIn('**UNSTABLE**', reflect.format_compose_report('## P\n', [result]))
        # With no repeat requested the same command passes: the flakiness is only visible on the repeat.
        (self.repo / 'seen').unlink()
        with mock.patch.dict(os.environ, {'ALLOW_UNSANDBOXED_SHELL': '1'}):
            [single] = reflect.probe_proposed_commands(proposal, self.repo, enabled=True, repeats=1)
        self.assertEqual(single['status'], 'PASSED')

    def test_a_repeat_run_that_times_out_is_killed_and_reported(self):
        (self.repo / 'test_hang.py').write_text(
            'import os\nimport time\nimport unittest\n\n\nclass Hang(unittest.TestCase):\n    def test_hang(self):\n'
            '        if os.path.exists("seen"):\n            open("pid", "w").write(str(os.getpid()))\n            time.sleep(60)\n'
            '        open("seen", "w").close()\n')
        proposal = '```probe-commands\npython3 -m unittest test_hang\n```\n'
        with mock.patch.dict(os.environ, {'ALLOW_UNSANDBOXED_SHELL': '1'}):
            [result] = reflect.probe_proposed_commands(proposal, self.repo, timeout_sec=3, enabled=True)
        self.assertEqual(result['status'], 'UNSTABLE')
        self.assertIn('timed out after 3s on the repeat run', result['output_snippet'])
        pid = int((self.repo / 'pid').read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_only_three_distinct_commands_run(self):
        flags = ['--help', '-h', '-v --help', '-b --help', '-f --help']
        proposal = '```probe-commands\n' + '\n'.join(f'python3 -m unittest {f}' for f in flags) + '\npython3 -m unittest --help\n```\n'
        with mock.patch.dict(os.environ, {'ALLOW_UNSANDBOXED_SHELL': '1'}):
            results = reflect.probe_proposed_commands(proposal, self.repo, enabled=True)
        self.assertEqual([r['status'] for r in results], ['PASSED'] * 3 + ['SKIPPED'] * 2)
        self.assertIn('at most 3 probe commands run', results[3]['output_snippet'])

    def test_counts_come_from_the_runner_totals(self):
        counts = reflect.extract_coverage_evidence
        # Cargo: a crate whose tests are all in tests/ prints "0 passed" for the lib first
        cargo = ('test result: ok. 0 passed; 0 failed; 0 ignored; finished in 0.00s\n'
                 'test result: ok. 5 passed; 1 failed; 0 ignored; finished in 0.40s\n'
                 'test result: ok. 0 passed; 0 failed; 0 ignored; finished in 0.00s\n')
        self.assertEqual((counts(cargo)['tests_run'], counts(cargo)['has_coverage']), (6, True))
        # Jest: the suite count must not be read as the test count
        jest = 'Test Suites: 2 passed, 2 total\nTests:       1 failed, 38 passed, 39 total\nTime: 4.1s'
        self.assertEqual(counts(jest)['tests_run'], 39)
        self.assertEqual(counts(jest)['summary'], '38/39 tests passed')
        self.assertEqual(counts('Test Files  1 passed (1)\n     Tests  2 failed | 6 passed (8)\n')['tests_run'], 8)
        # pytest: only the summary line counts, and a Cargo "finished in" line is not one
        self.assertEqual(counts('collected 3 items\n=== 3 passed in 0.02s ===')['tests_run'], 3)
        self.assertEqual(counts('1 passed, 2 warnings in 0.10s')['tests_run'], 1)
        self.assertEqual(counts('  3 passing (12ms)\n  1 failing')['tests_run'], 4)

    def test_go_packages_without_tests_do_not_empty_the_run(self):
        counts = reflect.extract_coverage_evidence
        mixed = '?   \texample.com/cmd\t[no test files]\nok  \texample.com/pkg\t0.300s\n'
        self.assertTrue(counts(mixed)['has_coverage'])
        self.assertIsNone(counts(mixed)['tests_run'])
        self.assertFalse(counts('?   \texample.com/cmd\t[no test files]\n')['has_coverage'])
        self.assertFalse(counts('ok  \texample.com/pkg\t0.010s [no tests to run]\n')['has_coverage'])
        # A Go run has no test count, so it can be listed but never compared or recommended.
        report = reflect.format_compose_report('## P\n', [
            self.probe('pytest', 50, 3.0), {**self.probe('go test ./...', None, 0.5, has_coverage=True)}])
        self.assertNotIn('Recommended Test Profile:', report)


if __name__ == '__main__':
    unittest.main()
