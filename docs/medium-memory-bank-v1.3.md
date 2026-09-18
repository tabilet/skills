# Better Agents, Less Scaffolding: Memory-Bank v1.3.0

<!-- Medium publishing asset: medium-memory-bank-v1.3-infographic.png.
Upload this image immediately below the article title; it is intentionally
not embedded in the manuscript.
Alt text: Memory-bank v1.3.0 separates native-agent execution, active project facts and lessons, and frozen historical evidence. Closure gates protect retirement; supporting cards show approved upgrades, DSH integration, and clearer skills.
Before Medium publication, replace the local companion link (medium-use-cases.md)
with the companion article's published Medium URL.
Image generation: built-in image_gen; final prompt follows.
Use case: infographic-diagram.
Asset type: a polished editorial infographic for a Medium article about memory-bank v1.3.0. Create a brand new landscape image, about 16:10, high resolution, readable at article width.
Primary request: Explain how a small portable engineering harness lets the native coding agent do implementation while the project retains focused active memory and durable evidence.
Style: match an editorial series using dark charcoal background, cream paper-like panels, amber and burnt-orange accents, subtle printed texture, bold condensed sans-serif headings, restrained dimensional document and folder illustrations. Precise layout, generous margins, strong contrast. No provider logos or cartoon people.
Layout: large title at top. A slim top strip represents the native agent. Below it, two spacious document panels show active memory and frozen history, connected through a clearly labeled closure gate. Along the bottom, three compact feature cards show project upgrades, DSH support, and clearer skill instructions. A small final footer states the shared safety principles.
Exact text, render verbatim and use no additional text:
Title: "MEMORY-BANK v1.3.0"
Subtitle: "LONG-LIVED MEMORY. FOCUSED WORK."
Top strip: "NATIVE AGENT" and "Code • Tools • Session"
First main panel: "ACTIVE MEMORY" and "Current facts" and "Active milestones" and "lessons.md"
Arrow / closure gate between panels: "Verify • Review" and "Consolidate • Reconcile"
Second main panel: "FROZEN HISTORY" and "Complete milestone records" and "Superseded knowledge"
A subtle return path from history toward the active panel: "Retrieve when needed"
Bottom feature card 1: "PROJECT UPGRADES" and "memory-bank-upgrade" and "Approve precise rule merges"
Bottom feature card 2: "DSH INTEGRATION" and "Same six skill bundles" and "Web + headless"
Bottom feature card 3: "CLEARER SKILLS" and "Read relevant guidance" and "Finish approved work"
Footer: "ONE LEDGER OWNER • EXPLICIT APPROVAL • VERIFIED ACCEPTANCE"
Constraints: This is an infographic, not a screenshot or mockup. Draw arrows only for the described memory lifecycle; retrieval means consulting evidence, not moving retired tasks back into active work. Do not imply that installing a skill migrates a project. Do not include prices, performance claims, extra features, watermarks, or unreadable decorative microtext.
-->

*Long-lived project memory, focused milestones, and six portable skills for the next generation of coding agents.*

