import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '_golden'))
from common import *

write_summaries()
ledger([{'ident': 'M01', 'title': 'SQLite storage', 'goal': 'Persist tasks in SQLite.', 'depends': 'none', 'rows': [('Store tasks in a SQLite database `tasks.db` (table `tasks`) instead of `tasks.json`; keep save(path) and load(path)', '[ ]', ''), ('Read an existing tasks.json on first load and move it into tasks.db', '[ ]', '')]}])
