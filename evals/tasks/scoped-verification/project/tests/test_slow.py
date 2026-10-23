import pathlib
import time
import unittest


class SlowTests(unittest.TestCase):
    def test_full_regression(self):
        pathlib.Path('.slow_ran').write_text('ran')
        time.sleep(25)
