# Tutorial: From An Idea To A Running Project

You have an idea and an empty directory. No code yet.

This walkthrough goes from that to an agent implementing your project against a
memory bank it wrote itself, in seven steps:

1. Make an empty directory.
2. Open your agent in it.
3. **Talk through the idea** — product, tech stack, milestones.
4. Point the agent at this package and copy the placeholder files.
5. The agent fills in the memory bank from your conversation.
6. It splits the work into status files by feature.
7. `/goal` implements them in order.

Steps 1, 2, and 4 take a minute. Step 3 is where the real work happens, and
steps 5–7 are only as good as it was.

The example is a Mario-style platformer called `stomper`, because a game
decomposes into feature areas cleanly enough to show why step 6 exists. Every
file shown below was produced by actually running this.

## What You Need

- **`git`**, and an agent — Claude Code, Codex, or anything that reads files and
  runs commands in your repo.
- **A clone of this package**, which you copy files out of:

  ```bash
  git clone https://github.com/tabilet/skills.git
  ```

  Below, `/path/to/skills` is that clone.
- **An idea you can talk about for ten minutes.** That is the actual
  prerequisite.

The example project uses Node and Python 3; yours needs whatever it needs.

## Step 1 — An Empty Directory

```bash
mkdir stomper && cd stomper
git init
```

That is all. Do not scaffold anything, do not create source files. The point of
what follows is that the project's shape comes out of the conversation, not out
of a template you picked before thinking.

## Step 2 — Open Your Agent

```bash
claude
```

Do not ask it to write code yet. Do not mention this package yet either.

## Step 3 — Talk Through The Idea

**This is the step that determines everything downstream**, and it is the one
people skip. The memory bank an agent writes in step 5 is a transcript of the
decisions you reached here. Decisions you never reached come out as vague prose,
and vague prose is what makes an agent build the wrong thing confidently.

Chat until five things are settled:

| What | Why it matters later | Lands in |
|---|---|---|
| **What it is** | Scope. | `product.md` |
| **What it is *not*** | The most valuable thing you will say. | `product.md` |
| **Tech stack and constraints** | Rules the agent must not break. | `tech-stack.md` |
| **How you know it works** | Every task closes against this. | `tech-stack.md`, `AGENTS.md` |
| **The feature areas, and their order** | Becomes milestones and lanes. | `milestone.md` |

Talk in your own words. The exchange that shaped this example ran roughly:

> **You:** I want a side-scrolling platformer like early Mario. Runs in a
> browser. I mostly want to learn what makes movement feel good.
>
> **Agent:** Original art, or are you planning to use Mario sprites?
>
> **You:** Original — I don't want Nintendo's assets anywhere near it. Draw
> everything in code.
>
> **Agent:** What's the stack? A framework like Phaser would save you time, but
> it also hides the physics, which is the part you said you want to learn.
>
> **You:** Then no framework. Plain canvas, ES modules, no build step. I want to
> open the file and have it run.
>
> **Agent:** Then how do we verify anything? Canvas rendering isn't testable
> headlessly, and "feels good" isn't either.
>
> **You:** …good question.
>
> **Agent:** One split works well here: keep physics, collision, and entity
> state in modules that import nothing from the DOM. Those get real unit tests
> under `node --test`. Rendering and audio read that state and are verified by
> playing. It costs you one architectural rule, and it's the rule that makes the
> project testable at all.
>
> **You:** Do that. And the feature areas are basically: the world and camera,
> the player and how it collides, enemies you can stomp, the HUD, and sound.
> Sound is last and I might skip it.

Notice what that produced: **a non-goal** (no Nintendo assets, no build step),
**an architectural rule** (simulation imports nothing from the DOM), and **a
verification command** (`node --test`). Those three are what an agent needs to
work unsupervised. They came from being pushed on "how do we verify anything" —
which is the question to make sure gets asked, about your project, before you
move on.

## Step 4 — Point The Agent At This Package

Now bring in the files. From the project root:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

