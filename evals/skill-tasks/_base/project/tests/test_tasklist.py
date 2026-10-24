import os
import tempfile
import unittest

from src import tasklist


class TasklistTests(unittest.TestCase):
    def test_add_then_list(self):
        tasklist.TASKS.clear()
        tasklist.add("write report")
        self.assertEqual([t["title"] for t in tasklist.listing()], ["write report"])

    def test_save_then_load_keeps_tasks(self):
        tasklist.TASKS.clear()
        tasklist.add("write report")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "tasks.json")
            tasklist.save(path)
            tasklist.TASKS.clear()
            tasklist.load(path)
        self.assertEqual([t["title"] for t in tasklist.listing()], ["write report"])


if __name__ == "__main__":
    unittest.main()
