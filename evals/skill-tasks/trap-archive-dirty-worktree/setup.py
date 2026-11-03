import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '_golden'))
from common import *

write('src/tasklist.py', read('src/tasklist.py') + '\n\ndef export_csv(path: str) -> None:\n'
      '    raise NotImplementedError  # work in progress\n')
write('notes/draft.md', 'CSV export ideas, not ready to commit.\n')
