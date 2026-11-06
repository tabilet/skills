"""Portable reader fixtures, also consumed by the companion DSH plugin."""
import json
import unittest
from test_harness import ROOT, harness, retirement_text


class ParserConformance(unittest.TestCase):
    def test_shared_reader_contract(self):
        fixtures = json.loads((ROOT / 'tests/fixtures/parser-conformance.json').read_text())
        for case in fixtures:
            with self.subTest(case=case['name']):
                if case['kind'] == 'status':
                    self.assertEqual(harness.status_rows(case['text']), case['rows'])
                    self.assertEqual(harness.status_marker_problems(case['text']), case['problems'])
                elif case.get('invalid'):
                    with self.assertRaises(ValueError):
                        harness.retired_record(case['text'], case['file'])
                else:
                    self.assertEqual(harness.retired_record(case['text'], case['file']), case['record'])


class StatusTableStateColumn(unittest.TestCase):
    """The State column is read from each table's own header, not a fixed index."""

    def test_id_task_state_layout_reads_its_state_column(self):
        text = ("| ID | Task | State | Notes |\n"
                "|---|---|---|---|\n"
                "| M01.1 | First | `[+]` | done |\n"
                "| M01.2 | Second | `[ ]` | todo |\n")
        rows = harness.status_rows(text)
        self.assertEqual([(row['item'], row['state']) for row in rows],
                         [('M01.1', 'completed'), ('M01.2', 'pending')])
        self.assertEqual(harness.status_marker_problems(text), [])

    def test_item_state_layout_is_unchanged(self):
        text = ("| Item | State | Notes |\n"
                "|---|---|---|\n"
                "| Deliver | `[+]` | done |\n")
        rows = harness.status_rows(text)
        self.assertEqual([(row['item'], row['state']) for row in rows], [('Deliver', 'completed')])

    def test_data_cell_named_state_does_not_move_the_column(self):
        for header in ("", "| Item | State | Notes |\n|---|---|---|\n"):
            with self.subTest(header=header):
                text = header + "| Deliver | `[+]` | State |\n"
                rows = harness.status_rows(text)
                self.assertEqual([(row['item'], row['state']) for row in rows],
                                 [('Deliver', 'completed')])
                self.assertTrue(harness.status_marker_problems(text.replace('`[+]`', '[+]')))

    def test_unknown_marker_in_id_layout_is_reported(self):
        text = ("| ID | Task | State | Notes |\n"
                "|---|---|---|---|\n"
                "| M01.1 | First | [+] | unbackticked |\n")
        self.assertTrue(harness.status_marker_problems(text))

    def test_retired_id_task_state_layout_preserves_literal_status(self):
        status = ("| ID | Task | State | Notes |\n"
                  "|---|---|---|---|\n"
                  "| M01.1 | First | `[+]` | done |\n")
        text = retirement_text(status)
        self.assertEqual(harness.retired_record(text, 'status-M01.md')['status'], status)

    def test_historical_legacy_marker_uses_state_column_only(self):
        status = ("| ID | Task | State | Notes |\n"
                  "|---|---|---|---|\n"
                  "| M01.1 | First \\| `[x]` | `[x]` | literal `[x]` |\n")
        record = harness.historical_record(retirement_text(status), 'status-M01.md')
        self.assertEqual(record['status'], status)
        self.assertEqual(record['blockers'], ['historical `[x]` markers are lookup only'])
        self.assertEqual([(row['item'], row['state'], row['cells'][1], row['cells'][3])
                          for row in harness.status_rows(record['task_status'])],
                         [('M01.1', 'completed', 'First | `[x]`', 'literal `[x]`')])

    def test_state_column_resets_between_tables_and_excludes_review(self):
        text = ("| ID | Task | State | Notes |\n"
                "|---|---|---|---|\n"
                "| M01.1 | First | `[+]` | done |\n\n"
                "| Iteration | Findings | State |\n"
                "|---|---|---|\n"
                "| 1 | clean | `[~]` |\n\n"
                "| Item | State | Notes |\n"
                "|---|---|---|\n"
                "| Deliver | `[ ]` | todo |\n\n"
                "| Headerless | `[!]` | blocked |\n")
        self.assertEqual([(row['item'], row['state']) for row in harness.status_rows(text)],
                         [('M01.1', 'completed'), ('Deliver', 'pending'), ('Headerless', 'blocked')])
        self.assertEqual(harness.status_marker_problems(text), [])

    def test_missing_state_column_is_reported_without_crashing(self):
        text = ("| ID | Task | State | Notes |\n"
                "|---|---|---|---|\n"
                "| M01.1 | First |\n")
        self.assertEqual(harness.status_rows(text), [])
        self.assertEqual(harness.status_marker_problems(text),
                         ['line 3: unknown or non-backticked state marker'])
