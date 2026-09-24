import os
import json
import contextlib
import io
import types
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import test_harness as h


class RunnerRepairs(unittest.TestCase):
    def test_incompatible_audit_toolkit_is_gap_without_changing_task_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=h.make_repo(Path(tmp)/'repo')
            database=Path(tmp)/'audit.db'
            sys.path.insert(0,str(h.HARNESS.parent))
            import tabilet_index  # ensure its real audit dependency is loaded first
            def model(*args):
                source=repo/'tabilet/memory-bank/status-M01.md'
                source.write_text(source.read_text().replace(h.marker('[ ]'),h.marker('[+]')))
                h.run('git','add','-A',cwd=repo)
                commit=h.run('git','-c','user.name=Test','-c','user.email=test@example.test','commit','-qm','done',cwd=repo)
                self.assertEqual(commit.returncode,0,commit.stderr)
                return {'final':'done'}
            env=h.HarnessIntegrationTests().harness_env(tmp,ALLOW_UNSANDBOXED_SHELL='1')
            stderr=io.StringIO()
            with (mock.patch.object(sys,'argv',[str(h.HARNESS),str(repo),'--audit-db',str(database)]),
                  mock.patch.dict(os.environ,env,clear=True),
                  mock.patch.object(h.harness,'one_agent_run',side_effect=model),
                  mock.patch.dict(sys.modules,{'tabilet_audit':types.SimpleNamespace(TOOLKIT_INTERFACE=99)}),
                  contextlib.redirect_stderr(stderr)):
                with self.assertRaises(SystemExit) as stopped:h.harness.main()
            self.assertEqual(stopped.exception.code,7)
            self.assertIn('incompatible audit toolkit modules',stderr.getvalue())
            self.assertFalse(database.exists())

    def test_missing_sqlite_module_is_gap_without_changing_task_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=h.make_repo(Path(tmp)/'repo')
            database=Path(tmp)/'audit.db'
            def model(*args):
                source=repo/'tabilet/memory-bank/status-M01.md'
                source.write_text(source.read_text().replace(h.marker('[ ]'),h.marker('[+]')))
                h.run('git','add','-A',cwd=repo)
                commit=h.run('git','-c','user.name=Test','-c','user.email=test@example.test','commit','-qm','done',cwd=repo)
                self.assertEqual(commit.returncode,0,commit.stderr)
                return {'final':'done'}
            env=h.HarnessIntegrationTests().harness_env(tmp,ALLOW_UNSANDBOXED_SHELL='1')
            stderr=io.StringIO()
            # A None entry makes `import sqlite3` raise ImportError, as on a
            # Python built without SQLite.
            with (mock.patch.object(sys,'argv',[str(h.HARNESS),str(repo),'--audit-db',str(database)]),
                  mock.patch.dict(os.environ,env,clear=True),
                  mock.patch.object(h.harness,'one_agent_run',side_effect=model),
                  mock.patch.dict(sys.modules,{'sqlite3':None}),
                  contextlib.redirect_stderr(stderr)):
                with self.assertRaises(SystemExit) as stopped:h.harness.main()
            self.assertEqual(stopped.exception.code,7)
            self.assertIn("Audit gap: unable to initialize recorder: Python's sqlite3 module is unavailable",stderr.getvalue())
            self.assertIn(h.marker('[+]'),(repo/'tabilet/memory-bank/status-M01.md').read_text())
            self.assertFalse(database.exists())

    def test_competing_post_run_gates_keep_precedence_with_optional_audit(self):
        for audited in (False,True):
            for failure,expected in (('dirty',5),('no_commit',6),('history',9),('transition',8)):
                with self.subTest(audited=audited,failure=failure), tempfile.TemporaryDirectory() as tmp:
                    repo=h.make_repo(Path(tmp)/'repo')
                    database=Path(tmp)/'audit.db'
                    def model(*args):
                        source=repo/'tabilet/memory-bank/status-M01.md'
                        source.write_text(source.read_text().replace(h.marker('[ ]'),h.marker('[~]')))
                        if failure in ('history','transition'):
                            if failure=='history':h.run('git','checkout','-qb','different',cwd=repo)
                            h.run('git','add','-A',cwd=repo)
                            commit=h.run('git','-c','user.name=Test','-c','user.email=test@example.test','commit','-qm','invalid',cwd=repo)
                            self.assertEqual(commit.returncode,0,commit.stderr)
                        return {'final':'done'}
                    env=h.HarnessIntegrationTests().harness_env(tmp,ALLOW_UNSANDBOXED_SHELL='1')
                    argv=[str(h.HARNESS),str(repo)] + (['--audit-db',str(database)] if audited else [])
                    patches=[mock.patch.object(sys,'argv',argv),mock.patch.dict(os.environ,env,clear=True),mock.patch.object(h.harness,'one_agent_run',side_effect=model)]
                    if failure=='no_commit':patches.append(mock.patch.object(h.harness,'git_clean',return_value=True))
                    with patches[0],patches[1],patches[2]:
                        if failure=='no_commit':patches[3].start()
                        try:
                            with self.assertRaises(SystemExit) as stopped:h.harness.main()
                        finally:
                            if failure=='no_commit':patches[3].stop()
                    self.assertEqual(stopped.exception.code,expected)
                    if audited:
                        with sqlite3.connect(database) as connection:
                            reasons=[json.loads(row[0]).get('details',{}).get('reason') for row in connection.execute("SELECT payload_json FROM events WHERE event_type='run_failed'")]
                        self.assertEqual(len(reasons),1)
                        self.assertEqual(reasons[0],{5:'uncommitted changes after model run',6:'model made no commit',9:'history rewrite or branch change',8:'invalid row transition'}[expected])
    def test_embedded_task_keeps_runner_audit_ownership_self_contained(self):
        self.assertIn('Inside the API runner, the runner owns the audit lifecycle: do not look',
                      h.harness.EMBEDDED_TASK)
        self.assertIn('In an interactive skill run, read the\nbundled', h.harness.EMBEDDED_TASK)

    def test_single_file_install_works_without_optional_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'tackle-memory-bank-api-loop'
            shutil.copy(h.HARNESS,target)
            result=subprocess.run([sys.executable,'-B',str(target),'--help'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_blocked_transition_and_commit_before_failed_gate(self):
        for outcome in ('blocked','dirty','unexpected','inside','long'):
            with self.subTest(outcome=outcome),tempfile.TemporaryDirectory() as tmp:
                repo=h.make_repo(Path(tmp)/'repo',h.marker('[~]'))
                database=(repo if outcome=='inside' else Path(tmp))/'audit.db'
                def model(*args):
                    if outcome=='unexpected':raise RuntimeError('test interruption')
                    self.assertEqual(h.run('git','status','--porcelain',cwd=repo).stdout,'')
                    source=repo/'tabilet/memory-bank/status-M01.md'
                    source.write_text(source.read_text().replace(h.marker('[~]'),h.marker('[!]')))
                    h.run('git','add','-A',cwd=repo)
                    commit=h.run('git','-c','user.name=Test','-c','user.email=test@example.test','commit','-qm','blocked',cwd=repo)
                    self.assertEqual(commit.returncode,0,commit.stderr)
                    if outcome=='dirty':(repo/'uncommitted').write_text('changed')
                    return {'final':'x' * 1025 if outcome=='long' else 'Blocked by a missing prerequisite.'}
                env=h.HarnessIntegrationTests().harness_env(tmp,ALLOW_UNSANDBOXED_SHELL='1')
                with mock.patch.object(sys,'argv',[str(h.HARNESS),str(repo),'--audit-db',str(database),'--audit-capture','relevant']),mock.patch.dict(os.environ,env,clear=True),mock.patch.object(h.harness,'one_agent_run',side_effect=model):
                    with self.assertRaises((SystemExit,RuntimeError)) as stopped:h.harness.main()
                if outcome=='inside':
                    self.assertFalse(database.exists())
                    self.assertEqual(stopped.exception.code,7)
                    continue
                c=sqlite3.connect(database)
                try:
                    expected={'blocked':'blocked','dirty':'failed','unexpected':'failed','long':'blocked'}[outcome]
                    self.assertEqual(c.execute('SELECT result FROM runs').fetchone()[0],expected)
                    provenance=c.execute('SELECT fingerprint_fidelity,instruction_set_version,host_version FROM run_provenance').fetchone()
                    self.assertEqual(provenance, ('partial',None,None))
                    if outcome!='unexpected':
                        self.assertEqual(c.execute("SELECT COUNT(*) FROM events WHERE event_type='commit_observed'").fetchone()[0],1)
                        message=c.execute(
                            "SELECT c.content,m.fidelity,m.redaction_note FROM captured_message_content c JOIN captured_messages m USING(message_id) WHERE m.role='assistant'"
                        ).fetchone()
                        if outcome=='long':
                            self.assertLessEqual(len(message[0].decode('utf-8')),1024)
                            self.assertEqual(message[1:],('incomplete','automatic bounded extract; source exceeded 1024 characters'))
                        else:
                            self.assertIn(b'Blocked',message[0])
                    if outcome=='dirty':
                        self.assertEqual(c.execute("SELECT COUNT(*) FROM events WHERE event_type='task_transition'").fetchone()[0],1)
                    if outcome=='blocked':
                        self.assertEqual(c.execute("SELECT milestone_id,new_state FROM events WHERE event_type='task_transition'").fetchone(),('M01','blocked'))
                finally:c.close()
