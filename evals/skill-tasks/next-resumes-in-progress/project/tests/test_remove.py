import unittest

from src import tasklist


class RemoveTests(unittest.TestCase):
    def test_remove_drops_only_that_task(self):
        tasklist.TASKS.clear()
        tasklist.add("a")
        tasklist.add("b")
        tasklist.remove(1)
        self.assertEqual([t["title"] for t in tasklist.listing()], ["b"])


if __name__ == "__main__":
    unittest.main()
