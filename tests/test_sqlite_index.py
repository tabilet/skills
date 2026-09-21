import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import tabilet_audit as a
import tabilet_index as ix
import test_harness as h


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.root=h.make_repo(self.base/'project')
        self.c=a.open_database(self.base/'state/audit.db');self.addCleanup(self.c.close)
        self.source=self.root/'tabilet/memory-bank/status-M01.md'

    def sync(self,**kwargs):return ix.sync(self.c,self.root,**kwargs)
    def hashes(self):return {str(p.relative_to(self.root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.root/'tabilet').rglob('*.md')}

    def test_search_fallback_and_no_project_writes(self):
        before=self.hashes()
        first=self.sync();w=first['workspace_id']
        result=ix.search(self.c,w,'feature',kind='task',state='pending')
        self.assertEqual(len(result['results']),1)
        self.assertEqual(result['results'][0]['milestone_id'],'M01')
        self.assertEqual(result['results'][0]['line'],5)
        self.assertEqual(self.hashes(),before)
        with mock.patch.object(ix,'parse_document',side_effect=AssertionError('unchanged documents must reuse parse')):
            self.sync()
        fallback=self.sync(force_literal=True)
        self.assertEqual(fallback['search_mode'],'literal')
        self.assertEqual(len(ix.search(self.c,w,'FEATURE',kind='task')['results']),1)
        self.assertEqual(ix.search(self.c,w,'feature',kind='task',offset=1)['results'],[])
        self.assertIn('tasks',ix.show(self.c,w,'tabilet/memory-bank/status-M01.md'))

    def test_real_task_renames_duplicates_reorder_and_retirement_preserve_audit(self):
        initial=self.sync();w=initial['workspace_id']
        run=a.start_run(self.c,w,'next')
        event={'schema':'tabilet.audit.event/v1','event_id':'original','run_id':run,'workspace_id':w,
            'operation':'next','event_type':'task_observed','recorded_at':a.utc_now(),
            'subject':{'milestone_id':'M01','task_label':'Implement feature','status_path':'tabilet/memory-bank/status-M01.md'},
            'details':{'schema':'tabilet.audit.details/v1'}}
        a.append_event(self.c,event)
        recorded=self.c.execute("SELECT payload_json FROM events WHERE event_id='original'").fetchone()[0]
        self.source.write_text('# Tasks\n\n| Item | State | Notes |\n|---|---|---|\n| Duplicate | `[+]` | first |\n| Renamed | `[+]` | second |\n| Duplicate | `[+]` | third |\n')
        self.sync()
        tasks=a.records(self.c,'SELECT * FROM index_tasks ORDER BY line')
        self.assertEqual([r['label'] for r in tasks],['Duplicate','Renamed','Duplicate'])
        self.assertEqual(len({(r['sha256'],r['line']) for r in tasks}),3)
        h.retire_fixture(self.root)
        result=self.sync(rebuild=True)
        self.assertTrue(result['complete'])
        self.assertEqual(self.c.execute('SELECT lifecycle,outcome FROM index_milestones').fetchone(),('retired','completed'))
        tasks=a.records(self.c,'SELECT * FROM index_tasks ORDER BY line')
        retired=self.root/tasks[0]['path']
        self.assertIn('Duplicate',retired.read_text().splitlines()[tasks[0]['line']-1])
        self.assertEqual(len(tasks),3) # specification example must not become a task
        self.assertEqual(self.c.execute("SELECT payload_json FROM events WHERE event_id='original'").fetchone()[0],recorded)

    def test_failed_refresh_preserves_generation_and_deleted_optional_file_disappears(self):
        extra=self.root/'tabilet/memory-bank/lessons.md';extra.write_text('# Lesson\nneedle')
        first=self.sync();w=first['workspace_id']
        extra.unlink();self.sync()
        self.assertEqual(ix.search(self.c,w,'needle')['results'],[])
        stable=ix.status(self.c,w)['generation']
        self.source.write_text('| Invalid | [done] | note |\n')
        with self.assertRaises(a.AuditError):self.sync()
        state=ix.status(self.c,w)
        self.assertEqual(state['generation'],stable)
        self.assertFalse(state['complete']);self.assertTrue(state['diagnostics'])
        self.assertEqual(len(ix.search(self.c,w,'feature',kind='task')['results']),1)

    def test_change_during_scan_and_publication_rollback(self):
        initial=self.sync();w=initial['workspace_id']
        original=ix.read_document
        def racing(root,path):
            value=original(root,path)
            if path.endswith('status-M01.md'):self.source.write_text(self.source.read_text()+'\nchanged')
            return value
        with mock.patch.object(ix,'read_document',side_effect=racing),self.assertRaises(a.AuditError):self.sync()
        self.assertEqual(ix.status(self.c,w)['generation'],initial['generation'])
        self.c.execute("CREATE TRIGGER stop_index BEFORE INSERT ON index_tasks BEGIN SELECT RAISE(ABORT,'interrupted'); END")
        self.c.commit()
        with self.assertRaises(a.AuditError):self.sync()
        self.assertEqual(ix.status(self.c,w)['generation'],initial['generation'])
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM index_tasks').fetchone()[0],1)

    def test_symlinks_legacy_invalid_ids_and_duplicate_milestones(self):
        first=self.sync()
        self.source.unlink();self.source.symlink_to(self.root/'AGENTS.md')
        with self.assertRaises(a.AuditError):self.sync()
        self.source.unlink();self.source.write_text('| Task | `[+]` | verified |\n')
        (self.root/'memory-bank').mkdir()
        with self.assertRaisesRegex(a.AuditError,'mixed layout'):self.sync()
        (self.root/'memory-bank').rmdir()
        bad=self.root/'tabilet/memory-bank/status-M00.md';bad.write_text(self.source.read_text())
        with self.assertRaisesRegex(a.AuditError,'invalid declared'):self.sync()
        bad.unlink()
        history=self.root/'tabilet/docs/history';history.mkdir(parents=True)
        (history/'status-M01.md').write_text(h.retirement_text(self.source.read_text()))
        with self.assertRaisesRegex(a.AuditError,'duplicate'):self.sync()
        self.assertEqual(ix.status(self.c,first['workspace_id'])['generation'],first['generation'])

    def test_archive_only_and_evolution_with_unversioned_provenance(self):
        root=self.base/'archive-only'
        (root/'tabilet/docs').mkdir(parents=True)
        archive=root/'tabilet/docs/archive-M01.md'
        archive.write_text('# Context M01\n\n**Context.** package\n**Baseline.** unversioned\n**Coverage.** verified\n**Supersedes.** none\n')
        (root/'tabilet/evolution').mkdir()
        for kind in ('prompt','result'):(root/f'tabilet/evolution/{kind}-v1.md').write_text('# Direction\ntext')
        state=ix.sync(self.c,root)
        self.assertIsNone(state['git_head'])
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM index_tasks').fetchone()[0],0)
        self.assertEqual(self.c.execute('SELECT relation FROM index_relationships').fetchone()[0],'evolution_pair')
        archive.write_text(archive.read_text()+'\nchanged')
        state=ix.sync(self.c,root)
        self.assertTrue(any('frozen source changed' in d for d in state['diagnostics']))
        archive.unlink();ix.sync(self.c,root)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM index_documents WHERE kind='context_archive'").fetchone()[0],0)

    def test_branch_change_explicit_ids_and_relationships(self):
        milestone=self.root/'tabilet/memory-bank/milestone.md'
        milestone.write_text(milestone.read_text()+'\n**Dependencies.** M02\n')
        self.source.write_text('| ID | State | Notes |\n|---|---|---|\n| FEATURE-1 | `[ ]` | custom explicit ID |\n')
        first=self.sync()
        self.assertEqual(self.c.execute('SELECT explicit_id FROM index_tasks').fetchone()[0],'FEATURE-1')
        self.assertTrue(any('unresolved depends_on' in d for d in first['diagnostics']))
        h.run('git','checkout','-qb','another',cwd=self.root)
        second=self.sync()
        self.assertEqual(second['branch'],'another')
        self.assertNotEqual(first['generation'],second['generation'])

    def test_template_copy_and_linked_dependencies(self):
        import shutil
        copied=self.base/'template-project'
        shutil.copytree(Path(__file__).resolve().parents[1]/'template',copied)
        state=ix.sync(self.c,copied)
        self.assertTrue(state['complete'])
        milestone=copied/'tabilet/memory-bank/milestone.md'
        milestone.write_text(milestone.read_text()+'\n**Dependencies.** [M01](status-M01.md)\n')
        state=ix.sync(self.c,copied)
        self.assertTrue(state['complete'])

    def test_explorer_projection_and_readiness_explain_explicit_dependencies(self):
        self.source.write_text(
            '# Tasks\n\n'
            '| ID | State | Notes |\n|---|---|---|\n'
            '| TASK-A | `[+]` | prerequisite |\n'
            '| TASK-B | `[ ]` | Depends on: TASK-A |\n'
        )
        milestone=self.root/'tabilet/memory-bank/milestone.md'
        milestone.write_text('# Milestone\n\n## M01 - Delivery\n\nSummary of the milestone.\n**Acceptance.** Review the evidence.\n')
        state=self.sync();w=state['workspace_id']
        projection=a.records(self.c,'SELECT milestone_id,display_order,summary,acceptance_text FROM index_milestone_projection')
        self.assertEqual(projection[0]['milestone_id'],'M01')
        self.assertIn('Summary of the milestone.',projection[0]['summary'])
        dependencies=a.records(self.c,'SELECT source_key,target_key,relationship FROM index_task_dependencies')
        self.assertEqual(dependencies,[{'source_key':'TASK-B','target_key':'TASK-A','relationship':'depends_on'}])
        ready=ix.readiness(self.c,w,self.root)
        self.assertEqual([row['task']['task_key'] for row in ready['ready']],['TASK-B'])
        self.source.write_text(
            '# Tasks\n\n| ID | State | Notes |\n|---|---|---|\n'
            '| TASK-A | `[ ]` | prerequisite |\n'
            '| TASK-B | `[ ]` | Depends on: TASK-A |\n'
        )
        self.sync()
        ready=ix.readiness(self.c,w,self.root)
        self.assertEqual([row['task']['task_key'] for row in ready['ready']],['TASK-A'])
        self.assertEqual(ready['waiting'][0]['task']['task_key'],'TASK-B')
        self.assertIn('dependency is pending',ready['waiting'][0]['reason'])

    def test_readiness_withholds_recommendations_for_stale_sources_or_multiple_in_progress(self):
        state=self.sync();w=state['workspace_id']
        self.source.write_text(self.source.read_text().replace('`[ ]`','`[~]`'))
        stale=ix.readiness(self.c,w,self.root)
        self.assertEqual(stale['source_freshness'],'stale')
        self.assertEqual(stale['recommendations'],[])
        self.sync()
        self.source.write_text(
            '# Tasks\n\n| Item | State | Notes |\n|---|---|---|\n'
            '| First | `[~]` | one |\n| Second | `[~]` | two |\n'
        )
        self.sync()
        multiple=ix.readiness(self.c,w,self.root)
        self.assertEqual(multiple['recommendations'],[])
        self.assertTrue(any('multiple in-progress' in item['reason'] for item in multiple['needs_review']))

    def test_readiness_detects_duplicate_ids_cycles_and_cancelled_prerequisites(self):
        milestone = self.root / 'tabilet/memory-bank/milestone.md'
        milestone.write_text(
            '# Milestone\n\n## M01 - First\n\n**Acceptance.** first\n\n'
            '## M02 - Second\n\n**Acceptance.** second\n**Dependencies.** M01\n'
        )
        self.source.write_text(
            '# Status\n\n| ID | State | Notes |\n|---|---|---|\n'
            '| SAME | `[X]` | cancelled prerequisite |\n'
            '| A | `[ ]` | Depends on: B |\n'
        )
        second = self.root / 'tabilet/memory-bank/status-M02.md'
        second.write_text(
            '# Status\n\n| ID | State | Notes |\n|---|---|---|\n'
            '| SAME | `[ ]` | duplicate in another milestone |\n'
            '| B | `[ ]` | Depends on: A |\n'
        )
        state = self.sync(); ready = ix.readiness(self.c, state['workspace_id'], self.root)
        self.assertFalse(ready['recommendations'])
        self.assertTrue(any(item['reason'] == 'dependency cycle requires review' for item in ready['needs_review']))
        self.assertTrue(any('requires review' in item['reason'] for item in ready['waiting']))

    def test_retirement_fenced_heading_does_not_change_task_or_relation_locations(self):
        self.source.write_text('| Old attempt | `[-]` | successor: M02 |\n')
        retired=h.retire_fixture(self.root)
        text=retired.read_text()
        # An inner Markdown example includes a fake envelope heading and fence.
        text=text.replace('Example only:', '````text\n## Status record\n```markdown\nfake\n```\n````\nExample only:')
        retired.write_text(text)
        state=self.sync()
        task=self.c.execute('SELECT line FROM index_tasks').fetchone()[0]
        self.assertIn('Old attempt',text.splitlines()[task-1])
        relation=self.c.execute("SELECT line FROM index_relationships WHERE relation='successor'").fetchone()[0]
        self.assertIn('successor: M02',text.splitlines()[relation-1])
        stable=state['generation']
        retired.write_text(text.replace('**Review.** passed','**Review.** failed'))
        with self.assertRaises(a.AuditError):self.sync()
        self.assertEqual(ix.status(self.c,state['workspace_id'])['generation'],stable)
