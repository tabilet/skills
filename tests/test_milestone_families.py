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

    def test_extended_root_ids_work_across_discovery_selection_and_retirement(self):
        # Fresh fixtures keep each root and its frozen history independent.
        for root_id in ('M99', 'M100', 'M130', 'M153'):
            with self.subTest(root=root_id):
                fixture = FamilyTests('test_identity_and_deferred_option_discovery')
                fixture.setUp()
                try:
                    fixture.base.set_project([(root_id, [('T01', '`[ ]`', 'Ready.')])])
                    (fixture.bank / 'status-M01.md').unlink(missing_ok=True)
                    amendment = fixture.child(root_id + '-01', 'amend')
                    option = fixture.child(root_id + '-02', 'option', state='[+]')
                    snapshot = core.row_snapshot(fixture.root)
                    self.assertEqual([], snapshot['history']['problems'])
                    self.assertEqual({root_id, root_id + '-01', root_id + '-02'}, set(snapshot['families']))
                    self.assertEqual(root_id, fixture.select(fixture.receipt(
                        (root_id, root_id + '-01')))['row']['milestone_id'])
                    for path, identity in ((amendment, root_id + '-01'), (option, root_id + '-02')):
                        self.assertEqual(identity, core.status_identity(path.name))
                        parsed = index.parse_document('tabilet/memory-bank/'+path.name,
                                                      'active_status', path.read_text(), '0'*64)
                        self.assertEqual(identity, parsed['index_milestones'][0]['milestone_id'])
                    amendment.write_text(amendment.read_text().replace('`[ ]`', '`[+]`'))
                    frozen = fixture.retire(amendment)
                    record = core.retired_record(frozen, amendment.name)
                    self.assertEqual(root_id + '-01', record['metadata']['Milestone'])
                    self.assertEqual(frozen, (fixture.root/'tabilet/docs/history'/amendment.name).read_text())
                    option_frozen = fixture.retire(option)
                    option_record = core.retired_record(option_frozen, option.name)
                    self.assertEqual(root_id + '-02', option_record['metadata']['Milestone'])
                    self.assertEqual(frozen, (fixture.root/'tabilet/docs/history'/amendment.name).read_text())
                    self.assertEqual(option_frozen, (fixture.root/'tabilet/docs/history'/option.name).read_text())
                    self.assertEqual((root_id + '-01', 'T01'), index.dependency_target(root_id + '-01/T01'))
                finally:
                    fixture.doCleanups()

    def test_extended_identity_validation_keeps_child_and_archive_limits(self):
        for root_id in ('M99', 'M100', 'M130', 'M153'):
            for name in ('status-'+root_id+'.md', 'amend-'+root_id+'-01.md', 'option-'+root_id+'-99.md'):
                self.assertTrue(core.STATUS_NAME.fullmatch(name), name)
        for name in ('status-M1.md', 'status-M00.md', 'status-M001.md', 'amend-M100-00.md',
                     'option-M130-100.md', 'status-M153-01.md'):
            self.assertIsNone(core.STATUS_NAME.fullmatch(name), name)
        self.assertIsNone(index.ARCHIVE.fullmatch('archive-M100.md'))

    def test_malformed_wide_child_dependency_does_not_resolve_as_root(self):
        text = '## M130 - Delivery\n\n**Dependencies.** M100-100\n'
        parsed = index.parse_document('tabilet/memory-bank/milestone.md', 'milestone', text, '0'*64)
        self.assertFalse(any(edge['target'] == 'milestone:M100' for edge in parsed['index_relationships']))

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
        child=self.bank/'amend-M01-01.md'
        child.write_text(child.read_text()+'\n**Review gate.** passed\n')
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


    def test_review01_child_closes_last_row_and_retires(self):
        path=self.child(state='[~]')
        before=core.row_snapshot(self.root)
        path.write_text(path.read_text().replace('`[~]`','`[+]`'))
        self.retire(path)
        after=core.row_snapshot(self.root)
        self.assertEqual([],core.validate_row_transition(before,after))
        self.assertIn('`[+]`',after['history']['records'][path.name]['specification'])
        record=self.root/'tabilet/docs/history'/path.name
        record.write_text(record.read_text().replace('Original behavior works.','Changed requirement.'))
        self.assertTrue(core.validate_row_transition(before,core.row_snapshot(self.root)))

    def test_review03_status_prose_does_not_create_execution_dependencies(self):
        self.base.set_project([('M01',[('T01','`[ ]`','Ready.')]),('M02',[('T01','`[ ]`','Ready.')])])
        path=self.bank/'status-M01.md'
        path.write_text(path.read_text()+'\nDepends on: M02 fixture data was discussed here.\n')
        selected=self.select(self.receipt(('M01',)))
        self.assertEqual('M01',selected['row']['milestone_id'])

    def test_review04_pending_acceptance_waits_for_approved_amendment(self):
        self.child()
        receipt=self.receipt()
        receipt['approved_horizon'][0]['tasks'][0]['resume_after']=['M01-01']
        self.assertEqual('M01-01',self.select(receipt)['row']['milestone_id'])
        path=self.bank/'amend-M01-01.md'
        path.write_text(path.read_text().replace('`[ ]`','`[+]`'))
        self.verified(receipt,'M01-01')
        self.assertEqual('M01',self.select(receipt)['row']['milestone_id'])

    def test_review05_blocked_by_grammar_uses_approved_milestone_acceptance(self):
        self.base.set_project([('M01',[('T01','`[!]`','Blocked by: M01-01; resume after amendment acceptance.')])])
        self.child(state='[+]')
        receipt=self.receipt()
        receipt['approved_horizon'][0]['tasks'][0]['resume_after']=['M01-01']
        self.verified(receipt,'M01-01')
        self.assertTrue(self.select(receipt)['row']['resume_authorized'])
        receipt['closure']['milestones'].clear()
        self.assertEqual('closure',self.select(receipt)['status'])

    def test_review06_option_claim_is_visible_to_global_owner_gate(self):
        import os, subprocess, sys
        self.child('M01-02','option',state='[~]')
        self.assertEqual(['option-M01-02.md'],[r['file'] for r in core.rows_in_state(self.root,'in_progress')])
        subprocess.run(['git','add','-A'],cwd=self.root,check=True,capture_output=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.test','commit','-qm','Claim option'],cwd=self.root,check=True,capture_output=True)
        with tempfile.TemporaryDirectory() as temp:
            env={**os.environ,'XDG_STATE_HOME':temp,'LLM_API_KEY':'synthetic','LLM_MODEL':'synthetic','ALLOW_UNSANDBOXED_SHELL':'1'}
            result=subprocess.run([sys.executable,'-B',str(pathlib.Path(__file__).resolve().parents[1]/'harness/tackle-memory-bank-api-loop'),str(self.root)],env=env,text=True,capture_output=True,timeout=15)
        self.assertEqual(15,result.returncode,result.stderr)
        self.assertIn('option task already owns',result.stderr)

    def test_review07_root_specification_cannot_disappear(self):
        (self.bank/'milestone.md').write_text('# Milestones\n')
        with self.assertRaisesRegex(horizon.HorizonError,'specification'):
            self.select(self.receipt(('M01',)))

    def test_review08_prior_closure_is_reused_with_current_sources_only(self):
        import uuid, subprocess
        self.base.set_project([('M01',[('T01','`[+]`','Previously accepted.')])])
        feature=self.root/'src/feature.py';feature.parent.mkdir(exist_ok=True);feature.write_text('accepted = True\n')
        subprocess.run(['git','add','-A'],cwd=self.root,check=True,capture_output=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.test','commit','-qm','Accepted parent'],cwd=self.root,check=True,capture_output=True)
        prior=self.receipt(('M01',))
        prior.update(schema='tabilet.api.receipt/v1',receipt_id=str(uuid.uuid4()),project_path=str(self.root.resolve()),
                     branch=core.git_branch(self.root),commit_ids=[core.git_head(self.root)],state='completed',active_operation=None)
        prior['closure']['milestones']['M01']={'phase':'verified','closure_state':'verified','review_iterations':1,
            'evidence':[{'phase':phase,'source':'model','verified':True} for phase in ('review','acceptance','consolidation','downstream')]}
        self.child('M01-02','option')
        current=self.receipt(('M01-02',))
        with tempfile.TemporaryDirectory() as temp:
            store=existing.proposal_api.ReceiptStore(pathlib.Path(temp)/'receipts')
            store.create(self.root,prior)
            malformed=dict(prior,receipt_id=str(uuid.uuid4()),approved_horizon=None,closure=None)
            store.create(self.root,malformed)
            selected=horizon.select_next_row(core,self.root,current,receipt_store=store)
            self.assertEqual('M01-02',selected['row']['milestone_id'])
            self.assertNotIn('M01',current['closure']['milestones'])
            new_child=self.child()
            self.assertEqual('waiting',horizon.select_next_row(core,self.root,current,receipt_store=store)['status'])
            new_child.unlink()
            feature.write_text('accepted = False\n')
            self.assertEqual('waiting',horizon.select_next_row(core,self.root,current,receipt_store=store)['status'])
            feature.write_text('accepted = True\n')
            parent=self.bank/'status-M01.md';parent.write_text(parent.read_text()+'\nChanged acceptance record.\n')
            self.assertEqual('waiting',horizon.select_next_row(core,self.root,current,receipt_store=store)['status'])

    def test_review09_amendment_inherits_parent_priority_without_order_edge(self):
        self.base.set_project([('M01',[('T01','`[+]`','Own work ready.')]),('M02',[('T01','`[ ]`','Independent root.')])])
        child=self.child()
        receipt=self.receipt(('M01','M01-01','M02'))
        self.assertEqual('M01-01',self.select(receipt)['row']['milestone_id'])
        child.write_text(child.read_text()+'\nDepends on: M02\n')
        self.assertEqual('M02',self.select(receipt)['row']['milestone_id'])

    def test_review10_child_subheadings_survive_retirement(self):
        child=self.child(state='[+]')
        child.write_text(child.read_text()+'\n## Tasks\n\nCompleted tasks above.\n## Review\n\nAccepted.\n')
        self.retire(child)
        snapshot=core.row_snapshot(self.root)
        self.assertEqual([],snapshot['history']['problems'])
        self.assertIn('## Tasks',snapshot['history']['records'][child.name]['specification'])
        record=self.root/'tabilet/docs/history'/child.name
        record.write_text(record.read_text().replace('## M01-01 - Child','## M01-03 - Wrong'))
        errors=core.row_snapshot(self.root)['history']['problems']
        self.assertTrue(any('amend-M01-01.md' in value for value in errors))
        self.assertFalse(any('status-M01-01.md' in value for value in errors))

    def test_review11_supersession_accepts_filename_link_and_root_owner(self):
        for successor in ('amend-M01-02.md','[repair](../../memory-bank/amend-M01-02.md)','M05'):
            with self.subTest(successor=successor):
                # Each case has its own immutable history.
                helper=FamilyTests();helper.setUp()
                try:
                    helper.base.set_project([('M01',[('T01','`[+]`','Own work ready.')]),('M05',[('T01','`[ ]`','Root repair.')])])
                    old=helper.child(state='[X]')
                    if successor != 'M05':helper.child('M01-02',state='[+]')
                    text=helper.retire(old);record=helper.root/'tabilet/docs/history'/old.name
                    record.write_text(text.replace('**Outcome.** completed','**Outcome.** superseded\n**Disposition.** Owner approved replacement.\n**Successor.** '+successor))
                    idx=record.parent/'index.md';idx.write_text(idx.read_text().replace('| M01-01 | completed |','| M01-01 | superseded |'))
                    ids=('M01','M05') if successor=='M05' else ('M01','M01-02')
                    receipt=helper.receipt(ids)
                    if successor=='M05':
                        self.assertEqual('M05',helper.select(receipt)['row']['milestone_id'])
                        p=helper.bank/'status-M05.md';p.write_text(p.read_text().replace('`[ ]`','`[+]`'));helper.verified(receipt,'M05')
                    else:helper.verified(receipt,'M01-02')
                    self.assertEqual('M01',helper.select(receipt)['milestone']['id'])
                finally:helper.doCleanups()

    def test_review12_parent_cannot_retire_ahead_of_active_amendment_review(self):
        self.base.set_project([('M01',[('T01','`[~]`','Last task.')])])
        child=self.child(state='[+]');child.write_text(child.read_text()+'\n**Review gate.** active\n')
        before=core.row_snapshot(self.root)
        parent=self.bank/'status-M01.md';parent.write_text(parent.read_text().replace('`[~]`','`[+]`'));self.retire(parent)
        self.assertTrue(any('required amendment' in value for value in core.validate_row_transition(before,core.row_snapshot(self.root))))

    def test_review13_rowless_option_withdrawal_preserves_history_without_task(self):
        path=self.child('M01-02','option',rows=False)
        before=core.row_snapshot(self.root);text=self.retire(path)
        record=self.root/'tabilet/docs/history'/path.name
        record.write_text(text.replace('**Outcome.** completed','**Outcome.** cancelled\n**Disposition.** Owner declined obsolete proposal.').replace('**Review.** passed','**Review.** not applicable').replace('**Review iterations.** 1','**Review iterations.** 0'))
        idx=record.parent/'index.md';idx.write_text(idx.read_text().replace('| M01-02 | completed |','| M01-02 | cancelled |'))
        after=core.row_snapshot(self.root)
        self.assertEqual([],core.validate_row_transition(before,after))
        self.assertEqual([],core.status_rows(after['documents'][path.name]))
        parsed=index.parse_document('tabilet/docs/history/'+path.name,'history_status',record.read_text(),'a'*64)
        self.assertEqual([],parsed['index_tasks'])
        record.write_text(record.read_text().replace('**Outcome.** cancelled','**Outcome.** completed'))
        self.assertTrue(core.row_snapshot(self.root)['history']['problems'])

    def test_review14_preflight_ignores_stray_record_names(self):
        import tabilet_planning
        (self.bank/'status-M01.md').unlink()
        for name in ('status-draft.md','option-notes.md','amend-notes.md'):
            (self.bank/name).write_text('# Notes\n')
        self.assertIsNone(tabilet_planning.preflight_project('init',self.root))
        self.assertEqual('missing_initialized_state',tabilet_planning.preflight_project('propose',self.root)['reason'])

    def test_parent_declaration_accepts_normal_markdown_whitespace(self):
        path=self.child();path.write_text(path.read_text().replace('Parent: M01','**Parent:** M01   '))
        self.assertEqual([],core.row_snapshot(self.root)['history']['problems'])


    def test_claimed_option_suppresses_other_readiness(self):
        import tabilet_audit
        self.child('M01-02','option',state='[~]')
        with tempfile.TemporaryDirectory() as temp:
            connection=tabilet_audit.open_database(pathlib.Path(temp)/'state/audit.db')
            try:
                synced=index.sync(connection,self.root)
                state=index.readiness(connection,synced['workspace_id'],self.root)
                self.assertEqual([],state['ready'])
                self.assertEqual('M01-02',state['resume'][0]['task']['milestone_id'])
            finally:connection.close()


    def test_rowless_withdrawal_cannot_bypass_existing_claim(self):
        parent=self.bank/'status-M01.md'
        parent.write_text(parent.read_text().replace('`[ ]`','`[~]`'))
        path=self.child('M01-02','option',rows=False)
        before=core.row_snapshot(self.root);text=self.retire(path)
        record=self.root/'tabilet/docs/history'/path.name
        record.write_text(text.replace('**Outcome.** completed','**Outcome.** cancelled\n**Disposition.** Owner declined option.').replace('**Review.** passed','**Review.** not applicable').replace('**Review iterations.** 1','**Review iterations.** 0'))
        idx=record.parent/'index.md';idx.write_text(idx.read_text().replace('| M01-02 | completed |','| M01-02 | cancelled |'))
        after=core.row_snapshot(self.root)
        self.assertTrue(core.validate_row_transition(before,after,('status-M01.md','T01',1)))
        self.assertTrue(core.validate_row_transition(before,after))

    def test_parent_retirement_checks_superseded_root_repair_owner(self):
        self.base.set_project([('M01',[('T01','`[~]`','Last task.')]),('M05',[('T01','`[ ]`','Required repair.')])])
        old=self.child(state='[X]');text=self.retire(old)
        record=self.root/'tabilet/docs/history'/old.name
        record.write_text(text.replace('**Outcome.** completed','**Outcome.** superseded\n**Disposition.** Owner approved replacement.\n**Successor.** M05'))
        idx=record.parent/'index.md';idx.write_text(idx.read_text().replace('| M01-01 | completed |','| M01-01 | superseded |'))
        before=core.row_snapshot(self.root)
        self.assertEqual([],before['history']['problems'])
        parent=self.bank/'status-M01.md'
        parent.write_text(parent.read_text().replace('`[~]`','`[+]`'))
        # Preserve M05's specification when packaging M01.
        roadmap=self.bank/'milestone.md'
        remaining=roadmap.read_text().split('## M05',1)[1]
        self.retire(parent)
        roadmap.write_text('# Milestones\n\n## M05'+remaining+'\n[History](../docs/history/index.md)\n')
        after=core.row_snapshot(self.root)
        self.assertTrue(any('M05' in value and 'required amendment owner' in value for value in core.validate_row_transition(before,after)))


if __name__ == '__main__':
    unittest.main()
