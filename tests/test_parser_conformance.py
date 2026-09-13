"""Portable reader fixtures, also consumed by the companion DSH plugin."""
import json
import unittest
from test_harness import ROOT, harness


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
