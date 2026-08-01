Read `AGENTS.md`, then read the memory bank in the order required by
`AGENTS.md`.

Find the next actionable pending row in `memory-bank/status.md`.

Tackle exactly one row:

- Implement the change.
- Update relevant memory-bank or docs files.
- Mark the row complete only when verified.
- Run the required verification.
- Commit the change with a scoped commit message.

If completing this row completes a milestone, run the milestone review procedure
from `memory-bank/milestone.md` before final handoff. Commit review fixes
separately.

Stop if there is no actionable pending row, if the next row is blocked, or if
the task is ambiguous enough to require human input.
