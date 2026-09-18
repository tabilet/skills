# Tutorial: From An Idea To A Running Project

You have an idea and an empty directory. No code yet.

This walkthrough goes from that to an agent implementing your project against a
memory bank it wrote from interviewing you:

1. Install the seven v1.5.0 skills, once.
2. Make an empty directory.
3. Run `memory-bank-init` and answer its questions.
4. Approve the breakdown it proposes.
5. Read what it wrote.
6. Run the work: one row at a time, or a whole ordered set.

Twenty minutes, and most of it is step 3 — which is a conversation, not typing.

The example is a Mario-style platformer called `stomper`, because a game
decomposes into feature areas cleanly enough to show why lanes exist. The initial
setup examples come from generated files; the later retirement walkthrough is
illustrative.

## What You Need

- **`git`**, and an agent — Claude Code, Codex, or DSH Web.
- **An idea you can talk about for ten minutes.** That is the actual
  prerequisite. Everything else is mechanical.

The example project uses Node and Python 3; yours needs whatever it needs.

## Step 1 — Install The Skills

The examples below describe the published seven-skill v1.5.0 release.

In Claude Code:

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

In Codex, which has its own plugin system and reads the same manifest:

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

Codex wants the `@marketplace` qualifier when the plugin name is not unique
across your marketplaces, so `memory-bank@tabilet` is the form to learn.

