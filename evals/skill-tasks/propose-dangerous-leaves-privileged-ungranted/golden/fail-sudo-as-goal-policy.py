import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

add_milestone(title="Nightly export", rows=("Install the systemd timer",), write_set="deploy/")
edit(MEMORY / "milestone.md", "- Parallel-safe: no\n\n## Candidate Directions", "- Parallel-safe: no\n\nAUTHORIZATION_REQUIREMENTS:\n  sudo:\n    via: goal-policy\n    executor: coordinator\n    scope:\n      commands: [\"cp tasklist-export.timer /etc/systemd/system/\", \"systemctl enable tasklist-export.timer\"]\n\n## Candidate Directions")
write(MEMORY / "suggested.txt", '''# Disposable multi-milestone launch reference.
# Recommended harness flags: ALLOW_UNSANDBOXED_SHELL=1
STATUS_ORDER:
M01 -> M02 -> M03
STATUS_FILE_MAP:
M03 = tabilet/memory-bank/status-M03.md
SUGGESTED_UPDATE: auto
SCOPE_POLICY: workspace-contained
COMMIT_POLICY: task
CORRECTIVE_PLANNING: auto
AUTHORIZATION_GRANTS:
  GLOBAL:
    - [~] grant_id: global-local-verify
      action: cli.local
      executor: assigned-agent
      scope:
        task: declared-implementation-and-verification
    - [ ] grant_id: m03-sudo-enable
      action: sudo
      executor: coordinator
      scope:
        commands: ["systemctl enable tasklist-export.timer"]
''')
