import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
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
        self.assertEqual(self.command('reflect', '--check')['available'], True)

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

    def test_backend_timeouts_count_as_budget_not_failure(self):
        self.record_completed_task()
        telemetry = reflect.extract_telemetry(self.repo)
        timeout = subprocess.TimeoutExpired('claude', 1)
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch('shutil.which', side_effect=lambda name: '/bin/x' if name == 'claude' else None), \
                mock.patch('subprocess.run', side_effect=timeout):
            with self.assertRaises(reflect.BudgetExceeded):
                reflect.invoke_improver_llm(telemetry, self.repo, timeout_sec=5)

    def test_probes_are_opt_in_and_never_use_a_shell(self):
        marker = self.repo / 'pwned'
        proposal = f"```probe-commands\npython3 --version\ntouch {marker}; echo hi\nrm -rf x\n```\n"
        off = reflect.probe_proposed_commands(proposal, self.repo)
        self.assertEqual({r['status'] for r in off}, {'SKIPPED'})
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual({r['status'] for r in reflect.probe_proposed_commands(proposal, self.repo, enabled=True)},
                             {'SKIPPED'})
        with mock.patch.dict(os.environ, {'ALLOW_UNSANDBOXED_SHELL': '1'}):
            on = reflect.probe_proposed_commands(proposal, self.repo, enabled=True)
        self.assertEqual([r['status'] for r in on], ['PASSED', 'SKIPPED', 'SKIPPED'])
        self.assertFalse(marker.exists())

    def test_probe_timeout_kills_the_process_group(self):
        proposal = "```probe-commands\nsleep 30\n```\n"
        with mock.patch.dict(os.environ, {'ALLOW_UNSANDBOXED_SHELL': '1'}):
            result = reflect.probe_proposed_commands(proposal, self.repo, timeout_sec=1, enabled=True)
        self.assertEqual(result[0]['status'], 'TIMEOUT')


if __name__ == '__main__':
    unittest.main()