If you are in Claude Code, bridge the agent file — one line, no duplicate to
drift ([details](../README.md#wiring-up-your-agent)):

```bash
ln -s AGENTS.md CLAUDE.md
```

Then hand off. This prompt is the whole of step 4:

```text
Read AGENTS.md, memory-bank/*, and evolution/* — they are placeholder templates
from a starter package I just copied in.

Fill them in from the conversation we just had. Do not invent requirements I
did not state; ask me instead. Specifically:

- product.md: what this is, who it's for, and the non-goals we agreed on.
- architecture.md: the module layout and the DOM-free simulation boundary.
- tech-stack.md: the stack, and the verification commands.
- milestone.md: define the status ID lanes, one per feature area, then the
  milestones and their acceptance criteria, and the execution order.
- One status-<LANE><NN>.md per milestone, with actionable rows small enough
  that one row is one commit.
- evolution/prompt-v1.md and result-v1.md: the initial direction, and the fact
  that nothing is built yet.

Replace every bracketed placeholder. Tell me which ones you couldn't fill.
```

The last line matters. An agent that cannot fill something should say so rather
than invent it, and the leftovers are usually a decision you never actually made
in step 3.

## Step 5 — The Agent Fills The Memory Bank

The template ships 48 bracketed placeholders. You are not filling them by hand —
that is what the conversation was for.

What comes back:

```text
stomper/
├── AGENTS.md              ← commands, boundaries, hard rules
├── CLAUDE.md -> AGENTS.md
├── GOAL.md                ← the execution protocol, used in step 7
├── memory-bank/
│   ├── product.md         ← what it is, and the non-goals
│   ├── architecture.md    ← module layout, the DOM-free rule
│   ├── tech-stack.md      ← stack, and how it's verified
│   ├── milestone.md       ← lanes, milestones, execution order
│   └── status-*.md        ← one per feature area (step 6)
└── evolution/
    ├── prompt-v1.md
    └── result-v1.md
```

**Read what it wrote.** This is your job in this step, and it takes five
minutes. Three things worth checking:

*Did the non-goals survive?* They are the highest-value lines in the memory bank
and the easiest for an agent to soften into nothing:

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

Rendering reads that state and draws it; it never owns it. This is what keeps
the simulation testable under `node --test`, and it is the boundary most likely
to erode under time pressure.
```

*Is the verification command real?* If `tech-stack.md` says something the agent
has never run, every task after this will close against a command that does not
work. Run it yourself now, even with zero tests, and confirm it exits cleanly.

Fix anything wrong by telling the agent, not by hand-editing. It is faster, and
it keeps the memory bank consistent with what the agent believes.

## Step 6 — Lanes By Feature

The starter ships one status file, `status-M01.md`, on the default `M` lane. For
a small project that is the right answer and you should keep it.

This project earns more. Its feature areas have genuinely different acceptance
criteria — collision correctness is unit-testable, audio is a playtest — so
they review as separate units. The agent defined a lane per area in
`milestone.md`:

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

and an execution order, because these are not independent:

```markdown
W01 -> P01 -> E01 -> U01 -> A01?
```

`P01` needs tile queries from `W01`; `E01` reuses `P01`'s collision resolver.
The trailing `?` on `A01` marks it **conditional** — skipped rather than
cancelled when its trigger is absent.

Two details from the real run:

- `status-M01.md` was **deleted.** Every piece of work classifies into a feature
  lane, so an unused default lane is just a file that makes readers wonder what
  belongs in it.
- IDs are never reused or renamed once their file exists. Pick letters you can
  live with. See [Status ID lanes](../README.md#status-id-lanes).

A status file is a table of rows, each small enough to be one commit:

```markdown
# Status P01 - The Player Moves, Jumps, And Collides

**Depends on.** W01 (needs `tileAt`).

**Acceptance.** `node --test` passes, including the tile-seam regression test.
Variable jump height and coyote time verified by playtest.

| Item | State | Notes |
|---|---|---|
| Fixed timestep integration | `[ ]` | Accumulator loop. Physics must not vary with frame rate. |
| Horizontal accel and friction | `[ ]` | Separate ground and air friction constants. |
| Gravity and terminal velocity | `[ ]` | |
| Axis-separated AABB resolution | `[ ]` | Horizontal, then vertical. Resolving both at once causes seam catching. |
| Tile-seam regression test | `[ ]` | Walk across a flat run of tiles at several speeds; assert no horizontal stall. |
| Variable jump height | `[ ]` | Releasing the key early cuts upward velocity. |
| Coyote time and jump buffer | `[ ]` | ~6 frames each. The two together are most of what makes it feel right. |
```

**The backticks around `` `[ ]` `` are load-bearing.** A bare `[ ]` is invisible
to every tool that reads the file — see [When It Goes
Wrong](#when-it-goes-wrong). Markers are `` `[ ]` `` pending, `` `[+]` `` done,
`` `[~]` `` in progress, `` `[!]` `` blocked, `` `[X]` `` cancelled.

Note what those rows are not: they are not "build the player." Each names a
thing that is either done or not, and two of them exist only because the chat
surfaced a specific failure mode worth testing for.

## Checkpoint — Before You Start A Long Run

Everything so far is prose an agent interprets loosely. Before handing it a run
that works unattended, get a hard yes or no.

This package ships an optional [API harness](../README.md#install-the-api-harness)
that runs local checks before it calls any API — is there an `AGENTS.md`, is
this a git worktree, are there lane files, are there actionable rows, is the
worktree clean. Point it at a dead endpoint to reach those checks and stop:

```bash
git add -A && git commit -m "Add memory bank from design conversation"

LLM_MODEL=check LLM_API_KEY=x LLM_API_BASE=http://127.0.0.1:1/v1 MAX_RUNS=1 \
  python3 /path/to/skills/harness/tackle-memory-bank-api-loop .
echo $?
```

**Exit `21`** — "the API could not be reached" — is what you want. Every check
on your side passed; the only failure was the network call you sabotaged on
purpose. No API key, no cost, no model involved.

The same harness can show you what it found:

```text
| Status file | Actionable rows | Blocked rows |
|---|---|---|
| memory-bank/status-A01.md | 3 | 0 |
| memory-bank/status-E01.md | 6 | 0 |
| memory-bank/status-P01.md | 7 | 0 |
| memory-bank/status-U01.md | 5 | 0 |
| memory-bank/status-W01.md | 5 | 0 |
```

Twenty-six rows of work, parsed out of the files an agent wrote from a ten-minute
conversation. If a lane you expected shows `0`, its markers are wrong.

## Step 7 — Hand It To `/goal`

One row at a time is the everyday workflow — *"tackle next pending item in memory
bank"*, and nothing else to learn. For a defined sequence of milestones, this is
what [GOAL.md](../GOAL.md) is for. It reconciles dependencies before each
milestone, reconciles the milestones downstream of one that just closed, and
stops rather than guessing when a decision or authority is missing.

The request is the same whatever your agent — it names the file, the order, and
the commit policy:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER:
W01 -> P01 -> E01 -> U01 -> A01?

DOWNSTREAM_IMPACTS:
W01 -> P01, E01
P01 -> E01, U01

COMMIT_POLICY: task
```

Three things about that block:

**`COMMIT_POLICY` is not optional in practice.** Its default is `none`, meaning
no commits at all. For the length of a goal run it is the *entire* commit rule —
`AGENTS.md` may say every row is a commit unit, but `none` overrides it, and
that is correct behavior rather than a conflict. Write `task` for the usual
per-row commits.

**`DOWNSTREAM_IMPACTS` is why this beats a to-do list.** When `W01` closes, the
tilemap that actually got built is not exactly the one `P01` was written
against. The arrows say: before starting `P01`, go re-read it and rewrite what
is now wrong. Plans written before the code exists are always a little wrong;
this is the step that fixes them instead of implementing them anyway.

**`A01?` is skipped, not cancelled**, when its trigger is absent. It stays
pending and does not block the goal from completing.

### How to send it

`/goal` is not the same command in every agent, so this part differs. Full
detail in [Run an ordered set of
milestones](../README.md#run-an-ordered-set-of-milestones).

**Claude Code.** `/goal` is built in, and it does not start a task — it sets a
stop condition that Claude checks before finishing, so the session keeps working
across turns. Send the block above as an ordinary message, then:

```text
/goal every row in W01, P01, E01 and U01 is `[+]` and node --test passes
```

`/goal active` shows it, `/goal clear` ends it early. If you want the block
itself saved as a command, name it anything but `goal` — the built-in owns that
name. `.claude/commands/milestones.md` works.

**Codex.** There is no built-in `/goal`, so you make one: custom prompts are
markdown files in `~/.codex/prompts/` invoked by filename. Put the block in
`~/.codex/prompts/goal.md` with `STATUS_ORDER: $ARGUMENTS`, and run
`/goal W01 -> P01 -> E01 -> U01 -> A01?`.

**Anything else.** Paste the block as an ordinary request. Naming the file is
all the protocol needs.

Then watch the first milestone. `git log` should show one commit per row, each
with code and its status-row flip together. If the agent closed three rows in
one commit, say so now — the memory bank is instructions, not enforcement, and
early corrections stick.

## When It Goes Wrong

Verified against real runs of the checkpoint above:

| Exit | Meaning | Usual cause |
|---|---|---|
| `21` | Reached the network. **Everything else passed.** | Nothing. This is success. |
| `0` | "No actionable memory-bank rows remain." | **Markers without backticks** — `[ ]` instead of `` `[ ]` ``. Your rows are invisible. |
| `11` | No lane files found. | Filename is `status-P1.md`, not `status-P01.md`. The number is always **two digits**. |
| `4` | Worktree was dirty before the run. | Commit or stash first. |
| `3` | Only `` `[!]` `` blocked rows remain. | Not a failure. A human needs to unblock something. |
| `10` | No `AGENTS.md`. | Wrong directory, or the copy in step 4 did not land. |

Exit `0` is the one that costs an afternoon, because nothing looks broken: the
agent reads the file, finds no rows it recognizes, and reports there is nothing
to do. If a run ends instantly with nothing to do, check the backticks first.

Full table in [EXECUTION.md](EXECUTION.md#exit-codes).

## What You Own At The End

A project whose memory bank came out of a conversation you had, in files you can
edit or delete, with no dependency on the package you copied them from.

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
