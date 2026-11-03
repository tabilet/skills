import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '_golden'))
from common import *

seed_archived_storage()
pathlib.Path('src/tasklist').mkdir()
pathlib.Path('src/tasklist.py').rename('src/tasklist/core.py')
write('src/tasklist/__init__.py', '"""Tasklist package; the implementation lives in core."""\n'
      'from .core import TASKS, add, complete, listing, load, save  # noqa: F401\n')
git('add', '-A')
git('commit', '-qm', 'Move tasklist into a package; no behavior change')
