"""Project-local storage, worktree identity, and legacy read boundaries."""
from __future__ import annotations

import concurrent.futures
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import types
from unittest import mock
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
import tabilet_audit as audit
import test_harness as harness

CLI = Path(__file__).resolve().parents[1] / 'harness/tabilet_audit_host.py'


class ProjectStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = harness.make_repo(self.base / 'project')
        self.environment = dict(os.environ, XDG_STATE_HOME=str(self.base / 'state'))
        self.environment.pop('TABILET_AUDIT_DB', None)

    def command(self, *args, cwd=None, ok=True):
        result = subprocess.run([sys.executable, '-B', str(CLI), *map(str, args)],
                                cwd=cwd or self.base, env=self.environment,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return json.loads(result.stdout) if ok else result.stderr

    def path(self, project=None):
        return audit.default_database_path(project_root=project or self.project)

    def lease(self):
        target = self.base / 'project.goal' / 'A01'
        result = harness.run('git', 'worktree', 'add', '-b', 'goal/A01', str(target), cwd=self.project)
        self.assertEqual(result.returncode, 0, result.stderr)
        return target

    def test_defaults_are_distinct_for_same_named_projects_and_do_not_create_storage(self):
        other = harness.make_repo(self.base / 'other' / 'project')
        first = self.path(); second = self.path(other)
        self.assertNotEqual(first, second)
        self.assertEqual(first, self.project / 'tabilet/audit.sqlite3')
        self.assertFalse(first.exists()); self.assertFalse(second.exists())
        alias = self.base / 'alias'; alias.symlink_to(self.project, target_is_directory=True)
        self.assertEqual(self.path(alias), first)
        self.assertEqual(self.path(self.project / 'tabilet'), first)
        self.assertIn('must already exist', self.command('index', 'status', self.project, ok=False))
        self.assertFalse(first.exists())

    def test_project_location_matches_the_shared_cross_language_contract(self):
        fixture = json.loads((CLI.parents[1] / 'tests/fixtures/project-storage.json').read_text())
        self.assertEqual(fixture['schema'], 'tabilet.project-storage/v2')
        self.assertEqual(self.path(), self.project / fixture['database_relative'])
        self.command('audit', 'enable', self.project)
        self.assertIn(fixture['ignore_pattern'], (self.project/'tabilet/.gitignore').read_text())
        with contextlib.closing(audit.open_readonly_database(self.path())) as connection:
            self.assertEqual(connection.execute('SELECT value FROM schema_meta WHERE key=?',
                                                (fixture['enable_key'],)).fetchone(), ('1',))

    def test_worktrees_share_database_and_keep_durable_membership_after_cleanup(self):
        lease = self.lease()
        self.assertEqual(audit.project_storage_root(lease), self.project)
        self.assertEqual(self.path(lease), self.path())
        with contextlib.closing(audit.open_database(self.path(), project_roots=[self.project])) as connection:
            parent_workspace = audit.ensure_workspace(connection, self.project)
            child_workspace = audit.ensure_workspace(connection, lease)
            self.assertNotEqual(parent_workspace, child_workspace)
            parent = audit.start_run(connection, parent_workspace, 'goal')
            child = audit.start_run(connection, child_workspace, 'next', parent_run_id=parent)
            self.assertEqual(connection.execute('SELECT parent_run_id FROM runs WHERE run_id=?',
                                                (child,)).fetchone(), (parent,))
        runs = self.command('--project', self.project, 'audit', 'runs')['results']
        self.assertEqual({row['run_id'] for row in runs}, {parent, child})
        removed = harness.run('git', 'worktree', 'remove', str(lease), cwd=self.project)
        self.assertEqual(removed.returncode, 0, removed.stderr)
        with contextlib.closing(audit.open_database(self.path(), project_roots=[self.project])) as connection:
            self.assertEqual(audit.bound_project(connection), str(self.project))
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM workspaces').fetchone()[0], 2)

    def test_explicit_database_rejects_another_project_before_changes(self):
        other = harness.make_repo(self.base / 'other')
        path = self.path()
        with contextlib.closing(audit.open_database(path, project_roots=[self.project])) as connection:
            audit.ensure_workspace(connection, self.project)
        original = path.read_bytes()
        with self.assertRaisesRegex(audit.AuditError, 'different project'):
            audit.open_database(path, project_roots=[other])
        with self.assertRaisesRegex(audit.AuditError, 'different project'):
            audit.open_readonly_database(path, project_root=other)
        self.assertEqual(path.read_bytes(), original)
        with contextlib.closing(audit.open_database(path)) as connection:
            with self.assertRaisesRegex(audit.AuditError, 'different project'):
                audit.ensure_workspace(connection, other)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM workspaces').fetchone()[0], 1)

    def test_concurrent_binding_has_one_project_owner(self):
        other = harness.make_repo(self.base / 'other')
        path = self.base / 'state/explicit.sqlite3'
        audit.open_database(path).close()
        def register(root):
            try:
                with contextlib.closing(audit.open_database(path, project_roots=[root])) as connection:
                    audit.ensure_workspace(connection, root)
                return str(root)
            except audit.AuditError:
                return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(register, (self.project, other)))
        self.assertEqual(sum(value is not None for value in results), 1)
        with contextlib.closing(audit.open_readonly_database(path)) as connection:
            self.assertIn(audit.bound_project(connection), results)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM workspaces').fetchone()[0], 1)

    def test_old_shared_database_is_readable_but_never_selected_or_modified(self):
        other = harness.make_repo(self.base / 'other')
        old = self.base / 'state/tabilet/audit.sqlite3'
        with contextlib.closing(audit.open_database(old)) as connection:
            # Simulate an existing shared v4 database before project binding.
            for number, project in enumerate((self.project, other)):
                connection.execute('INSERT INTO workspaces VALUES (?,?,?,?,?,?)',
                                   (f'old-{number}', str(project), None, None,
                                    '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'))
            connection.commit()
        old.chmod(0o644)
        original = old.read_bytes()
        with self.assertRaisesRegex(audit.AuditError, 'older shared audit database'):
            audit.open_database(old, project_roots=[self.project])
        if os.name != 'nt':
            self.assertEqual(stat.S_IMODE(old.stat().st_mode), 0o644)
        with contextlib.closing(audit.open_readonly_database(old)) as connection:
            exported = audit.strict_json_loads(audit.export_json(connection))
            self.assertEqual(exported['runs'], [])
        result = self.command('index', 'sync', self.project)
        self.assertEqual(result['database_path'], str(self.path()))
        self.assertTrue(result['complete'])
        self.assertEqual(old.read_bytes(), original)
        self.assertTrue(self.path().is_file())

    def test_cli_selects_project_for_finish_events_and_overrides_without_new_commands(self):
        self.command('audit', 'enable', self.project)
        started = self.command('audit', 'begin', self.project, 'goal', '--run-id', 'project-run')
        self.assertEqual(started['database_path'], str(self.path()))
        finished = self.command('--project', self.project, 'audit', 'finish', 'project-run', 'completed')
        self.assertTrue(finished['index']['complete'])
        runs = self.command('--project', self.project, 'audit', 'runs')['results']
        self.assertEqual([row['run_id'] for row in runs], ['project-run'])
        self.assertEqual(self.command('audit', 'runs', cwd=self.project)['results'], runs)
        self.environment['TABILET_AUDIT_DB'] = 'project'
        self.assertEqual(self.command('index', 'status', self.project)['database_path'], str(self.path()))
        override = self.base / 'state/custom.sqlite3'
        self.command('--audit-db', override, 'index', 'sync', self.project, ok=False)
        self.assertFalse(override.exists())
        other = harness.make_repo(self.base / 'other')
        self.assertIn('different projects', self.command('--project', other, 'index', 'sync', self.project, ok=False))

    def test_copied_database_is_rejected_by_implicit_current_directory_reads(self):
        self.command('audit', 'enable', self.project)
        other = harness.make_repo(self.base / 'other')
        (other / 'tabilet').mkdir(exist_ok=True)
        shutil.copy2(self.path(), self.path(other))
        for action in ('runs', 'export'):
            self.assertIn('different project', self.command('audit', action, cwd=other, ok=False))
            self.assertIn('different project',
                          self.command('--project', other, 'audit', action, ok=False))

    def test_invalid_worktree_pointer_and_relative_override_do_not_create_database(self):
        lease = self.lease()
        gitdir = Path((lease / '.git').read_text().strip().removeprefix('gitdir: '))
        (gitdir / 'gitdir').write_text(str(self.base / 'wrong/.git') + '\n')
        with self.assertRaisesRegex(audit.AuditError, 'no valid project registration'):
            self.path(lease)
        with self.assertRaisesRegex(audit.AuditError, 'absolute path'):
            audit.resolve_database_path('relative.sqlite3', project_root=self.project)
        self.assertFalse(self.path().exists())

    def test_manual_opt_in_is_per_repository_and_indexing_does_not_enable(self):
        other = harness.make_repo(self.base / 'other')
        self.environment['TABILET_AUDIT_DB'] = str(self.path())
        self.assertFalse(self.command('audit', 'status', self.project)['enabled'])
        self.assertFalse(self.command('audit', 'disable', self.project)['exists'])
        self.assertFalse(self.path().exists())
        self.command('index', 'sync', other)
        self.assertFalse(self.command('audit', 'status', other)['enabled'])
        before = self.path(other).read_bytes()
        self.command('audit', 'begin', other, 'next', ok=False)
        self.assertEqual(self.path(other).read_bytes(), before)
        self.assertTrue(self.command('audit', 'enable', self.project)['enabled'])
        args = types.SimpleNamespace(audit_capture='metadata', provider='openai', model='test')
        with mock.patch.dict(os.environ, {'TABILET_AUDIT_DB': str(self.path())}):
            with harness.harness.AuditRun(args, self.project, 'next', None, 'clean') as recorder:
                self.assertIsNotNone(recorder.run_id)
                recorder.finish('completed')
            with harness.harness.AuditRun(args, other, 'next', None, 'clean') as recorder:
                self.assertIsNone(recorder.run_id)
                recorder.finish('completed')
        self.assertEqual(self.path(other).read_bytes(), before)
        self.assertEqual(len(self.command('--project', self.project, 'audit', 'runs')['results']), 1)

    def test_disable_and_delete_stop_recording_without_losing_markdown(self):
        original = {p: p.read_bytes() for p in self.project.rglob('*.md')}
        self.command('audit', 'enable', self.project)
        run = self.command('audit', 'begin', self.project, 'next')
        self.command('--project', self.project, 'audit', 'finish', run['run_id'], 'completed')
        before = self.command('--project', self.project, 'audit', 'export')
        self.command('audit', 'disable', self.project)
        self.assertEqual(self.command('--project', self.project, 'audit', 'export'), before)
        self.command('audit', 'begin', self.project, 'next', ok=False)
        for file in self.path().parent.glob('audit.sqlite3*'):
            file.unlink()
        self.assertFalse(self.command('audit', 'status', self.project)['enabled'])
        self.command('index', 'sync', self.project)
        self.assertFalse(self.command('audit', 'status', self.project)['enabled'])
        self.assertEqual({p: p.read_bytes() for p in original}, original)

    def test_worktrees_share_opt_in_and_ignore_rules_preserve_existing_content(self):
        lease = self.lease()
        ignored = self.project/'tabilet/.gitignore'
        original = b'keep-existing-rule\n!/audit.sqlite3\n'
        ignored.write_bytes(original)
        self.command('audit', 'enable', lease)
        self.assertTrue(self.command('audit', 'status', self.project)['enabled'])
        self.assertEqual(ignored.read_bytes(), original+b'/audit.sqlite3*\n')
        self.command('audit', 'enable', lease)
        self.assertEqual(ignored.read_bytes(), original+b'/audit.sqlite3*\n')
        for suffix in ('', '-wal', '-shm', '-journal', '.init-test'):
            self.assertEqual(harness.run('git', 'check-ignore', '-q',
                'tabilet/audit.sqlite3'+suffix, cwd=self.project).returncode, 0)
        self.command('audit', 'disable', lease)
        self.assertFalse(self.command('audit', 'status', self.project)['enabled'])

    def test_unsafe_ignore_and_non_reserved_database_paths_are_rejected(self):
        outside = self.base/'outside';outside.write_bytes(b'preserve')
        (self.project/'tabilet/.gitignore').symlink_to(outside)
        self.command('audit', 'enable', self.project, ok=False)
        self.assertFalse(self.path().exists())
        self.assertEqual(outside.read_bytes(), b'preserve')
        with self.assertRaisesRegex(audit.AuditError, 'only tabilet/audit.sqlite3'):
            audit.open_database(self.project/'tabilet/other.sqlite3', project_roots=[self.project])

    def test_disabling_a_live_recorder_stops_further_events(self):
        self.command('audit', 'enable', self.project)
        args = types.SimpleNamespace(audit_capture='metadata', provider='openai', model='test')
        with harness.harness.AuditRun(args, self.project, 'next', None, 'clean') as recorder:
            self.assertIsNotNone(recorder.run_id)
            self.command('audit', 'disable', self.project)
            recorder.emit('verification_observed', details={'result':'after disable'})
            recorder.finish('completed')
        events = self.command('--project', self.project, 'audit', 'events')['results']
        self.assertEqual([event['event_type'] for event in events], ['run_started'])

    def test_tracked_database_cannot_be_enabled_or_changed_by_setup(self):
        with contextlib.closing(audit.open_database(self.path(), project_roots=[self.project])):
            pass
        harness.run('git', 'add', '-f', 'tabilet/audit.sqlite3', cwd=self.project)
        original = self.path().read_bytes()
        self.assertIn('tracked by Git', self.command('audit', 'enable', self.project, ok=False))
        self.assertEqual(self.path().read_bytes(), original)
        self.assertFalse(self.command('audit', 'status', self.project)['enabled'])

    def test_recording_never_rewrites_project_ignore_configuration(self):
        self.command('audit', 'enable', self.project)
        ignore = self.project/'tabilet/.gitignore'
        original = b'/audit.sqlite3*\n# A user-owned addition\nother-output\n'
        ignore.write_bytes(original)
        started = self.command('audit', 'begin', self.project, 'propose')
        self.command('--project', self.project, 'audit', 'finish', started['run_id'], 'completed')
        self.assertEqual(ignore.read_bytes(), original)

    def test_default_database_symlink_does_not_redirect_a_writer(self):
        path = self.path()
        actual = self.base / 'state/archived.sqlite3'
        with contextlib.closing(audit.open_database(actual, project_roots=[self.project])) as connection:
            audit.ensure_workspace(connection, self.project)
        original = actual.read_bytes()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(actual)
        self.assertEqual(self.path(), path)
        with self.assertRaisesRegex(audit.AuditError, 'symlink destination rejected'):
            audit.open_database(path, project_roots=[self.project])
        self.assertEqual(actual.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
