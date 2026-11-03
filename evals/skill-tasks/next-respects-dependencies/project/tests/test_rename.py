import unittest

from src import tasklist


class RenameTests(unittest.TestCase):
    def test_rename_changes_the_title(self):
        tasklist.TASKS.clear()
        tasklist.add("draft")
        tasklist.rename(1, "final")
        self.assertEqual(tasklist.listing()[0]["title"], "final")


if __name__ == "__main__":
    unittest.main()
