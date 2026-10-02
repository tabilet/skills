# Optional stage planning

`tabilet/stages.md` is an optional project-owned overview of delivery stages.
When it is absent, the project has one implicit stage and existing milestone,
status, and goal behavior applies. A stage is a planning context, never an
executable status or a substitute for milestone acceptance. Do not create an
empty stages file for a one-stage project.

Use this minimal shape when stages are approved:

```markdown
# Stages

**Current stage.** STG-01

## STG-01

**Name.** [Meaningful name]
**Intent.** [Next delivery outcome]

## STG-02

**Name.** [Tentative name]
**Intent.** [Preliminary idea in the user's words]
```

In a generated project, replace every bracketed example with approved content.
Heading order records intended order; `Current stage` identifies the stage for
the approved active horizon. When the current stage has no executable work,
retain its ID until a later approved proposal chooses the next stage. Do not
infer completion from a heading, task cancellation, or session end.
The current ID must resolve to a live stage entry. Withdrawing that entry
requires an approved replacement current ID in the same proposal.

Stage IDs start at `STG-01`, increase monotonically, and have at least two
digits. Keep an ID stable through a name or order change. Never reuse an ID;
retain a withdrawn stage as a short entry with its reason and any replacement.
The `STG-` namespace is separate from status and archive IDs. Resolve an
unknown, duplicate, or ambiguous stage reference before planning dependent work.
Keep an adopted stages file even if the project later has one remaining stage;
its withdrawn entries reserve past IDs.

A future stage needs only an ID, tentative name, and brief intent. Add known
context, assumptions, dependencies, open questions, and a trigger for detailed
planning when helpful. Label inferred details as provisional. Do not interview
the user to fill remote-stage fields or invent facts to make them look complete.
Ask about a future stage only when a decision affects the current stage's scope,
contract, dependency, or acceptance.

Only the current approved horizon has milestone IDs, status files, and goal
launch input. Put its stage ID in each relevant active milestone specification;
future stage ideas have none of those execution artifacts. Candidate Directions
remain unnumbered: link a direction to a stage when useful, without duplicating
its description. A preliminary stage need not have a candidate's deferral
reason or promotion trigger. A new stage does not automatically promote a
candidate.

Revisit stages through an approved planning proposal. Distinguish enriching a
stage's context from explicitly requesting executable milestones. When adopting
stages in an initialized project, preserve completed history, current row states,
review counters, and approved work. Assign the existing active horizon to the
current stage by default. A stage label alone never defers a pending row: an
explicitly approved rescope must withdraw affected untouched work and reconcile
its dependencies and launch input. Closure and retirement retain their existing
evidence gates. Stage progression requires a fresh planning decision.
