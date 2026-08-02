# Tutorial: From An Idea To A Running Project

You have an idea and an empty directory. No code yet.

This walkthrough goes from that to an agent implementing your project against a
memory bank it wrote from interviewing you:

1. Install the three commands, once.
2. Make an empty directory.
3. Run `/memory-bank-init` and answer its questions.
4. Approve the breakdown it proposes.
5. Read what it wrote.
6. Run the work: one row at a time, or a whole ordered set.

Twenty minutes, and most of it is step 3 — which is a conversation, not typing.

The example is a Mario-style platformer called `stomper`, because a game
decomposes into feature areas cleanly enough to show why lanes exist. Every file
shown below was really generated.

## What You Need

- **`git`**, and an agent — Claude Code or Codex.
- **An idea you can talk about for ten minutes.** That is the actual
  prerequisite. Everything else is mechanical.

The example project uses Node and Python 3; yours needs whatever it needs.

## Step 1 — Install The Three Commands

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

**Invocation differs between the two.** Claude Code registers these as slash
commands, so `/memory-bank-init` autocompletes. Codex registers them as skills
reached by name — ask for them without a slash: *"use the memory-bank-init
skill"*. Every `/command` written below is the Claude Code form; drop the slash
in Codex.

Either agent can also take them as plain files you own instead of a managed
plugin — no clone, no temp directory, nothing to clean up:

```bash
mkdir -p ~/.codex/skills            # or ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.codex/skills 'skills-main/skills'
```

You now have three commands, and they are the whole interface:

| Command | When |
|---|---|
| `/memory-bank-init` | Once per project, on the way in. |
| `/memory-bank-next` | Every day. One row, verified, committed. |
| `/memory-bank-goal` | Several milestones in a defined order. |

