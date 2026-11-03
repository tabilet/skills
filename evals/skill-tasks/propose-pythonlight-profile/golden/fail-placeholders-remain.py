import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone()
import re
text = read(MEMORY / "tech-stack.md")
text = text.replace("`[standard | browserlight | golight | rustlight | tslight | jslight | pythonlight]`", "`pythonlight`")
text = re.sub(r"\*\*Focused tests\*\*: \[[^\n]*\]", "**Focused tests**: `python3 -m unittest` (30-second target, 2-minute cap)", text)
text = re.sub(r"\*\*Full regression\*\*: \[[^\n]*\]", "**Full regression**: `python3 -m unittest` (20-minute cap)", text)
text = re.sub(r"\*\*Execution cadence\*\*: \[", "**Execution cadence**: [", text)
for name in ():
    text = re.sub(r"\*\*" + name + r"\*\*: \[([^\n]*)\]", lambda m: "**" + name + "**: " + m.group(1), text)
write(MEMORY / "tech-stack.md", text)
write("AGENTS.md", read("AGENTS.md") + "\n- Verification and testing standards: see tabilet/memory-bank/tech-stack.md.\n")
