# Review of `docs/api-automation-plan.md`

**Verdict:** the safety design is careful and mostly right. The weak points are
where it lives, how much the first release takes on, and one central decision it
puts off. The consumer direction at the end should come out of the plan.

## What's strong

- **Clear authority.** Markdown stays the source of truth, the approval receipt
  lives outside the project, and the receipt is described as execution authority
  "not a replacement for Markdown task truth". That's the right split.
- **No writes before approval.** Planning gets read-only tools with traversal and
  symlink checks, `reject` writes nothing, and `confirm` approves only the exact
  proposal shown. Before applying, it rechecks branch, hashes and IDs for drift.
- **Docker is the right fix for the runner's biggest weakness.** Today the runner
  needs `ALLOW_UNSANDBOXED_SHELL=1` and runs model commands directly on your
  machine. A container with no network, no home directory, no credentials and no
  Docker socket is a real upgrade.
- **External actions stay excluded.** Push, deploy, payments and messages each
  need their own approval, and fetching a remote review still needs separate
  consent.
- **It reuses the existing runner** instead of building a second execution engine.

## Problems

### 1. It argues against this repository's own boundary without saying so

`AGENTS.md` lists "Provider SDKs, agent frameworks, or CLI wrappers" as out of
scope and calls the repository "a copyable starter, not an application". A
`tabilet chat` that interviews you, plans, runs work in Docker and resumes is
exactly that kind of application. The plan never argues the point, and the
non-goals require that.

The plan also doesn't say why someone who already uses Claude Code or Codex,
where the seven skills already run, would switch. The real reason is unattended,
sandboxed execution of several milestones after one approval. That reason should
be stated, and it may point to a separate repository, like the DSH companion,
rather than this one.

### 2. It postpones its central decision

One `confirm` authorizes planning and execution together. The hard rules say
Propose and Reconcile hand off "without implementing, committing, or launching
execution". The plan says this "must be reconciled with repository instructions
when implemented", but that reconciliation is the design. Decide it now.

The approval scope is also large: one word can start commits across several
milestones. Add spending, turn and commit limits to the receipt, or a checkpoint
at each milestone. The repository already sets a cost ceiling for paid
acceptance tests.

### 3. It relies on a lock that doesn't exist

The plan says to "acquire the same project lock used by the runner", but the
runner has no lock. A search for `lock`, `flock` and `fcntl` in
`tackle-memory-bank-api-loop` finds only "blocked"/"blocker" text.

"One ledger writer across all Tabilet launchers" therefore needs a new lock.
Interactive Claude Code or Codex sessions can't take part in it, so it can only
protect Tabilet's own launchers. The plan should say so.

### 4. Mounting the project writable in Docker leaves a way out through `.git`

With the whole project mounted writable, the container can write `.git/config`
and `.git/hooks`:

- If the model sets `core.fsmonitor` to a command, the host controller's next
  `git status` runs that command on the host, outside the sandbox.
- Host-side commits run any hooks the model planted.

Mount `.git` read-only, and have the host run all Git commands with hardening
such as `-c core.fsmonitor=false -c core.hooksPath=/dev/null`. The plan also
doesn't say who commits: the model inside the container, or the host.

### 5. "Reuse the runner" is only partly true

The runner deliberately has no provider tool-calling; it uses a single
`run_shell` JSON command. Read-only planning tools and an interview loop are a
new protocol. The plan should count that as new surface area.

### 6. Automatic acceptance means the model grades its own work

The controller "continues through the review-fix gate" and reports the horizon
complete "only after every required milestone meets its acceptance criteria".
The same model runs the review and judges acceptance. That may be acceptable,
but say it plainly, and consider requiring a human `accept` at the end of the
horizon rather than only at its start.

### 7. The first release is too big

It covers init, propose, review intake, execution, closure, Docker, receipts and
resume. A smaller first step keeps most of the safety value without the
authorization question: `tabilet status` plus running the existing runner's
approved rows inside Docker. Add `chat` and combined approval afterwards.

### 8. Smaller gaps

- **Stopping a run:** there's no way described to watch or stop a running
  horizon, only what happens on timeout.
- **Container setup:** with no network, most real projects' tests can't install
  their dependencies. First runs will stop at "missing dependencies" until the
  user builds a suitable image, which is a significant onboarding cost.
- **Location:** the plan sits on `sqlite`, a branch that already has unresolved
  pre-merge issues.

## The consumer direction

The closing note is honest that this would be a separate product, but it doesn't
belong in the plan, and the coffee-shop example cuts against the idea:

- **What transfers is generic.** Conversation, approval, checkpoints and resume
  are standard agent patterns. What makes Tabilet valuable doesn't carry over:
  Git-backed Markdown ledgers, commits as units of work, and verification by
  tests.
- **Finding a coffee shop is a one-shot search.** It needs no milestones,
  approval gate or resume, so it would compete head-on with ChatGPT and Maps
  with no advantage.
- **It conflicts with the safety model.** Consumer value usually lies in external
  actions such as bookings, purchases and messages, which the plan deliberately
  forbids.

If you keep a consumer idea, a better example is a long-running personal project
with durable state: a move, a renovation, a job search, a multi-week trip. There,
a plain-file plan you own that survives across sessions is a real differentiator.
Put that in a separate note and keep the plan about software.

## Decide before implementation

1. Does this belong in this repository or in a separate product repository?
   (Problem 1)
2. How does combined authorization relate to the hard rules, and what limits cap
   one approval? (Problem 2)
3. How are `.git` and host-side Git hardened against the container? (Problem 4)
4. What is the first-release slice? (Problem 7)