Coding agents have improved enough over the past year to change how I approach
vibe coding. Start with a capable agent such as Codex, Claude Code, or Google's
[Antigravity](https://antigravity.google/). Add the smallest set of skills and
project conventions your work actually needs, and let the agent handle the
coding, tool use, and implementation details.

You still own the product decisions, the acceptance criteria, and the call to
ship. As agents get better at carrying those decisions out, you get more
attention back for making them.

That is why this observation in OpenAI's
[Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
resonated with me:

> Models have gotten much better at understanding nuance and ambiguity, so overly specific guidance can now hinder results where it previously helped.

Instructions accumulate for good reasons. An agent missed a test, so you added
a rule. It edited too much, so you added an approval step. It lost the plan, so
you added another planning document. A year later some of those rules still
protect something important, and others preserve workarounds for behavior that
has changed.

In my previous article,
[Manage Existing Codebase Using Agentic Engineering Harness](https://medium.com/@peterbi_91340/manage-existing-codebase-using-agentic-engineering-harness-c362f556f96f),
I described how to turn repository evidence and engineering reviews into an
approved plan. This one asks what happens after you have used that plan for
months. How do you keep what matters, keep the next task understandable, and
improve the instructions themselves?

[Memory-bank v1.3.0](https://github.com/tabilet/skills/tree/v1.3.0) is my latest
answer.

## Where the pressure comes from

This workflow has a practical track record in substantial codebases. The
repository's [operational notes](https://github.com/tabilet/skills/blob/v1.3.0/AGENTS.md#status-id-lanes)
record deployments with roughly **120 milestone/status files across 17 domain
lanes**. That is experience from real use, rather than an independent performance
benchmark.

At that scale, the recurring difficulty is continuity. A later task depends on
a decision made several sessions ago. An old review describes code that has
already changed. A completed milestone still contains evidence that somebody
will need, but it no longer belongs in the active plan.

Those pressures shape this release. Long-lived memory and a manageable active
context become more valuable as the project accumulates completed work.

## Long-lived memory

Version 1.3.0 gives completed milestones a defined storage lifecycle.

Once a milestone has passed verification, its bounded review gate, knowledge
consolidation, and downstream reconciliation, its complete specification and
status document can retire into `docs/history/status-<LANE><NN>.md`. The history
index records the permanent ID, outcome, and record location.

The record preserves the original documents as literal Markdown, together with
closure evidence. It freezes after retirement. A later correction creates new
work or new knowledge with a link back to the earlier evidence.

For example, after M01 closes and M02 becomes the remaining active milestone:

```text
memory-bank/
  product.md
  architecture.md
  tech-stack.md
  lessons.md
  milestone.md          active plan
  status-M02.md         active tasks

docs/history/
  index.md              retired IDs and outcomes
  status-M01.md         complete frozen M01 record
  knowledge.md          materially superseded knowledge, when needed
```

M01 keeps its identity after the file moves. An old reference can resolve
through the history index. A project whose milestones have all retired remains
initialized; it does not become a blank project again.

This memory survives a chat reset, an agent switch, or the end of a subscription
because it belongs to the repository. Git adds intermediate revisions, while
the retained Markdown itself carries the evidence.

## Bounded context

A larger context window makes more material available. It does not make every
old task relevant to today's change.

Memory-bank keeps the active horizon focused on the next meaningful outcome
and the dependencies needed to deliver it. Later ideas remain unnumbered
Candidate Directions until their promotion conditions are met. An implementation
row should fit a fresh working context; a milestone is the unit of review.

Retirement completes that design. The closed milestone's status file,
specification, and index row leave active memory. Its evidence remains
retrievable through one history-index link. The agent consults the relevant
historical record when a question needs it.

"Bounded" describes how work and memory are organized. It is not a hard token
ceiling, automatic truncation, or a guarantee that every task fits any model.
Genuinely active work still needs enough context, and changes crossing a
boundary still require downstream reconciliation.

Finishing a milestone therefore shrinks what the next one has to read, without
discarding anything.

## Lessons worth keeping

Retiring task history raises another question: which parts should remain close
to the next task?

`memory-bank/lessons.md` holds curated, applicable learning with rationale and
evidence. Useful lessons describe something a future agent should account for,
such as an ownership constraint or a failure mode whose cause was easy to miss.

Consider an order-total implementation. Its completed milestone contains all
the task notes and test results. The enduring lesson might be that tests using
only single-unit orders concealed a quantity bug, so future pricing tests need
multi-unit cases. With a link to that evidence, the lesson can stay active after
the detailed milestone record retires.

Duplicate lessons are merged. Before materially superseding a fact or lesson,
the workflow preserves its old wording, source, reason for change, and
replacement in `docs/history/knowledge.md`. Routine wording edits need no
journal entry.

This gives current knowledge and historical knowledge different jobs. The next
agent can learn the rule that applies now and, when necessary, trace why it
changed. It need not reconstruct that answer from a lifetime of conversation.

## Upgrading an existing project

Installing newer skills cannot safely rewrite every project that used an older
version. Those projects have their own commands, policies, plans, and history.

The new `memory-bank-upgrade` skill compares an existing project's adopted
workflow with the reference template bundled inside the skill. It identifies
missing rules, compatible local equivalents, deliberate exclusions, and
conflicts requiring a decision. It then presents specific file actions for
approval before writing.

A useful request is:

```text
Use memory-bank-upgrade to compare this project's workflow with the bundled
contract. Preserve our plans, local policies, task states, IDs, review counts,
and history. Show the complete proposed file changes before writing.
```

After approval, the agent applies the scoped merges and verifies preservation.
Existing task tables, completed evidence, custom goal protocols, and frozen
history are protected. Already compatible projects need no changes.

An upgrade adopts operating rules. Implementation and retirement of older
milestones require their own scope and evidence. A separately installed API
runner also needs a separate compatibility check or update.

The [upgrade guide](https://github.com/tabilet/skills/blob/v1.3.0/README.md#upgrade-an-existing-project)
explains that transition. It is especially useful for adopting lessons and
retirement in a project that already has months of history.

## Another runtime

Version 1.3.0 adds documented integration with **DeepSeek Harness, or DSH**,
through its existing filesystem skill loader.

The same six complete skill directories go into `$DSH_HOME/skills`, normally
`~/.dsh/skills`. Supporting references stay inside their bundles. DSH supplies
the runtime; the project keeps the same Markdown format and engineering
contracts.

Web provides an interactive route for discovery, proposals, and separate
approvals. Headless execution accepts a complete authorized request and must
stop safely when a required answer, file, verification command, or permission
is missing. A successful process exit can still leave an unfinished milestone.

Native todos and native goals can help a runtime maintain continuity. Acceptance
still comes from the project's requirements, actual verification, and review
evidence. One active ledger has one execution owner, even when several sessions
or launchers are available.

The tested DSH configuration is **0.1.5-rc.1 on Linux with Node 24**. It covers
the Web and headless profiles; rendered UI and native question-card interaction
remain untested. This release makes no Antigravity-specific compatibility claim.

Use the [DSH integration guide](https://github.com/tabilet/skills/blob/v1.3.0/docs/DSH.md) for installation, backups,
updates, removal, and the full acceptance record. It also distinguishes the
runtime integration tests from the live workflow tests.

## Clearer instructions

The [OpenAI article](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
recommends concise selection descriptions, loading supporting
instructions when relevant, revisiting accumulated rules, and making completion
and permission boundaries clear. Those ideas are useful to a portable skill
package even when its users run different models.

The v1.3.0 review applied them to the actual memory-bank contracts. Across six
skills, the selection descriptions shrank from **267 to 124 words**. The main
goal skill shrank from **1,013 to 557 words**, including frontmatter. Optional
invocation and runtime help moved into a bundled reference, while the project
protocol continues to own execution sequencing.

Timing matters as much as length. Init, archive, and reconcile now read their
write contracts before preparing proposals, so the proposed files and formats
can be correct before approval. That inspection grants no writing authority.

After approval, the instructions tell the agent to carry the approved work
through verification and handoff. It should ask again for a new conflict or an
unapproved change, rather than repeatedly asking about the same authorized
action. A missing capability blocks the dependent step; independent authorized
inspection can continue.

Upgrade proposals also favor focused section diffs over repeating unchanged
documents. These changes make the instructions easier to apply at the moment
the agent must decide what to read, what to change, or where to stop.

## Persistence across sessions

The release also tightens several small rules with large consequences.

An agent resumes the sole in-progress row before selecting another. Consumed
or superseded historical rows remain evidence and are never retried. When an
implementation invalidates a current product or architecture fact, the same
task corrects it, even if a later documentation task exists.

The milestone review gate retains its iteration count across interruptions and
reviewers. The initial full review is iteration 1; serious fixes require
verification and another full milestone review. A clean pass is required within
ten iterations. Starting another session does not reset that allowance.

When the project has a compatible approved `GOAL.md`, initialization can create
`memory-bank/suggested.txt`, and reconciliation can refresh it. This is disposable
launch input, checked against the current plan before use. Without that protocol,
the workflows omit the suggestion; one-task execution remains available. The
milestone and status files continue to own the plan.

Commit policy remains explicit. Ordered execution can use task commits or an
authorized no-commit policy. Runtime completion cannot invent acceptance or
permission to publish, deploy, or begin a different workflow.

These rules make session boundaries survivable. The next agent can establish
what was selected, what passed, and what remains unfinished from project state.

## What the tests showed

For this version, **30 repository checks** and **13 credential-free DSH tests**
passed. The DSH tests exercise the real loader and check what survives
installation, updates, removal, and duplicate installations.

Eight live scenario groups covered initialization, archive preflight, review
reconciliation, task resumption, ordered goals, memory retirement and retrieval,
safe stopping, and project upgrades. The tests inspected file hashes, Git
history, task rows, verification results, and observed tool calls.

The failures were useful. An archive proposal confused planned behavior with
current behavior. An initialization proposal invented a hypothetical future
blocker. Both prompted narrow instruction corrections and fresh checks.

One no-commit goal claimed completion with a duplicate history-index link. An
independent parser caught it, and an explicitly prompted closure continuation
repaired the maintained document while preserving frozen history. That result
is recorded as an assisted pass.

The wording comparisons were similarly mixed: both description versions scored
12/12 on small selection probes; upgrade proposals became shorter, while
reconciliation proposals became longer. Smaller instructions did not establish
a universal reduction in response length or cost.

All 672 paid requests, including failed attempts and reruns, stayed within the
US$10 test ceiling. Conservative accounting was **US$6.19**; pricing the observed
DeepSeek usage with cache hits estimated **US$0.57**, not an invoice. That is
also a concrete reminder that API economics vary substantially by model and
workload. These live tests used `deepseek-flash`, not GPT-6 Astra. The
[acceptance report](https://github.com/tabilet/skills/blob/v1.3.0/docs/DSH.md#acceptance-evidence)
records the scope and limitations.

## Getting started

Update the six complete skill bundles using the
[maintained installation guide](https://github.com/tabilet/skills#install-the-six-skills).
Then use `memory-bank-upgrade` to review the project rules you want to adopt.
Approve the specific merges, inspect the result, and resume work from the
existing plan. Older milestones need a separate retirement request and enough
closure evidence to justify it.

If you are starting with a broad codebase that has no harness, the
[previous article's archive-and-initialize route](https://medium.com/@peterbi_91340/manage-existing-codebase-using-agentic-engineering-harness-c362f556f96f)
still applies. A small coherent project can initialize directly.

As agents improve, I want more of my attention on the product and its
engineering decisions, and less on steering the tool. The project holds the
facts, the learning, the boundaries, and the acceptance evidence that make those
decisions possible. The agent does the work.

So point your agent at the upgrade skill, approve the merges you want, retire a
milestone you have already finished, and see how much of your instruction file
you no longer need.
