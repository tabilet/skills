import unittest
from parse import parse_int


class ParseTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_int('42'), 42)
        self.assertIsNone(parse_int('forty-two'))
