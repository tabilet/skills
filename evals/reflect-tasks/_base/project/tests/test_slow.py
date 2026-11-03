import time
import unittest
from src.parser import parse_line


class SlowTests(unittest.TestCase):
    def test_slow_integration(self):
        time.sleep(0.6)
        self.assertEqual(parse_line("  slow  "), "slow")


if __name__ == "__main__":
    unittest.main()
