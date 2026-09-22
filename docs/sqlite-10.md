# SQLite 10 — Explorer local server, API, and shared navigation

Plan state: [+]

Depends on: [SQLite 9 — Data contracts, migrations, and readiness](sqlite-9.md).

Next: [SQLite 11 — Three views and follow-up prompts](sqlite-11.md).

This implementation ledger preserves the accepted contract and completion evidence.

## Delivery contract

Add a standalone browser entry point to the optional toolkit:

```bash
tabilet-audit explorer /absolute/project --port 8000
```

Use the existing database configuration and default external location. Serve one
explicit project/workspace per instance, even when the account database contains
other workspaces. Bind to localhost and print the browser URL; do not require a
desktop browser on the server or open one automatically. Support access through
an SSH local-port tunnel. Report an occupied port without terminating unrelated
processes. Stopping the server closes its resources without changing task state.

The server uses Python's standard library. Ship local HTML, CSS, and JavaScript
assets; Node and external asset/CDN access are not runtime requirements. The
disabled-audit API runner keeps its standalone installation contract. This server
does not introduce a second agent execution harness.

## Project-scoped API

Use a small explicit JSON API. Every response is scoped to the selected project;
client-supplied run IDs, document references, and task references must not widen
that scope.

| Method and endpoint | Responsibility |
|---|---|
| `GET /api/health` | Project/branch identity, database availability/version, index generation, refresh state, and diagnostics. |
| `GET /api/overview` | Recorded summaries, active-state counts, attention items, and history/archive/evolution groups. |
| `GET /api/timeline` | Filtered, paginated workflow entries and parent/child grouping references. |
| `GET /api/runs/{run_id}` | Selected messages, phases, observed outputs, task changes, verification, commits, and gaps for one run. |
| `GET /api/todo` | Explained readiness groups and suggested order, with validation/freshness evidence. |
| `GET /api/search` | Filtered text and metadata results with document/task references and locations. |
| `GET /api/document` | A declared source preview or indexed version, clearly identifying which was returned. |
| `POST /api/refresh` | Explicitly create/migrate supported external storage and refresh the selected project's derived index. |
| `POST /api/follow-up` | Revalidate a selected reference and prepare a copyable prompt; no task execution or project write. |

Use bounded pagination and stable ordering. Timeline pagination must not skip or
repeat previously displayed entries when new runs arrive; use an opaque cursor
containing the ordering boundary. Dates remain stored as UTC, with browser-local
display and an accessible exact timestamp. Expose gaps and missing fields as
structured data rather than burying them in a successful-looking empty response.

Keep each response's related reads consistent with one database generation/read
transaction. Use request-local SQLite connections. Never expose an arbitrary SQL,
shell-command, filesystem-browse, or agent-launch endpoint.

## Refresh and source access

Opening the server or a view does not create, migrate, or refresh storage. Missing
storage gets a setup screen with an explicit **Create index** action. Existing
storage gets **Refresh project**; explain when that action also requires a known
database migration. Both actions operate only on external storage and projections.

Poll lightweight health/activity information every five seconds while the page
is visible. Pause polling in background tabs. Polling observes recorded activity
and published generations; it never triggers an implicit source scan or migration.
After detecting updates, update view data while preserving selection and filters.

Failed refreshes expose diagnostics and retain the last published generation.
Keep available audit entries, indexed documents, and safe source previews usable.
An old successful refresh is not proof that disk is still current. Validate live
sources for task recommendations and follow-up preparation; report changed hashes,
missing sources, invalid records, and ambiguous references explicitly.

Only declared project Markdown may be previewed. Reuse bounded reads and
symlink/path-boundary checks. On invalid or partial layouts, source previews are
evidence with diagnostics, not an alternative validated workflow projection.
Audit source links do not authorize fetching remote content or reading arbitrary
files outside the selected project.

## Browser shell and shared components

Provide a header with project name, branch, refresh status, search, and the tabs
**Overview**, **Timeline**, and **To-do**. Overview is the initial route. Preserve
view, filters, and selected detail in a bookmarkable URL; browser back/forward
must restore the same context.

