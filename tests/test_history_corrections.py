"""Literal history, correction integrity, and the execution boundary."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
import test_harness as h
import tabilet_audit as audit
import tabilet_horizon as horizon
import tabilet_index as index
import tabilet_proposal as proposal
import tabilet_recovery as recovery

core = h.harness
FIXTURES = Path(__file__).parent / 'fixtures/retired-history'


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def entry(text, operations, identity='M01'):
    return dict(milestone_id=identity, record_path=f'tabilet/docs/history/status-{identity}.md',
                record_sha256=digest(text), corrections=operations)


def manifest(entries):
    return json.dumps(dict(schema=core.HISTORY_CORRECTIONS_SCHEMA, records=entries))


class HistoryCorrectionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        h.make_repo(self.root)
        self.text = h.retirement_text('| Task | `[+]` | verified |\n')

    def expansion(self):
        text = self.text.replace('**Evidence.** unversioned', '**Evidence.** abcdef0').replace(
            '**Worktree.** unversioned', '**Worktree.** clean')
        correction = entry(text, [dict(kind='expand-evidence-commit', recorded='abcdef0', resolved='abcdef0' + '1' * 33)])
        return text, correction

    def test_literal_fixtures_lookup_discovery_dependencies_and_runner_share_evidence(self):
        corrections_text = (FIXTURES / 'corrections.json').read_text()
        corrections = core.history_corrections(corrections_text)
        history = self.root / 'tabilet/docs/history'
        history.mkdir(parents=True)
        (history / 'corrections.json').write_text(corrections_text)
        rows = []
        for identity in ('M99', 'M100', 'M153'):
            name = f'status-{identity}.md'
            raw = (FIXTURES / (name + '.literal')).read_bytes()
            (history / name).write_bytes(raw)
            record = core.historical_record(raw.decode(), name, corrections.get('tabilet/docs/history/' + name))
            self.assertEqual(record['blockers'], [])
            self.assertIn(record['status'], raw.decode())
            parsed = index.parse_document('tabilet/docs/history/' + name, 'history_status', raw.decode(), digest(raw.decode()), corrections)
            self.assertEqual(len(parsed['index_tasks']), len(core.status_rows(record['status'])))
            for task in parsed['index_tasks']:
                self.assertIn(task['label'], raw.decode().splitlines()[task['line'] - 1])
            rows.append(f"| {identity} | completed | {record['metadata']['Retired']} | [{identity}]({name}) | fixture |\n")
        (history / 'index.md').write_text('| Milestone | Outcome | Retired | Record | Summary |\n|---|---|---|---|---|\n' + ''.join(rows))
        # A dependency on a corrected retired record is accepted, while the
        # active row itself still needs ordinary execution authorization.
        bank = self.root / 'tabilet/memory-bank'
        (bank / 'milestone.md').write_text('# Milestones\n\n[History](../docs/history/index.md)\n\n## M01 - Delivery\n\n**Depends on.** M99\n')
        snapshot = core.row_snapshot(self.root)
        self.assertEqual(snapshot['history']['problems'], [])
        self.assertEqual(len(snapshot['history']['records']), 3)
        live = horizon._live_projection(core, self.root)
        self.assertIn('M99', live['milestones'])
        with audit.open_database(self.root / 'tabilet/audit.sqlite3') as connection:
            state = index.sync(connection, self.root)
            ready = index.readiness(connection, state['workspace_id'], self.root)
            self.assertEqual(len(ready['ready']), 1)
            # Manifest edits invalidate cached derived records even when their
            # frozen source bytes are unchanged; deletion cannot reuse them.
            (history / 'corrections.json').unlink()
            with self.assertRaises(audit.AuditError):
                index.sync(connection, self.root)
        for identity in ('M99', 'M100', 'M153'):
            self.assertEqual((history / f'status-{identity}.md').read_bytes(), (FIXTURES / f'status-{identity}.md.literal').read_bytes())

    def test_schema_rejects_duplicates_conflicts_authority_and_missing_evidence(self):
        text, correction = self.expansion()
        core.history_corrections(manifest([correction]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            core.history_corrections(manifest([correction, correction]))
        for operation in (
            dict(kind='execution-authority', approved=True),
            dict(kind='supply-metadata', field='Authorization', value='approved', evidence=[]),
            dict(kind='identify-specification', heading='## Approved', evidence=[]),
        ):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                core.history_corrections(manifest([entry(text, [operation])]))
        with self.assertRaisesRegex(ValueError, 'duplicate correction JSON key'):
            core.history_corrections('{"schema":"a","schema":"b","records":[]}')
        bad = copy.deepcopy(correction)
        bad['corrections'] *= 2
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            core.history_corrections(manifest([bad]))

    def test_hashes_and_ids_are_bound_to_the_literal_bytes(self):
        text, correction = self.expansion()
        parsed = core.historical_record(text, 'status-M01.md', correction)
        self.assertEqual(parsed['status'], '| Task | `[+]` | verified |\n')
        self.assertEqual(parsed['literal_metadata']['Evidence'], 'abcdef0')
        with self.assertRaisesRegex(ValueError, 'stale'):
            core.historical_record(text + '\n', 'status-M01.md', correction)
        with self.assertRaises(ValueError):
            core.historical_record(text, 'status-M02.md', correction)

    def test_missing_review_cannot_be_supplied_by_a_prospective_task(self):
        text = self.text.replace('**Review.** passed\n', '')
        quote = 'Run tests and perform deep code review.'
        text = text.replace('| verified |', '| ' + quote + ' |')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if quote in value)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                                       evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_review_correction_requires_an_explicit_passed_result(self):
        for quote, accepted in (('review not passed', False),
                                ('review failed, but tests passed', False),
                                ('review performed', False),
                                ('Review: passed', True)):
            with self.subTest(quote=quote):
                text = self.text.replace('**Review.** passed\n', '').replace('| Task |', quote + '\n\n| Task |')
                line = next(n for n, value in enumerate(text.splitlines(), 1) if quote in value)
                correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                    evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                if accepted:
                    self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['metadata']['Review'], 'passed')
                else:
                    with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
                        core.historical_record(text, 'status-M01.md', correction)

        text = self.text.replace('**Review.** passed\n', '').replace('| Task |', 'Not Review: passed\n\n| Task |')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if 'Not Review: passed' in value)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote='Review: passed')])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_unfinished_rows_and_inconsistent_counters_remain_blocking(self):
        text = self.text.replace('`[+]`', '`[ ]`')
        self.assertIn('retired status contains unfinished task rows', core.historical_record(text, 'status-M01.md')['blockers'])
        text = self.text.replace('| Task', 'Review gate iterations: 3\n\n| Task')
        self.assertIn('retained review counter conflicts with retirement metadata', core.historical_record(text, 'status-M01.md')['blockers'])

    def test_recovery_preserves_source_bytes_locations_and_refuses_modified_content(self):
        raw_status = '| Task | `[+]` | verified |\n'
        start = next(n for n, value in enumerate(self.text.splitlines(), 1) if value == raw_status.rstrip())
        operation = dict(kind='recover-document', document='status', content=raw_status, sha256=digest(raw_status),
                         source=dict(commit='a' * 40, path='tabilet/docs/history/status-M01.md', start_line=start,
                                     end_line=start, source_sha256=digest(self.text)))
        correction = entry(self.text, [operation])
        result = core.historical_record(self.text, 'status-M01.md', correction)
        self.assertEqual(result['status'], raw_status)
        self.assertEqual(result['offsets']['status'], start - 1)
        changed = copy.deepcopy(correction)
        changed['corrections'][0]['content'] = raw_status.replace('verified', 'changed')
        with self.assertRaisesRegex(ValueError, 'hash'):
            core.historical_record(self.text, 'status-M01.md', changed)

    def test_recovery_cannot_change_or_omit_retained_task_states(self):
        original = self.text.replace('`[+]`', '`[ ]`')
        changed = '| Task | `[+]` | verified |\n'
        correction = entry(original, [dict(kind='recover-document', document='status',
            content=changed, sha256=digest(changed), source=dict(commit='a' * 40,
                path='tabilet/memory-bank/status-M01.md', start_line=1, end_line=1,
                source_sha256='a' * 64))])
        with self.assertRaisesRegex(ValueError, 'cannot change or discard'):
            core.historical_record(original, 'status-M01.md', correction)

    def test_execution_and_closure_cannot_add_a_manifest_or_use_a_compatibility_retirement(self):
        h.retire_fixture(self.root)
        before = core.row_snapshot(self.root)
        (self.root / core.HISTORY_CORRECTIONS).write_text(manifest([]))
        after = core.row_snapshot(self.root)
        self.assertNotEqual(horizon.snapshot_digest(before), horizon.snapshot_digest(after))
        self.assertIn('history corrections changed during execution', core.validate_row_transition(before, after))
        self.assertIn('history corrections changed during closure', horizon._closure_integrity_problems(before, after))
        # Both approval snapshots and interrupted-run recovery retain JSON.
        paths, _ = proposal._workflow_snapshot(core, self.root)
        self.assertIn(core.HISTORY_CORRECTIONS, paths)
        self.assertTrue(recovery._workflow_path(core.HISTORY_CORRECTIONS, core))
        h.run('git', 'add', '-A', cwd=self.root)
        h.run('git', 'commit', '-qm', 'history', cwd=self.root)
        commit = h.run('git', 'rev-parse', 'HEAD', cwd=self.root).stdout.strip()
        recovered = recovery._snapshot_at(core, self.root, commit)
        self.assertEqual(after['history']['corrections_sha256'], recovered['history']['corrections_sha256'])

    def test_projects_without_corrections_preserve_the_previous_snapshot_digest(self):
        # Frozen output of the pre-manifest snapshot contract. Existing
        # approval receipts without a manifest must not become stale solely
        # because this optional capability was added.
        previous = '4d7243b53a74e0f8213f8b76c4d240c6e6eb29a524f34bbefa29e83dc6916339'
        self.assertEqual(horizon.snapshot_digest({}), previous)
        self.assertEqual(horizon.snapshot_digest({'history': {'corrections_sha256': None}}), previous)
        self.assertNotEqual(horizon.snapshot_digest({'history': {'corrections_sha256': 'a' * 64}}), previous)

    def test_new_retirement_with_historical_alias_is_rejected(self):
        before = core.row_snapshot(self.root)
        path = h.retire_fixture(self.root)
        path.write_text(path.read_text().replace('\n## Status record\n', '\n## Final status\n'))
        after = core.row_snapshot(self.root)
        self.assertTrue(any('strict contract' in message for message in core.validate_row_transition(before, after)))

    def test_successor_correction_resolves_dependencies_without_rewriting_evidence(self):
        text = h.retirement_text('| Old | `[-]` | superseded |\n| New | `[+]` | accepted |\n')
        number = next(n for n, line in enumerate(text.splitlines(), 1) if '| New |' in line)
        correction = entry(text, [dict(kind='historical-successor', item='Old', successor='New',
            evidence=[dict(start_line=number, end_line=number, quote='| New | `[+]` | accepted |')])])
        record = core.historical_record(text, 'status-M01.md', correction)
        self.assertNotIn('Accepted successor:', record['status'])
        rows = [dict(key=row['item'], task_id=row['item'], milestone_id='M01',
                     file='status-M01.md', label=row['item'], notes=' '.join(row['cells'][2:]))
                for row in core.status_rows(record['task_status'])]
        self.assertEqual(horizon._successor_for(None, rows[0], rows)['task_id'], 'New')

    def test_summary_code_pipes_are_historical_only(self):
        source = self.root / 'tabilet/memory-bank/status-M01.md'
        source.write_text(source.read_text().replace('`[ ]`', '`[+]`'))
        path = h.retire_fixture(self.root)
        index_path = path.parent / 'index.md'
        index_path.write_text(index_path.read_text().replace('| fixture |', '| `project.yaml|json` |'))
        # retire_fixture uses a different summary; replace the actual last cell.
        lines = index_path.read_text().splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.startswith('| M01 |'):
                cells = core.table_rows(line)[0]['cells']
                lines[i] = '| ' + ' | '.join(cells[:4]) + ' | `project.yaml|json` |\n'
        index_path.write_text(''.join(lines))
        snapshot = core.history_snapshot(self.root)
        self.assertEqual(snapshot['problems'], [])
        self.assertEqual(snapshot['index_compatibility'], ['status-M01.md'])
        self.assertEqual(core.historical_index_cells(['M01', 'completed', 'date', 'record', 'extra', 'column']),
                         ['M01', 'completed', 'date', 'record', 'extra', 'column'])

    def test_manifest_symlinks_and_nonregular_files_are_rejected(self):
        path = self.root / core.HISTORY_CORRECTIONS
        path.parent.mkdir(parents=True)
        path.symlink_to(self.root / 'missing.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            core.read_history_corrections(self.root)
        path.unlink()
        path.mkdir()
        with self.assertRaisesRegex(ValueError, 'regular file'):
            core.read_history_corrections(self.root)

    def test_malformed_json_values_are_validation_errors(self):
        text, correction = self.expansion()
        for bad in (dict(kind=[]), dict(kind='supply-metadata', field=[], value='passed', evidence=[]),
                    dict(kind='resolve-evidence-set', commits=[{}], evidence=[])):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                core.history_corrections(manifest([entry(text, [bad])]))
        with self.assertRaisesRegex(ValueError, 'input limit'):
            core.history_corrections(' ' * (core.HISTORY_INPUT_LIMIT + 1))


if __name__ == '__main__':
    unittest.main()
