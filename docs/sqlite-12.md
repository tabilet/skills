# SQLite 12 — Explorer testing, packaging, and documentation

Plan state: [+]

Depends on: [SQLite 11 — Views and follow-up prompts](sqlite-11.md).

Full dependency order: [SQLite 9](sqlite-9.md) -> [SQLite 10](sqlite-10.md) ->
[SQLite 11](sqlite-11.md) -> SQLite 12.

This implementation ledger records the reviewable explorer and its acceptance
evidence. Publishing, merging, pushing,
marketplace changes, and agent execution are separate actions.

## Acceptance objective

Prove that a user can start a copied toolkit, understand project status from the
overview, open an earlier request and its observed results, inspect task readiness
and blockers, and copy an appropriate follow-up prompt. The experience must work
with partial audit capture, invalid/stale source data, and remote browser access.

Preserve the existing SQLite guarantees: external optional storage, authoritative
Markdown, immutable historical observations, no new full-file snapshot capture,
and a standalone API runner when auditing is disabled. The explorer is an optional
consumer and index-refresh interface, not a required project component.

## Acceptance matrix

| Area | Required scenarios and evidence |
|---|---|
| Data upgrade | Known v1/v2 databases, v3 creation, interrupted migration/retry, unsupported/foreign database rejection, and byte-preserved legacy snapshots. |
| Recorded timeline | Request, clarification, proposal, approval, applied output, verification, commit, blocker, retirement, and parent/child run navigation. |
| Capture gaps | Exact, redacted, summarized, incomplete, absent, and legacy records without explorer fields; no fabricated transcripts or relationships. |
| Historical identity | Renamed/reordered/duplicate task labels, active-to-retired relocation, changed current text, and unresolved old references. |
| Readiness | Explicit dependencies, stable suggested order, a sole in-progress row, ownership conflicts, blockers, cycles, cancellation, supersession, and unfinished review. |
| Source freshness | Manual edits, branch changes, deletion, malformed records, failed refresh, publication during reads, and a source change before prompt preparation. |
| Incomplete projects | Missing database, empty/partial index, invalid legacy metadata, all-retired projects, archive-only context, and available evidence without recommendations. |
| Access and rendering | Project isolation, token/origin checks, path traversal, symlink sources, malicious Markdown/chat, remote asset references, and safe external navigation. |
| Browser usability | Keyboard access, focus, desktop/narrow layouts, back/forward, deep links, filters, pagination, visible-tab polling, and clipboard fallback. |
| Operation boundaries | Viewing and copying do not write project files, launch agents, call models, create task execution records, or grant approval; refresh writes only supported external storage. |

Tests use disposable projects and databases. Existing neighboring packages may
provide read-only acceptance examples, but their noncanonical IDs or frozen
records must not be silently repaired to make tests pass. Reproduce those cases
in isolated fixtures for repeatable regression coverage.

## Packaging and runtime verification

Package the server, browser assets, audit/index helpers, and parser dependencies
as one documented optional toolkit installation. Verify a fresh copied installation
from a directory outside the repository, including missing-asset diagnostics and
relocation. Browser assets must be available without a checkout or network access.

The installed runtime requires Python's standard library and a browser. Keep
browser-test tooling and any Node development dependencies in repository-only
test infrastructure. Do not add them to the project template or require them for
the existing Python verification command. Preserve the seven portable skill
bundles and their shared-reference parity checks.

Exercise the default localhost launch and an SSH tunnel to port 8000. Verify that
a narrow Chromebook-like browser can navigate and copy/select a prompt without
assuming a local editor or desktop environment exists on the server. Local-server
testing alone does not establish that a public website or release has deployed.

## Scale and performance evidence

Extend the existing disposable 120-status-file, 17-lane, 2,400-task fixture with
retired records, archive/evolution groups, audit runs, child runs, and enough
timeline entries to exercise several pages.

Measure initial overview load, timeline pagination, task classification, search,
detail navigation, and explicit refresh separately. Record fixture size, Python/
SQLite/browser versions, timings, and peak response sizes. Keep task/timeline
collections paginated so the UI does not render thousands of expanded records.
Use measurements to identify regressions; do not turn one development host's
timings into an unsupported service-level guarantee.

## Operator and public documentation

Update the existing SQLite guide and README to explain:

