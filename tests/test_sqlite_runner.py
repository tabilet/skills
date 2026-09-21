import os
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
    def test_single_file_install_works_without_optional_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'tackle-memory-bank-api-loop'
            shutil.copy(h.HARNESS,target)
            result=subprocess.run([sys.executable,'-B',str(target),'--help'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_blocked_transition_and_commit_before_failed_gate(self):
        for outcome in ('blocked','dirty','unexpected','inside'):
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
                    return {'final':'Blocked by a missing prerequisite.'}
                env=h.HarnessIntegrationTests().harness_env(tmp,ALLOW_UNSANDBOXED_SHELL='1')
                with mock.patch.object(sys,'argv',[str(h.HARNESS),str(repo),'--audit-db',str(database),'--audit-capture','relevant']),mock.patch.dict(os.environ,env,clear=True),mock.patch.object(h.harness,'one_agent_run',side_effect=model):
                    with self.assertRaises((SystemExit,RuntimeError)) as stopped:h.harness.main()
                if outcome=='inside':
                    self.assertFalse(database.exists())
                    self.assertEqual(stopped.exception.code,7)
                    continue
                c=sqlite3.connect(database)
                try:
                    expected={'blocked':'blocked','dirty':'failed','unexpected':'failed'}[outcome]
                    self.assertEqual(c.execute('SELECT result FROM runs').fetchone()[0],expected)
                    if outcome!='unexpected':
                        self.assertEqual(c.execute("SELECT COUNT(*) FROM events WHERE event_type='commit_observed'").fetchone()[0],1)
                        self.assertIn('Blocked',c.execute("SELECT text FROM captured_messages WHERE role='assistant'").fetchone()[0])
                    if outcome=='blocked':
                        self.assertEqual(c.execute("SELECT milestone_id,new_state FROM events WHERE event_type='task_transition'").fetchone(),('M01','blocked'))
                finally:c.close()
