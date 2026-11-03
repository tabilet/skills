import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '_golden'))
from common import *

seed_archived_storage()
write('src/tasklist.py', '"""Tasklist: add, complete and list tasks; store them in a SQLite database."""\nimport sqlite3\n\nTASKS: list[dict] = []\n\n\ndef add(title: str) -> dict:\n    task = {"id": len(TASKS) + 1, "title": title, "done": False}\n    TASKS.append(task)\n    return task\n\n\ndef complete(task_id: int) -> None:\n    for task in TASKS:\n        if task["id"] == task_id:\n            task["done"] = True\n\n\ndef listing() -> list[dict]:\n    return list(TASKS)\n\n\ndef save(db_path: str = "tasks.db") -> None:\n    with sqlite3.connect(db_path) as db:\n        db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, done INTEGER NOT NULL)")\n        db.execute("DELETE FROM tasks")\n        db.executemany("INSERT INTO tasks VALUES (?, ?, ?)", [(t["id"], t["title"], int(t["done"])) for t in TASKS])\n\n\ndef load(db_path: str = "tasks.db") -> None:\n    with sqlite3.connect(db_path) as db:\n        rows = db.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()\n    TASKS[:] = [{"id": i, "title": title, "done": bool(done)} for i, title, done in rows]\n')
edit('tests/test_tasklist.py', 'tasks.json', 'tasks.db')
git('add', '-A')
git('commit', '-qm', 'Store tasks in a SQLite database')
