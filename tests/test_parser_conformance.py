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


class EvidenceTableLinks(unittest.TestCase):
    def test_links_in_non_state_tables_are_not_markers(self):
        for link in ('[RED](red.log)', '[RED](logs/run(1).log)',
                     '[RED](red.log "failure evidence")', '[RED][log]',
                     '[log][]', '[log]', '[RED](red.log) / [GREEN](green.log)'):
            with self.subTest(link=link):
                text = ('| Check | Evidence |\n|---|---|\n'
                        f'| Regression | {link} |\n\n[log]: red.log\n')
                self.assertEqual(harness.status_rows(text), [])
                self.assertEqual(harness.status_marker_problems(text), [])

    def test_links_do_not_hide_bad_markers_or_literal_code(self):
        for state in ('[RED](red.log) `[?]`', '**[ ]** [RED](red.log)',
                      '[RED][log] [x]', '[RED][missing]', '[missing][]',
                      '`[RED](red.log)`', '``[RED](red.log)``', '`[?]`(red.log)',
                      '`[log]`', '[RED](unclosed', '[RED](not a destination)'):
            with self.subTest(state=state):
                text = f'| Evidence | {state} |\n\n[log]: red.log\n'
                self.assertEqual(harness.status_marker_problems(text),
                                 ['line 1: unknown or non-backticked state marker'])

    def test_state_headers_still_require_exact_markers(self):
        for state in ('[RED](red.log)', '[RED][log]', '[log][]', '[log]'):
            for header, row in (('| Item | State |', f'| Task | {state} |'),
                                ('| ID | Task | State |', f'| M01.1 | Task | {state} |')):
                with self.subTest(state=state, header=header):
                    text = f'{header}\n{row}\n\n[log]: red.log\n'
                    self.assertEqual(harness.status_marker_problems(text),
                                     ['line 2: unknown or non-backticked state marker'])

    def test_code_block_reference_definitions_cannot_hide_markers(self):
        for definition in ('```markdown\n[unknown]: red.log\n```',
                           '    [unknown]: red.log'):
            with self.subTest(definition=definition):
                text = f'| Task | [unknown] |\n\n{definition}\n'
                self.assertTrue(harness.status_marker_problems(text))

    def test_empty_reference_label_cannot_hide_pending_marker(self):
        self.assertTrue(harness.status_marker_problems('| Task | [ ] |\n\n[ ]: red.log\n'))
