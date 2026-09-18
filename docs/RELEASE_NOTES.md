# memory-bank v1.5.0

The seventh skill, `memory-bank-propose`, turns a requested feature, candidate
promotion, or future direction change in an initialized project into approved
planning updates. It asks only consequential questions, presents one complete
approval request, and rechecks affected files and permanent IDs before writing.
It does not implement, commit, retire, or launch execution. Init and Propose
share focused discovery guidance; Propose and Reconcile share plan-update
safeguards in byte-identical bundle-local references. The template gains a
portable requested-change procedure; existing projects adopt it explicitly.

The DSH companion prepares Propose requests from one required multiline field
using the existing draft guards. Website guidance and the banner include the
seventh skill. Structural and model-free checks verify packaging and integration,
not autonomous planning quality. No paid acceptance was run.

The v1.5.0 plugin and companion ship seven skills. Install from the v1.5.0 tag
and the companion's matching prebuilt GitHub archive. Existing projects keep
their local rules until an approved Upgrade adopts the new procedure.

# memory-bank v1.4.0

v1.4.0 keeps the six canonical skills, project format, and Python harness shared
across agents, and adds conformance fixtures for read-only integrations. The
separate [tabilet-skills repository](https://github.com/tabilet/tabilet-skills)
owns the installable DSH companion, native Memory Bank views, and workflow request
preparation. See [both installation routes](DSH.md#install-the-dsh-companion).

The companion pins this repository's immutable release commit and payload hashes.
Its Web and headless targets use Linux, Node 24.14.1, and locked DSH rc.2
components; an isolated rc.1 launcher with rc.2 components is also checked. This
repository retains the existing all-rc.1 compatibility suite and standard-library
Python checks. Skill semantics and project contracts are unchanged from v1.3.0;
no new paid live runs are part of v1.4.0 acceptance.

Installing or updating either route does not migrate projects. Existing compatible
projects work directly; adopt newer rules through an approved Upgrade proposal.
The sidebar reads project Markdown and prepares conversation drafts. It does not
write task state, approve work, submit requests, or establish milestone acceptance.
Removal leaves project memory and the direct filesystem route available.

Canonical GitHub publication, companion GitHub/npm publication, catalog submission,
and accepted market listing are separate gates. Consult the companion's
[release record](https://github.com/tabilet/tabilet-skills/blob/main/docs/ACCEPTANCE.md)
for their actual state. The existing Medium drafts remain scoped to v1.3.0.

# memory-bank v1.3.0

v1.3.0 adds curated lessons, frozen milestone history, and approved project-rule
upgrades. It supports DSH through six portable skills and hardens interrupted
workflows and acceptance checks. Projects continue to own their Markdown files; updates do not migrate
existing instructions or history automatically.

## Long-term memory

- Keep applicable, evidence-linked learning in `memory-bank/lessons.md`.
  Preserve materially superseded knowledge in the append-only
  `docs/history/knowledge.md` journal.
- After verification, the bounded review gate, consolidation, and downstream
  reconciliation, retire a milestone's complete specification and status into
  a frozen `docs/history/status-<LANE><NN>.md` record.
- Reserve IDs across active and retired storage. An all-retired project stays
  initialized; stale goal paths resolve through history without retrying old
  tasks. Cancelled or superseded outcomes are not proof of delivered acceptance.

## DSH integration

- Install all six complete bundles through DSH's existing filesystem loader.
  The primary destination is `$DSH_HOME/skills`, defaulting to `~/.dsh/skills`;
  documented installation, update, and removal preserve unrelated content.
- Use `/memory-bank-*` or ordinary-language requests. Web supports interviews
  and separate workflow approvals; headless supports fully authorized work and
  safe stopping when a required answer or capability is absent.
- Tested configuration: DSH **0.1.5-rc.1**, Linux, Node **24.14.1**, with all DSH
  components and dependencies locked in the separate compatibility suite.
  SDK, ACP, minimal profiles, other platforms, and older DSH versions are outside
  this tested scope. Claude Code and Codex retain their existing invocation forms.

## Workflow and runner hardening

- Goal order and policies come from the invoking request, without runtime
  argument substitution. Explicit input overrides disposable suggestions.
- Missing files, verification, permissions, or required answers stop the affected
  step; independent authorized work can continue and the step resumes when its
  requirement is restored. Session completion, native goals, and native todos do not establish
  milestone acceptance or authorize another ledger writer.
- Interrupted review and closure resume from persisted state. The ten-iteration
  review counter does not reset across sessions.
- Initialization evaluates the selected boundary's independent contexts before
  planning, reuses supplied decisions, and asks about consequential choices.
  It keeps planned behavior separate from current facts and allocates blocker
  rows only for actual blockers.
- Init, archive, and reconcile load their write contracts before proposing file
  actions. Approval still gates writes; approved work continues through checks
  and handoff without asking for the same approval again.
- Shorter skill descriptions clarify selection. The goal skill delegates to
  the canonical protocol and loads bundled invocation/runtime help only when
  needed. Upgrade proposals prefer focused section diffs and preserve local
  conventions and exclusions.
- A task corrects invalidated current memory facts in the same change, including
  when a later documentation row remains pending.
- Retirement validates full Git evidence IDs, the record envelope, and retained
  source documents before removing active sources.
- The standard-library API runner rejects malformed or empty active status
  files, invalid IDs, missing required instructions, incomplete retirement, and
  rewritten history. Valid all-retired state is recognized without a model call.
  Active milestones without status records are rejected even before the first
  retirement, and required instructions are checked again after every run.

## Upgrading from v1.2.0

The new sixth command, `memory-bank-upgrade`, compares an existing project's
rules with its bundled template, proposes specific merges for approval, then
applies the approved changes. It preserves tasks, permanent IDs, local policies,
review counters, and frozen history; it does not execute work or bulk-retire
milestones. Already compatible projects are unchanged. See the
[project-upgrade procedure](../README.md#upgrade-an-existing-project).

1. Update the installed skill bundles using the maintained installation guide.
   Preserve their supporting references and init's bundled protocol.
2. Review project instructions and the new template contracts before explicitly
   adopting lessons or retirement. Preserve existing plans, permanent IDs,
   evidence, and frozen archives. Do not bulk-copy templates over a live project
   or reinitialize an existing harness.
3. If using the API runner, update that separately installed executable before
   adopting retirement. A plugin or skill update does not replace the runner.
   Correct malformed status rows and missing project instructions before running
   the stricter checks; failed validation is not evidence that the work is done.
4. Update an existing project goal protocol only as a reviewed, explicit project
   change. The six task markers and commit-policy meanings remain unchanged;
   retirement adds a storage lifecycle, not another task marker or skill.

## Verification

- All **30 repository checks** pass for the prepared release snapshot.
- All **13 credential-free DSH compatibility tests** pass with locked dependencies.
- All **eight live scenario groups**, including project upgrade, were rechecked
  after the instruction review using DeepSeek `deepseek-flash`. Final artifacts
  pass after the recorded corrections, including one assisted closure repair.
  All 672 requests include failed attempts, comparisons, and reruns: estimated
  usage cost **US$0.57**, conservative accounting **US$6.19** against the
  **US$10** ceiling. Description-selection probes scored 12/12 for both baseline
  and candidate; smaller instructions did not uniformly shorten model responses.
- Web workflows were exercised through the actual profile's authenticated
  browser-facing endpoints; visual UI and native question-card interaction were
  not tested. Live acceptance
  used disposable projects, and paid tests never run automatically on pull
  requests.

See [installation and update instructions](../README.md#install-the-six-skills),
the [DSH integration and acceptance report](DSH.md), the
[use-case guide](USE_CASES.md), and [runner behavior](EXECUTION.md).
