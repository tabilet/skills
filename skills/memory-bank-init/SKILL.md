---
name: memory-bank-init
description: Interview the user about a project, then generate its memory bank - product, architecture, tech stack, milestones, and status lanes. Use when a project has no memory-bank/ yet.
disable-model-invocation: false
argument-hint: (no arguments)
---

# Initialize A Memory Bank

Three phases: **grill**, **propose**, **write**. Write no file until phase 3.

The output is a memory bank the user owns outright. It has no link back to
wherever this skill came from, and nothing will update it but them.

## Phase 1 - Grill

Interview the user until you share an understanding of the project. Rules:

- **One question at a time.** Wait for the answer before asking the next.
  Asking several at once is bewildering and produces shallow answers.
- **Give your recommended answer with each question**, so agreeing costs one
  word. A question with no recommendation attached is work you handed back.
- **Facts you can look up, look up. Decisions are the user's.** If the answer is
  discoverable from the repository - the test command, the language, the
  dependencies, the CI config - read it and confirm briefly rather than asking.
  Never guess at a decision to save a question.
- **Walk the tree in order.** Later answers depend on earlier ones.
- **Do not act until the user confirms** you have it right.

*(Interview technique adapted from the `grilling` skill in
[mattpocock/skills](https://github.com/mattpocock/skills), MIT.)*

### The tree

1. **What is this, and who uses it?**
2. **What is it not?** Push until you have at least two real non-goals. These
   are the highest-value lines in the memory bank and the ones users skip; they
   are what stops an agent helpfully building the wrong thing.
3. **Stack and constraints.** Include the constraints that are choices - no
   build step, no runtime dependencies, must run offline.
4. **How do you know it works?** A command that exits non-zero on failure.
   **This question gates everything after it**: acceptance criteria are written
   against it, and without one no unattended work is possible. If the honest
   answer is "there is no such command yet," the first status row is creating
   one. If part of the project can only be judged by hand - feel, rendering,
   layout - say so explicitly and note which parts.
5. **Boundaries.** What this project owns, and what belongs elsewhere.
6. **Feature areas.** The domains the work splits into. Candidate lanes.
7. **Order and dependencies** between those areas.

**Existing project:** read the README, tests, build and CI files *first*, then
ask only what they cannot tell you. Usually that is questions 2, 5, and 7.

**Empty directory:** everything is a question, and question 4 is the one people
have not thought about.

Stop when you can state in one paragraph what the project is, how you would know
it works, and what the first milestone delivers. Say it back and ask the user to
confirm.

## Phase 2 - Propose

Present the breakdown as a numbered list. **Write nothing to disk yet.**

Show the lane letters and what each means, the milestones with their acceptance
criteria, the first milestone's rows, and the execution order with dependencies.

Rules for the breakdown:

- **A milestone is a vertical slice.** It cuts a narrow but complete path
  through every layer and is demoable or verifiable on its own. "The player
  moves, jumps, and collides" is a milestone. "The database layer" is not - it
  is a horizontal slice that is never independently done.
- **A row is one commit.** Small enough to be plainly done or not done, and
  sized to fit in a single fresh context window.
- **Every milestone's acceptance names the verification command** from question
  4. An acceptance criterion nobody can run is a wish.
- **Start with one lane** (`M`) unless the areas genuinely have different
  acceptance criteria. Splitting early buys nothing. Lane letters can never be
  renamed once their file exists, so propose them only when they have earned it.

Then ask the user:

- Is the granularity right - too coarse, too fine?
- Are the dependencies correct? Does each milestone depend only on what
  genuinely gates it?
- Should anything be merged or split?

Iterate until the user approves. A wrong breakdown is cheap to fix now and
expensive to fix once six files exist.

## Phase 3 - Write

Only after approval.

```text
AGENTS.md                        what an agent reads first
GOAL.md                          optional protocol for multi-milestone runs
memory-bank/product.md           what this is, who it is for, what it is not
memory-bank/architecture.md      layout, data flow, the boundaries that matter
memory-bank/tech-stack.md        stack, dependencies, verification commands
memory-bank/milestone.md         lane meanings, milestone index, acceptance
memory-bank/status-<LANE><NN>.md one per milestone, one row per task
evolution/prompt-v1.md           the initial direction
evolution/result-v1.md           the state this starts from
```

`GOAL.md` is **copied, never written from memory.** It is a portable protocol
that must stay byte-identical across every project that carries it, so
reproducing it by hand corrupts it. Copy the `GOAL.md` that sits beside this
skill file — under `${CLAUDE_PLUGIN_ROOT}` when this was installed as a plugin,
otherwise in this skill's own directory. If you cannot find it, say so and leave
it out rather than writing an approximation; the project still works without it,
and `/memory-bank-goal` will tell the user where to get it.

Tell the user it is optional and can be deleted: it is one way to run several
milestones in order, not a requirement of the memory bank.

`AGENTS.md` stays short: what to read and in what order, the essential commands,
the boundaries, the hard rules, and the work cadence. It points at the memory
bank rather than restating it.

Status files are tables. **The backticks around every marker are required** - a
bare `[ ]` is invisible to tools that read these files, and the run will report
that no work remains:

```markdown
# Status M01 - <milestone title>

**Acceptance.** <the verification command, and what it must show>

| Item | State | Notes |
|---|---|---|
| <task> | `[ ]` | <constraint, edge case, or decision from the interview> |
```

Markers: `` `[ ]` `` pending, `` `[+]` `` done, `` `[~]` `` in progress,
`` `[!]` `` blocked, `` `[X]` `` cancelled.

### Before reporting done, check your own output

1. Every marker is wrapped in backticks.
2. Every status filename is `status-<LANE><NN>.md` with the number zero-padded
   to **two** digits - `status-M01.md`, never `status-M1.md`.
3. The milestone index in `milestone.md` lists exactly the status files that
   exist, and every link resolves.
4. No bracketed placeholder is left anywhere.

Then tell the user what you could not fill and why. Anything left is a decision
that was never actually made - ask for it rather than inventing it.

Finally, state the two sentences that run the project from here: *"tackle next
pending item in memory bank"* for one task, and `/memory-bank-goal` for an
ordered set of milestones.
