# Tabilet: A Minimal Engineering Harness

Coding agents work better when a project can explain itself: what it is, what is
done, and what comes next. The **Tabilet Harness** gives you a small set of plain-text
files—a **Tabilet memory bank**—that does exactly that. You install / copy them into your project and
own them from that moment on. The memory bank itself needs no runtime; optional tools have their own prerequisites.

For a project with uncertain later delivery, the optional
[`tabilet/stages.md`](#stage-planning) records broad stages. Init plans milestones
for the current stage and can leave later stages as brief ideas. 


Read the [published guides](https://tabilet.github.io/skills/) in English or Simplified Chinese.

## Contents

1. [Getting started](#chapter-1-getting-started)
    - 1.1 [Suggested models](#11-suggested-models)
    - 1.2 [Install for your agent](#12-install-for-your-agent)
    - 1.3 [Plain files installation](#13-plain-files-installation)
    - 1.4 [DSH installation](#14-dsh-installation)
    - 1.5 [Update installed skills](#15-update-installed-skills)
    - 1.6 [Uninstall or remove skills](#16-uninstall-or-remove-skills)
2. [Filled-in example and memory-bank structure](#chapter-2-what-a-filled-in-memory-bank-looks-like)
3. [Project setup](#chapter-3-project-setup)
    - 3.1 [Set up a new project](#31-set-up-a-new-project) ([Wiring up your agent](#wiring-up-your-agent))
    - 3.2 [Set up an existing project](#32-set-up-an-existing-project) ([Archive a large package](#archive-a-large-existing-package))
    - 3.3 [Stage planning](#33-stage-planning)
4. [Planning and review workflows](#chapter-4-planning-and-review-workflows)
    - 4.1 [Propose a requested change](#41-propose-a-requested-change)
    - 4.2 [Reconcile a new review](#42-reconcile-a-new-review)
5. [Use the memory bank](#chapter-5-use-the-memory-bank)
    - 5.1 [Status ID lanes](#51-status-id-lanes)
    - 5.2 [Keep long-term memory](#52-keep-long-term-memory-without-growing-the-active-plan)
    - 5.3 [Upgrade an existing project](#53-upgrade-an-existing-project)
    - 5.4 [Run an ordered set of milestones](#54-run-an-ordered-set-of-milestones)
6. [Optional SQLite audit and lookup](#chapter-6-optional-sqlite-audit-and-lookup)
    - 6.1 [Sync and Repair](#61-sync-and-repair)
7. [Install the API harness](#chapter-7-install-the-api-harness)
    - 7.1 [Changes since v2.4.0](#71-changes-since-v240)
    - 7.2 [Setup and Run](#72-setup-and-run)
    - 7.3 [LLM prompt caching](#73-llm-prompt-caching)
    - 7.4 [First run & guardrails](#74-first-run-guardrails)
    - 7.5 [API-only workflow](#75-api-only-workflow)
    - [Tabilet controller guide](docs/tabilet-controller.md)
    - [Execution harness reference](docs/EXECUTION.md)
8. [What the harness is](#chapter-8-what-the-harness-is)
    - 8.1 [Repository contents](#81-repository-contents)
    - 8.2 [Maintenance rules](#82-maintenance-rules)

Your project ends up looking like this:

```text
your-project/
├── AGENTS.md                 what an agent should read first
├── docs/                     other project documentation
└── tabilet/
    ├── GOAL.md               optional project addendum to the bundled goal protocol
    ├── stages.md             optional overview of delivery stages
    ├── audit.sqlite3         optional local audit database and index
    ├── memory-bank/           current facts and active work
    │   ├── product.md         product scope, domain model, and non-goals
    │   ├── architecture.md    layout, data flow, boundaries
    │   ├── tech-stack.md      commands, dependencies, verification
    │   ├── lessons.md         applicable lessons and their evidence
    │   ├── milestone.md       active milestones and later directions
    │   ├── status-M01.md      one file per active milestone
    │   └── suggested.txt      optional launch reference
    ├── docs/                  optional frozen archives and retired history
    │   ├── archive-A01.md
    │   └── history/
    └── evolution/             versioned direction snapshots
        ├── prompt-v1.md
        └── result-v1.md
```

The term *memory bank* was popularised by [Cline](https://docs.cline.bot/best-practices/memory-bank); the **Tabilet memory bank** is a different
implementation of the same idea, in plain files with no runtime.

Throughout, **harness** means a repeatable command that proves something works,
such as your test suite, a CI job, or a script. Your project defines its own in
`tech-stack.md`. The **Tabilet Harness** also ships two optional API paths: a standalone
loop that drives an agent through one row using the host shell, and a
Docker-backed controller that shows the proposed plan and limits before
confirmation, then resumes through verified milestone closure. Required manual
evidence pauses completion until it is supplied. See the
[controller guide](docs/tabilet-controller.md).

<a id="getting-started"></a>
## Chapter 1. Getting Started

**New to this?** [docs/TUTORIAL.md](docs/TUTORIAL.md) walks a toy project from
an empty directory to a first committed task in twenty minutes, using
the `memory-bank-init` skill to do the setup. The rest of this README is
reference material, and the tutorial is a guided path through it.

Already have a project or a new review? [Skill use cases](docs/USE_CASES.md)
shows individual and combined workflows, including automatic retirement versus
explicit context snapshots.

<a id="suggested-models"></a>
<a id="71-suggested-models"></a>
<a id="12-suggested-models"></a>
### 1.1 Suggested models

Skills use the host agent's selected model by default. Choose stronger reasoning
for ambiguous planning and milestone review; a faster model can suit a clear,
bounded task. Goal and Next support an optional [model policy](docs/goal.md#optional-model-policy)
for supported hosts. Project files remain provider-independent.

<a id="72-supported-agents-claude-code-codex-agy-dsh"></a>
<a id="13-install-for-your-agent"></a>
<a id="install-the-five-skills"></a>
<a id="install-the-six-skills"></a>
<a id="install-the-seven-skills"></a>
<a id="chapter-7-install-the-seven-skills"></a>
<a id="11-install-the-seven-skills"></a>
### 1.2 Install for your agent

Claude Code, Codex, and `agy` (Google Antigravity) read the same `SKILL.md` format
**and the same manifest**. DSH loads the same complete directories through its
filesystem skill loader; see [DSH installation](#14-dsh-installation).

**Claude Code:** Run these commands in your terminal:

```bash
claude plugin marketplace add tabilet/skills
claude plugin install memory-bank@tabilet
```

**Codex** has its own plugin system, and reads
`.claude-plugin/plugin.json` as a fallback, so the same repository works:

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

Codex requires the `@marketplace` qualifier when a plugin name is not unique
across your configured marketplaces, so `memory-bank@tabilet` is the form worth
learning. `codex plugin marketplace upgrade` refreshes the snapshot when a new
version ships.

**agy (Antigravity):**

`agy` has a built-in plugin manager and can install directly from GitHub:

```bash
agy plugin install https://github.com/tabilet/skills
```

*(Or from a local clone: `agy plugin install .`)*

`agy` registers all seven skills as slash commands and installs them into
`~/.gemini/config/plugins/memory-bank`. Verify with `agy plugin list`.

**Plugin installations are namespaced.** This follows current [Claude Code
skill namespacing](https://code.claude.com/docs/en/slash-commands), [Codex
skill invocation](https://developers.openai.com/plugins/build/skills), and
`agy` slash command registration:

| Agent | Archive | Init | Propose change | Upgrade rules | Reconcile review | Next row | Ordered milestones |
|---|---|---|---|---|---|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-archive` | `/memory-bank:memory-bank-init` | `/memory-bank:memory-bank-propose` | `/memory-bank:memory-bank-upgrade` | `/memory-bank:memory-bank-reconcile` | `/memory-bank:memory-bank-next` | `/memory-bank:memory-bank-goal` |
| Codex plugin | `$memory-bank:memory-bank-archive` | `$memory-bank:memory-bank-init` | `$memory-bank:memory-bank-propose` | `$memory-bank:memory-bank-upgrade` | `$memory-bank:memory-bank-reconcile` | `$memory-bank:memory-bank-next` | `$memory-bank:memory-bank-goal` |
| agy plugin | `/memory-bank:memory-bank-archive` | `/memory-bank:memory-bank-init` | `/memory-bank:memory-bank-propose` | `/memory-bank:memory-bank-upgrade` | `/memory-bank:memory-bank-reconcile` | `/memory-bank:memory-bank-next` | `/memory-bank:memory-bank-goal` |
| DSH filesystem | `/memory-bank-archive` | `/memory-bank-init` | `/memory-bank-propose` | `/memory-bank-upgrade` | `/memory-bank-reconcile` | `/memory-bank-next` | `/memory-bank-goal` |

Plain English also works across all agents. After installing, run
`memory-bank-init` for a new or small existing project. A large existing package
may first need `memory-bank-archive`; see [existing project setup](#set-up-an-existing-project).

<a id="as-plain-files-you-own"></a>
<a id="73-plain-files-installation"></a>
<a id="14-plain-files-installation"></a>
### 1.3 Plain files installation

**As plain files you own** rather than a managed plugin, install into each
agent's personal skill directory:

```bash
# Codex and agy personal skill directory
mkdir -p ~/.agents/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.agents/skills 'skills-main/skills'

# Claude Code alternative
mkdir -p ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.claude/skills 'skills-main/skills'
```

Plain-file skills are unnamespaced: `/memory-bank-archive` and
`/memory-bank-init` in Claude Code and agy, `$memory-bank-archive` and
`$memory-bank-init` in Codex, with the same pattern for `upgrade`, `propose`, `reconcile`, `next`, and
`goal`. `agy` also scans project-local skills in `.agents/skills/`.

To pin a published version, replace `refs/heads/main` with its tag path and
match the archive's directory name. For tag `v1.3.0`, those are
`refs/tags/v1.3.0` and `skills-1.3.0` respectively: the extracted directory omits
the tag's leading `v`. A tag download is available only after publication.

The Tabilet plugin installs the *generator*, not the output. What it writes into your
project is yours, is never updated from here, and survives uninstalling it.

The skill is deliberately not named `goal`: Claude Code and Codex reserve
built-in `/goal` for keeping a durable objective active, while
`memory-bank-goal` supplies this repository's multi-milestone protocol. The two
work together; see [Run an ordered set of
milestones](#run-an-ordered-set-of-milestones).

<a id="dsh-installation"></a>
<a id="74-dsh-installation"></a>
<a id="15-dsh-installation"></a>
### 1.4 DSH installation

The optional [tabilet-skills companion](https://github.com/tabilet/tabilet-skills)
packages the seven v2.16.1 skills and provides a read-only Memory Bank sidebar
and reviewable workflow request previews. The tested companion target is Linux,
Node 24.14.1, and DSH 0.1.5-rc.2. Direct filesystem installation is also
available; its acceptance evidence has a separate runtime scope.

See the [DSH guide](docs/DSH.md#install-the-dsh-companion) for installation,
updates, support boundaries, and acceptance evidence. For reproducible source
installation, use the `v2.16.1` tag and its matching guide. A plugin update does
not migrate project rules or history.

<a id="update-installed-skills"></a>

<a id="75-update-installed-skills"></a>
<a id="16-update-installed-skills"></a>
### 1.5 Update installed skills

Updating installed skills refreshes the tools available to your agent. Remember:
**updating installed skills does not alter your project's memory bank files or rules**.
To adopt newer workflow rules in an existing project, use `memory-bank-upgrade`
after updating the skills.

- **Claude Code:**
  ```bash
  claude plugin marketplace update tabilet
  claude plugin update memory-bank@tabilet
  ```
  *(Or inside an active session: `/plugin marketplace update tabilet`, then `/plugin install memory-bank@tabilet`, followed by `/reload-plugins`.)*
- **Codex:**
  ```bash
  codex plugin marketplace upgrade tabilet
  codex plugin add memory-bank@tabilet
  ```
  *(Start a new Codex session to load the updated skills.)*
- **agy:**
  Re-run the [agy installation command](#12-install-for-your-agent) to pull the latest version from GitHub.
- **DSH:**
  Follow [update or removal](docs/DSH.md#update-or-remove) to update the companion package or replace the filesystem bundles under `$DSH_HOME/skills` with complete folders from the new release.
- **Plain-file installs:**
  Re-download or copy the updated `skills/` folders into `~/.agents/skills/` (or `~/.claude/skills/`).

<a id="uninstall-or-remove-skills"></a>
<a id="76-uninstall-or-remove-skills"></a>
<a id="17-uninstall-or-remove-skills"></a>
### 1.6 Uninstall or remove skills

Uninstalling removes the generator skills from your agent environment. Project
Markdown files in your repositories remain untouched and continue to function as
authoritative documentation and manual task tracking.

- **Claude Code:**
  ```bash
  claude plugin uninstall memory-bank@tabilet
  # Optional: claude plugin marketplace remove tabilet
  ```
  *(Or inside Claude Code: `/plugin` to open the interactive manager and uninstall.)*
- **Codex:**
  ```bash
  codex plugin remove memory-bank@tabilet
  # Optional: codex plugin marketplace remove tabilet
  ```
- **agy:**
  ```bash
  agy plugin uninstall memory-bank
  ```
- **DSH:**
  ```bash
  dsh plugin --profile web remove tabilet-skills
  ```
  *(Remove the headless profile installation separately if installed there.)*
- **Plain-file installs:**
  Delete only the `memory-bank-*` directories from `~/.agents/skills/` (or `~/.claude/skills/`).

### If you already use `/grill-me`

After a design interview, run `memory-bank-init` in the same session to turn
agreed decisions into an approved, persistent project plan. The interview
technique is adapted from [mattpocock/skills](https://github.com/mattpocock/skills).

<a id="what-a-filled-in-memory-bank-looks-like"></a>
<a id="chapter-3-what-a-filled-in-memory-bank-looks-like"></a>
## Chapter 2. What A Filled-In Memory Bank Looks Like

The template ships placeholders. Here is the same Tabilet memory bank filled in for a
small shopping service, so you can see the destination before the directions.

`tabilet/memory-bank/product.md` starts as `[project-name] is [one or two sentences
describing the project]` and becomes:

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.

## Domain model

| Concept | Meaning | Relationships and invariants |
|---|---|---|
| Cart | A shopper's pending purchase. | Belongs to one shopper and contains line items. |
| Line item | A product and requested quantity in a cart. | Belongs to exactly one cart. |
| Checkout | The transition from an active cart to payment. | Starts only from a non-empty cart with current pricing. |
```

`tabilet/memory-bank/milestone.md` is the file that decides how everything else is
organised. It names the lanes and states what each one covers:

```markdown
## Status ID Pattern

M01, M02, ...   Default lane: cross-cutting work, infrastructure, chores
S01, S02, ...   Storefront: cart, checkout, product pages
A01, A02, ...   Accounting: pricing, invoices, payment reconciliation

Lane meanings:

- `M`: anything that does not belong to a product domain.
- `S`: shopping surface. Owned by the storefront team.
- `A`: money. Changes here need a second reviewer.

## Status Files

| Milestone | Status File | Summary |
|---|---|---|
| S01 | [status-S01.md](status-S01.md) | Cart and checkout. |
| A02 | [status-A02.md](status-A02.md) | Payment contract. |

## S01 - Cart And Checkout

**Goal.** A shopper can fill a cart and complete a purchase.

**Scope.**

- Cart CRUD behind `POST /cart`.
- Line-item and order-total pricing.
- Handoff to the payment provider.

**Acceptance.** `make test` passes, and a scripted end-to-end purchase
succeeds against the staging payment sandbox.
```

Then `tabilet/memory-bank/status-S01.md` carries the rows for that milestone:

```markdown
# Status S01 - Cart And Checkout

| Item | State | Notes |
|---|---|---|
| Add POST /cart endpoint | `[+]` | Verified by tests/cart_test.py. |
| Cart total calculation | `[~]` | Rounding rules are being resolved. |
| Wire cart to checkout | `[ ]` | Blocked on the A02 payment contract. |
| Guest checkout | `[X]` | Cancelled; accounts required at launch. |
| Legacy rounding attempt | `[-]` | Consumed failed attempt; successor: Cart total calculation. |
```

**The backticks around each marker are required by the included API harness.**
It matches
`` `[ ]` ``, not `[ ]`. The current harness rejects a task marker such as
`| Item | [ ] | Notes |` with exit `11`, including when other rows are valid.
Empty or unreadable status files also stop the run. Older separately installed
runners can silently overlook malformed rows; updating skills does not update
that runner.

<a id="chapter-4-project-setup"></a>
## Chapter 3. Project Setup

<a id="set-up-a-new-project"></a>
<a id="41-set-up-a-new-project"></a>
### 3.1 Set Up A New Project

If you installed [the seven skills](#install-the-seven-skills),
`memory-bank-init` does everything in this section: it interviews you, proposes
lanes and milestones, waits for your approval, and then writes the files already
filled in. The two routes below are the same work done by hand.

For a medium or large project, Init asks about stages without requiring a
detailed plan for distant work.

<a id="411-manual"></a>
#### 3.1.1 Manual

Clone the template repository once; `/path/to/skills` below is the checkout path:

```bash
git clone https://github.com/tabilet/skills.git /path/to/skills
```

From a new project root:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Then edit the copied files in this order:

1. `tabilet/memory-bank/product.md`: define product scope, canonical domain terminology,
   concept relationships and business invariants, and non-goals.
2. `tabilet/memory-bank/architecture.md`: define layout, data flow, and boundaries.
3. `tabilet/memory-bank/tech-stack.md`: define commands, dependencies, and harnesses.
4. `tabilet/memory-bank/milestone.md`: define the status ID lanes (see
   [Status ID lanes](#status-id-lanes)) and the first milestone.
5. `tabilet/memory-bank/status-M01.md`: define the first milestone's actionable rows.
   See [what a filled-in memory bank looks
   like](#what-a-filled-in-memory-bank-looks-like), and note that the marker
   backticks matter.
6. `tabilet/evolution/prompt-v1.md`: record the initial direction.
7. `tabilet/evolution/result-v1.md`: record the current starting state.
8. `AGENTS.md`: replace placeholders with project-specific commands and rules.

If the project needs multiple delivery stages, create `tabilet/stages.md` with
a current `STG-` ID and brief entries for later stages, then associate the first
milestones with the current stage. Leave the file absent for a one-stage project;
see [Stage Planning](#stage-planning).

Keep `README.md` simple and user-facing. Put long-form references in `docs/`.

<a id="wiring-up-your-agent"></a>
<a id="412-wiring-up-your-agent"></a>
#### 3.1.2 Wiring up your agent

`AGENTS.md` is an [open cross-vendor standard](https://agents.md) stewarded by
the Agentic AI Foundation. Most coding agents read it with no setup at all,
among them Codex, Antigravity (`agy`), Cursor, Gemini CLI, GitHub Copilot's coding agent, Devin,
Windsurf, Jules, Junie, Zed, Aider, VS Code, Warp, goose, opencode, and Amp.

No vendor-specific file ships in `template/`. If your agent reads a different
filename, bridge it to `AGENTS.md` in one line rather than keeping a second copy
that will drift:

| Agent | Bridge |
|---|---|
| Anything on the list above | Nothing to do |
| Claude Code | `ln -s AGENTS.md CLAUDE.md`, or a `CLAUDE.md` containing `@AGENTS.md` |
| Anything else that reads its own file | Symlink or import `AGENTS.md` the same way |

On Windows, symlinks need Administrator or Developer Mode, so prefer the import
form there.

<a id="413-with-help-of-an-ai-agent"></a>
#### 3.1.3 With Help Of An AI Agent

Instead of filling the copied template yourself, describe the project and ask an
agent to replace the placeholders with supported facts, verification commands,
and an actionable first milestone. Copying into an existing project can
overwrite files; back up or commit existing work first.

<a id="set-up-an-existing-project"></a>

<a id="42-set-up-an-existing-project"></a>
### 3.2 Set Up An Existing Project

`memory-bank-init` handles a small existing package directly. It reads what the
repository already states in the README, tests, build and CI files, interfaces,
schemas, source layout, and infrastructure, then asks only about decisions the
evidence cannot settle.

For a large existing package, init first performs a cheap topology pass. When
the selected boundary spans several stable product-domain or ownership
contexts, or cannot be evidenced reliably in one initialization pass, it stops
before writing and requires `memory-bank-archive` as a preflight. This is an
adaptive evidence boundary, not a file-count or line-count threshold.

<a id="archive-a-large-existing-package"></a>
<a id="421-archive-a-large-existing-package"></a>
#### 3.2.1 Archive A Large Existing Package

Start from a clean Git commit and run:

```text
/memory-bank:memory-bank-archive   # Claude Code plugin
$memory-bank:memory-bank-archive   # Codex plugin
```

The skill maps the whole selected product boundary breadth-first and proposes
stable domain or ownership contexts before writing. After approval it creates
frozen context dossiers such as `tabilet/docs/archive-C01.md`, records the full baseline
commit, and creates or refreshes the current `tabilet/memory-bank/product.md` and
`tabilet/memory-bank/architecture.md` summaries.

Archive lanes classify contexts independently from status lanes. Their numbers
are snapshot chronology, not work priority. Every context must be `verified`
before the required preflight is complete; partial or blocked coverage prevents
init from proceeding. Archives contain evidence-backed facts, never milestones,
status rows, candidate directions, or goal input.

Verified archives never change. A later archive run creates the next successor
ID only when a context's high-level domain, ownership, component, flow,
contract, dependency, operational, or verification facts materially changed.
Normal code work keeps `product.md` and `architecture.md` current and records
implementation in status history; it does not rewrite the baseline archive.

After the archive index shows every selected context as verified, run
`memory-bank-init`. It consumes the archive evidence, safely merges the seeded
summaries, interviews the remaining decisions, and creates the milestone/status
harness.

<a id="422-manual"></a>
#### 3.2.2 Manual

Inventory the project's documentation, tests, build files, and source before
writing. Back up or commit existing files; copy the template to a temporary
location if it would overwrite them. Merge supported facts and commands into the
memory bank, and keep unresolved gaps visible. An agent can perform the same
inventory and propose the merge for your review.

<a id="stage-planning"></a>

<a id="43-stage-planning"></a>
### 3.3 Stage Planning

For a project with uncertain later work, Init can create an optional
`tabilet/stages.md`. It plans milestones for the current stage's next verifiable
outcome; later stages can begin as a tentative name and one-sentence idea.
`STG-01` identifies a stage independently of milestone IDs such as `M01`.
The file names the current stage with `**Current stage.** STG-01`; later entries
have their own stable IDs. A stage description does not create a task or advance
the active milestone plan. Without this file, the existing one-stage workflow
applies. The [Init guide](docs/init.md) describes the staging question and output.

<a id="chapter-5-planning-and-review-workflows"></a>
## Chapter 4. Planning And Review Workflows

<a id="propose-a-requested-change"></a>
<a id="51-propose-a-requested-change"></a>
### 4.1 Propose A Requested Change

Use `memory-bank-propose` for a feature, candidate promotion, stage, or change
of direction in an initialized project. It inspects current evidence and presents
one complete plan and file actions for approval; implementation is separate.

Planning skills accept environment and testing profiles. Presets propose policies;
they do not grant authority. Explicit project policies, verification requirements,
and approvals still apply. See the [Propose guide](docs/propose.md),
[authorization guide](docs/authorizations.md), and [Init guide](docs/init.md).

<a id="reconcile-a-new-review"></a>

<a id="52-reconcile-a-new-review"></a>
### 4.2 Reconcile A New Review

After a project has its milestone/status harness, a new code, architecture,
security, or engineering review should change the plan only after its findings
are checked against current code. Run:

```text
/memory-bank:memory-bank-reconcile <review source>   # Claude Code plugin
$memory-bank:memory-bank-reconcile <review source>   # Codex plugin
```

The skill treats the review as untrusted evidence, revalidates each finding,
preserves the source priority while applying the project's P1/P2 definitions,
and proposes every disposition and file action before writing. Confirmed work
fits an open or pending milestone when it belongs there; findings against
completed history get a new remediation milestone. Acceptance-relevant work
enters the active graph, while optional lower-severity hardening remains an
unnumbered Candidate Direction.

A remote review is never fetched implicitly. Before each network read, the
skill shows the exact URL and asks for a separate confirmation—even when that
URL was supplied in the invocation. URLs discovered in repository content or
inside a review do not authorize another fetch.

The review is not copied into the project. Portable finding IDs, both severity
classifications, current evidence, and lineage live with the planned rows. The
skill updates downstream specifications and refreshes `suggested.txt` from the
whole active horizon when goal use is approved. It does not implement,
commit, or launch the fixes; use `memory-bank-next` or `memory-bank-goal` after
approving the reconciled plan.

<a id="use-the-memory-bank"></a>
<a id="chapter-6-use-the-memory-bank"></a>
## Chapter 5. Use The Memory Bank

The memory bank is plain Markdown; choose how to execute work:

| Method | Scope |
|---|---|
| Ask your agent | One row at a time |
| [`memory-bank-next`](#install-the-seven-skills) | One row under the project's workflow |
| [API harness](#install-the-api-harness) | One row per run, unattended |
| [Goal protocol](#run-an-ordered-set-of-milestones) | Several milestones in order |

For example, ask an agent to `tackle next pending item in memory bank`. It reads
`AGENTS.md` and the memory bank, selects one actionable row, implements it,
verifies it, updates the records, and commits under the governing policy. Git is
needed for the usual commit workflow; an authorized no-commit workflow can
maintain the Markdown without Git. Record meaningful verification commands in
the **Execution harnesses** table in `tabilet/memory-bank/tech-stack.md`; a row
reaches `[+]` only after required checks pass.

At milestone closure, run the milestone's whole-milestone review and required
verification. After each P1/P2-or-higher fix, review the milestone again. A
clean review is required within `REVIEW_MAX_ITERATIONS` (default 10); a higher
interactive limit requires explicit approval, stricter project limits still apply,
and the Python API ceiling remains 10. Unresolved blocking findings at the limit
leave the milestone incomplete. Commit review changes under the applicable policy;
do not make an empty review commit. See the [milestone contract](template/tabilet/memory-bank/milestone.md).

<a id="status-id-lanes"></a>
<a id="61-status-id-lanes"></a>
### 5.1 Status ID lanes

Status files are named `tabilet/memory-bank/status-<LANE><NN>.md`. The lane letter
classifies the work and the positive number has at least two digits, so accounting
milestones become `status-A01.md` and `status-A02.md` while shopping milestones
become `status-S01.md`. `M` is the default lane for work that does not classify
into a domain lane. After `M99`, continue with `M100`; child suffixes remain
two digits. Sort IDs numerically when order matters. `tabilet/memory-bank/milestone.md` records
what each letter means and never lets an ID be reused.

Choose lanes by durable product domain; start with `M` when unsure. Candidate
directions remain unnumbered until their promotion and breakdown are approved.

Status rows use these markers:

| Symbol | Meaning |
|---|---|
| `[ ]` | Pending; actionable when its dependencies pass |
| `[+]` | Completed |
| `[~]` | In progress; zero or one general row across the active ledger |
| `[!]` | A current unresolved blocker |
| `[X]` | Cancelled |
| `[-]` | Closed historical evidence; never retried and non-blocking for its accepted successor |

The new `[-]` marker is additive: the five earlier markers keep their existing
meanings. Use it only for a consumed failed attempt or superseded row retained
for audit, and name the accepted successor in the row notes. Before invoking an
operational launcher, its exact authorized operation row must be `[~]`; that
marker records the selection but does not grant external-mutation authority.

<a id="keep-long-term-memory-without-growing-the-active-plan"></a>
<a id="62-keep-long-term-memory-without-growing-the-active-plan"></a>
### 5.2 Keep long-term memory without growing the active plan

Keep current facts, active work, and applicable lessons in the memory bank.
After a milestone passes its review, verification, consolidation, and downstream
reconciliation, the project's adopted procedure can retire its specification and
status to frozen records in `tabilet/docs/history/`. Terminal task markers alone
do not establish acceptance; permanent IDs and frozen history are never reused or
rewritten. Superseded knowledge belongs in the append-only knowledge journal.

Retirement is distinct from `memory-bank-archive`, which captures optional frozen
context baselines. Existing projects must explicitly adopt retirement; installing
skills alone does not move files or change rules. See the
[retirement contract](template/tabilet/memory-bank/milestone.md#long-term-memory-and-retirement)
and [worked example](docs/TUTORIAL.md#example-a-milestone-closes-and-a-lesson-survives).

<a id="upgrade-an-existing-project"></a>

<a id="63-upgrade-an-existing-project"></a>
### 5.3 Upgrade an existing project

After updating the skills, use `memory-bank-upgrade` to compare an existing
project's workflow rules with the bundled contract. It presents a complete merge
proposal and applies only approved changes, preserving project plans, custom
policies, task states, IDs, review counters, and frozen history. Updating the
skills alone does not change project files or migrate v1.5.0 projects.

Invoke `/memory-bank:memory-bank-upgrade` in Claude Code,
`$memory-bank:memory-bank-upgrade` in Codex, or `/memory-bank-upgrade` in DSH.
See the [Upgrade guide](docs/upgrade.md), including the separate v1.5.0
migration and explicit adoption of retirement.

<a id="run-an-ordered-set-of-milestones"></a>

<a id="64-run-an-ordered-set-of-milestones"></a>
### 5.4 Run an ordered set of milestones

The [stock goal protocol](GOAL.md) runs approved milestones in order, checks
dependencies and downstream effects, and stops when a required decision or
authority is missing. Request it explicitly:

```text
Using the memory-bank goal protocol, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

A trailing `?` marks a conditional milestone; an unmet trigger skips it without
cancelling it. `COMMIT_POLICY: none` is the goal default and makes no commits;
`task` requests per-task commits. The resolved goal commit policy governs for
the run. See [commit policy and project addenda](docs/goal.md#commit_policy-is-the-one-that-matters).

With the plugin, use `/memory-bank:memory-bank-goal` in Claude Code or
`$memory-bank:memory-bank-goal` in Codex. Other agents can use the request above;
for a plain-file installation, copy the complete `skills/memory-bank-goal/`
directory, including its protocol registry and references.

When approved planning produces `tabilet/memory-bank/suggested.txt`, it is an
advisory launch reference; reconcile it with the live plan. Planning skills omit
new launch input if the selected protocol is unavailable or incompatible.
Proposed `AUTHORIZATION_GRANTS` do not grant permission: explicit human approval
of the resolved request and concrete scope is required. When resuming from the
suggestion, match its SHA256 against human approval before activating grants;
checksum approval alone does not approve proposed grants. Existing action,
commit, and external-mutation restrictions remain in force. See the
[authorization guide](docs/goal.md#authorization-requirements-and-grants) and
[continuation rules](docs/goal.md#continuing-approved-launch).

<a id="641-keep-a-long-run-active"></a>
<a id="541-keep-a-long-run-active"></a>
#### 5.4.1 Keep a long run active

The built-in `/goal` in [Claude Code](https://code.claude.com/docs/en/goal) and
[Codex](https://learn.chatgpt.com/use-cases/follow-goals) is an optional
persistence layer, distinct from the memory-bank protocol. Include the protocol
request and a measurable completion condition in its objective. Codex supports
`/goal pause` and `/goal resume`; if unavailable, use
`codex features enable goals`. See the [Goal guide](docs/goal.md#built-in-goal-is-a-different-thing).

<a id="642-any-other-agent"></a>
<a id="542-any-other-agent"></a>
Other agents can use the protocol request directly. Optional delegation, review,
email alerts, project addenda, and resume controls are described in the
[Goal guide](docs/goal.md) and [sub-agent guide](docs/subagents.md).

<a id="optional-sqlite-audit-and-lookup"></a>

<a id="chapter-8-optional-sqlite-audit-and-lookup"></a>
<a id="chapter-7-optional-sqlite-audit-and-lookup"></a>
## Chapter 6. Optional SQLite Audit And Lookup

Markdown remains authoritative. Optional `tabilet-audit` records workflow
evidence and maintains a rebuildable lookup index at `tabilet/audit.sqlite3`;
linked worktrees share the primary checkout's database. The toolkit needs Python
3.9 or later, including `sqlite3` with SQLite 3.24.0 or later. Recording is
disabled by default and requires explicit per-project opt-in:

```bash
tabilet-audit audit enable /absolute/path/to/project
tabilet-audit audit status /absolute/path/to/project
```

See [installation and use](docs/sqlite.md#install-and-use-the-optional-toolkit)
for toolkit installation, ignore files, disabling audit, and platform instructions.

<a id="sync-and-repair"></a>

<a id="81-sync-and-repair"></a>
<a id="71-sync-and-repair"></a>
### 6.1 Sync and Repair

Use `tabilet-audit index sync /absolute/path/to/project` after manual Markdown
changes or when lookup data is stale. Sync does not enable audit or rewrite
Markdown and durable audit history. See [index recovery](docs/sqlite.md#recover-a-failed-retirement-index)
for diagnostics and rebuilding the index without changing frozen records; a
deleted audit history cannot be rebuilt from Markdown. For an older shared
database, ask your LLM agent to extract this project from its history and import
it into its own SQLite database.

<a id="install-the-api-harness"></a>

<a id="chapter-9-install-the-api-harness"></a>
<a id="chapter-8-install-the-api-harness"></a>
## Chapter 7. Install The API Harness

This section is optional. Everything above works without it, because the Tabilet Harness
only adds an unattended loop that drives an agent through the API instead of you
typing into one. Skip it if Codex, Claude Code, or another agent already does
that for you.

The Tabilet API harness is account-level because it can drive any project that follows
this memory-bank shape. It needs Git and Python 3.9 or later; Python's standard
library supplies its dependencies.

<a id="api-changes-since-v240"></a>
<a id="91-changes-since-v240"></a>
<a id="81-changes-since-v240"></a>
### 7.1 Changes since v2.4.0

The standalone runner executes one row per run and requires a commit. The
optional controller runs serial rows within an approved bounded horizon; neither
API path runs the Goal protocol's concurrent worktree leases. Updating skills
does not update an installed runner or audit toolkit. See the
[execution reference](docs/EXECUTION.md#changes-since-v240).

<a id="setup-and-run"></a>

<a id="92-setup-and-run"></a>
<a id="82-setup-and-run"></a>
### 7.2 Setup and Run

Install the standalone runner from a checkout:

```bash
mkdir -p ~/.local/bin
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
export PATH="$HOME/.local/bin:$PATH"
```

An actionable run gives model-generated commands an unsandboxed host shell.
`ALLOW_UNSANDBOXED_SHELL=1` acknowledges this risk; it does not isolate commands.
Use a disposable sandbox and a recoverable repository. Provider credentials are
not forwarded to commands by default; `TOOL_ENV_ALLOW` explicitly forwards named
variables and does not make the shell safe.

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_MODEL=gpt-5.6 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
# Or select Anthropic:
ALLOW_UNSANDBOXED_SHELL=1 LLM_PROVIDER=anthropic LLM_MODEL=claude-opus-5 ANTHROPIC_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

Model names change; check the [OpenAI](https://developers.openai.com/api/docs/models)
and [Anthropic](https://platform.claude.com/docs/en/about-claude/models/overview)
catalogs. See the [execution reference](docs/EXECUTION.md) for provider gateways,
limits, environment handling, and the separate controller.

<a id="llm-prompt-caching"></a>

<a id="93-llm-prompt-caching"></a>
<a id="83-llm-prompt-caching"></a>
### 7.3 LLM prompt caching

The runner uses provider-supported prompt caching where available; this does
not cache model responses. See [caching behavior](docs/EXECUTION.md#prompt-caching-and-context).

<a id="first-run"></a>

<a id="94-first-run-guardrails"></a>
<a id="84-first-run-guardrails"></a>
### 7.4 First run & guardrails

The runner checks repository and row state before and after each run. It stops
on conditions such as a dirty worktree, missing commit, or invalid status/history.
See the [exit-code table](docs/EXECUTION.md#exit-codes); terminal rows do not
by themselves prove milestone acceptance.

<a id="api-only-workflow"></a>

<a id="95-api-only-workflow"></a>
<a id="85-api-only-workflow"></a>
### 7.5 API-only workflow

The API runner reads project Markdown on each run. Optional SQLite audit records
its observed lifecycle and builds a lookup index without replacing the Markdown.
Enable audit separately and commit the setup ignore file before a clean-baseline
run. See the [API-only setup](docs/installation.md#api-only-workflow) and
[SQLite guide](docs/sqlite.md).

<a id="what-the-harness-is"></a>

<a id="chapter-10-what-the-harness-is"></a>
<a id="chapter-9-what-the-harness-is"></a>
## Chapter 8. What The Harness Is

The standalone API harness runs a model through a JSON command protocol and
checks Git and task transitions between runs. It resumes an existing in-progress
row, validates retired history, and stops when no actionable work remains. It is
not a sandbox. The [execution reference](docs/EXECUTION.md)
covers the runner and controller; the [model evaluation guide](docs/MODEL_EVAL.md)
describes measuring outcomes across models.

<a id="what-is-in-this-repository"></a>
<a id="chapter-2-what-is-in-this-repository"></a>
### 8.1 Repository contents

Project-level sample files in [template/](template/), copied into a project
root:

- [template/AGENTS.md](template/AGENTS.md)
- [GOAL.md](GOAL.md) — the stock multi-milestone execution protocol; it ships inside the skills, not in the template
- [template/tabilet/memory-bank/product.md](template/tabilet/memory-bank/product.md)
- [template/tabilet/memory-bank/architecture.md](template/tabilet/memory-bank/architecture.md)
- [template/tabilet/memory-bank/tech-stack.md](template/tabilet/memory-bank/tech-stack.md)
- [template/tabilet/memory-bank/lessons.md](template/tabilet/memory-bank/lessons.md)
- [template/tabilet/memory-bank/milestone.md](template/tabilet/memory-bank/milestone.md)
- [template/tabilet/memory-bank/status-M01.md](template/tabilet/memory-bank/status-M01.md)
- [template/tabilet/evolution/prompt-v1.md](template/tabilet/evolution/prompt-v1.md)
- [template/tabilet/evolution/result-v1.md](template/tabilet/evolution/result-v1.md)

The optional API runner and controller payload live in [harness/](harness/):

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)
- [harness/tabilet](harness/tabilet) and [harness/tabilet_install.py](harness/tabilet_install.py) install the optional controller.

The seven skills are in [skills/](skills/). Claude Code, Codex, and DSH read the
same `SKILL.md` bundles, so there is one source per skill:

- [memory-bank-archive](skills/memory-bank-archive/SKILL.md) — snapshot a large
  existing package into frozen, evidence-backed context archives
- [memory-bank-init](skills/memory-bank-init/SKILL.md) — interview a
  project into existence, then write its memory bank
- [memory-bank-upgrade](skills/memory-bank-upgrade/SKILL.md) — propose and apply
  approved workflow-rule upgrades while preserving existing project state
- [memory-bank-propose](skills/memory-bank-propose/SKILL.md) — plan a requested
  feature, candidate promotion, or future direction change
- [memory-bank-reconcile](skills/memory-bank-reconcile/SKILL.md) — validate a
  new review against current code and reconcile the approved work plan
- [memory-bank-next](skills/memory-bank-next/SKILL.md) — tackle one row,
  verify it, commit it
- [memory-bank-goal](skills/memory-bank-goal/SKILL.md) — run an ordered
  set of milestones

Init, archive, propose, and reconcile inspect their planning references before
presenting a complete proposal. They write only after its approval, then continue through
verification within that scope. Upgrade presents focused rule diffs while
preserving project content. Goal loads optional runtime help only when needed;
keep its supporting reference when copying the bundle.

Unlike the copyable template, `memory-bank-init` can derive project-specific
goal input; `memory-bank-reconcile` and `memory-bank-propose` can refresh it
when approved planning changes the active graph. When goal use is approved and the selected governing protocol is available and compatible,
they write `tabilet/memory-bank/suggested.txt` with a proposed `STATUS_ORDER`,
`STATUS_FILE_MAP`, and `DOWNSTREAM_IMPACTS`. The file is advisory and disposable,
covers only the approved active horizon, and excludes unnumbered candidate
directions; the milestone and status files remain authoritative. They omit the
launch reference when no compatible protocol exists instead of naming a missing
or incompatible file.

`.claude-plugin/` holds the compatibility manifest used to install the same
Tabilet plugin in Claude Code and Codex. Nothing in `template/` is vendor-specific.

Harness references:

- [Execution Harness](docs/EXECUTION.md)
- [Model Eval Harness](docs/MODEL_EVAL.md)
- [Controller Architecture](docs/api.md)
- [Autonomous Execution](docs/automation.md)
- [Milestone Authorizations](docs/authorizations.md)

<a id="maintenance-rules"></a>

<a id="101-maintenance-rules"></a>
<a id="91-maintenance-rules"></a>
### 8.2 Maintenance Rules

- Keep `AGENTS.md` short.
- Keep project `README.md` user-facing.
- Put long explanations in `docs/`.
- Put active truth in `tabilet/memory-bank/`.
- Put historical direction snapshots in `tabilet/evolution/`.
- Update memory in the same commit as the code or docs it describes.
- Add a new evolution version only for a real direction change.
- Delete duplicate docs once useful content has been merged.
