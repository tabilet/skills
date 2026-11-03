import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

shutil.copyfile(TREE / "template/tabilet/memory-bank/test-policy.md", MEMORY / "test-policy.md")
write(MEMORY / "tech-stack.md", read(MEMORY / "tech-stack.md") + "\n- **Test policy**: every test follows [test-policy.md](test-policy.md).\n")
write("AGENTS.md", read("AGENTS.md") + "\n## Requested changes\n\nRequested features, candidate promotions, and future direction changes after\ninitialization follow the requested-change procedure in\n`tabilet/memory-bank/milestone.md`.\n")
edit("AGENTS.md", "## Hard Rules", "## Hard Rules\n\n- Tests follow `tabilet/memory-bank/test-policy.md`.")
