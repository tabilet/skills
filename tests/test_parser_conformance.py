"""Portable reader fixtures, also consumed by the companion DSH plugin."""
import json
import sys
import unittest
from unittest import mock
from test_harness import ROOT, harness, retirement_text

sys.path.insert(0, str(ROOT / 'harness'))
import tabilet_audit as audit
import tabilet_audit_host as host
import tabilet_index as index


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
                     '[log][]', '[log]', '[RED](red.log) / [GREEN](green.log)',
                     '[![CI](badge.svg)](run.log)', '[log [1]](run.log)',
                     '[RED](a(b(c)).log)'):
            with self.subTest(link=link):
                text = ('| Check | Evidence |\n|---|---|\n'
                        f'| Regression | {link} |\n\n[log]: red.log\n')
                self.assertEqual(harness.status_rows(text), [])
                self.assertEqual(harness.status_marker_problems(text), [])

    def test_links_do_not_hide_reserved_markers(self):
        for state in ('[RED](red.log) `[?]`', '**[ ]** [RED](red.log)',
                      '[RED][log] [x]', '`[?]`(red.log)', '[ ](notes.md)',
                      '[+](abc123)', '[x](red.log)', '[~][log]', '[x][]',
                      '[?](unknown.log)', '[!][log]', '[X](cancelled.log)',
                      '[-](old.log)', '[ + ](spaced.log)', '[  ](pending.log)'):
            with self.subTest(state=state):
                text = f'| Evidence | {state} |\n\n[log]: red.log\n'
                self.assertEqual(harness.status_marker_problems(text),
                                 ['line 1: unknown or non-backticked state marker'])

    def test_prose_link_syntax_and_definitions_do_not_control_state(self):
        # This reader validates task state, not Markdown link syntax or citations.
        for prose in ('[RED][missing]', '[missing][]', '[unknown]', '[1]', '[CI]',
                      '`[RED](red.log)`', '``[RED](red.log)``', '`[log]`',
                      '[RED](unclosed', '[RED](not a destination)'):
            with self.subTest(prose=prose):
                self.assertEqual(harness.status_marker_problems(f'| Evidence | {prose} |\n'), [])
        for definition in ('- [log]: run.log', '[log]:\n  run.log'):
            self.assertEqual(harness.status_marker_problems(
                f'| Evidence | [log] |\n\n{definition}\n'), [])

    def test_state_headers_still_require_exact_markers(self):
        for state in ('[RED](red.log)', '[RED][log]', '[log][]', '[log]',
                      '[unknown]', '[ ](notes.md)', '[]', 'done', ''):
            for header, row in (('| Item | State |', f'| Task | {state} |'),
                                ('| ID | Task | State |', f'| M01.1 | Task | {state} |')):
                with self.subTest(state=state, header=header):
                    text = f'{header}\n{row}\n\n[log]: red.log\n'
                    self.assertEqual(harness.status_marker_problems(text),
                                     ['line 2: unknown or non-backticked state marker'])

    def test_reference_definitions_cannot_hide_reserved_markers(self):
        for label in (' ', 'x', '!', '?', '+', '~', 'X', '-'):
            for definition in (f'[{label}]: red.log', f'<!--\n[{label}]: red.log\n-->',
                               f'```markdown\n[{label}]: red.log\n```',
                               f'    [{label}]: red.log'):
                with self.subTest(label=label, definition=definition):
                    text = f'| Task | [{label}] |\n\n{definition}\n'
                    self.assertEqual(harness.status_marker_problems(text),
                                     ['line 1: unknown or non-backticked state marker'])

    def test_split_tables_require_a_state_header_for_nonlegacy_columns(self):
        for title in ('Second', '[Second](spec.md)'):
            text = ('| ID | Task | State |\n|---|---|---|\n'
                    '| M01.1 | First | `[+]` |\n\n'
                    f'| M01.2 | {title} | `[ ]` |\n')
            with self.subTest(title=title):
                self.assertEqual(harness.status_marker_problems(text),
                                 ['line 5: state marker outside the legacy second column; repeat the State header'])
                repaired = text.replace('\n\n', '\n\n| ID | Task | State |\n|---|---|---|\n')
                self.assertEqual(harness.status_marker_problems(repaired), [])
                self.assertEqual([r['state'] for r in harness.status_rows(repaired)],
                                 ['completed', 'pending'])

    def test_linked_task_headers_keep_state_column(self):
        for task_header in ('[Task](spec.md)', 'Task [M01]', '[Task]'):
            with self.subTest(task_header=task_header):
                text = (f'| ID | {task_header} | State | Notes |\n'
                        '|---|---|---|---|\n'
                        '| M01.1 | First | `[+]` | done |\n')
                self.assertEqual([(r['item'], r['state']) for r in harness.status_rows(text)],
                                 [('M01.1', 'completed')])
                self.assertEqual(harness.status_marker_problems(text), [])

    def test_markers_in_column_zero_are_reported(self):
        for cell in ('[ ] Task', '`[ ]` Task', '[ ]', '`[ ]`', '[ ](notes.md)', '[+]'):
            with self.subTest(cell=cell):
                text = f'| {cell} | notes |\n'
                self.assertEqual(harness.status_marker_problems(text),
                                 ['line 1: unknown or non-backticked state marker'])

    def test_data_cell_with_literal_state_is_reported_as_invalid_marker(self):
        text = ('| ID | Task | State | Notes |\n'
                '|---|---|---|---|\n'
                '| M01.1 | First | state | notes |\n')
        self.assertEqual(harness.status_marker_problems(text),
                         ['line 3: unknown or non-backticked state marker'])

    def test_historical_row_successor_respects_state_index(self):
        bad = ('| ID | Task naming successor: M02 | State | Notes |\n|---|---|---|---|\n'
               '| M01.1 | Task naming successor: M02 | `[-]` | failed attempt |\n')
        with self.assertRaises(ValueError):
            harness.retired_record(retirement_text(bad), 'status-M01.md')

        good = ('| ID | Task | State | Notes |\n|---|---|---|---|\n'
                '| M01.1 | Task | `[-]` | Accepted successor: M02 |\n')
        record = harness.retired_record(retirement_text(good), 'status-M01.md')
        self.assertEqual(len(harness.status_rows(record['status'])), 1)

    def test_legend_table_marker_exemption_and_task_detection(self):
        legend = ('| Symbol | Suggested Status | Interpretation |\n'
                  '|---|---|---|\n'
                  '| `[ ]` | Pending | Item is actionable. |\n'
                  '| `[+]` | Completed | Item is done. |\n')
        self.assertEqual(harness.status_marker_problems(legend), [])
        self.assertEqual(harness.status_rows(legend), [])

        # Non-backticked marker in column 0 of legend table is still caught
        bad_legend = legend.replace('`[ ]`', '[ ]')
        self.assertEqual(harness.status_marker_problems(bad_legend),
                         ['line 3: unknown or non-backticked state marker'])

    def test_historical_successor_when_state_is_last_column(self):
        status = ('| ID | Task | State |\n|---|---|---|\n'
                  '| M01.1 | Task 1 | `[-]` |\n'
                  '| M01.2 | Task 2 | `[+]` |\n')
        text = retirement_text(status)
        number = next(n for n, line in enumerate(text.splitlines(), 1) if '| M01.2 |' in line)
        op = {'kind': 'historical-successor', 'item': 'M01.1', 'successor': 'M01.2',
              'evidence': [{'start_line': number, 'end_line': number, 'quote': '| M01.2 | Task 2 | `[+]` |'}]}
        from test_history_corrections import entry
        correction = entry(text, [op])
        record = harness.historical_record(text, 'status-M01.md', correction)
        self.assertIn('| M01.1 | Task 1 | `[-]` | Accepted successor: M01.2 |', record['task_status'])
        self.assertEqual([r['state'] for r in harness.status_rows(record['task_status'])],
                         ['historical', 'completed'])


