# Tutorial: Your First Memory Bank

A start-to-finish walkthrough for someone who has never used this before. You
will take a small project, give it a memory bank, and run one task through it.

Twenty minutes. At the end you will have a project that can explain itself to an
agent, and you will have watched one row go from pending to committed.

This tutorial builds a throwaway toy so the steps stay visible. Everything in it
applies unchanged to a real repository — see
[Set Up An Existing Project](../README.md#set-up-an-existing-project) when you
are ready to do that.

## Before You Start

- **`git`.** Required. The memory bank is markdown in your repository, and the
  workflow commits after each task.
- **An agent** you already use — Claude Code, Codex, Cursor, or any tool that
  reads files and runs commands in your repo.
- **Python 3**, only because this tutorial's toy project happens to be Python.
  Your own project can be anything.
- **A clone of this repository**, which you copy files *out of*:

  ```bash
  git clone https://github.com/tabilet/skills.git
  ```

  Below, `/path/to/skills` means that clone. Nothing runs from it.

## Step 0: A Project To Work On

Make a tiny project so there is something real to point the memory bank at.

```bash
mkdir wordcount && cd wordcount
git init
```

`wordcount.py` — counts whitespace-separated words on stdin:

```python
import sys

def count(text):
    return len(text.split())

if __name__ == "__main__":
    print(count(sys.stdin.read()))
```

`test_wordcount.py` — the thing that proves it works:

```python
from wordcount import count

assert count("one two three") == 3
assert count("") == 0
print("ok")
```

Check it, ignore the bytecode Python drops next to it, and commit:

```bash
python3 test_wordcount.py      # ok
printf '__pycache__/\n' > .gitignore
git add -A && git commit -m "wordcount: first version"
```

That `python3 test_wordcount.py` command matters more than the code does. It is
this project's **harness** — the repeatable command that proves the project
works. Every task an agent finishes will be checked against it. A project with
no such command has nothing to verify against, and the whole loop degrades into
an agent asserting it is done.

## Step 1: Copy The Template

```bash
cp -R /path/to/skills/template/. .
```

Your project now has:

```text
wordcount/
├── AGENTS.md              what an agent reads first
├── GOAL.md                optional multi-milestone protocol; ignore for now
├── memory-bank/
│   ├── product.md         what this is, and is not
│   ├── architecture.md    layout, data flow, boundaries
│   ├── tech-stack.md      commands, dependencies, how you verify
│   ├── milestone.md       milestones and their acceptance criteria
│   └── status-M01.md      one row per task
├── evolution/             why the direction changed, when it did
├── wordcount.py
└── test_wordcount.py
```

These files are now **yours**. Nothing links back to the repository you copied
them from, and nothing will update them but you.

## Step 2: Fill In Four Things — Not Forty-Eight

The template ships **48 bracketed placeholders**. Do not sit down and fill them
all in. Most first attempts stall right here, writing architecture documentation
for a project that has not done anything yet.

Fill in four things. The rest gets written as you go, by you or by your agent,
in the same commits as the work that makes them true.

### 1. `memory-bank/product.md` — what this is

```markdown
# Product

## What this is

`wordcount` is a command-line word counter. It reads text on stdin and prints
the number of whitespace-separated words.

## Users

- People counting words in a pipeline.

## Non-goals

- Character or line counting. `wc` already does that.
```

The non-goals section earns its keep immediately. It is what stops an agent from
helpfully adding a `--lines` flag you never wanted.

### 2. `memory-bank/milestone.md` — what "next" means

```markdown
## Status ID Pattern

M01, M02, ...   Default lane: everything, until a domain earns its own letter.

## Status Files

| Milestone | Status File | Summary |
|---|---|---|
| M01 | [status-M01.md](status-M01.md) | Make the counter trustworthy. |

## M01 - Make The Counter Trustworthy

**Goal.** `wordcount` handles the input people actually pipe into it.

**Acceptance.** `python3 test_wordcount.py` prints `ok`.
```

Start with the `M` lane alone. Lanes exist so a large project can split work by
domain — `A01` accounting, `S01` shopping — and one letter is genuinely enough
until you have more work than one file can hold. Splitting early buys nothing.
See [Status ID lanes](../README.md#status-id-lanes) for when to add a letter.

### 3. `memory-bank/status-M01.md` — the actual work

```markdown
# Status M01 - Make The Counter Trustworthy

| Item | State | Notes |
|---|---|---|
| Empty input returns 0 | `[+]` | Covered by test_wordcount.py. |
| Accept a file path argument | `[ ]` | Fall back to stdin when absent. |
| Reject unreadable files clearly | `[ ]` | Non-zero exit, message on stderr. |
```

**The backticks around the markers are load-bearing.** `` `[ ]` `` is a pending
row; a bare `[ ]` is invisible to every tool that reads this file. This is the
single most common way a first memory bank silently does nothing — see
[When It Does Not Work](#when-it-does-not-work).

The markers: `` `[ ]` `` pending, `` `[+]` `` done, `` `[~]` `` in progress,
`` `[!]` `` blocked, `` `[X]` `` cancelled.

Write rows small enough that one of them is one commit. "Accept a file path
argument" is a row. "Improve the CLI" is not — an agent cannot tell when it is
finished.

### 4. The verification command, in two places

In `memory-bank/tech-stack.md`, replace the `[test command]` placeholder:

```markdown
| Unit tests | `python3 test_wordcount.py` | Counting is correct. | Python 3. |
```

And in `AGENTS.md`, replace the commands block:

````markdown
```bash
python3 test_wordcount.py    # prints "ok" when the project is sound
```
````

Both, because they answer different questions: `AGENTS.md` is what an agent reads
first and tells it how to check its work; `tech-stack.md` is where a human looks
up how the project is built.

Commit:

```bash
git add -A && git commit -m "Add memory bank"
```

## Step 3: Run One Task

Open the project in your agent and type:

> tackle next pending item in memory bank

That sentence is the entire interface. There is no slash command to learn and
nothing to install — which is why the same sentence works in Claude Code, in
Codex, or pasted into a chat window.

A run that went right looks like this:

1. The agent reads `AGENTS.md`, then the memory bank.
2. It picks **one** row — the first actionable one, guided by `milestone.md`.
3. It implements that row and nothing else.
4. It runs `python3 test_wordcount.py` and sees `ok`.
5. It updates `status-M01.md`, flipping that row to `` `[+]` ``.
6. It commits.

Then `git log --oneline` shows one commit, and `git show` shows the code change
and the status row flip together. **One row, one commit.** That is the only
discipline this asks for, and it is what makes the history reviewable later
without any extra tooling.

If the agent tried to do all three rows at once, say so and point it back at the
row it should have picked. Early runs need this; the memory bank is instructions,
not enforcement.

## Checkpoint: Is The Memory Bank Actually Well-Formed?

Everything so far has been prose an agent interprets loosely. Here is a way to
get a hard yes or no.

This repository ships an optional [API harness](../README.md#install-the-api-harness)
that drives a model through the memory bank unattended. Before it calls any API
it runs a series of local checks — is there an `AGENTS.md`, is this a git
worktree, are there lane files, are there actionable rows, is the worktree clean.
You can run it with a deliberately dead API endpoint to reach those checks and
nothing else:

```bash
LLM_MODEL=check LLM_API_KEY=x LLM_API_BASE=http://127.0.0.1:1/v1 MAX_RUNS=1 \
  python3 /path/to/skills/harness/tackle-memory-bank-api-loop .
echo $?
```

**Exit `21`** — "the API could not be reached" — is the result you want. It means
every check on your side passed and the only thing that failed was the network
call you sabotaged on purpose. No API key, no cost, no model involved.

Any other code means something is wrong with the project, and the number tells
you what. Full table in [EXECUTION.md](EXECUTION.md#exit-codes).

## When It Does Not Work

These are the four outcomes you are most likely to hit, each verified against a
real run of the checkpoint above:

| Exit | What it means | The usual cause |
|---|---|---|
| `21` | Reached the network. **Everything else passed.** | Nothing. This is success. |
| `0` | "No actionable memory-bank rows remain." | **Markers written without backticks** — `[ ]` instead of `` `[ ]` ``. Your rows are invisible. |
| `11` | No lane files found. | Filename is `status-M1.md`, not `status-M01.md`. The number is always **two digits**. |
| `4` | Worktree was dirty before the run. | Uncommitted changes. Commit or stash first. |

Exit `0` is the one that will cost you an afternoon, because nothing looks
broken. The agent reads the file, finds no rows it recognizes, and cheerfully
reports there is nothing to do. If a run ends instantly with nothing to do,
check the backticks first.

Two more worth knowing:

- **Exit `3`** — only `` `[!]` `` blocked rows are left. Not a failure. It means
  a human needs to unblock something before the work can continue.
- **Exit `10`** — no `AGENTS.md`. You are in the wrong directory, or the copy in
  Step 1 did not land.

## Where To Go Next

You now have the whole thing. Everything else is scale:

- **A real project.** [Set Up An Existing Project](../README.md#set-up-an-existing-project)
  has a prompt that reads your README, tests, and build files and drafts the
  memory bank from what the project already says. Faster than filling 48
  placeholders by hand, and a rough draft is genuinely enough to start.
- **More than one lane.** When one status file gets unwieldy, split by domain —
  [Status ID lanes](../README.md#status-id-lanes).
- **Unattended runs.** Point the harness at a real API instead of a dead port and
  it will work rows on its own: [Install The API Harness](../README.md#install-the-api-harness).
  Read [EXECUTION.md](EXECUTION.md) first — it is a guardrail, not a sandbox, and
  belongs on a repository you can restore.
- **A sequence of milestones.** For a release or a migration with real
  dependencies between parts, [GOAL.md](../GOAL.md) runs an ordered set. Invoke it
  with an explicit commit policy — `COMMIT_POLICY: task` for the usual one commit
  per row — because the protocol's default is to make no commits at all.

The memory bank is mutable. `product.md`, `architecture.md`, and `tech-stack.md`
get rewritten as the project changes, in the same commit as the change. Nothing
here is a snapshot you are stuck with, and any file that stops earning its place
can be deleted.
