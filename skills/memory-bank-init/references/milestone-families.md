## Milestone families

Keep the originally agreed delivery outcome stable. Small directly related
fixes stay in the current task. Substantial discoveries use flat child records:
`amend-M53-01.md` for required work, `option-M53-02.md` for optional work.
Both kinds share one permanent 01–99 sequence under a root ID; reserve IDs
across active and retired records, never reuse or silently rename them. No
recursive child families. Archive IDs remain a separate namespace.

An amendment must name the original requirement, evidence it is unmet, and
why a simpler implementation or verification route cannot satisfy it. Extra
features, broader coverage, environmental convenience and design perfection
are options. **External testing-tool repair is an option by default.** A failed
testing method does not establish a product defect. Promoting tool repair to
a blocking amendment requires an explicit owner decision even under
`CORRECTIVE_PLANNING: auto`; the agent cannot infer it from a failed test route.
Use a simpler valid method when possible, otherwise record missing evidence.
Mocks prove only what they exercise. They cannot pass required real acceptance;
an unmet original requirement needs repair or an explicit owner disposition.

Each child owns its specification and, once planned, task table and review in
one file under `tabilet/memory-bank/`. Begin it with `## M53-01 - [Title]` and
exactly one unfenced `Parent: M53` line. The filename determines its kind. Keep
only concise links in the parent and roadmap, not duplicate child specifications.
Initially an option can be a short finding with no rows. Required amendments
and selected options need full scope, acceptance, tasks and ordinary review.
Reclassification needs an explicit planning decision and preserved lineage;
use normal supersession with a fresh ID instead of silently renaming a file.

Finish independent parent work, then required amendments, then resume the
parent's deferred acceptance checks and final review. Affected required rows
remain `[!]`, naming the amendment and resumption condition; completed rows
and valid evidence stay complete. The parent is still open while awaiting
amendments. Each child has its own review; its closure cannot replace parent
acceptance or reset the parent's review counter. `Parent:` is a relationship,
not a dependency on the completed parent. Never add that circular edge.

For strict `STATUS_ORDER`, place the parent followed immediately by all its
required active amendments, before downstream milestones. This contiguous
family expands to parent work → amendments → parent closure. Each ID still
appears once. Reject missing/noncontiguous family members and dependency cycles.
Root-only orders keep their existing semantics. `STATUS_PRIORITY` adds no
ordering edges and uses the same family readiness/closure conditions. Preserve
ordinary dependencies, write ownership and parallel-safety checks.

`OPTION_POLICY: confirm` is the default; `ignore` is the other value. During
parent execution, record optional discoveries briefly and leave them alone:
no detailed planning, repeated inspections or implementation. Under `confirm`,
only after parent closure consolidate its options, remove duplication/obsolete
items and present one proposed implementation batch. Recommend yes for the
remaining useful batch, but wait for an actual owner answer; silence is not
approval. Independent main work may continue. Under `ignore`, omit option
refinement, prompts and execution throughout the current goal. Preserve the
backlog for later consideration; goal completion never activates it. With no
options there is no option decision. Options never block parent closure.

Approved options enter a newly approved execution horizon through existing
planning; they do not reopen the parent. An explicit option-selection request
can override an earlier ignore setting for the named work. Neither this policy
nor `SUGGESTED_UPDATE: auto` grants new actions, budgets or silent scope expansion.
Preserve grants, denials, consumed attempts, review counters and history. Existing
corrective-planning authority governs required amendments except for the explicit
external-tool promotion decision above. Keep status in child/parent records and
Git history; do not append dated progress paragraphs to `AGENTS.md`.

The standalone API loop indexes options for integrity but never selects them;
use direct Goal/Next with owner selection or an explicitly approved controller
receipt. The controller's horizon must bind each child's actual filename in
closure/task paths. It never imports Goal grants or dynamically expands a
receipt. A suspended parent row requires a fresh explicit receipt whose task
`resume_after` lists its sole amendment blockers; restore it only after all
those amendments have verified closure and other task dependencies pass.
Without that approved resumption condition, blocked rows still stop execution.

Retirement preserves the complete child file and specification in the ordinary
literal envelope under its same filename. Use the child source path for both
Source status and Source specification, retain `Parent:`, and index its child ID.
Completed parents may retire with deferred options linked to the frozen parent.
Never retire a parent ahead of a required amendment's acceptance. Root status
formats, six markers and existing retirement requirements remain compatible.
