"""Portable CLI acceptance: fixed local storage, manual opt-in, and reset."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / 'harness/tabilet_audit_host.py'


class AuditPlatformTests(unittest.TestCase):
    def test_native_python_cli_isolates_projects_without_environment_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root/'project A-é'; second = root/'project B'
            for project in (first, second):
                (project/'tabilet/memory-bank').mkdir(parents=True)
                (project/'AGENTS.md').write_text('# Agent\n', encoding='utf-8')
                (project/'tabilet/memory-bank/milestone.md').write_text(
                    '# Milestones\n\n## M01 - Delivery\n\n**Acceptance.** Verified.\n', encoding='utf-8')
                (project/'tabilet/memory-bank/status-M01.md').write_text(
                    '# Status\n\n| Item | State | Notes |\n|---|---|---|\n| Task | `[ ]` | Evidence |\n', encoding='utf-8')
            environment = dict(os.environ, TABILET_AUDIT_DB=str(root/'obsolete.sqlite3'), PYTHONIOENCODING='ascii')

            def command(*arguments):
                process = subprocess.run([sys.executable, '-B', str(CLI), *map(str, arguments)],
                                         cwd=root, env=environment, capture_output=True, encoding='utf-8')
                self.assertEqual(process.returncode, 0, process.stderr)
                return json.loads(process.stdout)

            self.assertFalse(command('audit', 'status', first)['exists'])
            self.assertTrue(command('audit', 'enable', first)['enabled'])
            self.assertEqual(command('audit', 'status', first)['database_path'],
                             str(first.resolve()/'tabilet/audit.sqlite3'))
            self.assertFalse(command('audit', 'status', second)['enabled'])
            self.assertTrue(command('index', 'sync', second)['complete'])
            self.assertFalse(command('audit', 'status', second)['enabled'])
            run = command('audit', 'begin', first, 'next')
            command('--project', first, 'audit', 'finish', run['run_id'], 'completed')
            records = command('--project', first, 'audit', 'runs')['results']
            self.assertEqual(len(records), 1)
            self.assertFalse(command('audit', 'disable', first)['enabled'])
            self.assertEqual(command('--project', first, 'audit', 'runs')['results'], records)
            for file in (first/'tabilet').glob('audit.sqlite3*'):
                file.unlink()
            self.assertFalse(command('audit', 'status', first)['enabled'])
            self.assertEqual((first/'tabilet/.gitignore').read_text(), '/audit.sqlite3*\n')
            self.assertFalse((root/'obsolete.sqlite3').exists())

    def test_runner_parsers_import_without_posix_file_locking(self):
        """The audit CLI loads the runner for its parsers, including on Windows."""
        script = (
            "import sys, importlib.machinery as m, importlib.util as u, pathlib\n"
            "sys.modules['fcntl'] = None\n"
            "path = sys.argv[1]\n"
            "loader = m.SourceFileLoader('runner_probe', path)\n"
            "module = u.module_from_spec(u.spec_from_loader(loader.name, loader))\n"
            "loader.exec_module(module)\n"
            "try:\n"
            "    with module.project_lock(pathlib.Path('.')): pass\n"
            "except module.ProjectLockError: print('lock-refused')\n"
        )
        runner = CLI.with_name('tackle-memory-bank-api-loop')
        process = subprocess.run([sys.executable, '-B', '-c', script, str(runner)],
                                 capture_output=True, encoding='utf-8')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stdout.strip(), 'lock-refused')


if __name__ == '__main__':
    unittest.main()
