import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

shutil.copyfile(TREE / "template/tabilet/memory-bank/test-policy.md", MEMORY / "test-policy.md")
write(MEMORY / "tech-stack.md", read(MEMORY / "tech-stack.md") + "\n- **Test policy**: every test follows [test-policy.md](test-policy.md).\n")
