import unittest

from src import tasklist


class TasklistTests(unittest.TestCase):
    def test_add_then_list(self):
        tasklist.TASKS.clear()
        tasklist.add("write report")
        self.assertEqual([t["title"] for t in tasklist.listing()], ["write report"])


if __name__ == "__main__":
    unittest.main()
