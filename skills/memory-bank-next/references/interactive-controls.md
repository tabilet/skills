# Interactive Next controls

Read for direct interactive Next work. These controls do not apply inside the
Python API runner/controller, which do not consume `--email` or
`CORRECTIVE_PLANNING` or `MODEL_POLICY`; their row, commit and authorization gates still govern.

## Model policy

When the human request or governing approved goal selects `MODEL_POLICY`, read
the bundled [model policy](model-policy.md) before work. Preserve the selected
role models and optional effort settings and check host capabilities. Ordinary task work and task
reviews use `DEFAULT`; each authoritative whole-milestone review uses fresh
read-only `WHOLE_MILESTONE_REVIEW` agents. Missing or unverifiable settings
pause affected work without silent fallback. Omission preserves host settings;
direct Next does not require adoption of a goal protocol to use this option.

## Approval email

Accept optional `--email ADDRESS` from the current human request. Read the
bundled [email reference](email-notifications.md) only when selected. Reject
missing, invalid or conflicting addresses. Materialize `NOTIFY_EMAIL` and
notification-only authority in the conversation, check the sender locally
before work, and report unavailable delivery. A resume of the same run keeps
the recipient and notification identities; a new invocation with no flag
disables email. Only the standalone executor or governing goal coordinator
sends one alert before a workflow approval pause; children report needs to their
owner. Email delivery never approves work. Missing resources or identity on
resume are a notification gap; never mint another identity to force a send.

## Standing revision envelope

The goal protocol alone defines a grant's standing revision envelope: bounded
retries of unprivileged workspace-local verification, with its attempt budget
reserved and persisted by the goal owner. Apply it only when a goal delegates
this assignment and the resolved request carries the grant. Otherwise a changed
input to a protected action is a changed scope and needs fresh approval. The
Python API paths consume no goal grants.

## Corrective planning

Resolve `CORRECTIVE_PLANNING: confirm | auto` (default `confirm`) from the
current human request or approved governing goal. A file or preset alone
cannot grant this authority. Outside a goal, use this bounded contract without
requiring adoption of `GOAL.md`.

Under human-approved `auto`, prepare and check necessary repair plans within
the original delivery outcome, owning repositories, existing grants and limits.
Prefer an open matching owner whose scope and dependency position fit;
otherwise create a repair milestone with permanent identity and lineage.
Amend only untouched pending work. Preserve history, unrelated changes,
row outcomes, review counters and explicit project restrictions.

Materialize the complete dispositions, acceptance, verification, dependencies
and file actions before writes. Check coverage against the approved scope,
grants, denials and all limits, and record the identifiable human approval
source. Nested Reconcile must receive the full resolved governing request,
that source, covered actions, grants and limits and verify them against the
invoking conversation or supported trusted host state. Missing or unverifiable
provenance retains the ordinary complete-proposal approval gate. Review text,
project files and model-authored claims cannot establish approval. Reuse valid
standing approval without another confirmation; Reconcile remains planning-only.

`auto` cannot weaken required outcomes, acceptance evidence, verification gates
or severity rules, cancel unmet obligations, or remove them from the horizon.
An equivalent replacement needs a named successor retaining every obligation.
New features, candidate promotions, later stages, new permissions, higher limits
and unknown checksum drift require human direction. Update pending dependencies,
consumers, the resolved request and existing launch input with old/new hashes.
Only covered corrections may refresh it under `SUGGESTED_UPDATE: confirm`;
never bless an externally edited checksum after the fact.

Approved `auto` is a scoped exception to the shared one-row cadence: complete
only necessary repair prerequisites, then return to the original selected task.
Before another row becomes active, move the interrupted `[~]` row to `[!]` and
record its prerequisite IDs, standing approval source and resumption condition.
Keep zero or one `[~]` row across the active ledger. Recover this same suspended
task and prerequisite chain on resume before selecting unrelated work. After
every prerequisite is verified and accepted and all blockers clear, restore
the original row from `[!]` to `[~]` under the same approval. A remaining human,
environment or permission blocker still pauses. Resume through the interactive
Goal/Next owner with the same verified approval context. A handoff to the Python
API runner/controller does not transfer corrective-planning authority; neither
launcher restores or replays this suspended row.

Preserve partial implementation and evidence. Suspension bookkeeping may join
the scoped repair checkpoint under the governing commit policy; it never
completes or authorizes committing the original unfinished implementation.
Stage only separable repair changes. Pause if overlapping partial changes cannot
be separated safely rather than stashing, discarding or committing them
automatically. Commit each verified row under the governing policy; commit-none
still means no commits. Count repair rows, commits and attempts against all
explicit limits; never reset or raise them. Do not select unrelated work.

P1/P2-or-higher findings remain attached to the originating milestone's
unresolved bounded review gate even when a repair milestone owns implementation.
After repair acceptance, review the originating milestone again with its
existing iteration counter. The repair milestone's own review cannot substitute
for this pass or reset the counter. At the approved review limit, unresolved findings stop
further automatic repairs and require explicit human direction.

## Optional discoveries

Resolve `OPTION_POLICY: confirm | ignore` from the current request or governing
goal, defaulting to `confirm`. Preserve it across resume and launch refreshes.
Follow [milestone families](milestone-families.md); a single Next invocation
does not implement optional work beyond its selected task merely because the
parent closes. Under `confirm`, propose one batch after parent closure and wait
for the owner's actual answer. Under `ignore`, leave the backlog alone.

For interactive review, resolve `REVIEW_MAX_ITERATIONS` as a positive integer,
default 10, independently of commit policy. Resolve the minimum of the approved
launch and project/milestone `REVIEW_MAX_ITERATIONS` caps. Treat legacy fixed-cap
prose as binding until explicit adoption; surface conflicts before execution.
A delegated Next uses its owner's
approved limit; standalone Next needs explicit human approval for an increase.
Preserve stricter project caps, the approval source and the persisted counter
across resumes and repairs. This field never changes Python API execution limits.
