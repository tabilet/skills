import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
import importlib.util
from unittest import mock
import test_harness as h

CLI=Path(__file__).resolve().parents[1]/'harness/tabilet_audit_host.py'


class CliTests(unittest.TestCase):
    def test_incompatible_toolkit_interface_fails_before_opening_database(self):
        sys.path.insert(0,str(CLI.parent))
        spec=importlib.util.spec_from_file_location('audit_host_under_test',CLI)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with mock.patch.object(module.index,'TOOLKIT_INTERFACE',99):
            self.assertEqual(module.main(['index','status','/nonexistent']),2)

    def test_missing_sqlite_module_is_one_plain_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Shadow the standard module the way a Python built without SQLite
            # behaves: importing sqlite3 raises ImportError.
            Path(tmp,'sqlite3.py').write_text("raise ImportError(\"No module named '_sqlite3'\")\n")
            env=dict(os.environ,PYTHONPATH=tmp)
            result=subprocess.run([sys.executable,'-B',str(CLI),'audit','runs'],text=True,capture_output=True,env=env)
            self.assertEqual(result.returncode,2,result.stderr)
            self.assertNotIn('Traceback',result.stderr)
            self.assertIn("Python's sqlite3 module is unavailable",result.stderr)
            self.assertIn('3.24.0 or later',result.stderr)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.repo=h.make_repo(self.base/'project')
        self.db=self.base/'state/audit.db'
        self.cli=CLI

    def command(self,*arguments,data=None,ok=True):
        env=dict(os.environ)
        env.pop('TABILET_AUDIT_CAPTURE',None)
        result=subprocess.run([sys.executable,'-B',str(self.cli),'--audit-db',str(self.db),*map(str,arguments)],input=json.dumps(data) if data is not None else None,text=True,capture_output=True,env=env)
        self.assertEqual(result.returncode,0 if ok else 2,result.stderr)
        self.assertNotIn('Traceback',result.stderr)
        return json.loads(result.stdout) if ok else result.stderr

    def test_fresh_complete_lifecycle_retries_queries_and_capture(self):
        started=self.command('audit','begin',self.repo,'goal','--run-id','parent','--capture','relevant')
        self.assertEqual(started,self.command('audit','begin',self.repo,'goal','--run-id','parent','--capture','relevant'))
        child=self.command('audit','begin',self.repo,'next','--parent-run-id','parent','--run-id','child')
        event={'schema':'tabilet.audit.event/v1','event_id':'event1','run_id':'child','workspace_id':child['workspace_id'],'operation':'next','event_type':'task_observed','subject':{'milestone_id':'M01','task_label':'Implement feature'},'details':{'schema':'tabilet.audit.details/v1','capture_source':'agent','fidelity':'summarized'}}
        first=self.command('audit','event',data=event)
        self.assertEqual(first,self.command('audit','event',data=event))
        message=dict(run_id='parent',role='user',text='Selected request',capture_source='host',fidelity='exact',message_id='request1')
        self.command('audit','message',data=message)
        self.command('audit','message',data=message)
        self.command('audit','message',data={**message,'run_id':'child','message_id':'denied'},ok=False)
        self.command('audit','finish','child','blocked')
        self.command('audit','finish','parent','blocked')
        results=self.command('audit','runs','--project',self.repo,'--milestone','M01','--task','Implement feature')['results']
        self.assertEqual([r['run_id'] for r in results],['child'])
        events=self.command('audit','events','--run-id','child','--limit','1','--offset','1')['results']
        self.assertEqual(events[0]['event_id'],'event1')
        exported=self.command('audit','export')
        self.assertIn('messages',exported['runs'][0])
        exported=self.command('audit','export','--include-content')
        self.assertEqual(sum(len(r['messages']) for r in exported['runs']),1)
        indexed=self.command('index','status',self.repo)
        self.assertTrue(indexed['complete'])
        self.assertEqual(len(self.command('index','search',self.repo,'feature','--kind','task')['results']),1)
        self.assertEqual(self.command('index','show',self.repo,'tabilet/memory-bank/status-M01.md')['tasks'][0]['milestone_id'],'M01')
        self.command('backup',self.base/'backup.db')
        self.command('backup',self.base/'backup.db',ok=False)
        self.command('restore',self.base/'restored.db')

    def test_all_operations_no_capture_and_read_commands_never_create(self):
        self.command('index','status',self.repo,ok=False)
        self.assertFalse(self.db.exists())
        for operation in ('init','archive','propose','reconcile','next','goal','upgrade'):
            result=self.command('audit','begin',self.repo,operation)
            self.command('audit','finish',result['run_id'],'completed')
        c=sqlite3.connect(self.db)
        try:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM captured_messages').fetchone()[0],0)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM runs').fetchone()[0],7)
        finally:c.close()

    def test_external_dependency_file_persists_across_finish_and_can_be_cleared(self):
        source=self.repo/'tabilet/memory-bank/status-M01.md'
        source.write_text(source.read_text().replace('`[ ]`','`[+]`')+'\n**Dependencies.** M79.\n')
        h.retire_fixture(self.repo)
        path='tabilet/docs/history/status-M01.md'
        mapping={'schema':'tabilet.index.external-dependencies/v1','references':[{
            'source_path':path,'source_sha256':hashlib.sha256((self.repo/path).read_bytes()).hexdigest(),
            'dependency_id':'M79','package':'apitools'}]}
        config=self.base/'dependencies.json';config.write_text(json.dumps(mapping))
        before=(self.repo/path).read_bytes()
        result=self.command('index','sync',self.repo,'--external-dependencies',config)
        self.assertEqual(result['diagnostics'],[])
        shown=self.command('index','show',self.repo,path)
        self.assertEqual(shown['relationships'][0]['target'],'external:apitools:M79')
        begun=self.command('audit','begin',self.repo,'next')
        finished=self.command('audit','finish',begun['run_id'],'completed')
        self.assertEqual(finished['index']['diagnostics'],[])
        self.assertEqual((self.repo/path).read_bytes(),before)
        cleared=self.command('index','sync',self.repo,'--clear-external-dependencies')
        self.assertTrue(any('unresolved depends_on: milestone:M79' in d for d in cleared['diagnostics']))
        self.assertIn('not allowed with argument',self.command('index','sync',self.repo,'--external-dependencies',config,'--clear-external-dependencies',ok=False))

    def test_events_apply_run_provenance_coverage_and_purge_filters(self):
        provenance={"invocation_kind":"interactive_skill","instruction_set_name":"memory-bank-next",
                    "instruction_set_version":"1","host_agent":"test-host","model":"test-model",
                    "capture_method":"instruction_driven","fingerprint_fidelity":"unavailable"}
        provenance_file=self.base/'provenance.json';provenance_file.write_text(json.dumps(provenance))
        begun=self.command('audit','begin',self.repo,'next','--run-id','filtered','--capture','relevant',
                           '--provenance',provenance_file)
        self.command('audit','begin',self.repo,'next','--run-id','other')
        for run, identifier in [('filtered','matching-event'),('other','other-event')]:
            self.command('audit','event',data={"schema":"tabilet.audit.event/v1","event_id":identifier,
                "run_id":run,"workspace_id":begun['workspace_id'],"operation":"next","event_type":"task_observed",
                "subject":{"milestone_id":"M01","task_label":"Task"},
                "details":{"schema":"tabilet.audit.details/v1","capture_source":"agent","fidelity":"summarized"}})
        self.command('audit','message',data={"run_id":"filtered","message_id":"filtered-message","role":"user",
            "text":"private","capture_source":"host","fidelity":"exact"})
        self.command('audit','coverage',data={"coverage_id":"filtered-coverage","run_id":"filtered",
            "scope":"skill_conversation","coverage":"complete","content_state":"available",
            "exact_count":1,"capture_method":"instruction_driven"})
        filters=['--instruction-set','memory-bank-next','--instruction-set-version','1','--host','test-host',
                 '--model','test-model','--capture-method','instruction_driven','--coverage','complete']
        expected=['filtered:started','matching-event']
        self.assertEqual([r['event_id'] for r in self.command('audit','events',*filters)['results']], expected)
        for index in range(0,len(filters),2):
            self.assertEqual([r['event_id'] for r in self.command('audit','events',*filters[index:index+2])['results']], expected)
        self.assertEqual(self.command('audit','events','--coverage','missing')['results'],[])
        purged=self.command('audit','purge-message','filtered-message','--reason','request','--confirm','filtered-message')
        self.assertTrue(purged['cleanup']['compaction']['ok'])
        self.assertEqual([r['event_id'] for r in self.command('audit','events','--purged','--milestone','M01','--task','Task')['results']],
                         ['matching-event'])
        self.assertEqual(self.command('audit','events','--coverage','complete')['results'],[])

    def test_relevant_message_capture_rejects_oversized_text(self):
        self.command('audit','begin',self.repo,'next','--run-id','bounded','--capture','relevant')
        oversized={
            'run_id':'bounded','message_id':'too-long','role':'user',
            'text':'x' * 1025,'capture_source':'host','fidelity':'exact',
        }
        error=self.command('audit','message',data=oversized,ok=False)
        self.assertIn('exceeds 1024 characters',error)
        summary={**oversized,'message_id':'summary','text':'User requested the next task with the stated constraints.',
                 'capture_source':'agent','fidelity':'summarized'}
        self.command('audit','message',data=summary)

    def test_finish_indexes_inconsistent_history_without_rewriting_source_or_audit(self):
        source=self.repo/'tabilet/memory-bank/status-M01.md'
        source.write_text(source.read_text().replace('`[ ]`', '`[~]`') +
            '\n## Milestone review\n\n| Iteration | State | Findings |\n|---|---|---|\n'
            '| 1 | findings fixed | evidence |\n| 2 | passed | clean |\n')
        retired=h.retire_fixture(self.repo)
        original=retired.read_bytes()
        started=self.command('audit','begin',self.repo,'next')
        finished=self.command('audit','finish',started['run_id'],'completed')
        self.assertTrue(finished['index']['complete'])
        state=self.command('index','status',self.repo)
        self.assertTrue(state['complete'])
        self.assertTrue(any('retired task retains in_progress' in d for d in state['diagnostics']))
        audit_before=self.command('audit','export')
        self.command('index','sync',self.repo,'--rebuild')
        self.assertEqual(self.command('audit','export'),audit_before)
        self.assertEqual(retired.read_bytes(),original)

    def test_packaged_toolkit_works_and_rebuild_preserves_audit(self):
        installation=self.base/'bin';installation.mkdir()
        for name in ('tabilet_audit.py','tabilet_index.py','tabilet_explorer.py','tackle-memory-bank-api-loop'):
            shutil.copy(CLI.with_name(name),installation/name)
        shutil.copytree(CLI.with_name('explorer'), installation/'explorer')
        self.cli=installation/'tabilet-audit';shutil.copy(CLI,self.cli)
        start=self.command('audit','begin',self.repo,'propose')
        self.command('audit','finish',start['run_id'],'completed')
        prior=self.command('audit','export')
        self.command('index','sync',self.repo,'--rebuild','--literal')
        self.assertEqual(self.command('audit','export'),prior)
        self.assertEqual(self.command('index','search',self.repo,'feature')['index']['search_mode'],'literal')
        environment=dict(os.environ);environment['HOME']=str(self.base/'home');Path(environment['HOME']).mkdir()
        process=subprocess.Popen(
            [sys.executable,'-B',str(self.cli),'--audit-db',str(self.db),'explorer',str(self.repo),'--port','0'],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=environment,
        )
        try:
            url=process.stdout.readline().strip().removeprefix('Tabilet Explorer: ')
            self.assertTrue(url.startswith('http://localhost:'), process.stderr.read() if process.poll() is not None else url)
            with urllib.request.urlopen(url,timeout=5) as response:
                self.assertIn('Tabilet Explorer',response.read().decode())
            with urllib.request.urlopen(url+'assets/explorer.js',timeout=5) as response:
                self.assertIn('Recorded then',response.read().decode())
        finally:
            process.terminate();process.wait(timeout=5)
            process.stdout.close();process.stderr.close()
        (installation/'explorer/index.html').unlink()
        process=subprocess.Popen(
            [sys.executable,'-B',str(self.cli),'--audit-db',str(self.db),'explorer',str(self.repo),'--port','0'],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=environment,
        )
        try:
            url=process.stdout.readline().strip().removeprefix('Tabilet Explorer: ')
            with self.assertRaises(urllib.error.HTTPError) as failure:
                urllib.request.urlopen(url,timeout=5)
            self.assertEqual(failure.exception.code,400)
            self.assertIn('missing explorer asset',failure.exception.read().decode())
            failure.exception.close()
        finally:
            process.terminate();process.wait(timeout=5)
            process.stdout.close();process.stderr.close()
        self.assertFalse(list(installation.rglob('__pycache__')))

    def test_internal_database_and_legacy_project_stop_before_writes(self):
        self.db=self.repo/'audit.db'
        self.command('audit','begin',self.repo,'init',ok=False)
        self.assertFalse(self.db.exists())
        self.db=self.base/'elsewhere.db'
        (self.repo/'memory-bank').mkdir()
        self.command('audit','begin',self.repo,'upgrade',ok=False)
        self.command('index','sync',self.repo,ok=False)
        self.assertFalse(self.db.exists())

    def test_begin_retry_reuses_recorded_identity_after_project_changes(self):
        first = self.command('audit', 'begin', self.repo, 'goal', '--run-id', 'stable-run')
        (self.repo / 'work-started-after-begin').write_text('changed after the recorded start')
        second = self.command('audit', 'begin', self.repo, 'goal', '--run-id', 'stable-run')
        self.assertEqual(second, first)

    def test_existing_mixed_layout_refresh_records_incomplete_index_state(self):
        self.command('index', 'sync', self.repo)
        (self.repo / 'memory-bank').mkdir()
        self.command('index', 'sync', self.repo, ok=False)
        state = self.command('index', 'status', self.repo)
        self.assertFalse(state['complete'])
        self.assertTrue(state['diagnostics'])
