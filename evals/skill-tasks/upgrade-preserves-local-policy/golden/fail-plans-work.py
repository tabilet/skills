import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

write("AGENTS.md", read("AGENTS.md") + "\n## Requested changes\n\nRequested features, candidate promotions, and future direction changes after\ninitialization follow the requested-change procedure in\n`tabilet/memory-bank/milestone.md`.\n")
add_milestone(ident="M02", title="Adopt the new rules", after="M01", depends="M01")