- Optional installation and the explorer launch command.
- The default overview and the timeline/to-do navigation model.
- How request capture and structured output references affect what can be shown.
- Recorded historical evidence versus current indexed/live Markdown.
- Suggested task order, prerequisites, blockers, and review requirements.
- Explicit create/refresh/migration actions, index diagnostics, and source access.
- Copy-only follow-ups, clipboard fallback, and SSH tunnelling from a Chromebook.
- External storage, captured/private content, backups, and recovery.

Update affected published guides in English and Simplified Chinese with matching
navigation/anchors. Keep implementation milestone ledgers as repository planning
documents; historical release articles remain historical. Document that DSH UI
embedding, direct agent launching, planning edits, and AI summaries are future
extensions rather than available controls.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL12-T01 | [+] | Complete credential-free service, migration, and source-lifecycle regressions. | The acceptance matrix's data, identity, readiness, freshness, and operation-boundary cases pass in disposable fixtures. |
| SQL12-T02 | [+] | Complete isolated browser tests for all three views and degraded states. | Desktop/narrow, keyboard, deep-link, polling, pagination, and copy/fallback journeys pass without credentials or model calls. |
| SQL12-T03 | [+] | Verify the copied toolkit and localhost/SSH access workflow. | Assets and helper modules work outside the checkout; no Node runtime or server desktop is required; missing components fail clearly. |
| SQL12-T04 | [+] | Measure representative scale and address material regressions. | Reproducible 120-status/2,400-task and multi-page audit measurements cover rendering, queries, classification, and refresh. |
| SQL12-T05 | [+] | Update operator, README, and bilingual website guidance. | Launch, views, capture limits, refresh, follow-up, tunnelling, and recovery instructions agree with the implemented interfaces. |
| SQL12-T06 | [+] | Run repository, DSH, browser, and website acceptance gates and complete review. | All required gates pass with recorded evidence; no blocking code, architecture, or user-journey findings remain. |

## Required gates and final handoff

Run:

```bash
python3 check.py
npm test --prefix tests/dsh
npm ci --prefix tests/browser --ignore-scripts --no-audit --no-fund
npx --prefix tests/browser playwright install chromium
npm test --prefix tests/browser
mkdocs build --strict
git diff --check
```

Also run the isolated explorer browser suite and the documented disposable scale
benchmark. Record exact commands, environment, outcomes, and any material limits.
Do not mark the explorer accepted based only on Python unit tests or a local
website build. If a required gate cannot run, keep acceptance pending and describe
the missing evidence.

The final handoff identifies the implemented commands, test evidence, supported
data states, and outstanding limitations. Stop at the completed local work unless
a separate instruction authorizes a merge, push, or release.

Review iteration: 3 (cross-milestone deep review fixes applied). The disposable
benchmark now includes 120 statuses, 17 lanes, 2,400 tasks, retired history,
archive/evolution groups, 250 parent runs, 25 child runs, timeline/detail queries,
and peak response size; its latest run reported a bounded 50-of-2,400-entry
To-do page and a 170,349-byte peak response.
`python3 check.py` (36 checks), the full credential-free Python suite (164 tests),
the focused SQLite suite (90 tests), DSH tests (13), `mkdocs build --strict`, six
isolated DOM journeys, two real Chromium journeys, copied-toolkit launch and
missing-asset tests, and the representative benchmark pass. Browser tooling is
repository-only under `tests/browser`; the shipped runtime remains Python
standard-library code and local static assets. No merge, push, publication, or
release action was performed.

Review iteration: 4. Regression coverage now includes milestone-scoped duplicate
task IDs, per-workspace v2 projection upgrades, deep dependency chains, closure
ordering, full-source follow-up races, bounded To-do and goal collections, strict
POST types, active-only counts, scoped historical task resolution, and failure
after initial database publication. The scale benchmark measures the bounded
To-do response as well as classification.

Review iteration: 5. Regression coverage now includes action authorization with
duplicate task IDs, foreign-workspace child links, HTTP scheme enforcement,
current branch reporting, bounded search pages, hidden review pages, exclusive
detail URLs, restored page positions, exact-line source excerpts, and abrupt
backup interruption before publication. Hosted explorer CI runs the focused
Python contracts and isolated DOM suite before its real Chromium journeys.
The same review also verifies the complete target schema before a migration
commits its version marker, keeps API-runner audit ownership self-contained,
rejects malformed nested follow-up source references, and reports stale source
line locations without substituting unrelated current text.
