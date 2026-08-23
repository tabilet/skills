# You've Been Grilled. Now Build the Whole Harness.

<!-- Medium publishing asset: medium-new-project-infographic.png. Upload it
immediately below the article title; it is intentionally not embedded here. -->

*Turning a ten-minute conversation into a memory bank, a set of milestones, and a blocker-aware ordered run.*

If you are a frequent user of skills like `/grill-me`, you have probably had this thought: the interview is great, but why stop at one skill? Why not build the whole engineering harness directly — the thing that knows what your project is, what is done, what is next, and can work through it?

That is what this package is: a file-owned engineering harness with five optional skills around it. The skills generate and operate the files, but the files do not depend on the plugin. It works standalone, and it works alongside `/grill-me` rather than against it.

The difference in one line: **`/grill-me` ends in understanding; this ends in files.**

That stopping point is deliberate — *"Do not act on it until I confirm we have reached a shared understanding."* It is exactly right for a general-purpose interview, and it is why that skill works on anything at all. But when the session closes, the understanding closes with it. Nothing is on disk, tomorrow's agent starts cold, and there is nothing to execute against.

This takes the same interview discipline and points it at files that outlive the session.

This article covers a **new project** — an empty directory and an idea. Using it on an existing codebase is a different story, and a different article.

---

## What you end up with

A compact set of plain-text files, mostly markdown, in your repository and owned outright by you:

```
your-project/
├── AGENTS.md              what an agent reads first
├── GOAL.md                optional protocol for multi-milestone runs
├── memory-bank/
│   ├── product.md         scope, domain model, and non-goals
│   ├── architecture.md    layout, data flow, the boundaries that matter
│   ├── tech-stack.md      stack, dependencies, how you verify
│   ├── milestone.md       active milestones, later directions, review rules
│   ├── status-M01.md      one permanent file per milestone, one row per task
│   └── suggested.txt      disposable goal order, file map, and impacts
└── evolution/             versioned direction snapshots
    ├── prompt-v1.md       the initial direction
    └── result-v1.md       the state it produced
```

