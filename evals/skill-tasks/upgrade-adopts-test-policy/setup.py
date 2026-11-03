import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '_golden'))
from common import *

pathlib.Path(MEMORY / 'test-policy.md').unlink()
write(MEMORY / 'tech-stack.md', '\n'.join(l for l in read(MEMORY / 'tech-stack.md').splitlines() if 'test-policy.md' not in l) + '\n')
git('add', '-A')
git('commit', '-qm', 'Project before the test policy existed')