Share components for operation/outcome labels, task states, source references,
capture fidelity, diagnostics, pagination, and detail navigation. Use a side
panel on wider screens and a full-page detail route on narrow screens. Provide
keyboard navigation, visible focus, meaningful headings, and accessible names.

Distinguish recorded historical evidence, indexed text, and live source previews.
When opening an old run, never label current text as the original output. Provide
an explicit path/line reference and readable source preview; do not assume a local
editor protocol will work through a remote browser or Chromebook.

## Local access and rendering boundaries

Generate a per-launch access token, require it for API access, and keep it out of
request/access-log URLs. Validate Host/Origin for API requests and require
same-origin authenticated POSTs for refresh. Do not expose the service on all
network interfaces or enable cross-origin access by default.

Treat captured chat, task labels, Markdown, and source paths as untrusted display
data. Render a safe subset of Markdown with escaped text; never execute embedded
HTML/scripts or automatically load remote assets. Internal links resolve only to
declared project sources. Deliberate external navigation must not be confused with
a trusted project-source preview.

## Tasks

| ID | Status | Task | Acceptance |
|---|---|---|---|
| SQL10-T01 | [+] | Add the explorer command, local server lifecycle, and bundled asset loading. | A copied toolkit serves the chosen project on localhost without Node, automatic database creation, or a desktop browser. |
| SQL10-T02 | [+] | Implement project-scoped read APIs and consistent pagination. | Overview/run/task/source responses agree with one generation, reject cross-project references, and preserve timeline pagination during new activity. |
| SQL10-T03 | [+] | Implement explicit refresh, setup, and degraded evidence access. | Reads do not migrate; refresh failures retain earlier evidence; invalid sources cannot become task recommendations. |
| SQL10-T04 | [+] | Implement access-token, origin, source-boundary, and rendering protections. | Unauthenticated/cross-origin requests, traversal, symlinks, injected markup, and undeclared sources are rejected or displayed safely. |
| SQL10-T05 | [+] | Build shared navigation, detail components, search shell, and visible-tab polling. | Deep links, browser history, keyboard use, narrow screens, and update detection work without implicit scans. |
| SQL10-T06 | [+] | Verify APIs, lifecycle, isolation, and downstream UI contracts. | Server tests and repository checks pass; SQLite 11 has stable interfaces and the milestone review has no blocking findings. |

## Verification and completion gate

Test database absent/old/current/unsupported, valid and partial project layouts,
external audit references, multiple workspaces in one database, requests during
refresh, failed refreshes, changing sources, and clean shutdown. Exercise missing
assets, occupied ports, unauthorized requests, malformed parameters, path
traversal, and display content containing scripts or remote asset references.

Use credential-free HTTP tests and a minimal browser smoke test for routing,
focus, source preview, and polling. Run `python3 check.py` and `git diff --check`.
SQLite 11 starts only after the server/API contract and milestone review pass.

Review iteration: 3 (cross-milestone deep review fixes applied). Timeline search is applied in
SQL before pagination across run, event, and captured-message evidence, and
health exposes audit activity so polling notices new runs as well as index
refreshes. Credential-free HTTP
tests, copied-toolkit smoke testing, and repository checks passed. The server
serves the richer bundled client and accepts its same-origin cookie while
retaining the header-token compatibility path. The server now rejects every
non-loopback bind, serves v1/v2 audit evidence before explicit migration,
normalizes mixed-precision activity timestamps, bounds timeline/run-detail
collections, records failed mixed-layout refreshes, and returns each Overview
from one read transaction. No project writes occur during reads or follow-up
preparation.

Review iteration: 4. To-do groups, goal children, run events, messages, and child
runs now have bounded pages. POST fields use strict JSON types, source details are
bookmarkable, and an absent database presents Create index. Follow-up preparation
requires a classified task or review milestone and revalidates the complete live
source inventory after selection.