The term *memory bank* was popularised by [Cline](https://docs.cline.bot/best-practices/memory-bank); this is a different implementation of the same idea, in plain files with no runtime.

No project CLI to adopt, no `.something/` scaffold that grows over time, no vocabulary you will have to migrate away from. The plugin never updates anything autonomously: a skill changes your files only when you invoke it and approve its proposal, and uninstalling it leaves your project exactly as it is.

`product.md` also carries the maintained domain model: canonical terminology,
relationships between concepts, and business invariants. `suggested.txt` is
created only when the project has an approved compatible `GOAL.md`; it is launch
input rather than project truth.

Five optional skills provide a repeatable interface:

- **`memory-bank-archive`** — before init when a large existing package needs frozen, commit-anchored context evidence. A new project like this one skips it.
- **`memory-bank-init`** — once per project, on the way in. It interviews you, proposes a breakdown, and writes the files after you approve.
- **`memory-bank-reconcile`** — whenever a new review arrives. It validates findings against current code and updates the approved plan without implementing fixes.
- **`memory-bank-next`** — every day. One task: implement, verify, commit.
- **`memory-bank-goal`** — several milestones, in a defined order.

---

## Installing: the two agents differ

Both agents install from the same repository and read the same manifest, but they surface the commands differently. This trips people up, so it is worth being explicit.

### Claude Code

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

The plugin is namespaced under current [Claude Code skill namespacing](https://code.claude.com/docs/en/slash-commands). Invoke the skills as `/memory-bank:memory-bank-archive`, `/memory-bank:memory-bank-init`, `/memory-bank:memory-bank-reconcile`, `/memory-bank:memory-bank-next`, and `/memory-bank:memory-bank-goal`.

### Codex

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

Two details are worth knowing.

First, Codex wants the `@marketplace` qualifier when a plugin name is not unique across your configured marketplaces. `memory-bank@tabilet` is the form to learn. Use `codex plugin marketplace upgrade` when a new version ships.

Second, plugin skills are namespaced in Codex too, using its [`$` skill invocation syntax](https://developers.openai.com/plugins/build/skills):

```
$memory-bank:memory-bank-init
```

The archive and review commands follow the same form:
`$memory-bank:memory-bank-archive` and `$memory-bank:memory-bank-reconcile`.

Plain English works in both agents, which is what this whole approach is built around anyway. If you install the skill directories as plain files rather than the plugin, they are unnamespaced: `/memory-bank-init` in Claude Code and `$memory-bank-init` in Codex. If you prefer never to think about it, `"tackle next pending item in memory bank"` does the everyday job in either one.

---

## Updating or removing the plugin

Updating is a two-part operation: refresh the marketplace, then update the
installed plugin. Removing the plugin does not remove the memory-bank files it
created in your projects; those files belong to you.

### Claude Code

Refresh `tabilet`, update the installed plugin, and load the new version into
the current session:

```bash
/plugin marketplace update tabilet
/plugin update memory-bank@tabilet
/reload-plugins
```

To uninstall the plugin:

```bash
/plugin uninstall memory-bank@tabilet
```

If you no longer want the marketplace either, remove it too. Removing a Claude
Code marketplace also uninstalls any remaining plugins installed from it.

```bash
/plugin marketplace remove tabilet
```

### Codex

Codex installs from its local marketplace snapshot, so refresh that snapshot
before adding the plugin again:

```bash
codex plugin marketplace upgrade tabilet
codex plugin add memory-bank@tabilet
```

Start a new Codex session to load the updated skills. To uninstall the plugin:

```bash
codex plugin remove memory-bank@tabilet
```

Optionally remove the marketplace once you no longer need anything from it:

```bash
codex plugin marketplace remove tabilet
```

---

## Step 1: an empty directory

```bash
mkdir stomper && cd stomper
git init
```

That is all. Do not scaffold. Do not pick a framework. The shape of the project should come out of the conversation, not out of a template you chose before thinking.

Our example is `stomper`, a Mario-style browser platformer — chosen because a game decomposes into feature areas cleanly enough to show why that matters later.

## Step 2: the interview

Run `/memory-bank:memory-bank-init` in Claude Code or `$memory-bank:memory-bank-init` in Codex and start talking.

This is the step that decides everything downstream, and it is a conversation rather than a form. The memory bank you end up with is a transcript of the decisions you reach here. Decisions you never reach come out as vague prose, and vague prose is what makes an agent build the wrong thing confidently.

It maps a dependency-ordered design tree and asks the whole **frontier** — every
independent decision whose prerequisites are settled — as a numbered round,
with a recommended answer attached to each. Your answers reshape the tree
before the next round. Ask for one-at-a-time pacing if you prefer it. Anything
it can read from the repository, it reads instead of asking — in an empty
directory that means almost everything is a question.

The coverage is adaptive rather than a fixed questionnaire: delivery boundary,
domain terminology and relationships, current and target state, system shape,
constraints, verification evidence, and the dependency graph of the work. A
branch grows only when the project makes it relevant.

The exchange that produced this example ran roughly:

> **init:** What are we building, and who is it for?
>
> **me:** A side-scrolling platformer like early Mario, in a browser. Mostly I want to learn what makes movement feel good.
>
> **init:** Original art, or Nintendo's sprites? I recommend original — shipping their assets is a licensing problem, and drawing in code keeps the repo dependency-free.
>
> **me:** Original. I don't want Nintendo's assets anywhere near it.
>
> **init:** Framework or plain canvas? I recommend plain canvas with ES modules and no build step — a framework like Phaser would save you time but hide the physics, which is the part you said you want to learn.
>
> **me:** Plain canvas. I want to open the file and have it run.
>
> **init:** Then how do we verify anything? Canvas rendering is not testable headlessly and "feels good" is not either. I recommend keeping physics, collision, and entity state in modules that import nothing from the DOM, so they run under `node --test`; rendering and audio get verified by playing. It costs one architectural rule and it is what makes the project testable at all.
>
> **me:** Do that.

Look at what that produced: **a non-goal** (no Nintendo assets, no build step), **an architectural rule** (simulation imports nothing from the DOM), and **a verification command** (`node --test`).

Those three are what an agent needs to work unsupervised. And the third one — the important one — arrived because the interview pushed back instead of accepting "a platformer" and starting to type.

**Your job here is to disagree.** The recommendations exist to be overridden. When it suggested my audience was "casual players who enjoy short retro browser games," that sounded plausible and was wrong: this is a learning project, and saying so produces milestones about jump feel rather than about onboarding strangers. An interview where you say yes to everything produces a memory bank describing the tool's assumptions, not your project.

## Step 3: approve the breakdown

Before writing anything, it proposes the selected delivery boundary, the next
user-verifiable outcome, lane meanings, every active milestone and its complete
set of commit-sized rows, the dependency order, later candidate directions,
and the exact create/merge/preserve/omit action for every destination file.
**Nothing is on disk yet.**

For `stomper`, the smallest dependency-closed active horizon that reaches a
playable game is:

```
M01 — world, tilemap, and camera
M02 — player movement and collision
M03 — enemies and pickups
M04 — HUD and game states

M01 -> M02 -> M03 -> M04
```

`M02` needs tile queries from `M01`; `M03` reuses `M02`'s collision behavior;
and `M04` presents state produced by all three. Audio stays outside the active
horizon as an unnumbered candidate direction, with a promotion trigger such as
"the first playtest confirms the core game and sound becomes the next delivery
outcome." It gets no lane, permanent ID, status file, or launch entry yet.

Two rules it applies, worth knowing so you can tell when it has them wrong:

**A milestone is a vertical slice.** It cuts a complete path through every layer and is demoable on its own. "The player moves, jumps, and collides" is a milestone. "The database layer" is not — it is never independently done.

**A task is one commit.** Small enough to be plainly done or not, and sized to fit in one fresh context window.

**The active horizon is dependency-closed.** It includes the prerequisites and
downstream dependent milestones required for the next verifiable outcome, not a
speculative roadmap of everything the project may eventually become.

Start with one lane unless you have a real reason for more. A different
acceptance method alone does not earn a lane; split one out only when a
long-lived domain has enough active work to drown out the rest or needs its own
review cadence. Lane letters cannot be renamed once their files exist, so
`stomper` stays on `M`.

## Step 4: read what it wrote

You will not see a single bracketed placeholder — the memory bank arrives filled in. Read it anyway. It takes five minutes and it is your last cheap correction.

Four things worth checking.

*Did the non-goals survive?* They are the highest-value lines in the file and the easiest to soften into nothing:

```markdown
## Non-Goals

- **No Nintendo assets.** No Mario sprites, music, or level layouts.
- **No build step.** No bundler, no transpiler, no node_modules to serve the game.
```

*Did the domain model preserve the project's vocabulary and relationships?*
This is active product truth, not a one-time glossary:

```markdown
## Domain model

| Concept | Meaning | Relationships and invariants |
|---|---|---|
| Level | One playable tilemap with a start and exit. | Owns the tile grid and entity spawn points. |
| Game session | One run through the current level. | Owns player state, score, and remaining lives. |
| Entity | A player, enemy, or pickup in a level. | Has one position; collisions resolve against the level grid. |
```

When a milestone changes one of those terms, relationships, or invariants,
`product.md` changes in the same commit. Technical representation — arrays,
classes, serialized fields — stays in `architecture.md`.

*Is the architectural rule stated as a rule, not a suggestion?*

```markdown
## The One Rule That Matters

`physics.js`, `world.js`, and `entities.js` **import nothing from the DOM.**
No `document`, no `canvas`, no `Audio`. They take state and return state.
```

*Is the verification command real?* Run it yourself now, even with zero tests. If `tech-stack.md` names a command that does not work, every task after this closes against nothing.

Here is what a status file looks like:

```markdown
# Status M02 - The Player Moves, Jumps, And Collides

**Depends on.** M01 (needs `tileAt`).

**Acceptance.** `node --test` passes, including the tile-seam regression test.

| Item | State | Notes |
|---|---|---|
| Fixed timestep integration | `[ ]` | Physics must not vary with frame rate. |
| Axis-separated AABB resolution | `[ ]` | Horizontal, then vertical. Both at once causes seam catching. |
| Tile-seam regression test | `[ ]` | Walk a flat run of tiles at several speeds; assert no stall. |
| Variable jump height | `[ ]` | Releasing early cuts upward velocity. |
| Coyote time and jump buffer | `[ ]` | ~6 frames each. Most of what makes it feel right. |
```

Note what those rows are *not*. They are not "build the player." Each names something either done or not, and two of them exist only because the interview surfaced a specific failure mode worth testing for.

**One gotcha that will cost you an afternoon if you hand-edit these files: the backticks around every marker are load-bearing for the included API harness parser.** `` `[ ]` `` is a pending task. A bare `[ ]` is invisible to that parser — an API-harness run reports "no actionable rows remain" and exits successfully, as though the work were finished. Nothing looks broken. If a run ends instantly with nothing to do, check the backticks first.

## Step 5: run the work

**One task at a time**, the everyday mode:

```
/memory-bank:memory-bank-next    # Claude Code plugin
$memory-bank:memory-bank-next    # Codex plugin
```

It reads `AGENTS.md`, finds the next actionable row in the right lane file, and does exactly one: implement, verify, update the status row, commit. Blocked rows are skipped in favour of actionable ones. `git log` should show one commit per task, with the code change and the status flip together.

When that row closes a milestone, `milestone.md` supplies the review context as
well as the procedure. P1 and P2 are engineering review priorities, not product
concepts, milestone ordering, or status markers: P1 is a severe acceptance,
correctness, security/privacy, data-integrity, or public-contract defect; P2 is
a material but more bounded supported-behavior, reliability, compatibility,
operations, or required-evidence defect. Project-specific definitions can
override those defaults.

The milestone closes only after a bounded review-fix gate passes. The initial
full-milestone review is iteration 1. Every P1, P2, or higher-severity fix is
verified and followed by another review of the whole milestone, not just the
patch. The counter persists across sessions. A clean pass must happen within 10
iterations; if the tenth review still finds a blocking issue, the milestone
stays incomplete and the run stops for user direction.

When a separate review arrives after initialization, run
`memory-bank-reconcile` before implementing it. The skill revalidates every
finding against current code, proposes whether it belongs in open work, a new
remediation milestone, or an unnumbered later direction, and waits for approval.
It preserves completed history and does not fix anything itself; `next` or
`goal` executes the reconciled work afterward.

**Or the whole ordered set**, which is the part that answers the question this article opened with:

```
/memory-bank:memory-bank-goal M01 -> M02 -> M03 -> M04
$memory-bank:memory-bank-goal M01 -> M02 -> M03 -> M04
```

One request can cover four milestones and their task rows in dependency order.
Each completed task is implemented, verified, and committed on its own. If only
blocked work remains — including a milestone that exhausts its ten review
iterations — the run stops for the missing decision or authority instead of
pretending the whole set necessarily finished.

Because this new project carries the approved compatible bundled `GOAL.md`, init
has also written the active horizon's order, ID-to-file map, and known downstream
relationships into `memory-bank/suggested.txt`. Run the goal skill with no
arguments to reconcile that disposable suggestion and show the complete
resolved request before execution. It is not another roadmap; delete it after
launch or whenever the milestone and status files make it stale. If a project
has no compatible goal protocol, init omits both this file and the ordered-run
handoff while leaving one-row execution available.

If `memory-bank-reconcile` later changes that active horizon, it refreshes the
same disposable suggestion from the complete approved graph; it does not create
a second review-specific launch file.

That last behavior is what makes this more than an agent running a to-do list.
When `M01` closes, the tilemap that actually got built is not quite the one
`M02` was written against — plans written before the code exists always are a
little wrong. The protocol re-reads and rewrites `M02` before starting it. After
the reviewed implementation closes, it also updates every status named by
`DOWNSTREAM_IMPACTS`, plus newly discovered consumers: dependencies,
assumptions, rows, acceptance, compatibility, verification, rollout, and
rollback all reconcile to the implementation that now exists.

Both [Claude Code](https://code.claude.com/docs/en/goal) and [Codex](https://learn.chatgpt.com/use-cases/follow-goals) provide a built-in `/goal` for keeping a long-running objective active. It is the persistence layer, not the execution protocol: `GOAL.md` still defines how milestones are reconciled, implemented, reviewed, and closed. Give the built-in command the protocol, order, commit policy, and measurable completion condition together:

```
/goal Using GOAL.md, reconcile memory-bank/suggested.txt against the current memory bank, then execute the resolved loop. COMMIT_POLICY: task. Completion condition: every required status is complete, every triggered conditional status is complete, and node --test passes.
```

Use `/goal` with no arguments to see its status and `/goal clear` to stop it in either agent. Codex additionally supports `/goal pause` and `/goal resume`; if the command is not listed, run `codex features enable goals`. Built-in `/goal` does not discover `GOAL.md` automatically, so keep the file name in the objective. Invoking the namespaced `memory-bank-goal` skill shown above remains the portable non-persistent path.

---

## What you actually own at the end

A project whose memory bank came out of a conversation you had, in files you own and edit, with no dependency on the thing that generated them.

The memory bank is mutable and expected to change. `product.md`,
`architecture.md`, and `tech-stack.md` get rewritten in the same commit as the
code that makes them true. That includes updating domain terminology, concept
relationships, and business invariants in `product.md`. `evolution/` gets a new
version only when direction genuinely shifts — rarely.

Three things to know as you keep going:

**A pending status file is a planning baseline, not a contract.** It was written before the code existed. Rewriting it when reality disagrees is the intended behaviour, not drift.

**Status IDs and files are permanent; pending rows can evolve.** Add, split, rewrite, cancel, or remove pending rows as reality changes. Do not rename or reuse `M02`, and keep its file as the durable milestone record.

**Candidate directions are deliberately less permanent.** They stay unnumbered
with a reason for deferral and a promotion trigger. When a trigger becomes true,
reconcile and approve the work before giving it the next unused status ID.

---

## So: standalone, or alongside?

Both work.

Run `memory-bank-init` on its own and it does the whole interview from scratch. Or run `/grill-me` first to explore a genuinely uncertain design, then `memory-bank-init` in the same session — it reads the decisions already in the conversation instead of re-asking them, because "look up facts, ask about decisions" applies to what you have already said, not just to what is in the repository. Expect a much shorter second interview.

Keep `/grill-me` for decisions that produce no project: an architecture argument, a hiring plan, a talk outline. Reach for `memory-bank-init` when the thing you are grilling about is a codebase that has to still know what it is next week.

*The interview technique here is adapted from the `grilling` skill in [mattpocock/skills](https://github.com/mattpocock/skills), MIT.*

*Package: [github.com/tabilet/skills](https://github.com/tabilet/skills), MIT.*