*(Prefer to do it by hand? Every step below has a manual equivalent in the
[README](../README.md#set-up-a-new-project). The commands are a convenience,
not a requirement.)*

## Step 2 — An Empty Directory

```bash
mkdir stomper && cd stomper
git init
claude
```

Do not scaffold anything. The project's shape comes out of the conversation, not
out of a template you picked before thinking.

## Step 3 — Run `/memory-bank-init`

```text
/memory-bank-init
```

**This step decides everything downstream**, and it is a conversation rather
than a form. The memory bank you end up with is a transcript of the decisions
you reach here; decisions you never reach come out as vague prose, and vague
prose is what makes an agent build the wrong thing confidently.

The command works down a dependency-ordered tree, **one question at a time, each
with a recommended answer attached** so agreeing costs one word. Anything it can
read from the repository it reads instead of asking — so in an empty directory
almost everything is a question, and in an existing repo it will already know
your stack and test command and ask you only about decisions.

What it works through, and where each answer lands:

| It asks | Why it matters | Lands in |
|---|---|---|
| What is this, who uses it? | Scope. | `product.md` |
| **What is it *not*?** | The most valuable thing you will say. | `product.md` |
| Stack and constraints | Rules the agent must not break. | `tech-stack.md` |
| **How do you know it works?** | Everything downstream closes against this. | `tech-stack.md`, `AGENTS.md` |
| Boundaries | What this owns, what it delegates. | `AGENTS.md` |
| Feature areas, and their order | Becomes lanes and milestones. | `milestone.md` |

### Already ran `/grill-me`?

Plenty of people install `/grill-me`, run it, and find they want more than a
sharpened design. They want the whole engineering harness on the other side of
it: several milestones, each carrying its own tasks, and a way to drive the
project to completion with a single batch command rather than a hundred
prompts. That is the gap this tutorial closes, and step 6 is where it lands —
one line that runs the entire project:

```text
/memory-bank-goal W01 -> P01 -> E01 -> U01 -> A01?
```

Five milestones, twenty-six tasks, each one implemented, verified, and
committed on its own, in dependency order, with the later milestones rewritten
as the earlier ones change what is true.

If you came here from
[mattpocock/skills](https://github.com/mattpocock/skills) and have just finished
a grilling session, **do not start over.** Run `/memory-bank-init` in the same
session and it will read the decisions already in the conversation instead of
re-asking them — "look up facts, ask about decisions" applies to what you have
already said, not just to the repository.

Expect a much shorter step 3: it will confirm what it picked up, ask about
whatever the grill did not reach — usually the verification command and the
order of work — and move on to the breakdown in step 4. That is the whole
difference between the two skills. `/grill-me` deliberately stops at shared
understanding; this turns that understanding into files that outlive the
session.

The exchange that produced this example ran roughly:

> **`/memory-bank-init`:** What are we building, and who is it for?
>
> **You:** A side-scrolling platformer like early Mario, in a browser. Mostly I
> want to learn what makes movement feel good.
>
> **`/memory-bank-init`:** Original art, or Nintendo's sprites? I recommend
> original — shipping their assets is a licensing problem, and drawing in code
> keeps the repo dependency-free.
>
> **You:** Original. I don't want Nintendo's assets anywhere near it.
>
> **`/memory-bank-init`:** Framework or plain canvas? I recommend plain canvas
> with ES modules and no build step — a framework like Phaser would save you
> time but hide the physics, which is the part you said you want to learn.
>
> **You:** Plain canvas. I want to open the file and have it run.
>
> **`/memory-bank-init`:** Then how do we verify anything? Canvas rendering is
> not testable headlessly and "feels good" is not either. I recommend keeping
> physics, collision, and entity state in modules that import nothing from the
> DOM, so they run under `node --test`; rendering and audio get verified by
> playing. It costs one architectural rule and it is what makes the project
> testable at all.
>
> **You:** Do that.
>
> **`/memory-bank-init`:** Feature areas? From what you have described I would
> suggest world and camera, player and collision, enemies, HUD, and audio — with
> audio last and conditional, since the game is playable without it.
>
> **You:** Right, and I might skip audio entirely.

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

Before writing anything, `/memory-bank-init` proposes the shape as a numbered
list: lane letters, milestones with acceptance criteria, the first milestone's
rows, and the execution order. **Nothing is on disk yet.**

For `stomper` it proposed five lanes, because the feature areas genuinely have
different acceptance criteria — collision correctness is unit-testable, audio is
a playtest:

```markdown
| Lane | Domain |
|---|---|
| `W` | World: tilemap, level data, camera. |
| `P` | Player: input, movement, collision resolution. |
| `E` | Entities: enemies, pickups, and their interactions with the player. |
| `U` | UI: HUD, score, lives, title and game-over states. |
| `A` | Audio: WebAudio cues. |
| `M` | Default lane, for work that classifies as none of the above. |
```

and this order, because these are not independent:

```markdown
W01 -> P01 -> E01 -> U01 -> A01?
```

`P01` needs tile queries from `W01`; `E01` reuses `P01`'s collision resolver.
The trailing `?` marks `A01` **conditional** — skipped rather than cancelled
when its trigger is absent.

It will ask you three things. Answer them honestly, because this is the cheap
moment to be wrong:

- **Is the granularity right?** Too coarse, too fine?
- **Are the dependencies correct?** Does each milestone depend only on what
  genuinely gates it?
- **Should anything be merged or split?**

Two rules it applies, worth knowing so you can tell when it has them wrong:

- **A milestone is a vertical slice** — a complete path through every layer,
  demoable on its own. "The player moves, jumps, and collides" is a milestone.
  "The database layer" is not; it is never independently done.
- **A row is one commit** — small enough to be plainly done or not, and sized to
  fit in one fresh context window.

**Start with one lane (`M`) unless you have a real reason.** Lane letters can
never be renamed once their file exists. This project earned five; most do not.

## Step 5 — Read What It Wrote

Only after you approve does it write:

```text
stomper/
├── AGENTS.md              ← commands, boundaries, hard rules
├── GOAL.md                ← copied, not written — a portable protocol
├── memory-bank/
│   ├── product.md         ← what it is, and the non-goals
│   ├── architecture.md    ← module layout, the DOM-free rule
│   ├── tech-stack.md      ← stack, and how it is verified
│   ├── milestone.md       ← lanes, milestones, execution order
│   └── status-{W,P,E,U,A}01.md
└── evolution/
    ├── prompt-v1.md
    └── result-v1.md
```

**These files are yours.** Nothing links back to the plugin, nothing updates
them, and uninstalling the commands leaves them exactly as they are.

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
# Status P01 - The Player Moves, Jumps, And Collides

**Depends on.** W01 (needs `tileAt`).

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

**The backticks around `` `[ ]` `` are load-bearing.** A bare `[ ]` is invisible
to every tool that reads the file — see [When It Goes
Wrong](#when-it-goes-wrong). Markers are `` `[ ]` `` pending, `` `[+]` `` done,
`` `[~]` `` in progress, `` `[!]` `` blocked, `` `[X]` `` cancelled.

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

LLM_MODEL=check LLM_API_KEY=x LLM_API_BASE=http://127.0.0.1:1/v1 MAX_RUNS=1 \
  python3 /path/to/skills/harness/tackle-memory-bank-api-loop .
echo $?
```

**Exit `21`** — "the API could not be reached" — is what you want. Every check
on your side passed; the only failure was the network call you sabotaged on
purpose. No API key, no cost, no model involved.

The same harness shows what it found:

```text
| Status file | Actionable rows | Blocked rows |
|---|---|---|
| memory-bank/status-A01.md | 3 | 0 |
| memory-bank/status-E01.md | 6 | 0 |
| memory-bank/status-P01.md | 7 | 0 |
| memory-bank/status-U01.md | 5 | 0 |
| memory-bank/status-W01.md | 5 | 0 |
```

Twenty-six rows of work, parsed out of files written from a ten-minute
conversation. If a lane you expected shows `0`, its markers are wrong.

## Step 6 — Run The Work

**One row at a time**, which is the everyday mode:

```text
/memory-bank-next
```

It reads `AGENTS.md`, finds the next actionable row in the right lane file, and
does **exactly one**: implement, verify, update the status row, commit. Blocked
rows are skipped in favour of actionable ones. If the row closes a milestone it
runs the milestone review first.

Plain English works identically — *"tackle next pending item in memory bank"* —
the command just carries the full instruction instead of your paraphrase of it.

**A whole ordered set**, for a release or a migration with real dependencies:

```text
/memory-bank-goal W01 -> P01 -> E01 -> U01 -> A01?
```

That follows [GOAL.md](../GOAL.md): reconcile before each milestone, implement,
verify, deep-review, then reconcile the milestones downstream of the one that
just closed. It sends `COMMIT_POLICY: task` for you — worth knowing, because
`GOAL.md`'s own default is `none`, meaning no commits at all.

Reconciling downstream is what makes this better than a to-do list. When `W01`
closes, the tilemap that actually got built is not the one `P01` was written
against — so `P01` gets re-read and rewritten before it starts, rather than
implemented as planned and wrong.

**In Claude Code, pair it with the built-in `/goal`** to keep the session going
across turns. That `/goal` is a different feature — it sets a stop condition,
not a task:

```text
/goal every row in W01, P01, E01 and U01 is `[+]` and node --test passes
```

Then watch the first milestone. `git log` should show one commit per row, code
and status-row flip together. If the agent closed three rows in one commit, say
so now — the memory bank is instructions, not enforcement, and early
corrections stick.

## When It Goes Wrong

Verified against real runs of the checkpoint above:

| Exit | Meaning | Usual cause |
|---|---|---|
| `21` | Reached the network. **Everything else passed.** | Nothing. This is success. |
| `0` | "No actionable memory-bank rows remain." | **Markers without backticks** — `[ ]` instead of `` `[ ]` ``. Your rows are invisible. |
| `11` | No lane files found. | Filename is `status-P1.md`, not `status-P01.md`. Always **two digits**. |
| `4` | Worktree was dirty before the run. | Commit or stash first. |
| `3` | Only `` `[!]` `` blocked rows remain. | Not a failure. A human needs to unblock something. |
| `10` | No `AGENTS.md`. | Wrong directory, or `/memory-bank-init` never finished. |

Exit `0` is the one that costs an afternoon, because nothing looks broken: the
agent reads the file, finds no rows it recognizes, and reports there is nothing
to do. If a run ends instantly with nothing to do, check the backticks first.

`/memory-bank-init` checks all three of these before it reports done, so they
mostly bite when you hand-edit afterwards. Full table in
[EXECUTION.md](EXECUTION.md#exit-codes).

## What You Own At The End

A project whose memory bank came out of a conversation you had, in files you can
edit or delete, with no dependency on the plugin that generated them.

The memory bank is mutable and expected to change: `product.md`,
`architecture.md`, and `tech-stack.md` get rewritten in the same commit as the
code that makes them true. `evolution/` gets a new version only when direction
genuinely shifts — rarely.

Two things to know as you keep going:

- **A pending status file is a planning baseline, not a contract.** It was
  written before the code existed. Rewriting it when reality disagrees is the
  intended behavior, not drift.
- **The lane letters are permanent, the rows are not.** Add, split, and delete
  rows freely. Renaming `P01` later is the one thing that hurts.

When a file stops earning its place, delete it. Nothing here breaks.