**Plugin invocation is namespaced.** Following current [Claude Code skill
namespacing](https://code.claude.com/docs/en/slash-commands) and [Codex skill
invocation](https://developers.openai.com/plugins/build/skills), Claude Code uses
`/memory-bank:memory-bank-archive`, `/memory-bank:memory-bank-init`,
`/memory-bank:memory-bank-upgrade`, `/memory-bank:memory-bank-propose`,
`/memory-bank:memory-bank-reconcile`,
`/memory-bank:memory-bank-next`, and
`/memory-bank:memory-bank-goal`. Codex uses
`$memory-bank:memory-bank-archive`, `$memory-bank:memory-bank-init`,
`$memory-bank:memory-bank-upgrade`, `$memory-bank:memory-bank-propose`,
`$memory-bank:memory-bank-reconcile`,
`$memory-bank:memory-bank-next`, and
`$memory-bank:memory-bank-goal`. Plain English also works in both.

Either agent can also take them as plain files you own instead of a managed
plugin — no clone, no temp directory, nothing to clean up:

```bash
mkdir -p ~/.agents/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.agents/skills 'skills-main/skills'

# Claude Code alternative
mkdir -p ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.claude/skills 'skills-main/skills'
```

Plain-file installs are unnamespaced: `/memory-bank-init` in Claude Code and
`$memory-bank-init` in Codex, with the same pattern for the other six skills in
v1.5.0.

For DSH, follow the [DSH route](#dsh-route) below.

The v1.5.0 release has seven commands:

| Skill | When |
|---|---|
| `memory-bank-archive` | Before init when a large existing package needs a frozen, commit-anchored context map. New projects skip it. |
| `memory-bank-init` | Once per project, on the way in. |
| `memory-bank-upgrade` | After a skill update, to review and adopt new rules in an existing project. |
| `memory-bank-propose` | When an initialized project needs a feature or candidate promotion. It proposes planning changes for approval. |
| `memory-bank-reconcile` | Whenever a new review arrives after initialization. Validate it and update the plan without implementing it. |
| `memory-bank-next` | Execute or resume one row, then verify and commit under the governing policy. |
| `memory-bank-goal` | Several milestones in a defined order. |

For existing packages, incoming reviews, and combined workflows, see
[Skill Use Cases](USE_CASES.md). It also contrasts
[automatic retirement](USE_CASES.md#6-automatic-retirement-during-normal-work)
with [explicit archive snapshots](USE_CASES.md#7-explicitly-snapshot-a-materially-changed-system).

*(Prefer to do it by hand? Every step below has a manual equivalent in the
[README](../README.md#set-up-a-new-project). The commands are a convenience,
not a requirement.)*

## Updating Or Removing The Plugin

Updating is a two-part operation: refresh the marketplace, then update the
installed plugin. Removing the plugin does not remove the memory-bank files it
created in your projects; those files belong to you.

Updating the plugin does not merge new rules into those project-owned files
either. Existing projects explicitly adopt the retirement instructions and, if
used, a compatible API runner before the workflow described in
[What You Own At The End](#what-you-own-at-the-end) applies. Cleanup of older
closed milestones is a separate request, not an installation side effect.
Follow [Upgrade an existing project](../README.md#upgrade-an-existing-project)
for that review. Invoke `/memory-bank:memory-bank-upgrade` in Claude Code,
`$memory-bank:memory-bank-upgrade` in Codex, or `/memory-bank-upgrade` in DSH Web.
Inspect its focused section diffs and approve the complete merge proposal.
Preserved content is summarized; unchanged manuals need not be repeated. Task tables,
IDs, custom instructions, review counters, and frozen history stay intact;
retiring old milestones requires a separate request. If the project is already
compatible, the skill reports a no-op. A headless write phase needs the exact
previously approved proposal; installing the skill never supplies that approval.

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

## DSH route

For the v1.5.0 sidebar route, install the
[DSH companion](DSH.md#install-the-dsh-companion) in the Web profile, then choose
**Memory Bank** in the selected project's native right sidebar. Inspect tasks,
current memory, acceptance evidence, and demand-loaded history there. The workflow
shortcuts open a request preview; insert it into an unchanged empty draft or copy
it, then send normally. They preserve each skill's approval gates. Updating the
plugin does not migrate the project; use Upgrade for an explicit proposal.

Use the same `stomper` example with DSH 0.1.5-rc.1 on Linux and Node 24. The
[DSH guide](DSH.md#acceptance-evidence) distinguishes tested runtime integration
from live workflow acceptance. Install the seven complete bundles from the
v1.5.0 release checkout into `$DSH_HOME/skills` (default
`~/.dsh/skills`), following its [installation](DSH.md#install-the-six-bundles)
and [backup/update/removal](DSH.md#update-or-remove) procedures. A shared agents
root is an alternative; inspect duplicate-name precedence. Existing Claude Code
and Codex commands above keep their existing forms.
Pin the v1.5.0 release tag for reproducible installation.

After creating `stomper` in Step 2, run `dsh web` from that directory and confirm
Web's selected workspace. In a fresh session check that all seven skills are
discoverable, then use `/memory-bank-init` for Step 3. Answer the same design-tree
questions and approve the complete milestone and file-action proposal in Step 4.
Read the generated files in Step 5. Preserve existing project instructions when
using this route in a small existing package. A broad package first needs an
explicitly requested, approved `/memory-bank-archive` preflight.

For Step 6 use `/memory-bank-next`, or an ordinary request to use that skill.
Keep one ledger owner. Later, run `/memory-bank-reconcile review.md` in Web to
validate and approve a new review before separately requesting implementation;
remote review URLs still need separate exact-URL confirmation before each fetch.
Installing new bundles never adopts new project instructions or retires old
milestones by itself.

After approving the project plan in Web, stop that session's execution before a
headless run. From the same `stomper` directory, for example:

```bash
dsh --profile headless 'Use memory-bank-next. The existing stomper plan is approved for one dependency-ready task. Resume the sole in-progress row first. Verify using AGENTS.md and node --test, then commit that task. No external mutations. Stop and report any missing answer, approval, permission, or verification capability.'
```

Substitute the actual verification commands if the interview chose a different
stack. Headless starts a fresh session; supply the actual authorized request,
not a reference to approvals available only in a different conversation. Use
Web for any unresolved interview or proposal. A question or incomplete milestone
can remain after exit 0. Inspect files, test output, review evidence, and commits.

For several milestones, use `/memory-bank-goal` with the approved explicit order
and commit policy. DSH's [native goal continuation](DSH.md#goals-and-execution-ownership)
is optional; its runtime round limit is independent of the persisted milestone
review count. Neither native todos nor goal completion replaces acceptance.

## Step 2 — An Empty Directory

```bash
mkdir stomper && cd stomper
git init
claude   # or: codex
```

Do not scaffold anything. The project's shape comes out of the conversation, not
out of a template you picked before thinking.

This is a new project, so there is nothing to archive. On a large existing
package, `memory-bank-init` may instead require `memory-bank-archive` first; the
archive skill maps every stable context at a clean commit and seeds current
`product.md` and `architecture.md` before init builds executable milestones.

## Step 3 — Run `memory-bank-init`

```text
/memory-bank:memory-bank-init   # Claude Code plugin
$memory-bank:memory-bank-init   # Codex plugin
```

**This step decides everything downstream**, and it is a conversation rather
than a form. The memory bank you end up with is a transcript of the decisions
you reach here; decisions you never reach come out as vague prose, and vague
prose is what makes an agent build the wrong thing confidently.

The command maps one delivery boundary as a dependency-ordered design tree. It
asks the whole **frontier** — every independent decision whose prerequisites are
settled — as a numbered round, with a recommended answer attached to each. Your
answers reshape the tree before the next round. Ask for one-at-a-time pacing if
you prefer it.

Anything it can read from the repository it reads instead of asking. In a small
existing project that includes instructions, docs, manifests, tests, CI, source
layout, interfaces, schemas, and infrastructure. A large existing boundary that
cannot be evidenced reliably in one pass is routed through the archive preflight
described above. Only decisions come back to you.

What it works through, and where each answer lands:

| Coverage root | Why it matters | Lands in |
|---|---|---|
| Delivery boundary, users, workflows, non-goals | Scope and ownership. | `product.md`, `AGENTS.md` |
| Domain terminology, relationships, invariants | Keeps the product and business model consistent. | `product.md` |
| Current and target state | Separates facts from intended change. | `product.md`, `evolution/` |
| System shape and public contracts | Prevents boundary and compatibility drift. | `architecture.md` |
| Stack, runtime, operations, hard rules | Rules the agent must not break. | `tech-stack.md`, `AGENTS.md` |
| Runnable and manual evidence | Everything downstream closes against this. | `tech-stack.md`, milestone acceptance |
| Work graph and delivery horizon | Becomes active lanes, milestones, and later directions. | `milestone.md` |

Those are roots, not six canned questions. Relevant answers grow branches for
data migrations, security and privacy, distributed failure, accessibility,
model evals, deployment and rollback, or external-system authority. A broad
repository is not permission to mix independent products into one bank: select
one product, ownership, and verification boundary and treat the rest as
dependencies or separate initializations.

### Already ran `/grill-me`?

Plenty of people install `/grill-me`, run it, and find they want more than a
sharpened design. They want the whole engineering harness on the other side of
it: several milestones, each carrying its own tasks, and a way to work through
them without a hundred repeated prompts. That is the gap this tutorial closes,
and step 6 is where it lands — a blocker-aware ordered run:

```text
/memory-bank:memory-bank-goal M01 -> M02 -> M03 -> M04. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.
```

It works in dependency order, rewriting later milestones as earlier ones change
what is true. Each completed task is verified and committed on its own. If only
blocked work remains, it stops for the missing decision or authority instead of
claiming the entire set necessarily finished.

If you came here from
[mattpocock/skills](https://github.com/mattpocock/skills) and have just finished
a grilling session, **do not start over.** Run `memory-bank-init` in the same
session and it will read the decisions already in the conversation instead of
re-asking them — "look up facts, ask about decisions" applies to what you have
already said, not just to the repository.

Expect a much shorter step 3: it will confirm what it picked up, ask about
whatever the grill did not reach — usually the verification command and the
order of work — and move on to the breakdown in step 4. That is the whole
difference between the two skills. `/grill-me` deliberately stops at shared
understanding; this turns that understanding into files that outlive the
session.

An abridged exchange that produced this example ran roughly:

> **`memory-bank-init`, round 1:** ❓ **Q1 — Delivery boundary:** What are we
> building, who uses it, and what outcome matters? I recommend treating the
> browser game itself as the boundary, with learning movement feel as the
> primary outcome.
>
> **You:** A side-scrolling platformer like early Mario, in a browser. Mostly I
> want to learn what makes movement feel good.
>
> **`memory-bank-init`, round 2:** ❓ **Q1 — Assets:** Original art, or
> Nintendo's sprites? I recommend original because shipping their assets is a
> licensing problem.
>
> ❓ **Q2 — Runtime:** Framework or plain canvas? I recommend plain canvas with
> ES modules and no build step: a framework would hide the physics you want to
> learn.
>
> **You:** 1 original; I don't want Nintendo assets anywhere near it. 2 plain
> canvas; I want to open the file and have it run.
>
> **`memory-bank-init`, round 3:** ❓ **Q1 — Verification:** Canvas rendering
> and “feels good” are not headless assertions. I recommend keeping simulation
> modules DOM-free so physics and collision run under `node --test`, with
> rendering verified by playtest.
>
> ❓ **Q2 — Delivery horizon:** I recommend ending the active horizon when the
> world, player, enemies, and HUD form a playable loop. Keep audio as an
> unnumbered candidate until you decide it matters.
>
> **You:** 1 do that. 2 right; I might skip audio entirely.

Notice what that produced: **a non-goal** (no Nintendo assets, no build step),
**an architectural rule** (simulation imports nothing from the DOM), and **a
verification command** (`node --test`). Those three are what an agent needs to
work unsupervised, and the third one arrived because the command pushed back
instead of accepting "a platformer" and starting to type.

**Your job in this step is to answer, disagree, and say "no, actually."** The
recommendations are there to be overridden. An interview where you said yes to
everything produced a memory bank describing the command's assumptions, not your
project.

## Step 4 — Approve The Breakdown

Before writing anything, `memory-bank-init` proposes the shape as a numbered
list: the delivery boundary, lane letters, every active milestone with its
acceptance and complete row set, the execution order, unnumbered candidate
directions, and every create/merge/preserve file action. **Nothing is on disk
yet.**

For `stomper` it proposed one active lane. Four feature areas are not, by
themselves, a reason to create four permanent namespaces:

```markdown
| Lane | Domain |
|---|---|
| `M` | Game delivery: world, player, entities, and UI. |
```

and this order, because these are not independent:

```markdown
M01 -> M02 -> M03 -> M04
```

`M02` needs tile queries from `M01`; `M03` reuses `M02`'s collision resolver.
That dependency-closed sequence reaches the next verifiable outcome: a complete
playable loop.

Audio stays outside that horizon:

| Candidate direction | Why deferred | Promotion trigger |
|---|---|---|
| WebAudio cues | The game is complete and testable without them. | The user decides sound is required for the next delivery outcome. |

It has no lane or status ID yet. Promotion triggers reconsideration and
approval; it does not allocate a permanent ID automatically.

It will ask you five things. Answer them honestly, because this is the cheap
moment to be wrong:

- **Is the delivery boundary right?** One coherent product and owner?
- **Is the granularity right?** Too coarse, too fine?
- **Are the dependencies correct?** Does each milestone depend only on what
  genuinely gates it?
- **Does the active horizon end at the right verifiable outcome?**
- **Are later candidates and every file action safe?**

Two rules it applies, worth knowing so you can tell when it has them wrong:

- **A milestone is a vertical slice** — a complete path through every layer,
  demoable on its own. "The player moves, jumps, and collides" is a milestone.
  "The database layer" is not; it is never independently done.
- **A row is one commit** — small enough to be plainly done or not, and sized to
  fit in one fresh context window.

**Start with one lane (`M`) unless you have a real reason.** Lane letters can
never be renamed once their file exists. This project stays on `M`; a later
domain earns another letter only when its volume or review cycle justifies it.

## Step 5 — Read What It Wrote

Only after you approve does it write:

```text
stomper/
├── AGENTS.md              ← commands, boundaries, hard rules
├── GOAL.md                ← copied, not written — a portable protocol
├── memory-bank/
│   ├── product.md         ← scope, domain model, and non-goals
│   ├── architecture.md    ← module layout, the DOM-free rule
│   ├── tech-stack.md      ← stack, and how it is verified
│   ├── lessons.md         ← reusable learning and evidence, initially empty
│   ├── milestone.md       ← active milestones and unnumbered candidates
│   ├── status-M01.md       ← world and camera
│   ├── status-M02.md       ← player movement and collision
│   ├── status-M03.md       ← enemies and pickups
│   ├── status-M04.md       ← HUD and game states
│   └── suggested.txt      ← disposable active-horizon order and impacts
└── evolution/
    ├── prompt-v1.md
    └── result-v1.md
```

**These files are yours.** They have no update subscription to the plugin.
Agents maintain them during authorized work, and uninstalling the commands
leaves them exactly as they are. `docs/history/` is created only when a milestone
or knowledge first needs retirement, not as an empty initialization artifact.

You will not see a bracketed placeholder — the memory bank arrives filled in.
Read it anyway; it takes five minutes and it is your last cheap correction.
Three things worth checking:

*Did the non-goals survive?* They are the highest-value lines and the easiest to
soften into nothing:

```markdown
## Non-Goals

- **No Nintendo assets.** No Mario sprites, music, or level layouts. Original
  art and levels only.
- **No build step.** No bundler, no transpiler, no `node_modules` to serve the
  game. Modules load natively in the browser.
```

*Is the architectural rule stated as a rule, not a suggestion?*

```markdown
## The One Rule That Matters

`physics.js`, `world.js`, and `entities.js` **import nothing from the DOM.** No
`document`, no `canvas`, no `Audio`. They take state and return state.
```

*Is the verification command real?* Run it yourself now, even with zero tests.
If `tech-stack.md` names a command that does not work, every task after this
closes against nothing.

A status file is a table of rows, each sized to be one commit:

```markdown
# Status M02 - The Player Moves, Jumps, And Collides

**Depends on.** M01 (needs `tileAt`).

**Acceptance.** `node --test` passes, including the tile-seam regression test.

| Item | State | Notes |
|---|---|---|
| Fixed timestep integration | `[ ]` | Accumulator loop. Physics must not vary with frame rate. |
| Axis-separated AABB resolution | `[ ]` | Horizontal, then vertical. Resolving both at once causes seam catching. |
| Tile-seam regression test | `[ ]` | Walk across a flat run of tiles at several speeds; assert no horizontal stall. |
| Variable jump height | `[ ]` | Releasing the key early cuts upward velocity. |
| Coyote time and jump buffer | `[ ]` | ~6 frames each. The two together are most of what makes it feel right. |
```

Note what those rows are not: they are not "build the player." Each names
something either done or not, and two exist only because the interview surfaced
a specific failure mode worth testing for.

**The backticks around `` `[ ]` `` are load-bearing for the included API
harness parser.** A bare `[ ]` is rejected by the current runner — see [When It Goes
Wrong](#when-it-goes-wrong). Other agents may still understand the prose, but
the shipped automation deliberately requires this exact table syntax. Markers
are `` `[ ]` `` pending, `` `[+]` `` done, `` `[~]` `` in progress,
`` `[!]` `` blocked, `` `[X]` `` cancelled, and `` `[-]` `` closed historical
evidence. The new marker is additive: all five earlier meanings stay unchanged.
A `[-]` row records a consumed failed attempt or superseded row, names its
accepted successor, is never retried, and does not block that successor. Across
the active ledger, zero or one general row may be `[~]`. An operational launcher
requires its exact authorized operation row to be `[~]` before invocation; the
marker does not grant external-mutation authority.

If something is wrong, tell the agent rather than hand-editing. Faster, and it
keeps the memory bank consistent with what the agent believes.

## Checkpoint — Before You Start A Long Run

Everything so far is prose an agent interprets loosely. Before handing it a run
that works unattended, get a hard yes or no.

The optional [API harness](../README.md#install-the-api-harness) runs local
checks before it calls any API — is there an `AGENTS.md`, is this a git
worktree, are there lane files, are there actionable rows, is the worktree
clean. Point it at a dead endpoint to reach those checks and stop:

```bash
git add -A && git commit -m "Add memory bank"

ALLOW_UNSANDBOXED_SHELL=1 LLM_MODEL=check LLM_API_KEY=x \
  LLM_API_BASE=http://127.0.0.1:1/v1 LLM_MAX_RETRIES=0 MAX_RUNS=1 \
  python3 /path/to/skills/harness/tackle-memory-bank-api-loop .
echo $?
```

**Exit `21`** — "the API could not be reached" — is what you want. Every check
on your side passed; the only failure was the network call you sabotaged on
purpose. No API key, no cost, no model involved.

The acknowledgment is required because a real run gives model commands an
unsandboxed host shell. It does not make that shell safe; use a disposable
sandbox and a repository you can restore.

The same harness shows what it found:

```text
| Status file | Actionable rows | In progress | Blocked | Historical |
|---|---|---|---|---|
| memory-bank/status-M01.md | 5 | 0 | 0 | 0 |
| memory-bank/status-M02.md | 7 | 0 | 0 | 0 |
| memory-bank/status-M03.md | 6 | 0 | 0 | 0 |
| memory-bank/status-M04.md | 5 | 0 | 0 | 0 |
```

Twenty-three rows of work, parsed out of files written from a ten-minute
conversation. If a lane you expected shows `0`, its markers are wrong.

## Step 6 — Run The Work

**One row at a time**, which is the everyday mode:

```text
/memory-bank:memory-bank-next   # Claude Code plugin
$memory-bank:memory-bank-next   # Codex plugin
```

It reads `AGENTS.md`, finds the next actionable row in the right lane file, and
does **exactly one**: implement, verify, update the status row, commit. Blocked
rows are skipped in favour of actionable ones. If the row closes a milestone it
runs the milestone review first.

Plain English works identically — *"tackle next pending item in memory bank"* —
the command just carries the full instruction instead of your paraphrase of it.

**A whole ordered set**, for a release or a migration with real dependencies:

```text
/memory-bank:memory-bank-goal M01 -> M02 -> M03 -> M04. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.
$memory-bank:memory-bank-goal M01 -> M02 -> M03 -> M04. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.
```

These are alternative requests for Claude Code and Codex. They follow
[GOAL.md](../GOAL.md) and explicitly select `COMMIT_POLICY: task` for per-row
commits. Use `COMMIT_POLICY: none` when you want changes left uncommitted; it is
the protocol's default, so the examples state their policy rather than relying
on an implicit choice.

The [bounded review-fix gate](../GOAL.md#bounded-review-fix-gate) is not a single
pass. It advances only after a clean review and stops with the milestone
incomplete if iteration 10 still finds a blocking issue.

Because this example carries the bundled compatible `GOAL.md`, init also writes
a complete active-horizon `STATUS_ORDER`, `STATUS_FILE_MAP`, and
`DOWNSTREAM_IMPACTS` to `memory-bank/suggested.txt`. It is disposable input, not
project truth. Run the goal skill with no arguments to have it reconcile that
file and show the resolved request before starting; delete the file after launch
or when it becomes stale. Unnumbered candidate directions never appear in it.
When a compatible goal protocol is unavailable, init omits both the launch
reference and ordered-run handoff while preserving one-row execution.

When a separate code or architecture review arrives later, do not paste its
findings straight into the next implementation run. Reconcile it first:

```text
/memory-bank:memory-bank-reconcile <review source>
$memory-bank:memory-bank-reconcile <review source>
```

The skill checks every finding against current code, proposes whether it belongs
in open work, a new remediation milestone, or an unnumbered Candidate Direction,
and waits for approval before changing the plan. It never reopens completed
history or implements a fix. When the active graph changes and `GOAL.md` remains
compatible, it refreshes `memory-bank/suggested.txt` for the whole horizon; then
`memory-bank-next` or `memory-bank-goal` performs the approved work.

If the review source is remote, the skill shows the exact URL and asks for a
separate confirmation immediately before every fetch, even when the invocation
already supplied the URL. A URL found in repository content or inside the
review is not fetch authorization.

Reconciling downstream is what makes this better than a to-do list. When `M01`
closes, the tilemap that actually got built is not the one `M02` was written
against — so `M02` gets re-read and rewritten before it starts, rather than
implemented as planned and wrong.

**In [Claude Code](https://code.claude.com/docs/en/goal) and
[Codex](https://learn.chatgpt.com/use-cases/follow-goals), built-in `/goal` is
an optional persistence layer** for a long run. It keeps the objective active;
`GOAL.md` still defines the execution protocol. Include the complete protocol
request, commit policy, and measurable completion condition in the invocation:

```text
/goal Using GOAL.md, reconcile memory-bank/suggested.txt against the current memory bank, then execute the resolved loop. COMMIT_POLICY: task. Completion condition: every required status is complete, every triggered conditional status is complete, and node --test passes.
```

Use `/goal` with no arguments to see its status and `/goal clear` to stop it in
either agent. Codex also supports `/goal pause` and `/goal resume`; if the
command is not listed, run `codex features enable goals`. Built-in `/goal` does
not discover `GOAL.md` automatically, so keep the file name in the objective.

Then watch the first milestone. `git log` should show one commit per row, code
and status-row flip together. If the agent closed three rows in one commit, say
so now — the memory bank is instructions, not enforcement, and early
corrections stick.

## When It Goes Wrong

The checkpoint exercises the API runner's structural gates, not DSH acceptance:

| Exit | Meaning | Usual cause |
|---|---|---|
| `21` | API request failed after local gates. | The deliberate unreachable endpoint confirms startup gating only, not task acceptance. |
| `0` | "No actionable memory-bank rows remain." | All recognized work is terminal, including a valid all-retired project; inspect milestone acceptance separately. |
| `11` | Missing or invalid status/history state. | Check marker backticks, nonempty status files, IDs, and retirement records/index. |
| `4` | Worktree was dirty before the run. | Commit or stash first. |
| `3` | Only `` `[!]` `` blocked rows remain. | Not a failure. A human needs to unblock something. |
| `15` | More than one `` `[~]` `` row is in progress. | Reconcile the active ledger to one current row before relaunching. |
| `10` | No `AGENTS.md`. | Wrong directory, or `memory-bank-init` never finished. |

At this new-project checkpoint, pending work is expected. If an older runner
exits instantly, check the backticks: older versions could silently ignore bare
markers. Updating installed skills does not upgrade a separately installed API
runner. Current validation stops on malformed task markers and empty files.

`memory-bank-init` checks all three of these before it reports done, so they
mostly bite when you hand-edit afterwards. Full table in
[EXECUTION.md](EXECUTION.md#exit-codes).

## What You Own At The End

A project whose memory bank came out of a conversation you had, in files you can
edit, with no dependency on the plugin that generated them.

The memory bank is mutable and expected to change: `product.md`,
`architecture.md`, and `tech-stack.md` get rewritten in the same commit as the
code that makes them true. That includes updating `product.md` when domain
terminology, concept relationships, or business invariants change. `evolution/`
gets a new version only when direction genuinely shifts — rarely.

`memory-bank-init` establishes the retirement convention. During execution,
`memory-bank-next` and `memory-bank-goal` carry it out through the project's
milestone-closing procedure, after review, verification, knowledge
consolidation, and downstream reconciliation pass. This is automatic within
the agent workflow, not a background cleanup job. No separate
`memory-bank-archive` invocation is needed: that skill creates optional frozen
context baselines, not retired task records. `memory-bank-reconcile` plans new
review work; it does not perform retirement.

Completed rows stay in the active status file until their whole milestone
qualifies. Open work, blockers, or missing closure evidence prevent retirement.
Existing projects adopt these conventions explicitly; updating a skill does
not migrate their files, and cleanup of older closed work needs a separate
request. All retirement writes follow the governing commit policy.

### Example: a milestone closes and a lesson survives

Suppose `stomper` has active milestones `M01` through `M04`. `M01` implements the
world and camera; `M02` consumes its tile queries. Finishing one `M01` task does
not move that task anywhere. It remains in `memory-bank/status-M01.md`, with its
verified completion marker and notes, while other `M01` work is still open.

When all `M01` work is terminal, its acceptance is verified, its review gate
passes, and its downstream impacts are reconciled, the closing agent:

1. Keeps the delivered tile-query contract in `architecture.md` and applicable
   camera-test learning in `lessons.md`, with links to the supporting evidence.
2. Preserves the full `M01` specification and final status document, including
   task notes and closure evidence, in `docs/history/status-M01.md`.
3. Adds `M01` to `docs/history/index.md`, removes its active status file,
   specification, and index row, and leaves one history-index link in
   `milestone.md`. It repairs maintained links, including the evidence behind
   the lesson and `M02`'s dependency on `M01`.

Now the active plan contains `M02`–`M04` and any unnumbered candidate directions.
Product, architecture, and stack facts remain current. The lesson survives
because it still informs camera changes; lessons are not discarded merely
because their source milestone closed. An existing disposable launch reference
also drops `M01`, or is removed if no active work remains.

For example, a lesson might say: “For the fixed-size viewport, exercise camera
bounds with both narrower and wider maps.” Suppose a later milestone introduces
resizing and replaces that guidance with a resize-aware test matrix. Before
replacing it, the agent appends the old wording, its source heading and evidence,
the reason it is obsolete, and its replacement reference to
`docs/history/knowledge.md`. The history index links that journal. The revised
lesson stays in `lessons.md`; unrelated useful lessons stay there too. This
preservation happens whenever knowledge is materially superseded, even outside
milestone closure. A typo correction needs no journal entry.

To answer “why did we choose those camera fixtures?”, search current lessons,
then the journal by topic or the history index for `M01`, and open its retired
record. The full Markdown evidence is readable without Git; Git supplies
intermediate revisions. Do not retry historical rows, reuse `M01`, or rewrite
its frozen record. Cancelled or superseded milestones would need their recorded
disposition checked, not be assumed to satisfy a completed dependency.

This keeps accumulated history out of routine startup reads. It is not a hard
size cap: active work and genuinely applicable learning can still grow. See the
[full lifecycle](../README.md#keep-long-term-memory-without-growing-the-active-plan).

### Keeping the active plan useful

Two things to know as you keep going:

- **A pending status file is a planning baseline, not a contract.** It was
  written before the code existed. Rewriting it when reality disagrees is the
  intended behavior, not drift.
- **Status IDs and their records are permanent once created.** Pending rows are a
  planning baseline: add, split, rewrite, cancel, or remove them as reality
  changes, but do not rename or reuse `M02`, and keep its status file as the
  durable milestone record, moving it into history only after documented closure.
