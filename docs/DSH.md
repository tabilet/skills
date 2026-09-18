# DSH integration

DSH supplies the agent runtime, tools, permissions, and session persistence.
Memory-bank supplies the project's engineering workflow: approved scope,
permanent task identities, verification, review, and retained evidence. The same
six skill bundles and project Markdown work through the direct filesystem
installation without a companion plugin or DSH-specific project files.

v1.4.0 adds a separate optional
[DSH companion](https://github.com/tabilet/tabilet-skills). This repository
continues to own the canonical skills, portable project contract, and Python
runner. The companion owns packaging, its read-only sidebar, and conversation
request preparation. Both use the same project files; there is no second ledger.

## Install the DSH companion

The companion's v1.4.0 target is Linux, Node **24.14.1**, and DSH **0.1.5-rc.2**
with a locked dependency graph. An isolated rc.1 launcher with rc.2 components
is a separate acceptance target. The all-rc.1 tests and v1.3.0 live evidence in
this guide remain scoped to their original configuration.

Check the companion's
[acceptance and publication record](https://github.com/tabilet/tabilet-skills/blob/main/docs/ACCEPTANCE.md)
for artifact identities and the distinct **published**, **catalog submission
pending**, and **listed** states. Install the published prebuilt GitHub archive
in each profile where it is wanted. For Web:

```bash
dsh plugin --profile web add \
  https://github.com/tabilet/tabilet-skills/releases/download/v1.4.0/tabilet-skills-1.4.0.tgz \
  --ignore-scripts
```

For headless, use the same command with `--profile headless`. The GitHub archive
does not require an npm account or a marketplace listing. npm publication and
catalog acceptance are separate release gates; consult the release record
before using an npm package name or relying on market search.

Restart that profile. Web exposes **Memory Bank** in the native right sidebar;
headless exposes the six skills without needing the UI. The package ships
prebuilt output and complete skill resources pinned by upstream commit and
hashes. It has no install scripts and bundles no DSH runtime. Direct filesystem
installation remains supported and does not depend on the companion.

The panel reads the selected session's project through DSH's file interfaces.
It uses change observations and a five-second visible refresh cycle, rechecks on
focus, and offers manual refresh. It reports incomplete reads, denied canonical
paths, malformed markers, duplicate identities, and multiple in-progress rows.
Historical bodies load only when opened. Recorded evidence and explicit review
counters remain separate from task-marker counts; terminal rows do not prove
milestone acceptance. Documents render as literal text without active HTML or
automatic external resources.

Shortcuts preview requests for all six skills. Goal requires explicit milestone
order, completion conditions, and commit policy; its visible default is `task`
and requests include `EXTERNAL_MUTATIONS: none`. Reconcile treats a review path
or URL as request text and preserves its separate remote-fetch confirmation.
Insertion requires the same session and unchanged empty plain-text draft with
no attachments; otherwise the user can copy the preview. The user sends normally.
No button submits, approves, edits status, or starts another ledger writer.

The bundle's filesystem provider has default-root discovery disabled and runs at
bundled priority. Project/user overrides retain their normal precedence. The
Compatibility view reports winning sources and known shadowing; review duplicates
before assuming an update is active. A task marker does not prove exclusive
ownership. Existing compatible projects work directly; adopting newer rules is
an explicit `memory-bank-upgrade` workflow, never an installation side effect.

To roll back, disable the companion row in the selected profile or run
`dsh plugin --profile web remove tabilet-skills` (and separately for headless).
Project records, unrelated configuration, and direct filesystem skills remain.

## Support boundary

The direct filesystem route was verified against **DSH 0.1.5-rc.1 on Linux with
Node 24**, using **Web** for interactive work and the **headless** one-shot
profile for fully authorized requests or safe stopping. Credential-free
integration and live workflow acceptance are separate gates; see [acceptance evidence](#acceptance-evidence)
for the observed results and remaining limitations. SDK, ACP, minimal profiles,
other platforms, and older releases are not certified here.

DSH integration is included in **memory-bank v1.3.0**. Use a v1.3.0-or-newer
checkout containing this guide. Before publication, use the reviewed release
working tree; marketplace installs and `main` downloads contain only changes
already published there. See the [release notes](RELEASE_NOTES.md) for upgrade
guidance and the [project-upgrade procedure](../README.md#upgrade-an-existing-project).
Updating installed skills does not migrate existing `AGENTS.md`,
goal protocols, memory banks, lessons, or histories. Adopt project lifecycle
changes explicitly; see [long-term memory](../README.md#keep-long-term-memory-without-growing-the-active-plan).

Prerequisites are Bash, Git for workflows that commit, Node 24, and a separately
installed DSH runtime. Repository Python checks need only the standard library.
The [locked test installation](#credential-free-verification) provides a local
DSH executable without changing a global installation. Do not assume the
launcher's version proves all component versions: upstream dependency ranges
can resolve newer prereleases. Our test manifest pins every DSH component and
the lockfile fixes the remaining dependency graph.

The upstream [filesystem loader](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.5-rc.1/packages/skill/skill-filesystem/README.md)
and [CLI entry modes](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.5-rc.1/apps/cli/README.md)
describe the runtime contracts used here. Installation is a directory copy;
DSH does not consume this repository's plugin manifest.

<a id="install-the-five-bundles"></a>

## Install the six bundles

The primary destination is `$DSH_HOME/skills`, defaulting to `~/.dsh/skills`.
Set `MEMORY_BANK_CHECKOUT` to the absolute release checkout path. Run the
following in Bash. It checks all destinations first, copies entire directories,
and treats an identical repeat installation as a no-op. A differing existing
bundle or a symlink stops installation; use the update procedure after reviewing
the existing content. Stop running sessions before changing installed bundles.

```bash
export MEMORY_BANK_CHECKOUT=/absolute/path/to/skills
```

<!-- dsh-install -->
```bash
(
  set -euo pipefail
  : "${MEMORY_BANK_CHECKOUT:?Set the absolute release checkout path}"
  dsh_skill_root="${DSH_SKILL_ROOT:-${DSH_HOME:-$HOME/.dsh}/skills}"
  bundles=(memory-bank-archive memory-bank-init memory-bank-upgrade memory-bank-reconcile memory-bank-next memory-bank-goal)
  for bundle in "${bundles[@]}"; do
    test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/SKILL.md"
    case "$bundle" in
      memory-bank-archive|memory-bank-init|memory-bank-reconcile)
        test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/references/write-contract.md" ;;
    esac
    if test "$bundle" = memory-bank-init; then
      test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/GOAL.md"
    fi
    if test "$bundle" = memory-bank-goal; then
      test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/references/runtime-help.md"
    fi
    if test "$bundle" = memory-bank-upgrade; then
      for resource in AGENTS.md GOAL.md memory-bank/{product,architecture,tech-stack,lessons,milestone,status-M01}.md evolution/{prompt-v1,result-v1}.md; do
        test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/assets/template/$resource"
      done
    fi
    target="$dsh_skill_root/$bundle"
    if test -L "$target"; then
      echo "Refusing symlink: $target" >&2; exit 1
    fi
    if test -e "$target" && ! diff -qr "$MEMORY_BANK_CHECKOUT/skills/$bundle" "$target" >/dev/null; then
      echo "Existing content differs: $target. Review and use the update procedure." >&2; exit 1
    fi
  done
  mkdir -p "$dsh_skill_root"
  for bundle in "${bundles[@]}"; do
    if ! test -e "$dsh_skill_root/$bundle"; then
      cp -R "$MEMORY_BANK_CHECKOUT/skills/$bundle" "$dsh_skill_root/$bundle"
    fi
  done
)
```

Copying only `SKILL.md` is incomplete. Initialization, archive, and reconciliation
have `references/write-contract.md`; initialization also carries the portable
`GOAL.md`. Upgrade carries `assets/template/`, a complete reference copy of the
project payload; preserve that tree too. Goal includes `references/runtime-help.md`
for invocation syntax and optional native continuation. DSH returns a skill's directory as its resource base. Relative
supporting resources resolve against that directory; project paths such as
`memory-bank/milestone.md` and the project's `GOAL.md` resolve in the selected
workspace. The init write contract explicitly identifies its bundled protocol.
Init, archive, and reconcile read their write contracts before preparing the
file-action proposal; approval gates writes, not those reads. Goal runtime help
is loaded only when invocation or continuation guidance is needed.

The shared agents directory is an alternative, useful when other agents should
see the same files. Before running any installation, update, or removal block,
set this override to select it:

```bash
export DSH_SKILL_ROOT="${DSH_AGENTS_HOME:-$HOME/.agents}/skills"
```

Omit that override for the primary DSH destination. Avoid installing the same
names in both places. For filesystem entries, lower ranks win:

| Rank | Root |
|---|---|
| 100 | Project `.dsh/skills` |
| 200 | Project `.agents/skills` |
| 300 | Configured custom skill roots |
| 400 | `$DSH_HOME/skills` (default `~/.dsh/skills`) |
| 500 | `$DSH_AGENTS_HOME/skills` (default `~/.agents/skills`) |
| 600 | Configured bundled root |

The project root is the nearest `.git` ancestor, or the lookup working directory
without Git. DSH also supports runtime providers; a runtime registration can
outrank user roots. A higher-priority stale or customized copy shadows an
updated user bundle. Inspect every root before deciding an update failed.

## Update or remove

Review the six named destinations first: these commands assume they are the
memory-bank bundles you intend to replace or remove. Save any local edits you
want to merge into the new source. Updates back up complete old bundles outside
the scanned skills root, then copy the complete candidate bundles, removing
obsolete bundle resources from the live installation. Unrelated skills and
content elsewhere in the DSH home are preserved.
Preflight requires each installed bundle's frontmatter to name the expected
command and each source bundle to contain its required supporting files. A
mismatched or unrecognizable command name stops the operation for inspection.
Missing destinations are added from the new checkout, so the same update block
adds `memory-bank-upgrade` to an earlier five-bundle installation. Existing
bundles are backed up before any replacement is copied.

<!-- dsh-update -->
```bash
(
  set -euo pipefail
  : "${MEMORY_BANK_CHECKOUT:?Set the absolute release checkout path}"
  dsh_skill_root="${DSH_SKILL_ROOT:-${DSH_HOME:-$HOME/.dsh}/skills}"
  bundles=(memory-bank-archive memory-bank-init memory-bank-upgrade memory-bank-reconcile memory-bank-next memory-bank-goal)
  for bundle in "${bundles[@]}"; do
    test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/SKILL.md"
    case "$bundle" in
      memory-bank-archive|memory-bank-init|memory-bank-reconcile)
        test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/references/write-contract.md" ;;
    esac
    if test "$bundle" = memory-bank-init; then
      test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/GOAL.md"
    fi
    if test "$bundle" = memory-bank-goal; then
      test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/references/runtime-help.md"
    fi
    if test "$bundle" = memory-bank-upgrade; then
      for resource in AGENTS.md GOAL.md memory-bank/{product,architecture,tech-stack,lessons,milestone,status-M01}.md evolution/{prompt-v1,result-v1}.md; do
        test -f "$MEMORY_BANK_CHECKOUT/skills/$bundle/assets/template/$resource"
      done
    fi
    test ! -L "$dsh_skill_root/$bundle"
    if ! test -e "$dsh_skill_root/$bundle"; then continue; fi
    test -f "$dsh_skill_root/$bundle/SKILL.md"
    test ! -L "$dsh_skill_root/$bundle/SKILL.md"
    awk -v expected="$bundle" '
      NR == 1 { if ($0 != "---") exit; next }
      $0 == "---" { closed = 1; exit }
      /^name:/ { valid = ($0 == "name: " expected) }
      END { exit !(valid && closed) }
    ' "$dsh_skill_root/$bundle/SKILL.md"
  done
  backup_root="${DSH_HOME:-$HOME/.dsh}/skill-backups"
  mkdir -p "$backup_root"
  backup_dir="$(mktemp -d "$backup_root/memory-bank.XXXXXXXX")"
  echo "Bundle backup: $backup_dir"
  for bundle in "${bundles[@]}"; do
    if test -e "$dsh_skill_root/$bundle"; then
      mv "$dsh_skill_root/$bundle" "$backup_dir/$bundle"
    fi
  done
  for bundle in "${bundles[@]}"; do
    cp -R "$MEMORY_BANK_CHECKOUT/skills/$bundle" "$dsh_skill_root/$bundle"
  done
)
```

If copying is interrupted, keep sessions stopped. Compare the backup with the
live paths and restore or finish the six bundles before starting DSH again.
Never run two install/update operations on the same root simultaneously.
Backups preserve local edits but do not merge them automatically.

Removal moves only those six bundles into a retained backup; it deletes no
project memory, credentials, configuration, or unrelated skills. Missing bundles
are harmless. A same-name file or symlink requires manual inspection.

<!-- dsh-remove -->
```bash
(
  set -euo pipefail
  dsh_skill_root="${DSH_SKILL_ROOT:-${DSH_HOME:-$HOME/.dsh}/skills}"
  bundles=(memory-bank-archive memory-bank-init memory-bank-upgrade memory-bank-reconcile memory-bank-next memory-bank-goal)
  for bundle in "${bundles[@]}"; do
    target="$dsh_skill_root/$bundle"
    test ! -L "$target"
    if test -e "$target"; then
      test -f "$target/SKILL.md"
      test ! -L "$target/SKILL.md"
      awk -v expected="$bundle" '
        NR == 1 { if ($0 != "---") exit; next }
        $0 == "---" { closed = 1; exit }
        /^name:/ { valid = ($0 == "name: " expected) }
        END { exit !(valid && closed) }
      ' "$target/SKILL.md"
    fi
  done
  backup_root="${DSH_HOME:-$HOME/.dsh}/skill-backups"
  mkdir -p "$backup_root"
  backup_dir="$(mktemp -d "$backup_root/memory-bank-removed.XXXXXXXX")"
  echo "Removed bundles retained in: $backup_dir"
  for bundle in "${bundles[@]}"; do
    if test -e "$dsh_skill_root/$bundle"; then
      mv "$dsh_skill_root/$bundle" "$backup_dir/$bundle"
    fi
  done
)
```

Restart the session after install or update so it cannot reuse an already loaded
old body. DSH watches catalog changes, but a previously loaded skill remains in
that session's context, and edits within resource subdirectories do not refresh
the catalog. Removing a user bundle may reveal a lower-priority duplicate;
check discovery again before concluding it is gone.

## Web workflow

Run `dsh web` from the target project, then select or confirm that workspace in
Web before creating the session. For the locked test installation, replace
`dsh` with the absolute `tests/dsh/node_modules/.bin/dsh` path in your release
checkout. Use a fresh session to inspect the skill menu and load a skill.

| Work | DSH session request |
|---|---|
| Map a broad package | `/memory-bank-archive` |
| Initialize | `/memory-bank-init` |
| Upgrade project rules | `/memory-bank-upgrade` |
| Reconcile a local review | `/memory-bank-reconcile review.md` |
| Execute one row | `/memory-bank-next` |
| Execute an explicit order | `/memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |

Ordinary language works too: “Use memory-bank-next to complete the next approved
row.” DSH supports user invocation and model discovery for these bundles. Skills
still need filesystem, shell, and any required verification capabilities. Check
the selected workspace and its `AGENTS.md`; DSH's native task list does not
replace the status ledger.

Use Web to answer initialization's frontier questions and approve the complete
boundary, milestone, and file-action proposals. Archive requires its approved
context map and clean baseline; reconciliation requires approved dispositions
before writes and separate confirmation of the exact URL before every remote
review fetch, even when the original request supplied it. Keep decisions in the
session until approved file actions make them project truth.

After a skill update, use `/memory-bank-upgrade` to compare an existing project's
rules with its bundled contract. Review and approve its precise merges in Web;
the skill preserves task tables, IDs, local policies, review counters, and frozen
history. It does not initialize a replacement bank or retire old milestones.
Already compatible projects are unchanged. A headless continuation needs the
exact approved proposal, just like the other write-gated workflows.

Runtime permission approvals and workflow approvals serve different purposes.
A tool may be available while a proposed file change still lacks user approval.
Conversely, an approved plan cannot bypass a denied filesystem or shell action.
DSH plan mode has its own approval mechanism; leave it through its supported UI
before an authorized write phase. If required questions or capabilities are
unavailable, stop the affected work and report what is missing.

## Headless workflow

The supported one-shot form creates a fresh persisted session and exits after
the agent becomes idle:

```bash
cd /absolute/path/to/project
dsh --profile headless 'Use memory-bank-next. The existing plan and next dependency-ready task are approved. Resume the sole in-progress row first. Verify using AGENTS.md, then make the scoped task commit. No external mutations. If an answer, approval, permission, file, or verification capability is missing, stop and report the exact blocker; do not infer approval.'
```

For an ordered run, supply the resolved request with its explicit policies and
acceptance. Example after the project has approved this order:

```bash
dsh --profile headless 'Use memory-bank-goal. Using GOAL.md, execute STATUS_ORDER: M01 -> M02. COMMIT_POLICY: none. EXTERNAL_MUTATIONS: none. Completion condition: both milestones meet their documented acceptance, verification, review, and closure requirements. Stop if any required answer or capability is unavailable.'
```

Replace these IDs and approvals with actual project decisions. A blanket
“approve everything” cannot stand in for an unseen init/archive/upgrade/reconcile
proposal or the separate remote-fetch confirmation. A new headless session does
not inherit a Web conversation: provide the exact previously approved proposal,
answers, and scope if continuing a write phase. If new decisions arise, return
to Web. Do not restart an unanswered interview repeatedly.

**Exit status alone is not milestone acceptance.** Even exit 0 can accompany a
plain-text question or an explanation of incomplete work. Inspect the generated
diff, status and history records, actual checks, review count, and remaining
blockers. A question tool or runtime permission request may leave the process
waiting; bound unattended invocations with an operator timeout and retain the
session evidence before resuming. A timeout or process exit grants no approval.
The optional Python API runner has different gates and exit codes; its commit
requirement does not apply to DSH's headless profile.

## Goals and execution ownership

DSH's native `/goal` can continue the same Web session. It supports status with
`/goal`, plus `pause`, `resume`, `clear`, and `edit <objective>`. Supply the
complete protocol request as the objective only when you intend to use
[GOAL.md](../GOAL.md):

```text
/goal Using GOAL.md, execute STATUS_ORDER: M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none. Completion condition: both required milestones meet their acceptance, verification, and bounded review gates, with downstream reconciliation and adopted retirement complete.
```

The [native goal service](https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.1.5-rc.1/packages/goal/goal)
owns runtime continuation. Its `maxGoalRounds` limit is separate from the
**persisted 10-iteration milestone review counter**. A round can contain many
model requests and tools; it is not a dollar budget. Resuming a session or goal
does not reset the review counter. DSH completion messages, todos, and goal state
are not acceptance evidence. Terminal task markers also cannot conceal an
unfinished milestone review or closure.

Use one execution owner for the active ledger, including Web, headless, the API
runner, and any other agent. Stop or pause the current owner before handing work
to another session, and wait for its current turn and tools to stop writing.
Pausing future goal rounds alone does not end an already running task.
No second writer is authorized by a native todo setting or
an idle UI. A selected `[~]` row records ownership, not external-mutation rights.

## Troubleshooting

| Symptom | Check |
|---|---|
| Missing skill | Confirm workspace, root, directory depth, valid frontmatter, and loader warnings. There must be one `<root>/<name>/SKILL.md` per bundle. |
| Unexpected skill version | Inspect higher-priority project/custom/runtime roots and duplicate names. Restart the session after updating. |
| Body loads, write phase fails | Check the full `references/` directory and init's bundled protocol. Resolve resources against the reported skill directory. |
| Resource reads work but shell cannot find a temporary skill path | Linux's bwrap workspace-write sandbox mounts a private `/tmp`. For isolated tests, put `DSH_HOME` outside `/tmp`, such as a fresh directory under `/var/tmp`; preserve the sandbox policy. |
| Read, shell, or verification denied | Use the approved runtime permission path or stop with the missing capability; never silently widen permissions. |
| Headless exits without completing | Inspect questions, blockers, tool results, and project acceptance; stdout and exit status describe the session only. |
| Review seems to restart at 1 | Read the stored review count, resume the interrupted iteration, and keep runtime rounds separate. |
| Old status path is missing | Resolve its permanent ID through the history index; never reinitialize an all-retired project or retry history. |
| Cancelled/superseded prerequisite | Follow its authorized disposition and accepted successor; it is not proof of delivered acceptance. |

## Credential-free verification

From the release checkout:

```bash
python3 check.py
npm ci --prefix tests/dsh --ignore-scripts --no-audit --no-fund
npm test --prefix tests/dsh
```

The separate DSH CI job installs the locked runtime and uses its actual
filesystem provider and registry. It exercises the installation snippets above
in disposable directories, validates full bodies, invocation policy, relative
resources and protocol bytes, and checks duplicate precedence. It requires no
provider credential and never calls a paid model. Python verification does not
install or require Node dependencies.

## Live acceptance procedure

Live tests are explicitly invoked by a human; they never run automatically on a
pull request. Use disposable projects with no Git remotes or production data.
Use separate `DSH_HOME` and `DSH_AGENTS_HOME` directories, a sanitized process
environment, and disable telemetry. Keep transcripts and generated projects
outside this repository's shipped payload. Do not copy personal configuration
wholesale or expose unrelated credentials to model-controlled tools.
On Linux with bwrap, place the isolated `DSH_HOME` outside `/tmp` so shell
commands can read the same bundled resources as the filesystem tools. A project
under `/tmp` remains accessible through its workspace mount.

Before the first paid request, require a test credential with an enforceable
**US$10 total ceiling**, current provider rates, and conservative accounting for
input, uncached tokens, output, reasoning, retries, and auxiliary requests.
Reserve the worst-case next request cost before dispatch and stop if the
remaining allowance cannot cover it. Runtime rounds, token meters, timeouts,
and a model's promise to stay under budget are insufficient cost controls.
Missing credentials, unavailable budget controls, or exhausted funds leave live
acceptance incomplete; never silently substitute a free loader test for it.

Run each scenario with bounded sessions and preserve before/after files and
commands. Grade artifacts and observed behavior, including denied actions:

| Scenario | Required evidence |
|---|---|
| 1. Small existing project | Original instructions survive init; approved boundary, rows, and verification match the repository. |
| 2. Broad package | Topology gate, approved archive proposal, every context verified, frozen bytes preserved by subsequent init. |
| 3. Review reconciliation | No writes before approval; complete dispositions; no implementation; no remote fetch before separate exact-URL confirmation. |
| 4. One row and resumption | One scoped task, sole `[~]` resumed, historical rows never retried; verification and commit inspected. |
| 5. Ordered goals | Both `task` and `none` policies; downstream specs reconciled; interrupted review counter persists across continuation. |
| 6. Long-term memory | Curated lessons, preserved superseded knowledge, full frozen retirement, evidence retrieval, and all-retired identity. |
| 7. Headless stopping | Missing approval, question channel, files, verification, or permission leaves affected work incomplete without invented consent. |
| 8. Project upgrade | No writes before proposal approval; approved rule merges preserve tasks, IDs, custom protocols, review counts, and frozen evidence. Repeat and all-retired upgrades are safe, and missing approval stops headless writes. |

For every paid run record runtime and component versions, model/provider,
scenario, observed results, usage, conservative reserved cost, actual billed cost
when available, cumulative spend, and residual failures. A final review must
have no unresolved P1/P2-or-higher findings before certification.

## Acceptance evidence

All eight live scenario groups were exercised again after the skill instruction
review. The [latest results](#skill-instruction-revision-acceptance) include
initial failures, corrections, and an assisted closure repair. Earlier runs are
retained below as historical evidence. This is bounded candidate acceptance, not
a release or a guarantee for other models, projects, or runtime versions.

Verified on 2026-09-12 in Linux 7.0.0-28-generic, Node 24.14.1, npm 11.18.0,
and Python 3.14.4. The test installation locks all 231 DSH components to
0.1.5-rc.1 (Cordis 4.0.2; 520 installed packages in total). The source tag is
`dsh-v0.1.5-rc.1`, commit `183f08e9c6dde7e36cd2318eaee70b0da08fb35e`.

| Gate | Observed result |
|---|---|
| Repository checks | All 30 checks pass in the prepared release snapshot, including lifecycle behavioral tests, protocol copies, links, commit-policy examples, and resource-loading contracts. `git diff --check` passes. At live-test time the source version check reported v1.2.0 at HEAD versus the uncommitted v1.3.0 manifest; the isolated release snapshot verified the matching version/tag state. |
| Actual DSH loader | All six complete bundles load; invocation policy, slash-request preservation, relative contracts, and bundled protocol bytes pass. |
| Locked installation and integration | All 13 DSH tests pass: repeat install, backed-up update/removal, interrupted-update recovery, unrelated content, symlink rejection, duplicate precedence, resources, and profile composition. The release review added bundle-identity and incomplete-source preflight regressions plus a five-to-six-bundle upgrade test to the original ten tests. |
| Credential-free headless launch | Actual headless profile exits 1 with `MISSING_CREDENTIAL`; disposable project bytes remain unchanged. This is runtime failure-path evidence, not a live scenario pass. |
| Live scenarios 1–7 | Final artifacts and tool histories pass the checks below. Latest reruns corrected archive/init proposals and required one explicitly prompted closure repair; first-attempt failures are not counted as passes. |
| Live scenario 8: project upgrade | Approved merges, preserved state, headless approval stop, and a fresh repeat no-op pass. The latest all-retired probe preserved every byte and identified no required merge, but offered optional additions and an unresolved optional scope decision. |
| Final scope review | Shared workflows, lifecycle implementation, tests, and public guidance reviewed after the live corrections. No unresolved P1/P2-or-higher finding in the changed scope. |

### Live environment and results

The provider was DeepSeek's official API, model ID `deepseek-flash`
(provider catalog: DeepSeek-V4.1-Flash). The initial session used high reasoning;
subsequent sessions used low reasoning. Requests ran from 18:48:55 to 19:06:12
UTC. Web used the actual `web` profile, standard agent preset, workspace
selection and skill catalog, and authenticated browser-facing HTTP endpoints
for requests and separate approval replies. No rendered-browser or visual UI
test was performed; this does not establish SDK or ACP support. Headless used
the actual one-shot CLI profile with complete authorized requests.

Every ledger had one execution owner. Different disposable projects had
independent sessions. Git fixtures had no remotes; the cancelled/superseded
outcome fixtures were explicitly unversioned. The isolated runtime used
workspace-write with runtime escalation disabled; the permission-denial fixture
used read-only. Workflow approvals were separate operator replies to concrete
proposals. No production data or personal configuration was loaded into the
test processes. Telemetry and auxiliary LLM titles were disabled.

| Scenario | Observed evidence |
|---|---|
| 1. Small existing project | Quill initialized after an explicit proposal approval. Original `AGENTS.md` text and source/test bytes survived; complete memory-bank/evolution files, valid status paths, and byte-identical bundled protocol were checked. An initial output-limit interruption was resumed without claiming success. |
| 2. Broad package | Parcel's catalog, orders, billing, and cross-cutting contexts received approved, full-commit-anchored, verified archives. Proposal stages made no writes. Subsequent approved initialization preserved all four archive hashes and original source/instructions, and merged current summaries. Archive/status `M01` overlap retained its independent namespaces and permanent ID. |
| 3. Review reconciliation | Confirmed arithmetic defect, duplicate planned work, unsupported allegation, and deferred lower-priority finding received distinct dispositions. Before approval the tree stayed clean. After approval only the four proposed planning files changed; implementation, tests, historical rows, and HEAD stayed unchanged. A supplied remote URL triggered separate exact-URL confirmation; no fetch occurred. |
| 4. One row and resumption | Resumed the sole existing `[~]` row, verified its behavior, corrected the invalidated current product fact, and made exactly one scoped commit. Historical `[-]` and remaining pending rows stayed byte-identical; the next row did not start. |
| 5. Ordered goals | Explicit `M01 -> M02` and policies overrode a stale reversed suggestion. `none` left HEAD unchanged; `task` produced two task commits and two substantive closure commits. M01 reconciled the pending M02 consumer before execution. A controlled interruption persisted review iteration 4 as started; a fresh headless continuation completed that same iteration, with 4 retained in its frozen record. |
| 6. Long-term memory | Current lessons became quantity-aware; the old literal wording, source, reason, and replacement survived in the knowledge journal. Both final goal fixtures passed the repository's actual retired-record parser and had no active status files. Retrieval and stale goal paths preserved every project-file hash. Init recognized all-retired identity. Additional cancelled and superseded milestone probes reported required acceptance incomplete without recreating history or executing an unauthorized successor. |
| 7. Headless stopping | Missing proposal approval, missing `GOAL.md`, missing required verification, and denied writes all stopped without project changes or commits. These live runs exited 0 while reporting incomplete work. The read-only denial caused no escalation attempt. |

### Usage and cost

All **259** paid requests, including failed acceptance attempts and reruns, are
included: **7,462,386 input tokens** (7,064,448 cache hits) and **186,491 output
tokens**, including 91,071 reasoning tokens. No provider request failed or
exceeded its reserved cost bound.

A local test-only gateway held the credential outside model-controlled process
environments and allowed only the approved model's chat-completion endpoint.
Before each request it reserved a conservative input-token bound (twice the
serialized UTF-8 payload bytes plus 8,192 framing tokens) and the maximum
completion allowance at peak, uncached rates. Output was capped at 8,192 tokens
initially, then 16,384. Reservations included concurrent requests; absent usage
would retain the entire reservation. Dispatch stopped before the US$10 total
allowance could be exceeded. Each headless process also had an eight-minute
timeout; the gateway allowed at most 600 requests. These are test controls,
not a shipped runtime wrapper.

At the verified [provider rates](https://api-docs.deepseek.com/quick_start/pricing),
the conservative charge treating every input token as uncached at peak rates
was **US$2.462505** against the **US$10** ceiling. The largest single request
reservation was US$0.213768. Usage priced with the observed cache hits and
Saturday off-peak rates estimates **US$0.192779**. The account balance endpoint
showed a rounded US$0.18 decrease; that account-wide snapshot is not a per-run
invoice, so exact billed cost remains unavailable. Rates used per million
tokens: peak uncached input/output US$0.30/US$1.20; off-peak uncached input,
cached input, and output US$0.15/US$0.003/US$0.60.

| Project / probe group, including reruns | Requests | Conservative charge (US$) | Usage estimate (US$) |
|---|---:|---:|---:|
| Small initialization and first row attempt | 39 | 0.367634 | 0.042490 |
| Broad topology, archive, initialization, namespace check | 35 | 0.435191 | 0.033199 |
| Review proposal, approved planning, remote-fetch stop | 13 | 0.116790 | 0.011863 |
| Initial no-commit goal, rejected retirement evidence | 26 | 0.266974 | 0.018389 |
| Corrected no-commit goal and stale-path retrieval | 43 | 0.409854 | 0.024406 |
| Task-policy checkpoint, continuation, retired-init retrieval | 63 | 0.672028 | 0.036952 |
| Corrected one-row run | 12 | 0.063576 | 0.005502 |
| Missing protocol / verification / write permission | 19 | 0.091744 | 0.013621 |
| Cancelled / superseded outcomes | 9 | 0.038713 | 0.006355 |

### Failures, corrections, and limits

The initial broad-package response used code size to bypass the topology gate
and proposed malformed status paths without loading the write contract. The
shared init skill now makes independent contexts decisive and reads the full
contract before proposing file actions. The same topology prompt then stopped
correctly, and subsequent initialization used the right paths and file set.
An unnecessary suggestion to rename a status because its archive ID matched was
also corrected: the shared rule now explicitly rejects that false collision,
and the follow-up retained the existing ID without writes.

The first no-commit goal stored abbreviated evidence commits in frozen records.
The actual repository parser rejected them, despite the model's completion
message. The shared protocol and retirement contract now require the full
`git rev-parse --verify HEAD` result and envelope/source validation before
removal. The failed fixture was preserved; a fresh rerun and the task-policy
continuation produced valid records. Existing project adoption of these
clarifications was explicit, not an automatic skill-update migration.

The first one-row run left an invalidated product fact unchanged. The shared
next skill and both API prompt copies now require current-fact corrections in
that row, even when a later documentation row exists. The fresh rerun corrected
the product fact in its single task commit and preserved later rows.

Two test-setup limits were also observed: bwrap hid a skill installation under
the host's `/tmp`, and an 8,192-token response cap interrupted initialization.
Moving the isolated DSH home outside `/tmp`, then resuming with a bounded
16,384-token allowance resolved them without widening filesystem permissions.
The tests exercise synthetic, small repositories and operator-supplied replies;
they do not certify visual UI behavior, arbitrary repository scale, unattended
approval, or other providers and platforms. No P1/P2-or-higher residual remains
in the final tested workflow cases; the initial failures remain part of this
evidence rather than being counted as passes.

Live acceptance used the v1.3.0 development worktree on repository baseline
`f118de2824ea0275d519f3f697930294b189e48a`; that commit does not contain the
tested changes. Hardening fixes include malformed/empty status detection,
missing instruction gates, correct fence handling, retired specification
identity, explicit request precedence, and recovery of interrupted reviews.

A supplemental skill-creator validator probe rejected the repository-required
`argument-hint` and `disable-model-invocation` fields. Those fields remain
intact; compatibility is checked by this repository's validator and the actual
DSH loader, rather than changing shared frontmatter to satisfy that narrower
validator.

### Release preparation review

A subsequent code, feature, and documentation review found and corrected:

- Missing active status files were detected only after the first retirement.
  The API runner now checks the active index and specifications in every
  project, and rejects required instructions removed or made unreadable during
  a run. Regression tests reproduce both failures.
- Template examples looked like allocated active work without status files.
  Additional examples now use literal fences; the template also preserves
  permanent IDs without a legacy renaming exception.
- Init's reference still said to wait for approval before reading, contrary to
  its skill's pre-proposal read requirement. Both now permit that read and
  require approval before writes; the repository check covers the agreement.
- The status template still described malformed markers as silently ignored.
  It now describes the current runner's rejection and makes runner-specific
  guidance conditional on actually using that optional executable.
- DSH update/removal preflight could move an unrelated same-name skill, and an
  incomplete source checkout could replace a complete installation. Documented
  commands now check bundle identity and required resources before mutation;
  two additional integration tests cover preservation on refusal.

The revised parser also rechecked eleven retained live-project fixtures,
including both final goal policies and cancelled/superseded outcomes, without
changing their bytes. This was a credential-free structural replay, not new
model acceptance. That replay made no paid requests; supplemental upgrade
acceptance and its spend are recorded below.

The release also adds `memory-bank-upgrade` as the sixth shared skill. Its
bundled template is checked byte-for-byte against the canonical project payload.
The README, tutorial, use-case guide, and release notes cover its approval-based
project-rule merges, preserved state, and no-op behavior.

### Project-upgrade live acceptance

The added scenario ran from 19:41:36 to 19:53:34 UTC on 2026-09-12 with the
same locked runtime, model, isolated configuration, and cumulative US$10 budget
gateway. The test credential remained `DSH_SKILLS` from `~/.profile`; no secret
was copied into the runtime environment or project files.

- Web inspection and proposal left every project byte unchanged. The approved
  upgrade changed only `AGENTS.md`, `memory-bank/milestone.md`, the active status
  preamble, and a new `memory-bank/lessons.md`.
- Independent hashes and parser checks verified unchanged task tables/notes,
  milestone specification, candidate direction, review iteration **4**, local
  severity and no-commit policies, custom goal protocol, current facts, frozen
  archive, retired record/index, and knowledge journal. No commit was created;
  project verification passed.
- Headless without proposal approval exited **0** with an unresolved approval
  and unchanged files. An all-retired project reported compatible rules and
  remained byte-identical. A fresh repeat after corrections also reported a
  no-op and preserved every file hash.

The first full proposal hit the 16,384-token response cap and resumed without
writes; only the completed, corrected proposal received approval. The first
repeat inspection flagged imported obligations for unused runner/evolution
features. The skill now explicitly preserves those exclusions and distinguishes
descriptive mentions from required capabilities. Two approved text corrections
adapted the fixture; a fresh repeat passed. These attempts remain in the costs.

| Accounting | Requests | Conservative US$ | Usage estimate US$ |
|---|---|---|---|
| Original scenarios 1–7 | 259 | 2.462505 | 0.192779 |
| Upgrade, including corrections and reruns | 72 | 0.960096 | 0.097857 |
| Combined | 331 | 3.422601 | 0.290636 |

Combined usage was 10,237,210 input tokens (9,664,384 cache hits) and 292,865
output tokens, including 155,640 reasoning tokens. The upgrade portion was
2,774,824 input tokens (2,599,936 cache hits) and 106,374 output tokens, including
64,569 reasoning tokens. These estimates use the rates above, not an invoice.
All reservations settled, with no provider errors or accounting-bound failures.
Final review found no unresolved P1/P2-or-higher issue in the changed scope.

Raw requests, responses, session transcripts, budget records, and generated
projects are retained outside the checkout and shipped payload. The isolated
Web process and budget gateway were stopped after testing. The global DSH
installation and existing personal/project configuration remain unchanged.
At the end of live acceptance, repository changes were uncommitted; that test
run performed no version bump, tag, push, release, or personal skill
installation. Release preparation is recorded in the [v1.3.0 notes](RELEASE_NOTES.md).

### Skill instruction revision acceptance

The final instruction revision was tested from **20:16:39 to 20:30:28 UTC on
2026-09-12**, using the same locked DSH/runtime versions and `deepseek-flash`
with high reasoning and a 16,384-token completion limit. A preserved pre-edit
candidate supplied the comparison baseline. Each project had its own isolated
workspace and one ledger writer; the baseline and candidate skill installations
were separate. The credential remained the selected `DSH_SKILLS` assignment
from `~/.profile`, outside model-controlled environments. The cumulative budget
was retained across all rounds. The request-count guard increased from 600 to
900 for this revision; the **US$10** ceiling and reservation rules did not change.

The revision applies portable instruction-writing ideas from the
[OpenAI article](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra):
concise selection descriptions, relevant resource loading, explicit decision
boundaries, and continuation through authorized work. It does not claim GPT-6
acceptance; these live tests used the model named above.

| Comparison | Observation |
|---|---|
| Skill selection descriptions | Total words fell from 267 to 124 across six skills. Six positive and six negative catalog-selection prompts scored 12/12 for both versions. These direct-provider probes measure description selection, not DSH's automatic routing. |
| Goal launcher | Its main `SKILL.md` fell from 1,013 to 557 words, including frontmatter. Invocation and native continuation help moved into a bundled reference. Neither ordinary goal-policy run read that optional help; both still loaded the canonical protocol. |
| Proposal resources | Candidate archive and reconcile loaded their write contracts before producing proposals. The baseline reconcile did not. All unapproved proposal fixtures remained unchanged. Actual-loader tests separately verify complete bodies, matching descriptions, and relative resources. |
| Proposal length | Paired upgrade output fell from 3,456 to 3,137 words, while reconcile grew from 1,024 to 1,494. Neither paired proposal was truncated. The initial shorter archive proposal had a factual defect and is not accepted as an improvement. These small samples do not establish uniform verbosity, latency, or cost gains. |

The eight scenario groups were graded with original-file hashes, Git history,
task-table comparisons, executable behavior checks, the repository's actual
active/history parser, and tool-call inspection:

| Scenario | Latest evidence |
|---|---|
| 1. Small initialization | Approved Web initialization preserved original instructions, code, tests, and README. One pending row combines implementation, tests, and invalidated current facts; the protocol bytes match the package and initialization made no commit. |
| 2. Broad archive and initialization | The topology gate recognized three independent contexts. Approved archives were verified at the full baseline commit; subsequent initialization preserved every archive hash and original source/instruction text. The final plan has one real pending row and an explicit future task-commit policy, without committing during initialization. |
| 3. Reconciliation | Unapproved proposals and the exact-URL remote-review probe made no writes or remote fetches. After explicit approval of the complete proposal and optional current-fact correction, only seven approved memory/history files changed. Code, tests, non-pending states, and HEAD were preserved; the journal retains superseded wording. |
| 4. One row | The existing sole `[~]` became `[+]` in one scoped commit. Historical and pending rows remained unchanged; implementation and invalidated current facts were corrected together and behavior was checked. |
| 5. Ordered goals | Both policies completed M01 then M02 and reconciled the consumer. `task` produced four scoped commits and a clean tree; `none` made no commits. A separate interrupted-review continuation retained iteration 4 in the retired M01 record and left M02 pending. The no-commit run needed the closure repair described below. |
| 6. Lessons and history | Both goal fixtures preserved superseded knowledge and full specification/status records, reserved IDs, and all-retired identity. Retrieval through stale paths changed no bytes. Cancelled and consumed rows remained literal historical evidence. |
| 7. Safe stopping | Missing protocol, missing required verification, denied writes, and missing proposal approval left work incomplete. The three capability probes exited 0 with unchanged project bytes and no escalation, showing why exit status is not acceptance. |
| 8. Upgrade | Approved merges changed only agent rules, milestone rules, a status preamble, and the new lessons file. Task tables/notes, specification, candidate direction, review counter 4, custom protocol, local policies, and frozen history were preserved. A fresh repeat was a no-op. An all-retired probe found no required merge and preserved all bytes while asking about optional scope. |

Three findings informed narrow instruction changes. Archive initially reported
a planned empty-order total as a current invariant; it now distinguishes
implemented behavior, documented ownership, and planned behavior. A fresh
fixture using the original prompt correctly recorded the planned behavior as a
gap. Init initially proposed a hypothetical future review-blocker row and
treated an initialization-only no-commit restriction as conflicting with future
task commits. Its contract now limits initial blockers to actual blockers and
preserves the explicitly approved policy for later execution. Fresh approved
initialization passed these checks.

The no-commit goal initially claimed completion with two history-index links in
active `milestone.md`. Independent parser validation rejected that state. An
explicit closure continuation removed only the duplicate maintained link;
frozen records, review counts, implementations, and HEAD remained unchanged.
The existing single-link rule was already correct, so no additional instruction
was added for this model error. This is an assisted pass and evidence that the
model's completion message still needs independent structural verification.

Web used authenticated browser-facing endpoints for conversation interviews and
separate approvals. Two native question-card waits were cancelled because the
test client had no card-answer adapter, then resumed with explicit text answers.
Silence was never treated as consent. Rendered UI and native card interaction
remain untested. The all-retired upgrade's optional suggestions also show that
the wording changes do not guarantee a concise no-op response.

| Accounting, including every attempt | Requests | Conservative US$ | Usage estimate US$ |
|---|---:|---:|---:|
| Earlier acceptance and upgrade | 331 | 3.422601 | 0.290636 |
| Instruction comparisons and scenario reruns | 341 | 2.770468 | 0.275523 |
| Cumulative | 672 | 6.193069 | 0.566159 |

The revision used **8,085,730 input tokens** (7,549,056 cache hits) and
**287,291 output tokens**, including 148,862 reasoning tokens. Cumulative usage
was **18,322,940 input tokens** (17,213,440 cache hits) and **580,156 output
tokens**, including 304,502 reasoning tokens. Estimates use the rates recorded
above; no per-run invoice is available. Every request had usage data, all
reservations settled, and no provider error or accounting-bound failure occurred.
Conservative remaining allowance was **US$3.806931**. The isolated Web process
and test gateway were stopped after the final run.

Final source review found no unresolved P1/P2-or-higher defect in the changed
package scope. The observed model errors and Web test limits remain explicit
above. Raw comparisons, tool histories, projects, independent grading results,
and accounting records stay outside the shipped payload. Updated installations
do not migrate existing project rules; live fixtures adopted protocol changes
explicitly. The release preview was an isolated snapshot of then-uncommitted
source changes. Subsequent repository commits record release preparation;
tagging and publication remain separate actions.
