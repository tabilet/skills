import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
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

    def test_provisional_stages_are_searchable_without_execution_edges(self):
        baseline=self.sync(); workspace=baseline['workspace_id']
        ready_before=ix.readiness(self.c,workspace,self.root)['ready']
        stages=self.root/'tabilet/stages.md'
        stages.write_text(
            '# Stages\n\n**Current stage.** STG-01\n\n'
            '## STG-01\n\n**Name.** First delivery\n'
            '**Intent.** Verify the core workflow.\n\n'
            '## STG-02\n\n**Name.** Tentative expansion\n'
            '**Intent.** Consider exports later.\n'
            '**Dependencies.** M01 is a possible prerequisite, not an approved plan.\n'
        )
        original=stages.read_bytes()
        self.sync()
        self.assertEqual(stages.read_bytes(),original)
        row=self.c.execute(
            "SELECT kind, text FROM index_documents WHERE path='tabilet/stages.md'"
        ).fetchone()
        self.assertEqual(row[0],'stages')
        self.assertIn('Consider exports later',row[1])
        matches=ix.search(self.c,workspace,'Tentative expansion',kind='stages')['results']
        self.assertEqual(len(matches),1)
        self.assertEqual(matches[0]['path'],'tabilet/stages.md')
        self.assertEqual(self.c.execute(
            "SELECT COUNT(*) FROM index_sections WHERE path='tabilet/stages.md'"
        ).fetchone()[0],3)
        self.assertEqual(self.c.execute(
            "SELECT COUNT(*) FROM index_relationships WHERE path='tabilet/stages.md'"
        ).fetchone()[0],0)
        self.assertEqual(self.c.execute(
            "SELECT COUNT(*) FROM index_tasks WHERE path='tabilet/stages.md'"
        ).fetchone()[0],0)
        self.assertEqual(ix.readiness(self.c,workspace,self.root)['ready'],ready_before)

    def test_malformed_fts_query_falls_back_to_literal(self):
        state=self.sync()
        for term in ('"', 'feature:', 'feature AND ('):
            result=ix.search(self.c,state['workspace_id'],term)
            self.assertEqual(result['results'],[])
            self.assertEqual(result['query_mode'],'literal')
        self.assertEqual(len(ix.search(self.c,state['workspace_id'],'feature')['results']) > 0,True)

    def test_task_notes_do_not_create_milestone_edges_and_prose_stays_visible(self):
        self.source.write_text(
            '| ID | State | Notes |\n|---|---|---|\n'
            '| T01 | `[ ]` | Depends on: M02/T99, discuss later |\n'
            '| T02 | `[ ]` | Depends on: T01, T01 |\n'
        )
        state=self.sync();w=state['workspace_id']
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM index_relationships WHERE relation="depends_on"').fetchone()[0],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM index_task_dependencies WHERE source_key="M01/T02"').fetchone()[0],1)
        readiness=ix.readiness(self.c,w,self.root)
        unresolved=next(row for row in readiness['waiting'] if row['task']['explicit_id']=='T01')
        self.assertIn('discuss later',unresolved['task']['notes'])
        self.assertTrue(any(not ref['resolved'] for ref in unresolved['task']['prerequisites']))

    def test_repeated_milestone_dependency_has_one_index_edge(self):
        milestone=self.root/'tabilet/memory-bank/milestone.md'
        milestone.write_text(milestone.read_text()+'\n**Dependencies.** M02\n**Depends on:** M02\n')
        self.source.write_text(self.source.read_text()+'\n**Dependencies.** M02\n')
        (self.root/'tabilet/memory-bank/status-M02.md').write_text(
            '| Item | State | Notes |\n|---|---|---|\n| Other | `[ ]` | pending |\n')
        milestone.write_text(milestone.read_text()+'\n## M02 - Other\n\n**Acceptance.** Other works.\n')
        self.sync()
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM index_relationships WHERE source='milestone:M01' AND relation='depends_on' AND target='milestone:M02'").fetchone()[0],1)

    def test_scope_prose_does_not_create_dependency_fields_in_active_or_retired_records(self):
        self.source.write_text(self.source.read_text()+
            '\n**Scope and compatibility.** Defer UI dependencies. This does not require future W28.\n'
            'Narrative mentions a Successor M79 without declaring one.\n'
            '\n- **Dependencies.** M02.\n')
        self.sync()
        self.assertEqual(set(self.c.execute("SELECT target FROM index_relationships WHERE relation='depends_on'")),{('milestone:M02',)})
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM index_relationships WHERE relation='successor'").fetchone()[0],0)
        self.source.write_text(self.source.read_text().replace('`[ ]`','`[+]`'))
        h.retire_fixture(self.root)
        state=self.sync()
        self.assertEqual(len(state['diagnostics']),1)
        self.assertIn('milestone:M02',state['diagnostics'][0])
        self.assertEqual(set(self.c.execute("SELECT target FROM index_relationships WHERE relation='depends_on'")),{('milestone:M02',)})

    def test_parser_revision_rebuilds_cached_prose_edges_automatically(self):
        self.source.write_text(self.source.read_text()+
            '\n**Scope.** Defer dependencies. W28 is not a prerequisite.\n')
        baseline=self.sync();w=baseline['workspace_id']
        with self.c:
            self.c.execute('UPDATE schema_meta SET value=? WHERE key=?',('v3',f'index_projection:{w}'))
            self.c.execute("INSERT INTO index_relationships VALUES (?,?,?,?,?,?)",(w,'tabilet/memory-bank/status-M01.md',8,'milestone:M01','depends_on','milestone:W28'))
        state=self.sync()
        self.assertEqual(state['diagnostics'],[])
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM index_relationships WHERE target='milestone:W28'").fetchone()[0],0)
        self.assertEqual(self.c.execute('SELECT value FROM schema_meta WHERE key=?',(f'index_projection:{w}',)).fetchone(),(ix.INDEX_PROJECTION,))

    def test_retired_sibling_dependencies_are_not_missing_local_milestones(self):
        self.source.write_text(self.source.read_text().replace('`[ ]`','`[+]`')+
            '\n**Dependencies.** Local M02, APItools M79, OpenUdon M89; the M89 implementation is published.\n'
            '[APItools M79](../../../apitools/tabilet/docs/history/status-M79.md)\n'
            '[OpenUdon M89](../../../openudon/tabilet/docs/history/status-M89.md)\n')
        h.retire_fixture(self.root)
        state=self.sync()
        unresolved=[d for d in state['diagnostics'] if 'unresolved depends_on' in d]
        self.assertEqual(len(unresolved),1)
        self.assertIn('milestone:M02',unresolved[0])
        targets={row[0] for row in self.c.execute(
            "SELECT target FROM index_relationships WHERE relation='depends_on'")}
        self.assertEqual(targets,{'milestone:M02','external:apitools:M79','external:openudon:M89'})

    def test_legacy_retirement_envelopes_preserve_literal_bytes_and_locations(self):
        status = self.source.read_text().replace('`[ ]`', '`[+]`')
        canonical = h.retirement_text(status)
        variants = (
            ('````', '## Status record', ''), ('~~~~', '## Status record', ''),
            ('````', '## Status', ''), ('~~~~', '## Status', ''),
            ('````', '## Status', 'markdown'), ('~~~~', '## Status', 'markdown'),
            ('````', '## Full status document', ''),
            ('~~~~', '## Full status document', 'markdown'),
        )
        for fence, heading, label in variants:
            with self.subTest(fence=fence, heading=heading, label=label):
                text = canonical.replace('\n`````\n\n## Status record\n',
                                         '\n`````\n\n' + heading + '\n')
                text = text.replace('\n`````markdown\n', '\n' + fence + label + '\n')
                text = text.replace('\n`````\n', '\n' + fence + '\n')
                with self.assertRaises(ValueError):
                    ix.parser().retired_record(text, 'status-M01.md')
                path = 'tabilet/docs/history/status-M01.md'
                parsed = ix.parse_document(path, 'history_status', text, 'digest')
                task = parsed['index_tasks'][0]
                self.assertIn('Implement feature', text.splitlines()[task['line'] - 1])
                record, _ = ix.retired_record_for_index(text, 'status-M01.md')
                self.assertEqual(record['status'], status)
                self.assertEqual(record['specification'],
                                 ix.parser().retired_record(canonical, 'status-M01.md')['specification'])
        retired = h.retire_fixture(self.root)
        retired.write_text(canonical.replace('\n`````markdown\n', '\n`````\n')
                          .replace('\n`````\n\n## Status record\n',
                                   '\n`````\n\n## Full status document\n'))
        before = self.hashes()
        state = self.sync()
        self.assertTrue(state['complete'])
        self.assertEqual(self.hashes(), before)
        stored = self.c.execute('SELECT text FROM index_documents WHERE path=?',
                                ('tabilet/docs/history/status-M01.md',)).fetchone()[0]
        self.assertEqual(stored, retired.read_text())

    def test_legacy_retirement_compatibility_still_rejects_invalid_records(self):
        self.source.write_text(self.source.read_text().replace('`[ ]`', '`[+]`'))
        retired = h.retire_fixture(self.root)
        valid = retired.read_text().replace('\n`````markdown\n', '\n`````\n')
        valid = valid.replace('\n`````\n\n## Status record\n', '\n`````\n\n## Status\n')
        retired.write_text(valid)
        initial = self.sync()
        bad_records = (
            valid.replace('**Review.** passed', '**Review.** failed'),
            valid.replace('`[+]`', '`[ ]`'),
            valid.replace('## Status', '## Unknown'),
            valid.replace('`````\n# Status', '`````python\n# Status'),
            valid.rsplit('`````', 1)[0],
            valid.replace('| Implement feature', '`````\n| Implement feature'),
            valid.replace('## Status\n', '## Full status document\n')
                 .replace('**Review.** passed', '**Review.** failed'),
        )
        for text in bad_records:
            with self.subTest(text=text[:40]):
                retired.write_text(text)
                with self.assertRaises(a.AuditError):
                    self.sync()
                self.assertEqual(ix.status(self.c, initial['workspace_id'])['generation'], initial['generation'])

    def test_active_sibling_dependency_requires_manual_reconciliation(self):
        self.source.write_text(self.source.read_text()+
            '\n**Dependencies.** APItools M79.\n'
            '[APItools M79](../../../apitools/tabilet/docs/history/status-M79.md)\n')
        state=self.sync()
        readiness=ix.readiness(self.c,state['workspace_id'],self.root)
        self.assertEqual(readiness['ready'],[])
        self.assertEqual(len(readiness['waiting']),1)
        self.assertIn('external:apitools:M79',readiness['waiting'][0]['reason'])
        self.assertTrue(any('manual reconciliation' in d
            for item in readiness['needs_review'] for d in item.get('diagnostics',[])))

    def test_unqualified_dependency_remains_local_with_sibling_link_elsewhere(self):
        self.source.write_text(self.source.read_text()+
            '\n**Dependencies.** M79.\n'
            '[Sibling M79](../../../apitools/tabilet/docs/history/status-M79.md)\n')
        state=self.sync()
        self.assertTrue(any('unresolved depends_on: milestone:M79' in d
                            for d in state['diagnostics']))
        self.assertEqual(self.c.execute(
            "SELECT target FROM index_relationships WHERE relation='depends_on'").fetchone(),
            ('milestone:M79',))

    def historical_mapping(self, dependency='M79', package='apitools'):
        self.source.write_text(self.source.read_text().replace('`[ ]`','`[+]`')+
                               f'\n**Dependencies.** {dependency}.\n')
        h.retire_fixture(self.root)
        path='tabilet/docs/history/status-M01.md'
        return {'schema':ix.EXTERNAL_DEPENDENCIES_SCHEMA,'references':[{
            'source_path':path,'source_sha256':hashlib.sha256((self.root/path).read_bytes()).hexdigest(),
            'dependency_id':dependency,'package':package}]}

    def test_explicit_historical_mapping_persists_without_source_or_audit_changes(self):
        mapping=self.historical_mapping()
        before=self.hashes();baseline=self.sync()
        self.assertTrue(any('unresolved depends_on: milestone:M79' in d for d in baseline['diagnostics']))
        run=a.start_run(self.c,baseline['workspace_id'],'next',run_id='map-observation')
        audit_before=self.c.execute('SELECT * FROM runs').fetchall()
        state=self.sync(dependency_map=mapping)
        self.assertEqual(state['diagnostics'],[])
        self.assertEqual(self.c.execute("SELECT target FROM index_relationships WHERE relation='depends_on'").fetchone(),('external:apitools:M79',))
        self.assertEqual(self.hashes(),before)
        self.assertEqual(self.c.execute('SELECT * FROM runs').fetchall(),audit_before)
        self.assertEqual(ix.readiness(self.c,state['workspace_id'],self.root)['ready'],[])
        # Ordinary audit-finish refreshes and later rebuilds retain the correction.
        self.assertEqual(self.sync()['diagnostics'],[])
        self.assertEqual(self.sync(rebuild=True)['diagnostics'],[])
        self.assertEqual(self.c.execute('SELECT run_id FROM runs').fetchone(),(run,))

    def test_clear_or_replace_historical_mapping_reconstructs_original_edges(self):
        mapping=self.historical_mapping()
        self.sync(dependency_map=mapping)
        changed=json.loads(json.dumps(mapping));changed['references'][0]['package']='other-owner'
        self.sync(dependency_map=changed)
        self.assertEqual(self.c.execute("SELECT target FROM index_relationships WHERE relation='depends_on'").fetchone(),('external:other-owner:M79',))
        empty={'schema':ix.EXTERNAL_DEPENDENCIES_SCHEMA,'references':[]}
        state=self.sync(dependency_map=empty)
        self.assertTrue(any('unresolved depends_on: milestone:M79' in d for d in state['diagnostics']))
        self.assertEqual(self.c.execute("SELECT target FROM index_relationships WHERE relation='depends_on'").fetchone(),('milestone:M79',))
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM schema_meta WHERE key LIKE 'index_external_dependencies:%'").fetchone()[0],0)
        self.assertEqual(self.sync()['diagnostics'],state['diagnostics'])

    def test_historical_mapping_does_not_change_active_dependencies_or_local_id_scope(self):
        mapping=self.historical_mapping(dependency='M02')
        status=self.root/'tabilet/memory-bank/status-M02.md'
        status.write_text('| Item | State | Notes |\n|---|---|---|\n| Other | `[ ]` | pending |\n\n**Dependencies.** M79.\n')
        milestone=self.root/'tabilet/memory-bank/milestone.md'
        milestone.write_text(milestone.read_text()+'\n## M02 - Other\n\n**Acceptance.** Other works.\n')
        baseline=self.sync()
        readiness_before=ix.readiness(self.c,baseline['workspace_id'],self.root)
        state=self.sync(dependency_map=mapping)
        targets=set(self.c.execute("SELECT source,target FROM index_relationships WHERE relation='depends_on'"))
        self.assertEqual(targets,{('milestone:M01','external:apitools:M02'),('milestone:M02','milestone:M79')})
        self.assertTrue(any('unresolved depends_on: milestone:M79' in d for d in state['diagnostics']))
        self.assertEqual(ix.readiness(self.c,state['workspace_id'],self.root)['ready'],readiness_before['ready'])
        invalid=json.loads(json.dumps(mapping));invalid['references'][0]['source_path']='tabilet/memory-bank/status-M02.md'
        with self.assertRaisesRegex(a.AuditError,'path, hash'):
            self.sync(dependency_map=invalid)

    def test_stale_historical_mapping_never_changes_dependency(self):
        mapping=self.historical_mapping()
        self.sync(dependency_map=mapping)
        path=self.root/mapping['references'][0]['source_path']
        path.write_text(path.read_text().replace('Keep this note.','A changed historical observation.'))
        state=self.sync()
        self.assertTrue(any('frozen source changed' in d for d in state['diagnostics']))
        self.assertTrue(any('stale external dependency mapping' in d for d in state['diagnostics']))
        self.assertTrue(any('unresolved depends_on: milestone:M79' in d for d in state['diagnostics']))
        self.assertEqual(self.c.execute("SELECT target FROM index_relationships WHERE relation='depends_on'").fetchone(),('milestone:M79',))

    def test_invalid_historical_mapping_retains_prior_generation_and_configuration(self):
        mapping=self.historical_mapping()
        baseline=self.sync(dependency_map=mapping)
        config=self.c.execute("SELECT value FROM schema_meta WHERE key LIKE 'index_external_dependencies:%'").fetchone()
        bad=json.loads(json.dumps(mapping));bad['references'][0]['dependency_id']='M80'
        with self.assertRaisesRegex(a.AuditError,'not declared'):
            self.sync(dependency_map=bad)
        self.assertEqual(ix.status(self.c,baseline['workspace_id'])['generation'],baseline['generation'])
        self.assertEqual(self.c.execute("SELECT value FROM schema_meta WHERE key LIKE 'index_external_dependencies:%'").fetchone(),config)
        self.assertEqual(self.sync()['diagnostics'],[])
        duplicates=json.loads(json.dumps(mapping));duplicates['references']*=2
        with self.assertRaisesRegex(a.AuditError,'duplicate'):
            self.sync(dependency_map=duplicates)

    def test_historical_mapping_conflict_and_invalid_input_stay_visible(self):
        mapping=self.historical_mapping()
        path=self.root/mapping['references'][0]['source_path']
        path.write_text(path.read_text().replace('**Dependencies.** M79.',
            '**Dependencies.** Other M79.\n[Other M79](../../../other/tabilet/docs/history/status-M79.md)'))
        mapping['references'][0]['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(a.AuditError,'conflicts with named owner'):
            self.sync(dependency_map=mapping)
        for field,value in [('package','../apitools'),('source_sha256','0'*63),('dependency_id','M00'),('source_path','tabilet/docs/history/../history/status-M01.md')]:
            bad=json.loads(json.dumps(mapping));bad['references'][0][field]=value
            with self.subTest(field=field),self.assertRaises(a.AuditError):
                ix.external_dependencies(bad)
        with self.assertRaises(a.AuditError):
            ix.external_dependencies({'schema':'unsupported','references':[]})

    def test_refresh_cannot_publish_against_concurrently_replaced_mapping(self):
        mapping=self.historical_mapping()
        baseline=self.sync(dependency_map=mapping)
        key=f'index_external_dependencies:{baseline["workspace_id"]}'
        replacement=json.loads(json.dumps(mapping));replacement['references'][0]['package']='other-owner'
        original=ix.publish
        def replace_before_publish(*args,**kwargs):
            with self.c:
                self.c.execute('UPDATE schema_meta SET value=? WHERE key=?',(a.canonical_json(replacement),key))
            return original(*args,**kwargs)
        with mock.patch.object(ix,'publish',side_effect=replace_before_publish):
            with self.assertRaisesRegex(a.AuditError,'mappings changed during refresh'):
                self.sync()
        self.assertEqual(ix.status(self.c,baseline['workspace_id'])['generation'],baseline['generation'])
        self.assertEqual(self.c.execute('SELECT value FROM schema_meta WHERE key=?',(key,)).fetchone(),(a.canonical_json(replacement),))
        # An explicit replacement reparses original bytes before publication.
        self.assertEqual(self.sync(dependency_map=replacement)['diagnostics'],[])

    def test_nested_milestone_heading_is_not_an_active_specification(self):
        milestone=self.root/'tabilet/memory-bank/milestone.md'
        milestone.write_text(milestone.read_text()+'\n### M02 example\n\nNested note.\n')
        state=self.sync()
        self.assertTrue(state['complete'])
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM index_milestone_projection').fetchone()[0],1)

    def test_historical_attempt_points_to_successor_without_veto(self):
        self.source.write_text(
            '| ID | State | Notes |\n|---|---|---|\n'
            '| T01 | `[-]` | Failed attempt; accepted successor T02 |\n'
            '| T02 | `[ ]` | Depends on: T01 |\n'
        )
        state=self.sync();view=ix.readiness(self.c,state['workspace_id'],self.root)
        successor=next(item['task'] for item in view['ready'] if item['task']['explicit_id']=='T02')
        self.assertEqual(successor['prerequisites'][0]['state'],'historical')
        self.assertIn('accepted successor T02',successor['prerequisites'][0]['notes'])

    def test_index_rejects_zero_status_id(self):
        (self.root/'tabilet/memory-bank/status-M00.md').write_text('| Item | State | Notes |\n|---|---|---|\n| X | `[ ]` | x |\n')
        with self.assertRaisesRegex(a.AuditError,'invalid declared filename'):
            self.sync()

    def test_earlier_failed_sync_cannot_mark_newer_generation_incomplete(self):
        first=self.sync(); workspace=first['workspace_id']
        waiting=threading.Event(); release=threading.Event(); original=ix.publish
        outcomes=[]
        def publish(*args,**kwargs):
            if threading.current_thread().name=='slow-sync':
                waiting.set()
                self.assertTrue(release.wait(5))
                raise OSError('injected earlier failure')
            return original(*args,**kwargs)
        def slow():
            with a.open_database(self.base/'state/audit.db') as connection:
                try: ix.sync(connection,self.root)
                except a.AuditError as exc: outcomes.append(str(exc))
        with mock.patch.object(ix,'publish',side_effect=publish):
            thread=threading.Thread(target=slow,name='slow-sync');thread.start()
            self.assertTrue(waiting.wait(5))
            newer=self.sync()
            release.set();thread.join(5)
        self.assertTrue(outcomes)
        self.assertEqual(ix.status(self.c,workspace)['generation'],newer['generation'])
        self.assertTrue(ix.status(self.c,workspace)['complete'])

    def test_milestone_search_and_table_local_task_ids(self):
        self.source.write_text(
            '| ID | State | Notes |\n|---|---|---|\n| T0 | `[+]` | prior |\n\n'
            '| Item | Status | Notes |\n|---|---|---|\n| Alpha | `[ ]` | current |\n'
        )
        milestone = self.root / 'tabilet/memory-bank/milestone.md'
        milestone.write_text('# Milestone\n\n## M01 - Delivery\n\n**Acceptance.** Feature works.\n')
        state = self.sync(); workspace = state['workspace_id']
        tasks = a.records(self.c, 'SELECT label,explicit_id FROM index_tasks ORDER BY line')
        self.assertEqual(tasks, [{'label': 'T0', 'explicit_id': 'T0'}, {'label': 'Alpha', 'explicit_id': None}])
        results = ix.search(self.c, workspace, 'Feature works', milestone_id='M01')['results']
        self.assertTrue(any(row['kind'] == 'section' and row['milestone_id'] == 'M01' for row in results))

    def test_mixed_layout_refresh_marks_previous_generation_incomplete(self):
        state = self.sync(); workspace = state['workspace_id']
        (self.root / 'memory-bank').mkdir()
        with self.assertRaises(a.AuditError):
            self.sync()
        failed = ix.status(self.c, workspace)
        self.assertFalse(failed['complete'])
        self.assertTrue(failed['diagnostics'])

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
        self.assertEqual(dependencies,[{'source_key':'M01/TASK-B','target_key':'TASK-A','relationship':'depends_on'}])
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
        self.assertEqual(ready['waiting'][0]['task']['prerequisites'][0]['label'], 'TASK-A')
        self.assertEqual(ready['ready'][0]['task']['dependents'][0]['label'], 'TASK-B')
        self.assertTrue(ready['waiting'][0]['task']['prerequisites'][0]['resolved'])

    def test_readiness_reports_stale_sources_and_multiple_in_progress(self):
        state=self.sync();w=state['workspace_id']
        self.source.write_text(self.source.read_text().replace('`[ ]`','`[~]`'))
        stale=ix.readiness(self.c,w,self.root)
        self.assertEqual(stale['source_freshness'],'stale')
        self.assertNotIn('recommendations', stale)
        self.sync()
        self.source.write_text(
            '# Tasks\n\n| Item | State | Notes |\n|---|---|---|\n'
            '| First | `[~]` | one |\n| Second | `[~]` | two |\n'
        )
        self.sync()
        multiple=ix.readiness(self.c,w,self.root)
        self.assertNotIn('recommendations', multiple)
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
        self.assertNotIn('recommendations', ready)
        self.assertTrue(any(item['reason'] == 'dependency cycle requires review' for item in ready['needs_review']))
        self.assertTrue(any('requires review' in item['reason'] for item in ready['waiting']))

    def test_dependencies_are_scoped_by_milestone_and_wait_for_closure(self):
        milestone = self.root / 'tabilet/memory-bank/milestone.md'
        milestone.write_text(
            '# Milestones\n\n## M01 - First\n\n**Acceptance.** first\n\n'
            '## M02 - Second\n\n**Dependencies.** M01\n\n**Acceptance.** second\n'
        )
        for identity in ('M01', 'M02'):
            state_marker = '[+]' if identity == 'M01' else '[ ]'
            (self.root / f'tabilet/memory-bank/status-{identity}.md').write_text(
                '# Status\n\n| ID | State | Notes |\n|---|---|---|\n'
                f'| A | `[+]` | prerequisite |\n| B | `[{state_marker[1]}]` | Depends on: A |\n'
            )
        state = self.sync(); workspace = state['workspace_id']
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM index_task_dependencies').fetchone()[0], 2)
        readiness = ix.readiness(self.c, workspace, self.root)
        waiting = {item['task']['milestone_id']: item['reason'] for item in readiness['waiting']}
        self.assertIn('milestone dependency requires review: M01', waiting['M02'])
        self.assertNotIn('B', [item['task']['task_key'] for item in readiness['ready'] if item['task']['milestone_id'] == 'M02'])

    def test_milestone_dependency_cycles_require_review(self):
        milestone = self.root / 'tabilet/memory-bank/milestone.md'
        milestone.write_text(
            '# Milestones\n\n## M01 - First\n\n**Dependencies.** M02\n\n'
            '**Acceptance.** first\n\n## M02 - Second\n\n**Dependencies.** M01\n\n'
            '**Acceptance.** second\n'
        )
        for identity in ('M01', 'M02'):
            (self.root / f'tabilet/memory-bank/status-{identity}.md').write_text(
                '# Status\n\n| ID | State | Notes |\n|---|---|---|\n'
                f'| {identity}-T01 | `[ ]` | pending |\n'
            )
        state = self.sync()
        readiness = ix.readiness(self.c, state['workspace_id'], self.root)
        review = next(item for item in readiness['needs_review']
                      if item['reason'] == 'milestone dependency cycle requires review')
        self.assertEqual(review['milestone_ids'], ['M01', 'M02'])
        self.assertNotIn('recommendations', readiness)

    def test_scoped_cross_milestone_task_cycle_requires_review(self):
        milestone = self.root / 'tabilet/memory-bank/milestone.md'
        milestone.write_text(
            '# Milestones\n\n## M01 - First\n\n**Acceptance.** first\n\n'
            '## M02 - Second\n\n**Acceptance.** second\n'
        )
        (self.root / 'tabilet/memory-bank/status-M01.md').write_text(
            '| ID | State | Notes |\n|---|---|---|\n'
            '| T01 | `[ ]` | Depends on: M02/T01 |\n'
        )
        (self.root / 'tabilet/memory-bank/status-M02.md').write_text(
            '| ID | State | Notes |\n|---|---|---|\n'
            '| T01 | `[ ]` | Depends on: M01/T01 |\n'
        )
        state = self.sync()
        readiness = ix.readiness(self.c, state['workspace_id'], self.root)
        review = next(item for item in readiness['needs_review']
                      if item['reason'] == 'dependency cycle requires review')
        self.assertEqual(review['milestone_ids'], ['M01', 'M02'])
        self.assertNotIn('recommendations', readiness)

    def test_deep_dependency_chain_does_not_use_python_recursion(self):
        total = 1100
        rows = ['# Status\n\n| ID | State | Notes |\n|---|---|---|\n']
        for number in range(total):
            dependency = f' Depends on: T{number + 1:04} ' if number + 1 < total else ' root '
            rows.append(f'| T{number:04} | `[ ]` |{dependency}|\n')
        self.source.write_text(''.join(rows))
        state = self.sync()
        readiness = ix.readiness(self.c, state['workspace_id'], self.root)
        self.assertEqual(len(readiness['waiting']), total - 1)
        self.assertFalse(any('cycle' in item['reason'] for item in readiness['needs_review']))

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
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM index_relationships WHERE relation='successor'").fetchone()[0], 0)
        self.assertIn('successor: M02', self.c.execute("SELECT notes FROM index_tasks").fetchone()[0])
        stable=state['generation']
        retired.write_text(text.replace('**Review.** passed','**Review.** failed'))
        with self.assertRaises(a.AuditError):self.sync()
        self.assertEqual(ix.status(self.c,state['workspace_id'])['generation'],stable)
