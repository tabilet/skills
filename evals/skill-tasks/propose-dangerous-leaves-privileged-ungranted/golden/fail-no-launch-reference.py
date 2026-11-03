import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Nightly export", rows=("Install the systemd timer",), write_set="deploy/")
edit(MEMORY / "milestone.md", "- Parallel-safe: no\n\n## Candidate Directions", "- Parallel-safe: no\n\nAUTHORIZATION_REQUIREMENTS:\n  sudo:\n    via: explicit\n    executor: coordinator\n    scope:\n      commands: [\"cp tasklist-export.timer /etc/systemd/system/\", \"systemctl enable tasklist-export.timer\"]\n\n## Candidate Directions")
