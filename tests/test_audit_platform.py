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
            self.assertEqual((first/'tabilet/.gitignore').read_text(), '/memory-bank/suggested-harness-update.md\n/audit.sqlite3*\n')
            self.assertFalse((root/'obsolete.sqlite3').exists())

    def test_unchanged_file_path_and_descriptor_metadata_are_comparable(self):
        script = (
            "import json, os, pathlib, sys, tempfile\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import tabilet_index as ix\n"
            "with tempfile.TemporaryDirectory() as directory:\n"
            "    path = pathlib.Path(directory) / 'sample.md'\n"
            "    path.write_text('unchanged', encoding='utf-8')\n"
            "    os.utime(path, ns=(1000000000, 1000000000))\n"
            "    by_path = path.stat()\n"
            "    with path.open('rb') as source:\n"
            "        by_fd = os.fstat(source.fileno())\n"
            "    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_birthtime_ns')\n"
            "    evidence = {kind: {field: getattr(info, field, None) for field in fields}\n"
            "                for kind, info in (('stat', by_path), ('fstat', by_fd))}\n"
            "    print(json.dumps(evidence))\n"
            "    assert ix.signature(by_path, cross_api=True) == ix.signature(by_fd, cross_api=True), evidence\n"
            "    text, _, _ = ix.read_document(path.parent, path.name)\n"
            "    assert text == 'unchanged'\n"
        )
        process = subprocess.run([sys.executable, '-B', '-c', script, str(CLI.parent)],
                                 capture_output=True, encoding='utf-8')
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        # Retain raw fields in CI output to confirm the native Windows behavior.
        print(process.stdout.strip())

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
