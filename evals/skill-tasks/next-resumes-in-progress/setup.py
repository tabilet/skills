import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '_golden'))
from common import *

ledger([{'ident': 'M01', 'title': 'Task editing', 'goal': 'Edit tasks after they are added.', 'depends': 'none', 'rows': [('Add complete(task_id) to src/tasklist.py', '[+]', 'Done.'), ('Add rename(task_id, title) to src/tasklist.py', '[ ]', '')]}, {'ident': 'M02', 'title': 'Task removal', 'goal': 'Remove tasks from the list.', 'depends': 'none', 'rows': [('Add remove(task_id) to src/tasklist.py', '[~]', 'Started: tests/test_remove.py describes the behavior; remove() is not written yet.'), ('Make remove() of an unknown id a no-op, with a test', '[ ]', '')]}])
