import unittest
from src.parser import parse_line


class FastTests(unittest.TestCase):
    def test_strip(self):
        self.assertEqual(parse_line("  hello  "), "hello")


if __name__ == "__main__":
    unittest.main()
