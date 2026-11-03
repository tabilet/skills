import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '_golden'))
from common import *

shutil.copyfile(TREE / 'GOAL.md', 'tabilet/GOAL.md')
git('add', '-A')
git('commit', '-qm', 'Add the goal protocol')
