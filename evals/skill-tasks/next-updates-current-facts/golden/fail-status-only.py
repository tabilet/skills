import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

text = read("src/tasklist.py").replace("import json\n", "import json\nimport sqlite3\n")
write("src/tasklist.py", text[:text.index("def save(")] + 'def save(path: str = "tasks.db") -> None:\n    with sqlite3.connect(path) as db:\n        db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, done INTEGER NOT NULL)")\n        db.execute("DELETE FROM tasks")\n        db.executemany("INSERT INTO tasks VALUES (?, ?, ?)", [(t["id"], t["title"], int(t["done"])) for t in TASKS])\n\n\ndef load(path: str = "tasks.db") -> None:\n    with sqlite3.connect(path) as db:\n        rows = db.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()\n    TASKS[:] = [{"id": i, "title": title, "done": bool(done)} for i, title, done in rows]\n')
set_row("M01", 'Store tasks in a SQLite database `tasks.db` (table `tasks`) instead of `tasks.json`; keep save(path) and load(path)', "[+]", "Done; tests/test_sqlite.py passes.")
commit("Store tasks in SQLite")
