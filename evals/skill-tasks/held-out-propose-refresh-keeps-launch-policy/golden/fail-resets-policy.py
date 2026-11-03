import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone()
edit(MEMORY / "suggested.txt", "M01 -> M02\n", "M01 -> M02 -> M03\n")
edit(MEMORY / "suggested.txt", "M02 = tabilet/memory-bank/status-M02.md\n", "M02 = tabilet/memory-bank/status-M02.md\nM03 = tabilet/memory-bank/status-M03.md\n")

edit(MEMORY / "suggested.txt", "COMMIT_POLICY: none", "COMMIT_POLICY: task")
edit(MEMORY / "suggested.txt", "REVIEW_MAX_ITERATIONS: 3", "REVIEW_MAX_ITERATIONS: 10")