class FrozenRecordCompatibility(unittest.TestCase):
    """A frozen retired record cannot be edited, so it is read as v2.23.0 read it."""

    NON_TASK_TABLES = {
        'marker-first row': '| [x] lint | ok |\n',
        'marker legend': '| Marker | Meaning |\n|---|---|\n| `[ ]` | Pending |\n| `[+]` | Completed |\n',
        'bold legend': '| **Symbol** | **Meaning** |\n|---|---|\n| `[ ]` | Pending |\n',
        'unrecognised legend': '| Mark | What it means |\n|---|---|\n| [x] | Done |\n',
    }

    def test_non_task_tables_do_not_invalidate_a_frozen_record(self):
        for name, table in self.NON_TASK_TABLES.items():
            with self.subTest(table=name):
                status = ('| Item | State | Notes |\n|---|---|---|\n| Task | `[+]` | done |\n\n' + table)
                text = retirement_text(status)
                record = harness.historical_record(text, 'status-M01.md')
                self.assertTrue(record['strict'])
                self.assertEqual(record['blockers'], [])
                parsed = index.parse_document('tabilet/docs/history/status-M01.md', 'history_status',
                                              text, 'x' * 64)
                self.assertEqual([row['state'] for row in parsed['index_tasks']], ['completed'])

    def test_active_files_still_report_a_marker_in_column_zero(self):
        self.assertEqual(harness.status_marker_problems('| [x] lint | ok |\n'),
                         ['line 1: unknown or non-backticked state marker'])
        self.assertEqual(harness.status_marker_problems('| [x] lint | ok |\n', first_column=False), [])

    def test_marker_legends_are_recognised_by_header_not_one_wording(self):
        for header in ('Marker | Meaning', '**Symbol** | **Meaning**', 'Status | Meaning', 'Symbol | Suggested Status | Interpretation'):
            with self.subTest(header=header):
                text = f'| {header} |\n|---|---|\n| `[ ]` | Pending |\n| `[+]` | Completed |\n'.replace('|---|---|', '|' + '---|' * (header.count('|') + 1))
                self.assertEqual(harness.status_marker_problems(text), [])
        misplaced = '| Done | Task |\n|---|---|\n| `[+]` | Fix the bug |\n'
        self.assertEqual(harness.status_marker_problems(misplaced),
                         ['line 3: unknown or non-backticked state marker'])


