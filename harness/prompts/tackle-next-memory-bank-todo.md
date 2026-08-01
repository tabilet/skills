Read `AGENTS.md`, then read the memory bank in the order required by
`AGENTS.md`.

Read `memory-bank/milestone.md` for the status ID pattern, the lane meanings,
and milestone priority. Then find the next actionable pending row in the
matching `memory-bank/status-<LANE><NN>.md` file.

Tackle exactly one row:

- Implement the change.
- Update relevant memory-bank or docs files.
- Mark the row complete only when verified.
- Run the required verification.
- Commit the change with a scoped commit message.

If completing this row completes a milestone, run the milestone review procedure
from `memory-bank/milestone.md` before final handoff. Commit review fixes
separately.

Skip blocked rows and pick another actionable row instead. Stop if no actionable
pending row remains in any lane, or if the task is ambiguous enough to require
human input.
