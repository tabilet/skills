import inspect
import os
import sqlite3
import tempfile
import unittest

from src import tasklist


class SqliteStorageTests(unittest.TestCase):
    def test_save_writes_a_tasks_table(self):
        tasklist.TASKS.clear()
        tasklist.add("write report")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "tasks.db")
            tasklist.save(path)
            with sqlite3.connect(path) as db:
                rows = db.execute("SELECT id, title, done FROM tasks").fetchall()
        self.assertEqual(rows, [(1, "write report", 0)])

    def test_the_default_file_is_tasks_db(self):
        self.assertEqual(inspect.signature(tasklist.save).parameters["path"].default, "tasks.db")
        self.assertEqual(inspect.signature(tasklist.load).parameters["path"].default, "tasks.db")


if __name__ == "__main__":
    unittest.main()
