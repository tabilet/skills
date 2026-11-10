import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '_golden'))
from common import *

ledger([{'ident': 'S04', 'title': 'Due dates', 'goal': 'Give tasks optional due dates.', 'depends': 'R03', 'rows': [('Add add_due(title, due) that records an optional due date', '[ ]', '')]}, {'ident': 'R03', 'title': 'Task editing', 'goal': 'Edit tasks after they are added.', 'depends': 'none', 'rows': [('Add complete(task_id) to src/tasklist.py', '[+]', 'Done.'), ('Publish renamed titles to the shared team board', '[!]', 'Blocked: needs the board API token, which is not available.'), ('Add rename(task_id, title) to src/tasklist.py', '[ ]', '')]}])
