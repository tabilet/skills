"""Shared historical table selection and its standalone/SQLite consumers."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
import tabilet_audit as audit
import tabilet_index as index
import test_harness as h

core = h.harness
HEADER = '| Milestone | Outcome | Retired | Record | Summary |\n|---|---|---|---|---|\n'
REFERENCE = '| Milestone | Checkpoint | Current record | Preserved scope |\n|---|---|---|---|\n'
CHECKPOINT = '| M01 | [Prior checkpoint](checkpoint.md) | [M01](status-M01.md) | Frozen notes |\n'


def entry(identity='M01', summary='Delivery'):
    return f'| {identity} | completed | 2026-09-12 | [{identity}](status-{identity}.md) | {summary} |\n'


class HistoricalTableTests(unittest.TestCase):
    def test_explicit_headers_select_retirement_in_either_order(self):
        canonical = HEADER + entry()
        reference = REFERENCE + CHECKPOINT
        for text in (canonical + reference, reference + canonical):
            with self.subTest(text=text):
                rows = core.historical_index_rows(text)
                self.assertEqual([r['cells'][0] for r in rows], ['M01'])
                self.assertEqual(text.splitlines()[rows[0]['line'] - 1], entry().strip())

    def test_multiple_tables_blank_gaps_headerless_rows_and_normalization(self):
        text = (entry('M01') + '\n\t\n' + entry('M02') +
                '|  MILESTONE  | Outcome | retired | RECORD | Summary |\n'
                '|:---|---:|:---:|---|---|\n' + entry('M03') + '\n\n' + entry('M04') +
                HEADER + entry('M05') + REFERENCE + CHECKPOINT + '\n \n' + CHECKPOINT +
                '\n# Legacy rows\n' + entry('M06'))
        rows = core.historical_index_rows(text)
        self.assertEqual([r['cells'][0] for r in rows], [f'M0{n}' for n in range(1, 7)])
        for row in rows:
            self.assertEqual(row, next(r for r in core.table_rows(text) if r['line'] == row['line']))

    def test_table_context_resets_at_prose_headings_and_code(self):
        for boundary in ('Ordinary prose\n', '## Legacy\n', '```md\n' + entry('M99') + '```\n',
                         '~~~\n' + entry('M99') + '~~~\n', '    | M99 | code |\n'):
            with self.subTest(boundary=boundary):
                text = REFERENCE + CHECKPOINT + '\n\n' + CHECKPOINT + boundary + entry()
                rows = core.historical_index_rows(text)
                self.assertEqual([r['cells'][0] for r in rows], ['M01'])
                self.assertEqual(rows[0]['line'], len(text.splitlines()))

    def test_fenced_headers_do_not_change_context_or_supply_rows(self):
        text = '````markdown\n' + HEADER + entry('M99') + '````\n' + entry()
        self.assertEqual(core.historical_index_rows(text), [core.table_rows(text)[0]])

    def test_header_requires_adjacent_matching_delimiter(self):
        for header in ('| Milestone | Checkpoint |\n', '| Milestone | Checkpoint |\n\n|---|---|\n',
                       '| Milestone | Checkpoint |\n|---|---|---|\n'):
            with self.subTest(header=header):
                self.assertEqual([r['cells'][0] for r in core.historical_index_rows(header + entry())], ['M01'])

    def test_other_five_column_tables_are_not_retirement_tables(self):
        text = ('| ID | Outcome | Retired | Record | Notes |\n|---|---|---|---|---|\n' +
                entry() + '\n\n' + entry('M02') + HEADER + entry('M03'))
        self.assertEqual([r['cells'][0] for r in core.historical_index_rows(text)], ['M03'])

    def test_selected_cells_keep_summary_pipes_and_physical_locations(self):
        text = '# History\n\n' + HEADER + entry(summary='`left|right` and escaped \\| note')
        row, = core.historical_index_rows(text)
        self.assertEqual(row, core.table_rows(text)[-1])
        self.assertEqual(row['line'], 5)
        self.assertEqual(len(row['cells']), 6)
        self.assertEqual(core.historical_index_cells(row['cells'])[-1], '`left|right` and escaped | note')


class HistoricalIndexIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = h.make_repo(base / 'project', h.marker('[+]'))
        self.record = h.retire_fixture(self.root)
        self.history = self.record.parent / 'index.md'
        self.milestone = self.root / 'tabilet/memory-bank/milestone.md'
        self.c = audit.open_database(base / 'audit.db')
        self.addCleanup(self.c.close)

    def test_reader_and_index_agree_and_keep_checkpoint_searchable(self):
        literal = self.record.read_bytes()
        for text in (HEADER + entry() + REFERENCE + CHECKPOINT,
                     REFERENCE + CHECKPOINT + HEADER + entry(summary='`left|right`')):
            with self.subTest(text=text):
                self.history.write_text(text)
                snapshot = core.history_snapshot(self.root)
                self.assertEqual(snapshot['problems'], [])
                self.assertEqual(set(snapshot['entries']), {'status-M01.md'})
                self.assertEqual(snapshot['entries']['status-M01.md'][1:3], ['completed', '2026-09-12'])
                state = index.sync(self.c, self.root)
                self.assertTrue(state['complete'])
                self.assertEqual(self.c.execute('SELECT milestone_id,lifecycle,outcome FROM index_milestones').fetchall(),
                                 [('M01', 'retired', 'completed')])
                matches = index.search(self.c, state['workspace_id'], 'Frozen notes')['results']
                self.assertTrue(any(row['path'] == 'tabilet/docs/history/index.md' for row in matches))
                self.assertEqual(self.history.read_text(), text)
                self.assertEqual(self.record.read_bytes(), literal)

    def test_multiple_retirement_tables_and_headerless_entries_agree(self):
        (self.record.parent / 'status-M02.md').write_text(
            h.retirement_text('| Task | `[+]` | verified |\n', 'M02'))
        for text in (HEADER + entry() + '\n\n' + entry('M02'),
                     HEADER + entry() + REFERENCE + CHECKPOINT + HEADER + entry('M02'),
                     entry() + '\n## Legacy\n' + entry('M02')):
            with self.subTest(text=text):
                self.history.write_text(text)
                self.assertEqual(core.history_snapshot(self.root)['problems'], [])
                self.assertTrue(index.sync(self.c, self.root)['complete'])
                self.assertEqual(self.c.execute('SELECT COUNT(*) FROM index_milestones').fetchone()[0], 2)

    def test_invalid_retirement_entries_still_fail_and_retain_previous_generation(self):
        baseline = index.sync(self.c, self.root)
        tasks = self.c.execute('SELECT * FROM index_tasks').fetchall()
        invalid = [
            (HEADER + entry() + REFERENCE + CHECKPOINT + HEADER + entry(), 'duplicate history index ID'),
            (HEADER + entry() + entry('M02'), 'missing'),
            (HEADER + entry().replace('completed', 'cancelled'), 'inconsistent'),
            (HEADER + entry().replace('2026-09-12', '2026-09-13'), 'inconsistent'),
            (HEADER + entry().replace('(status-M01.md)', '(status-M02.md)'), 'inconsistent'),
            (HEADER + entry(summary='extra | column'), 'inconsistent'),
            (HEADER + '| M01 | completed |\n', 'inconsistent'),
            (HEADER + entry('M00'), 'inconsistent'),
        ]
        for text, diagnostic in invalid:
            with self.subTest(text=text):
                self.history.write_text(text)
                self.assertTrue(any(diagnostic in p for p in core.history_snapshot(self.root)['problems']))
                with self.assertRaises(audit.AuditError):
                    index.sync(self.c, self.root)
                state = index.status(self.c, baseline['workspace_id'])
                self.assertEqual(state['generation'], baseline['generation'])
                self.assertFalse(state['complete'])
                self.assertEqual(self.c.execute('SELECT * FROM index_tasks').fetchall(), tasks)

    def test_projection_v10_cache_is_rebuilt_without_source_changes(self):
        baseline = index.sync(self.c, self.root)
        key = f"index_projection:{baseline['workspace_id']}"
        with self.c:
            self.c.execute('UPDATE schema_meta SET value=? WHERE key=?', ('v10', key))
        with mock.patch.object(index, 'parse_document', wraps=index.parse_document) as parse:
            state = index.sync(self.c, self.root)
            self.assertEqual(parse.call_count, len(index.inventory(self.root)))
        self.assertNotEqual(state['generation'], baseline['generation'])
        self.assertEqual(self.c.execute('SELECT value FROM schema_meta WHERE key=?', (key,)).fetchone(), (index.INDEX_PROJECTION,))

    def test_external_history_headings_are_excluded_and_duplicate_local_specs_fail(self):
        self.milestone.write_text(self.milestone.read_text() +
                                 '\n## Historical Browserdriver:M01 approved outcome\nRetained context.\n'
                                 '\n## Historical Browserdriver:M01 later outcome\nRetained context.\n')
        self.assertEqual(core.root_specifications(self.milestone.read_text()), {})
        self.assertEqual(core.history_snapshot(self.root)['problems'], [])
        self.assertTrue(index.sync(self.c, self.root)['complete'])
        self.milestone.write_text(self.milestone.read_text() + '\n## M02 Local\n\n## M02 Duplicate\n')
        self.assertIsNone(core.root_specifications(self.milestone.read_text())['status-M02.md'])
        with self.assertRaisesRegex(audit.AuditError, 'duplicate milestone specification: M02'):
            index.sync(self.c, self.root)

    def test_withdrawn_specs_preserve_cancelled_tasks_without_actionable_work(self):
        specifications = self.milestone.read_text()
        for identity, count in (('M54', 4), ('M55', 4), ('M60', 3)):
            specifications += (f'\n## {identity} Withdrawn\n\n**State.** Withdrawn; undelivered.\n'
                               f'\n````text\n### {identity} Original frozen specification\n````\n')
            (self.root / f'tabilet/memory-bank/status-{identity}.md').write_text(
                '# Withdrawn\n\nReview iterations: 0\n\n| Item | State | Notes |\n|---|---|---|\n' +
                ''.join(f'| Task {n} | `[X]` | Owner withdrew; undelivered |\n' for n in range(count)))
        self.milestone.write_text(specifications)
        snapshot = core.row_snapshot(self.root)
        self.assertEqual(snapshot['history']['problems'], [])
        state = index.sync(self.c, self.root)
        self.assertTrue(state['complete'])
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM index_tasks WHERE state='cancelled'").fetchone()[0], 11)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM index_tasks WHERE state IN ('pending','in_progress','blocked')").fetchone()[0], 0)
        ready = index.readiness(self.c, state['workspace_id'], self.root)
        self.assertEqual(ready['ready'], [])
        self.assertEqual(ready['waiting'], [])
        self.assertEqual(self.milestone.read_text(), specifications)


if __name__ == '__main__':
    unittest.main()
