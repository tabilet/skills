import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

archive("C02", "Task storage", head(), supersedes="C01", storage="a SQLite database `tasks.db` with one `tasks` table",
        correction="Storage moved from the JSON file recorded in C01 to SQLite.")
edit(MEMORY / "architecture.md", "Task model and JSON persistence.", "Task model and SQLite persistence.")
edit(MEMORY / "architecture.md", "`save()` writes it to `tasks.json` and `load()` reads it back.", "`save()` writes it to the `tasks` table in `tasks.db` and `load()` reads it back.")
edit(MEMORY / "architecture.md", "- `tasks.json` holds a JSON array of `{\"id\", \"title\", \"done\"}` objects.", "- `tasks.db` is a SQLite database with a `tasks(id, title, done)` table.")
edit(MEMORY / "architecture.md", "`save(path=\"tasks.json\")` and `load(path=\"tasks.json\")`", "`save(db_path=\"tasks.db\")` and `load(db_path=\"tasks.db\")`")
edit(MEMORY / "product.md", "Saved tasks live in one `tasks.json` file.", "Saved tasks live in one SQLite database, `tasks.db`.")
text = read(MEMORY / "architecture.md")
write(MEMORY / "architecture.md", "\n".join(l for l in text.splitlines() if not l.startswith("| [C01]")) + "\n")
add_archive_row("C02", "Task storage", head(), "none")
