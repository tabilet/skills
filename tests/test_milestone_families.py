"""Behavioral coverage for child identity, approval, selection and retirement."""
import hashlib
import pathlib
import tempfile
import unittest

import test_tabilet_horizon as existing

core = existing.core
horizon = existing.horizon
index = horizon._load_index_module()


class FamilyTests(unittest.TestCase):
    def setUp(self):
        self.base = existing.HorizonSelectionTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.root = self.base.project
        self.bank = self.root / 'tabilet/memory-bank'

    def child(self, identity='M01-01', kind='amend', state='[ ]', rows=True):
        path = self.bank / f'{kind}-{identity}.md'
        text = f'## {identity} - Child\n\nParent: {identity.split("-")[0]}\n\n**Acceptance.** Original behavior works.\n'
        if rows:
            text += f'\n| ID | State | Notes |\n|---|---|---|\n| T01 | `{state}` | Original requirement evidence. |\n'
        path.write_text(text)
        return path

    def receipt(self, ids=('M01', 'M01-01'), tasks=None):
        tasks = tasks or {identity: ['T01'] for identity in ids}
        receipt = self.base.receipt(ids, tasks)
        for item in receipt['approved_horizon']:
            identity = item['id']
            path = core.milestone_path(self.root, identity).relative_to(self.root).as_posix()
            item['closure_paths'] = ['tabilet/memory-bank/milestone.md', path]
            for task in item['tasks']:
                task['approved_paths'] = [path, 'src/feature.py']
        return receipt

    def verified(self, receipt, identity):
        receipt['closure']['milestones'][identity] = {'phase':'verified', 'closure_state':'verified'}

    def select(self, receipt):
        return horizon.select_next_row(core, self.root, receipt)

    def test_identity_and_deferred_option_discovery(self):
        self.child()
        self.child('M01-02', 'option', rows=False)
        snapshot = core.row_snapshot(self.root)
        self.assertEqual([], snapshot['history']['problems'])
        self.assertEqual({'M01','M01-01','M01-02'}, set(snapshot['families']))
        self.assertEqual(['amend-M01-01.md','status-M01.md'], [x['file'] for x in core.lane_summary(self.root)])
        self.assertIn('tabilet/memory-bank/option-M01-02.md', index.inventory(self.root))
        text = (self.bank/'option-M01-02.md').read_text()
        parsed = index.parse_document('tabilet/memory-bank/option-M01-02.md', 'active_status', text, hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual([], parsed['index_tasks'])
        self.assertEqual('M01-02', parsed['index_milestones'][0]['milestone_id'])
        self.assertEqual('parent', parsed['index_relationships'][0]['relation'])

    def test_duplicate_child_number_across_kinds_is_rejected(self):
        self.child()
        self.child(kind='option')
        problems = core.row_snapshot(self.root)['history']['problems']
        self.assertTrue(any('duplicate milestone identity' in p for p in problems))

    def test_orphan_and_wrong_parent_are_rejected(self):
        path = self.child('A01-01')
        self.assertTrue(any('orphan' in p for p in core.row_snapshot(self.root)['history']['problems']))
        path.write_text(path.read_text().replace('Parent: A01', 'Parent: M01'))
        self.assertTrue(any('Parent: A01' in p for p in core.row_snapshot(self.root)['history']['problems']))

    def test_invalid_child_names_do_not_disappear(self):
        for name in ('option-M01-00.md', 'amend-M01-01-01.md', 'status-M01-01.md', 'amend-M01.md'):
            with self.subTest(name=name):
                path = self.bank / name
                path.write_text('invalid')
                self.assertTrue(core.row_snapshot(self.root)['history']['problems'])
                path.unlink()

    def test_family_work_child_closure_parent_resumption_then_downstream(self):
        self.base.set_project([
            ('M01', [('T01','`[ ]`','Implement.'), ('T02','`[!]`','Deferred to: M01-01; real acceptance still required.')]),
            ('M02', [('T01','`[ ]`','Downstream.')]),
        ])
        roadmap = self.bank/'milestone.md'
        roadmap.write_text(roadmap.read_text()+'\nDepends on: M01\n')
        child = self.child()
        receipt = self.receipt(('M01','M01-01','M02'), {'M01':['T01','T02'],'M01-01':['T01'],'M02':['T01']})
        receipt['approved_horizon'][0]['tasks'][1]['resume_after'] = ['M01-01']
        self.assertEqual('T01', self.select(receipt)['row']['task_id'])
        parent = self.bank/'status-M01.md'
        parent.write_text(parent.read_text().replace('`[ ]`','`[+]`'))
        self.assertEqual('M01-01', self.select(receipt)['row']['milestone_id'])
        child.write_text(child.read_text().replace('`[ ]`','`[+]`'))
        selected = self.select(receipt)
        self.assertEqual('closure', selected['status'])
        self.assertEqual('M01-01', selected['milestone']['id'])
        self.verified(receipt, 'M01-01')
        selected = self.select(receipt)
        self.assertEqual('T02', selected['row']['task_id'])
        self.assertTrue(selected['row']['resume_authorized'])
        self.assertIn('real acceptance still required', parent.read_text())
        core_before = core.row_snapshot(self.root)
        horizon._mark_in_progress(core, self.root, selected['row'])
        self.assertIn('`[~]`', parent.read_text())
        self.assertEqual('blocked', core_before['states'][('status-M01.md','T02',1)])
        parent.write_text(parent.read_text().replace('`[~]`','`[+]`'))
        self.assertEqual('M01', self.select(receipt)['milestone']['id'])
        self.verified(receipt, 'M01')
        self.assertEqual('M02', self.select(receipt)['row']['milestone_id'])

    def test_mocked_progress_does_not_clear_unapproved_blocker(self):
        self.base.set_project([('M01',[('T01','`[!]`','Mock passes; real login unexecuted.')])])
        self.child(state='[+]')
        receipt = self.receipt()
        self.verified(receipt, 'M01-01')
        with self.assertRaisesRegex(horizon.HorizonError, 'blocked row'):
            self.select(receipt)

    def test_parent_closure_waits_for_verified_amendment(self):
        self.base.set_project([('M01',[('T01','`[+]`','Own work ready.')])])
        self.child(state='[+]')
        receipt = self.receipt()
        self.assertEqual('M01-01', self.select(receipt)['milestone']['id'])
        self.verified(receipt,'M01-01')
        self.assertEqual('M01', self.select(receipt)['milestone']['id'])

    def test_unapproved_amendment_cannot_be_implicitly_executed(self):
        self.base.set_project([('M01',[('T01','`[+]`','Done.')])])
        self.child()
        with self.assertRaisesRegex(horizon.HorizonError, 'outside approved horizon'):
            self.select(self.receipt(('M01',)))

    def test_options_neither_block_nor_enter_horizon_without_approval(self):
        self.base.set_project([('M01',[('T01','`[+]`','Done.')])])
        self.child('M01-02','option')
        receipt = self.receipt(('M01',))
        self.assertEqual('closure', self.select(receipt)['status'])
        self.verified(receipt,'M01')
        self.assertEqual('horizon_complete', self.select(receipt)['status'])
        self.assertEqual(0, sum(x['actionable'] for x in core.lane_summary(self.root)))

    def test_explicit_option_selection_waits_for_parent_closure(self):
        self.child('M01-02','option')
        receipt = self.receipt(('M01','M01-02'))
        self.assertEqual('M01', self.select(receipt)['row']['milestone_id'])
        self.base.set_project([('M01',[('T01','`[+]`','Done.')])])
        self.assertEqual('closure', self.select(receipt)['status'])
        self.verified(receipt,'M01')
        self.assertEqual('M01-02', self.select(receipt)['row']['milestone_id'])

    def test_file_kind_change_cannot_reuse_receipt(self):
        path = self.child()
        receipt = self.receipt()
        path.rename(self.bank/'option-M01-01.md')
        with self.assertRaisesRegex(horizon.HorizonError,'file kind changed'):
            self.select(receipt)

    def test_child_dependency_on_parent_is_cycle(self):
        path = self.child()
        path.write_text(path.read_text()+'\nDepends on: M01\n')
        with self.assertRaisesRegex(horizon.HorizonError,'cyclic'):
            self.select(self.receipt())

    def test_index_child_dependencies_do_not_truncate_to_root(self):
        path = self.child()
        path.write_text(path.read_text()+'\nDepends on: A02-03\n')
        parsed = index.parse_document('tabilet/memory-bank/'+path.name,'active_status',path.read_text(),'0'*64)
        edges = [x for x in parsed['index_relationships'] if x['relation']=='depends_on']
        self.assertEqual('milestone:A02-03', edges[0]['target'])
        self.assertEqual(('M01-01','T01'),index.dependency_target('M01-01/T01'))

    def retire(self, path):
        identity = core.status_identity(path.name)
        source = path.read_text()
        spec = core.milestone_specifications(self.root)[path.name]
        history = self.root/'tabilet/docs/history'
        history.mkdir(parents=True, exist_ok=True)
        source_spec = 'tabilet/memory-bank/'+path.name if '-' in identity else 'tabilet/memory-bank/milestone.md#'+identity.lower()
        text = f'''# Retired {identity}
**Milestone.** {identity}
**Outcome.** completed
**Retired.** 2026-10-25
**Source status.** tabilet/memory-bank/{path.name}
**Source specification.** {source_spec}
**Evidence.** {'a'*40}
**Worktree.** clean
**Review.** passed
**Review iterations.** 1
**Verification.** Focused check passed.
**Consolidated into.** lessons.md

## Milestone specification
````markdown
{spec}````

## Status record
````markdown
{source}````
'''
        (history/path.name).write_text(text)
        idx=history/'index.md'
        old=idx.read_text() if idx.exists() else '# History\n| ID | Outcome | Retired | Record | Notes |\n|---|---|---|---|---|\n'
        idx.write_text(old+f'| {identity} | completed | 2026-10-25 | [{identity}]({path.name}) | Preserved. |\n')
        path.unlink()
        roadmap=self.bank/'milestone.md'
        if path.name.startswith('status-'):
            roadmap.write_text('# Milestones\n')
        if '../docs/history/index.md' not in roadmap.read_text():
            roadmap.write_text(roadmap.read_text()+'\n[History](../docs/history/index.md)\n')
        return text

    def test_retired_child_and_deferred_option_preserve_parent_link(self):
        child=self.child(state='[+]')
        self.child('M01-02','option',rows=False)
        before=core.row_snapshot(self.root)
        frozen=self.retire(child)
        after=core.row_snapshot(self.root)
        self.assertEqual([],after['history']['problems'])
        self.assertIn('Parent: M01',after['documents'][child.name])
        self.assertEqual([],horizon._closure_integrity_problems(before,after,retirement_id='M01-01',review_iterations=1))
        parent=self.bank/'status-M01.md'
        parent.write_text(parent.read_text().replace('`[ ]`','`[+]`'))
        self.retire(parent)
        self.assertEqual([],core.row_snapshot(self.root)['history']['problems'])
        self.assertEqual(frozen,(self.root/'tabilet/docs/history'/child.name).read_text())
        self.child('M01-01','option')
        self.assertTrue(any('duplicate milestone identity' in p for p in core.row_snapshot(self.root)['history']['problems']))


    def test_accepted_active_amendment_does_not_prevent_parent_retirement(self):
        self.base.set_project([('M01',[('T01','`[+]`','Own work complete.')])])
        self.child(state='[+]')
        receipt=self.receipt()
        self.verified(receipt,'M01-01')
        self.assertEqual('M01',self.select(receipt)['milestone']['id'])
        self.retire(self.bank/'status-M01.md')
        self.assertEqual([],core.row_snapshot(self.root)['history']['problems'])
        self.assertEqual('horizon_complete',self.select(receipt)['status'])

    def test_superseded_amendment_uses_replacement_without_reopening_old_child(self):
        self.base.set_project([('M01',[('T01','`[+]`','Own work ready.')]),
                               ('M02',[('T01','`[ ]`','Downstream.')])])
        roadmap=self.bank/'milestone.md'
        roadmap.write_text(roadmap.read_text()+'\nDepends on: M01\n')
        old=self.child(state='[X]')
        old.write_text(old.read_text()+'\nDepends on: M02\n')
        self.child('M01-02',state='[+]')
        text=self.retire(old)
        path=self.root/'tabilet/docs/history'/old.name
        text=text.replace('**Outcome.** completed','**Outcome.** superseded\n**Disposition.** Owner approved replacement.\n**Successor.** M01-02')
        path.write_text(text)
        idx=path.parent/'index.md'
        idx.write_text(idx.read_text().replace('| M01-01 | completed |','| M01-01 | superseded |'))
        receipt=self.receipt(('M01','M01-02','M02'))
        self.assertEqual('M01-02',self.select(receipt)['milestone']['id'])
        self.verified(receipt,'M01-02')
        self.assertEqual('M01',self.select(receipt)['milestone']['id'])

    def test_index_projection_uses_child_owned_specification(self):
        self.child()
        self.child('M01-02','option',rows=False)
        documents={}; parsed={}
        for path,kind in index.inventory(self.root).items():
            text,digest,_=index.read_document(self.root,path)
            documents[path]={'kind':kind,'text':text,'sha256':digest}
            parsed[path]=index.parse_document(path,kind,text,digest)
        self.assertEqual([],index.validate_projection(documents,parsed))
        child=parsed['tabilet/memory-bank/amend-M01-01.md']['index_milestones'][0]
        self.assertIn('Original behavior works.',child['specification'])

    def test_option_transition_requires_explicit_controller_selection(self):
        path=self.child('M01-02','option')
        before=core.row_snapshot(self.root)
        path.write_text(path.read_text().replace('`[ ]`','`[+]`'))
        after=core.row_snapshot(self.root)
        self.assertTrue(any('explicit approved selection' in p for p in core.validate_row_transition(before,after)))
        self.assertEqual([],core.validate_row_transition(before,after,('option-M01-02.md','T01',1)))

    def test_receipt_parser_binds_child_filename_and_resume_condition(self):
        self.child()
        receipt=self.receipt()
        receipt['approved_horizon'][0]['tasks'][0]['resume_after']=['M01-01']
        validated=existing.proposal_api._validate_horizon(receipt['approved_horizon'],{'max_rows':5})
        self.assertEqual(['M01-01'],validated[0]['tasks'][0]['resume_after'])
        validated[1]['closure_paths'].append('tabilet/memory-bank/option-M01-01.md')
        with self.assertRaisesRegex(existing.proposal_api.ProposalError,'duplicates'):
            existing.proposal_api._validate_horizon(validated,{'max_rows':5})

    def test_recovery_snapshot_includes_children(self):
        import tabilet_recovery
        self.assertTrue(tabilet_recovery._workflow_path('tabilet/memory-bank/amend-M01-01.md'))
        self.assertTrue(tabilet_recovery._workflow_path('tabilet/memory-bank/option-M01-02.md'))
        self.assertFalse(tabilet_recovery._workflow_path('tabilet/memory-bank/option-M01-02-01.md'))


    def test_sqlite_options_searchable_but_not_ready(self):
        import tabilet_audit
        self.child()
        self.child('M01-02','option')
        with tempfile.TemporaryDirectory() as temp:
            connection=tabilet_audit.open_database(pathlib.Path(temp)/'state/audit.db')
            try:
                result=index.sync(connection,self.root)
                ready=index.readiness(connection,result['workspace_id'],self.root)
                self.assertEqual({'M01','M01-01'}, {x['task']['milestone_id'] for x in ready['ready']})
                self.assertEqual(['M01-02'],[x['milestone_id'] for x in ready['deferred_options']])
                stored=connection.execute("SELECT acceptance_text FROM index_milestone_projection WHERE milestone_id='M01-01'").fetchone()
                self.assertIn('Original behavior works.',stored[0])
                self.assertEqual(1,connection.execute("SELECT COUNT(*) FROM index_tasks WHERE milestone_id='M01-02'").fetchone()[0])
            finally:
                connection.close()


if __name__ == '__main__':
    unittest.main()