class NotesByColumnRole(unittest.TestCase):
    LAYOUTS = {
        'item-state-notes': ('| Item | State | Notes |\n|---|---|---|\n',
                             '| M01.1 - Try | `[-]` | {note} |\n| M01.2 - Retry | `[+]` | done |\n'),
        'id-task-state-notes': ('| ID | Task | State | Notes |\n|---|---|---|---|\n',
                                '| M01.1 | Try | `[-]` | {note} |\n| M01.2 | Retry | `[+]` | done |\n'),
        'id-task-notes-state': ('| ID | Task | Notes | State |\n|---|---|---|---|\n',
                                '| M01.1 | Try | {note} | `[-]` |\n| M01.2 | Retry | done | `[+]` |\n'),
        'linked-task-header': ('| ID | [Task](spec.md) | Notes | State |\n|---|---|---|---|\n',
                               '| M01.1 | Try | {note} | `[-]` |\n| M01.2 | Retry | done | `[+]` |\n'),
    }

    def status(self, layout, note):
        header, body = self.LAYOUTS[layout]
        return header + body.format(note=note)

    def test_successor_in_notes_is_read_wherever_the_notes_column_sits(self):
        for layout in self.LAYOUTS:
            with self.subTest(layout=layout):
                status = self.status(layout, 'Accepted successor: M01.2')
                record = harness.retired_record(retirement_text(status), 'status-M01.md')
                self.assertEqual(len(harness.status_rows(record['status'])), 2)

    def test_a_task_description_naming_a_successor_does_not_close_the_row(self):
        status = ('| ID | Task | Notes | State |\n|---|---|---|---|\n'
                  '| M01.1 | Task naming successor: M01.2 | failed attempt | `[-]` |\n'
                  '| M01.2 | Retry | done | `[+]` |\n')
        with self.assertRaises(ValueError):
            harness.retired_record(retirement_text(status), 'status-M01.md')

    def test_index_notes_and_dependencies_follow_the_notes_column(self):
        for layout in self.LAYOUTS:
            with self.subTest(layout=layout):
                header, _ = self.LAYOUTS[layout]
                sep_state = header.splitlines()[0].lower()
                notes_first = sep_state.index('notes') < sep_state.index('state')
                row = ('| M01.2 | Second | Depends on: M01.1 | `[ ]` |\n' if notes_first
                       else '| M01.2 | Second | `[ ]` | Depends on: M01.1 |\n')
                if layout == 'item-state-notes':
                    row = '| M01.2 - Second | `[ ]` | Depends on: M01.1 |\n'
                status = header + row
                parsed = index.parse_document('tabilet/memory-bank/status-M01.md', 'active_status',
                                              status, 'x' * 64)
                self.assertEqual([task['notes'] for task in parsed['index_tasks']], ['Depends on: M01.1'])
                self.assertEqual(len(parsed['index_task_dependencies']), 1)


class RunnerToolkitCompatibility(unittest.TestCase):
    def test_check_toolkit_accepts_the_shipped_runner(self):
        host.check_toolkit()

    def test_check_toolkit_refuses_a_runner_with_another_parser_interface(self):
        with mock.patch.object(index.parser(), 'PARSER_INTERFACE', 1):
            with self.assertRaises(audit.AuditError) as raised:
                host.check_toolkit()
        self.assertIn('incompatible runner', str(raised.exception))
        index.parser.cache_clear()
        with mock.patch.object(index, 'PARSER_INTERFACE', 3):
            with self.assertRaises(audit.AuditError):
                host.check_toolkit()
