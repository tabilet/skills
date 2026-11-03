import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

set_row("M01", 'Store tasks in a SQLite database `tasks.db` (table `tasks`) instead of `tasks.json`; keep save(path) and load(path)', "[+]")
edit(MEMORY / "architecture.md", "Task model and JSON persistence.", "Task model and SQLite persistence.")
edit(MEMORY / "architecture.md", "`save()` writes it to `tasks.json` and `load()` reads it back.", "`save()` writes it to the `tasks` table in `tasks.db` and `load()` reads it back.")
edit(MEMORY / "architecture.md", "- `tasks.json` holds a JSON array of `{\"id\", \"title\", \"done\"}` objects.", "- `tasks.db` is a SQLite database with a `tasks(id, title, done)` table.")
edit(MEMORY / "architecture.md", "`save(path=\"tasks.json\")` and `load(path=\"tasks.json\")`", "`save(path=\"tasks.db\")` and `load(path=\"tasks.db\")`")
edit(MEMORY / "product.md", "Saved tasks live in one `tasks.json` file.", "Saved tasks live in one SQLite database, `tasks.db`.")
commit("Store tasks in SQLite")
