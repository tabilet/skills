"""Project-local external storage, worktree identity, and legacy read boundaries."""
from __future__ import annotations

import concurrent.futures
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import tempfile
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
        return audit.default_database_path(self.environment, project_root=project or self.project)

    def lease(self):
        target = self.base / 'project.goal' / 'A01'
        result = harness.run('git', 'worktree', 'add', '-b', 'goal/A01', str(target), cwd=self.project)
        self.assertEqual(result.returncode, 0, result.stderr)
        return target

    def test_defaults_are_distinct_for_same_named_projects_and_do_not_create_storage(self):
        other = harness.make_repo(self.base / 'other' / 'project')
        first = self.path(); second = self.path(other)
        self.assertNotEqual(first, second)
        self.assertEqual(first.parent.name, hashlib.sha256(str(self.project).encode()).hexdigest())
        self.assertEqual(first, self.base / 'state/tabilet/projects' / first.parent.name / 'audit.sqlite3')
        self.assertFalse(first.exists()); self.assertFalse(second.exists())
        alias = self.base / 'alias'; alias.symlink_to(self.project, target_is_directory=True)
        self.assertEqual(self.path(alias), first)
        self.assertEqual(self.path(self.project / 'tabilet'), first)
        self.assertIn('must already exist', self.command('index', 'status', self.project, ok=False))
        self.assertFalse(first.exists())

    def test_project_ids_match_the_shared_cross_language_contract(self):
        fixture = json.loads((CLI.parents[1] / 'tests/fixtures/project-storage.json').read_text())
        self.assertEqual(fixture['schema'], 'tabilet.project-storage/v1')
        for vector in fixture['vectors']:
            path = audit.default_database_path(self.environment, project_root=vector['canonical_root'])
            self.assertEqual(path.parent.name, vector['project_id'])

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
        runs = self.command('--project', self.project, '--audit-db', self.path(), 'audit', 'runs')['results']
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
        result = self.command('--audit-db', override, 'index', 'sync', self.project)
        self.assertEqual(result['database_path'], str(override))
        self.assertTrue(override.is_file())
        other = harness.make_repo(self.base / 'other')
        self.assertIn('different projects', self.command('--project', other, 'index', 'sync', self.project, ok=False))

    def test_invalid_worktree_pointer_and_relative_override_do_not_create_database(self):
        lease = self.lease()
        gitdir = Path((lease / '.git').read_text().strip().removeprefix('gitdir: '))
        (gitdir / 'gitdir').write_text(str(self.base / 'wrong/.git') + '\n')
        with self.assertRaisesRegex(audit.AuditError, 'no valid project registration'):
            self.path(lease)
        with self.assertRaisesRegex(audit.AuditError, 'absolute external path'):
            audit.resolve_database_path('relative.sqlite3', project_root=self.project)
        self.assertFalse(self.path().exists())

    def test_default_database_symlink_does_not_redirect_a_writer(self):
        path = self.path()
        actual = self.base / 'state/archived.sqlite3'
        with contextlib.closing(audit.open_database(actual, project_roots=[self.project])) as connection:
            audit.ensure_workspace(connection, self.project)
        original = actual.read_bytes()
        path.parent.mkdir(parents=True)
        path.symlink_to(actual)
        self.assertEqual(self.path(), path)
        with self.assertRaisesRegex(audit.AuditError, 'symlink destination rejected'):
            audit.open_database(path, project_roots=[self.project])
        self.assertEqual(actual.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
