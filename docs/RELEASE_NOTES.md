# memory-bank v2.22.0

Adds optional advice for keeping an instrumented run on the project's own code,
with language defaults and a launch field to hold the options. The stock `GOAL.md`
protocol changes, so its fingerprint is new.

- **Instrumentation scope.** When a profile shows that an instrumented run spends
  most of its time in third-party code, or a stock default applies, a project may
  exclude that code from instrumentation. Its own code stays fully instrumented
  and every test still runs, unlike a rule 8 fixture skip. On first use the project
  measures and records the saving and what the exclusion can no longer detect in
  `tech-stack.md`. The milestone that completes a stage runs its instrumented
  gates without the exclusion, and an
  exclusion is never changed to get past a failure. This sits under "Capacity and
  unit size", so it is a recommendation, not a gate.
- **Go note.** `testing-profiles.md` gives the `-gcflags` form for excluding
  third-party modules from race instrumentation. Overriding `-race` per package is
  not a documented Go feature. It was measured on Go 1.26.6, so recheck the build
  and the saving after each toolchain update.
- **Language defaults.** `testing-profiles.md` now has a table of conservative
  defaults, each with its warning. Clang ASan and UBSan use an ignorelist. TSan,
  MSan, GCC and Rust sanitizers default to no exclusion, because partial
  instrumentation can produce false reports or has no documented form. Python,
  JS/TS and Java keep to coverage settings. A project may pass its own option, and
  records the default, its option, the saving and what is lost. Only the Go row has
  been measured; the others come from each tool's documentation.
- **`INSTRUMENTATION_SCOPE` launch field.** A new optional field in `suggested.txt`,
  next to `TEST_POLICY`, holds a project's options as one `<tool> = <option>` line
  per tool. In a new launch proposal, planning pre-fills the stock defaults for the
  project's tools, each with its warning, and you can edit or clear them before
  launch, like the other policies.
  Approving the launch adopts them, and `none` turns them off. A value that departs
  from a stock default also carries a warning. Changing it during a run needs
  explicit human approval, and it never changes to get past a failure.
- **Legacy record headings.** The combined-record reader now ends an ID at any
  non-word character except a dotted numeric task suffix. Task-like titles
  such as `M1.2` need the canonical milestone ID elsewhere in the specification,
  and a task number such as `M01.2` no longer counts as that ID. A record whose only
  evidence is its task numbers stops reading, where v2.21.1 accepted it.
  `## M2: Delivery` on `status-M01` is rejected like
  `## M2 - Delivery`, even when the body mentions `M01`. `## M1: Delivery` is read
  again with its explicit correction, which v2.21.1 had stopped accepting.
- **Evidence.** One project ran five whole packages with and without the exclusion
  at the same source. Race time fell 34% overall, from 83% in one package to a
  saving within run-to-run noise in another. No run in either form reported a data
  race. One project is a signal, not proof, which is why the advice stays optional.
- **Review fixes.** Reflection accepts absent or null token usage without losing
  a valid proposal. The parallel test check falls back to recursive unittest
  discovery when test packages exist, preserving package hooks and nested tests.
  Launch refresh preserves instrumentation options in unapproved drafts too.
- **Checks.** `check.py` locks the new wording in the policy, its upgrade copy, the
  three testing profiles and the goal guides.

**Scope.** `GOAL.md`, the goal skill, the write contracts and launch refresh rules,
the test policy and its upgrade copy, the testing profiles, the English and Chinese
goal guides, the runner's historical reader and the repository checks change. The
reflection audit tool also gains defensive usage-metadata handling.

**Upgrade note.** Installing the 2.22.0 plugin and runner changes no project file.
An existing project is offered the new advice through `memory-bank-upgrade`, which
writes only after you approve the complete proposal.
A launch that records the old protocol fingerprint needs its identity re-approved
before it runs on 2.22.0. A launch without the new field behaves as `none`, and a
refresh keeps that unless you approve a change.

# memory-bank v2.21.1

Tightens the v2.21.0 reader for combined legacy records. The stock `GOAL.md`
protocol is unchanged.

- **Identity by heading only.** The unpadded form of a record's own ID (`M1` for
  `M01`) now identifies the record only as the specification's first heading. A
  first heading that opens with any other ID of the record's lane, padded or not,
  is rejected even when the body mentions the record's own ID, so `## M2` on
  `status-M01` and `## M1` on `status-M02` no longer pass. A title heading needs
  the padded ID in the specification, so an incidental mention such as "Apple M1"
  no longer identifies a record. v2.21.0 accepted these cases.
- **Unpadded status declaration.** A retained status that declares the record's
  own unpadded ID (`**Milestone.** M1`, `Milestone: M1`) is now read. Any other
  declared ID is still rejected.
- **Wording.** The `milestone.md` paragraph says the record's own ID "may head its
  specification" without padding, and the corrections guide describes the same
  rule.

**Scope.** The shared runner's historical reader, the `milestone.md` template and
its upgrade copy, the corrections guide and the repository checks change. Records
that v2.21.0 read through a correction whose first heading is the record's own
unpadded ID or its padded ID keep working. Nothing is migrated, and installing the
plugin and runner changes no project file.

# memory-bank v2.21.0

Lets a frozen legacy record that holds several milestones under one ID be read
through an explicit correction. The stock `GOAL.md` protocol is unchanged.

- **Combined legacy records.** Some older projects kept several milestones in one
  status file, such as `M1` to `M5` in `status-M01.md`, with the milestones' own
  headings in the specification. The shared historical reader rejected such a
  record because no heading carried the padded ID `M01`. An
  `identify-specification` correction in `tabilet/docs/history/corrections.json`
  now also accepts the unpadded form of the record's own ID (`M1` for `M01`) as
  the matching heading, so the reader, the index and dependency projection can use
  the record. The correction is still explicit and hash-bound to the frozen bytes.
  A heading with another ID, an ID-style first heading that does not match, and a
  record with no correction stay rejected.
- **Retiring one.** `milestone.md` now says that a status file holding several
  milestones under one ID is not retired as one record: stop and report the
  combined file, and the owner splits it under separate IDs or decides otherwise.
  A combined record that already exists is frozen and is read only through the
  correction above.
- **Checks.** `check.py` locks the new `milestone.md` wording, and a new test
  covers the accepted and rejected forms.

**Scope.** The shared runner's historical reader, the `milestone.md` template and
its upgrade copy, the repository checks and one row of the corrections guide
change. New retirement records still use the strict envelope, and nothing is
migrated. `GOAL.md`, its fingerprint and the audit tools do not change.

**Upgrade note.** Installing the 2.21.0 plugin and runner changes no project file.
A project with a combined legacy record still needs the correction entry in its
own `corrections.json`, and the reader takes effect once it runs 2.21.0. An
existing project receives the new `milestone.md` paragraph through
`memory-bank-upgrade`, which writes only after you approve the complete proposal.

# memory-bank v2.20.0

Makes the per-row check cheaper and more precise, adds a rule for skipping an
instrumented variant on one large fixture, and adds optional planning rules that
keep a stage to what it can reach. The stock `GOAL.md` protocol is unchanged.

- **Row checks (rule 7).** Before a row is done or a task review starts, the check
  builds or type-checks the whole project where the toolchain has such a step,
  then runs static checks and the affected whole units. Direct consumers join when
  the row changes a public contract, a persisted format or behavior its consumers
  rely on. The race check runs on units whose concurrent code changed and on
  consumers of a changed concurrency contract, and this limits the row check,
  never a required gate. A project with a slow build names a narrower step in
  `tech-stack.md`. A row check may use the toolchain's test cache and says so.
- **Fresh gates.** Every run of a required gate, a rerun included, bypasses a
  test-result cache. Compiler and dependency caches stay. A required gate served
  from a test-result cache is a reviewer finding.
- **Rule 8: match the fixture to the variant.** A large capacity or maximum-size
  fixture may skip an instrumented variant (race, sanitizer, coverage) only when
  it still runs in a required gate without the variant, the skip is written in the
  test with its reason and reported, anything the variant checks on that path has
  its own smaller test, and the skip is not added to get past a failure. A
  property that appears only at full size keeps the variant. A skip that breaks a
  condition is a reviewer finding.
- **Capacity and unit size advice.** A new section of recommendations, not gates:
  run heavy instrumented targets serially on a shared host, plan a test-unit split
  as its own milestone, prefer tests that run in parallel, and keep test helpers
  near the domain they serve so a shared helper does not invalidate cached results.
- **Stage qualification and project specifics.** `Project specifics` gains `Row
  checks` and `Stage qualification` lines, and `tech-stack.md` gains matching
  verification-standards lines. Stage qualification is a required gate of the
  milestone that completes the stage, which depends on the stage's other
  milestones and is planned with its final horizon.
- **Scope control in planning.** A new stage's proposal includes a scope pass of
  keep, simplify or defer recommendations for you to decide, with a one-line "no
  change" outcome. A shared planning block in Init, Propose and Reconcile keeps
  planned work to what the stage can reach, maps final qualification to existing
  tests, and prefers one check that refuses every unsupported case unless
  acceptance requires the rare ones.
- **Optional guarantee levels.** `milestone.md` ships `Project levels: none`. A
  project may define levels for its persisted records so a rebuildable hint does
  not get the full durability set. You approve each record's level and an agent
  never assigns one. Defining or changing levels needs its own approved proposal,
  never standing corrective approval. A finding confined to an approved advisory
  record is Lower, citing the approval source and the evidence that losing the
  record breaks no supported flow, unless it is a privacy, credential or authority
  failure, breaks the record's size bound, makes a supported flow fail or leaves
  acceptance unmet.
- **Profiles.** The `golight` profile names the Go row check and says a rule 8 skip
  uses `t.Skip`, run with `-v` so the log reports it.
- **Upgrade.** `memory-bank-upgrade` compares rules 7 and 8, the capacity section
  and the reviewer list, and offers missing `Row checks` and `Stage qualification`
  lines in both `Project specifics` and `tech-stack.md`. Guarantee levels never
  count toward compatibility and are offered only alongside other changes, so a
  project with nothing else to change stays a no-op.

**Scope.** The skills, the template and the repository checks change; `GOAL.md`,
its fingerprint and the harness do not. Installing the 2.20.0 plugin alone changes
no project file.

**Upgrade note.** An existing project keeps its current test rules until it adopts
them through `memory-bank-upgrade`, which writes only after you approve the
complete proposal. An adopted project that runs required gates as cached commands,
such as `go test ./...`, should declare their no-cache form in `tech-stack.md`.

# memory-bank v2.19.0

Cuts the time a milestone spends re-running checks, keeps a safely refused
oversize input from blocking a review forever, and hardens the API runner and
reflection against transport failures. The stock `GOAL.md` protocol is
unchanged.

- **Focused checks and required gates.** The stock test policy gains rule 7.
  While editing, run the narrowest check. Before a row is done or a task review
  or re-review, run the affected whole units and their direct consumers (plus
  race or UI runs if concurrency or UI changed), recorded like a gate. The
  required gates run once immediately before the whole review and rerun only
  when something a gate reads has changed. If it is unclear what a gate reads,
  rerun it. A gate's state is the full `HEAD`, plus a saved diff and its hash
  for uncommitted work; status and record bookkeeping is ignored unless a gate
  reads it. Run cheapest first; after a failure finish the other cheap gates,
  fix, rerun the failed and affected gates, and run any skipped gate before
  the review. Rules 3 and 5 and the reviewer-finding list were adjusted to
  match.
- **Reuse at closure.** `milestone.md` step 8 lets a class O gate reuse its
  result when nothing it reads has changed; class R follows its own authority.
  The reuse is stated in the retired record's `**Verification.**`. A later
  closure rerun is reported in the step 9 summary, never written into the
  frozen record. The status-file preamble records the source revision or saved
  diff hash for each result.
- **Safe capacity refusals are Lower.** An extreme-size input that is refused
  deterministically and clearly, with nothing leaked, corrupted, lost or
  rewritten, with the data still reachable and the limit documented, is Lower
  rather than P1 or P2, provided no acceptance line, public contract or
  previously supported behavior promises that size. Register the finding as a
  `capacity limit` row citing the test and the documentation. The fix-now rule
  applies if later work builds on it; a human defers it or plans a fix at any
  review, and must do so at horizon closure. Narrowing a promised size needs
  your explicit approval, and the finding stays P1 until then. Projects whose
  own severity definitions disagree keep theirs.
- **Upgrade.** `memory-bank-upgrade` compares `test-policy.md` rule by rule
  (rules 3, 5, 7 and the reviewer list), compares `milestone.md` by content for
  the closure step and the capacity paragraph, and compares the status-file
  preamble. It offers each missing piece in its complete proposal and writes
  only after approval. A repeat run is no longer a no-op while any is missing.
  Project edits and severity definitions are preserved. Init's write contract
  carries the capacity paragraph for new projects.
- **API runner.** Transport failures while reading a response (a reset, a TLS
  error, a truncated body, a body shorter than its `Content-Length`, a
  malformed status line) are retried instead of escaping as a traceback or as
  invalid JSON. Anthropic's 529 overload status is retried, backoff is
  2/4/8 seconds with jitter, and the default API timeout is 600 seconds. Exit
  codes are unchanged.
- **Reflection.** `tabilet-audit reflect` reads captured message text that v4
  audit storage keeps in a separate table (it sent blank traces before),
  honours tombstones, reports provider token usage, labels the proposal with
  the provider actually used, and accepts `TABILET_REFLECT_API_BASE` for an
  explicit `--backend` only. Its REST call also catches malformed HTTP
  responses.
- **Propose and init.** Propose names the full `suggested.txt` path
  (`tabilet/memory-bank/suggested.txt`); generated verification sections say
  that brackets mean unfilled placeholders and must be removed. The README
  documents the stock test policy.
- **Repository checks.** `check.py` runs test files in parallel and caches a
  fully passing suite outside the repository; CI never uses the cache.

**Scope.** The skills, the template and the harness change; `GOAL.md` and its
fingerprint do not. Installing the 2.19.0 plugin alone changes no project file.

**Upgrade note.** An existing project keeps its current test and review rules
until it adopts them through `memory-bank-upgrade`, which writes only after you
approve the complete proposal. The runner and reflection changes ship in the
account-level harness: install the updated files separately.

# memory-bank v2.18.0

Makes the shared historical-record reader read older retired milestones with
fewer false rejections, without accepting a review that the record itself later
revokes, contradicts or never established. The reader serves the API runner,
dependency checks, lookup and the SQLite index.

- Reads retained status, envelope and review prose by subject and predicate
  instead of rejecting every review-related sentence. Ordinary test notes and
  matching restatements of the recorded pass stay accepted. Conflicting review
  and iteration counters, a reversal of the pass in the reader's vocabulary
  (voided, revoked, withdrawn, set aside, pending, conditional, and similar),
  and unresolved claims in the `Result`, `Review gate` and `Outcome` fields
  still block. Table, fence, indented-code, heading and task-row boundaries no
  longer hide a reversal that follows a recorded pass.
- Records that carry their own pass now **warn** on review wording the reader
  does not recognize, instead of blocking. The API runner prints up to ten
  warnings once before its first run and continues; the SQLite index adds
  `warning:` diagnostics and `tabilet status` reports `history_warnings`.
  Warnings never change an exit code, the record's review result, task
  eligibility or dependency acceptance. A record whose pass is supplied by a
  correction stays strict: any unrecognized prose after the pass blocks, and a
  correction cannot supply acceptance past it.
- Wording coverage is best effort. A reversal phrased outside the vocabulary
  can still be accepted on a record that carries its own pass, with at most a
  warning. The guarantees that do not depend on wording are structural:
  counters, context boundaries, the correction-backed path, the three verdict
  fields and warning/acceptance separation. See
  [historical record compatibility](history-corrections.md).
- An item in an `Item | State | Notes` ledger that starts with its milestone
  and numbered task ID, such as `M01.2 — Verify`, now supplies that explicit
  task ID for dependency resolution.
- Frozen records are never rewritten, and newly retired records still use the
  strict envelope.

**Scope.** This release changes the account-level harness, not the skills.
Skills, templates and the stock `GOAL.md` protocol are unchanged, so installing
the 2.18.0 plugin alone changes nothing. The new behavior ships in the API
runner (`tackle-memory-bank-api-loop`), the SQLite index and status helpers
(`tabilet_index.py`, `tabilet_status.py`) and the `tabilet` controller, which
loads the runner's reader from the file beside it. Install the updated harness
files to get it.

**Upgrade note.** A record that v2.17.0 accepted silently may now print review
wording warnings, and a record containing a counter conflict or a reversal of
its own pass (previously accepted unread) now stops with exit `11` until its
evidence is reconciled or an approved correction is recorded. Correct such a
record through the correction manifest rather than by editing frozen text.
Update the installed runner, controller and SQLite toolkit separately, and
rebuild the index on its next sync. The registry version moves with this
release. The separately published DSH companion is not updated by this release.

# memory-bank v2.17.0

Adds a stock test policy and a review gate that converges, so test failures stop
turning into human dispositions and fresh reviewers stop re-sweeping an unchanged
milestone.

- Adds `tabilet/memory-bank/test-policy.md`. Checks are class O (offline,
  self-checking, PASS or FAIL, never UNKNOWN) or class R (real effect, needing
  separately named human authority). The policy grants no authority and never
  removes a grant's limits. A new optional `TEST_POLICY` launch field and a
  shared resolution order (approved request, then the path `AGENTS.md` declares,
  then the default file, then `none`) are added to the goal protocol and to
  Next's interactive controls.
- Changes the stock `GOAL.md` protocol (new fingerprint). The bounded
  review-fix gate now blocks on P1 and higher only. Iteration 1 reviews the whole
  milestone; later iterations review the previous blocking findings, the change
  since the recorded reviewed state and its direct consumers. P2 and Lower
  findings are fixed now or carried in a new `Open review findings` register
  (`FND-` IDs) in `milestone.md`; every review fix is itself reviewed and the
  final allowed iteration makes no further review change. The verification-attempt
  gate now covers class R checks, or every expensive or protected check when no
  test policy applies.
- Adoption is explicit through `memory-bank-upgrade`. Until a project adopts them,
  its stricter text stays binding, including P2 blocking. New `memory-bank-init`
  projects receive both by default.
- The `tabilet` controller and the Python API runner code are unchanged. The
  controller keeps its own deterministic gate: it runs its own full review, any
  reported P0, P1 or P2 blocks retirement, and it does not read the register, so
  milestones it runs keep P2 blocking.

Updating the plugin does not update an installed API runner, controller or SQLite
toolkit. The embedded task text of the runner gains the test-policy sentence; the
installed runner needs a separate update to carry it.

# memory-bank v2.16.2

Improves compatibility with older retired milestone records across the API
runner, controller and SQLite index while preserving their original evidence.

- Adds a shared historical reader and an optional, hash-bound correction
  manifest for reviewed interpretations of historical evidence. Corrections
  do not grant execution authority or rewrite frozen records; incomplete or
  conflicting evidence remains blocking.
- Keeps new retirements subject to the strict contract and preserves the API
  review ceiling of 10. Correction changes are included in workflow snapshots
  and cannot be made during task execution or closure.
- Updates the SQLite index projection so the next sync rebuilds affected lookup
  data. See [historical record compatibility](history-corrections.md) for the
  supported formats, evidence requirements and approval boundaries.

The stock `GOAL.md` protocol is unchanged. Updating the plugin does not update
an installed API runner, controller or SQLite toolkit; update those separately.
The separately published DSH companion is not updated by this release.

# memory-bank v2.16.1

Fixes discovery, indexing, execution selection and retirement for milestone root
IDs above 99, such as `M100`, `M130` and `M153`. Root IDs use at least two digits;
existing IDs remain unchanged. Amendment and option child suffixes, and context
archive IDs, retain their separate two-digit limits.

- Aligns runner, controller proposal validation, SQLite indexing and v1.5 migration
  scanning with the root-ID grammar. The SQLite projection revision forces a
  rebuild on the next index sync without rewriting project Markdown or audit records.
- Adds coverage for `M99`, `M100`, `M130` and `M153`, their child records,
  selection, indexing, retirement, migration, and the unchanged API review ceiling
  of 10. The template and published guidance now describe the extended range.
- Leaves frozen history untouched and preserves strict history validation. Recognizing
  a longer filename does not make an existing nonconforming history record valid;
  projects with such records still require separate reconciliation of the original
  format and evidence without weakening review gates.

The stock `GOAL.md` protocol bytes are unchanged from v2.16.0; the registry version
moves with this release. Installing updated skills does not update account-level API
runner or audit toolkit executables. Update those separately where installed.

# memory-bank v2.16.0

Makes approved Goal runs continue with fewer redundant confirmations while keeping
explicit authority, bounded verification and review, and frozen history intact.

- Adds interactive `REVIEW_MAX_ITERATIONS`, default 10 independently of commit
  policy. Explicitly approved higher ceilings preserve consumed iterations across
  resumes and repairs. Project and milestone caps intersect with the launch cap;
  legacy fixed-cap prose stays binding until explicit adoption.
- Distinguishes pending task rows from proposed grants, reuses existing scoped
  approval, and skips confirmation for empty or model-free reflection results.
  Continuous-run planning can propose option deferral and dependency-ready priority
  while preserving explicit choices and strict ordering.
- Records authorized launch refresh transitions so resumes can verify the current
  approved state without treating expected checksum changes as unexplained drift.
  Interrupted writes are inspected; a hash chain alone never grants authority.
- Defines exact-commit and explicitly approved accepted-goal push scopes. Approved
  plan-only human commits require full-diff evidence. Legacy grants remain pinned.
  `EXTERNAL_MUTATIONS` can reference concrete grant IDs, and duplicate legacy
  declarations are intersecting constraints. `workspace-contained` covers approved
  local CLI work only; it no longer adds push destinations. Dangerous-mode planning
  proposes separate concrete push grants rather than organization-wide authority.
- Keeps Python API execution capped at 10 reviews. Existing extended interactive
  history remains readable, but a new API retirement cannot claim a higher limit
  using self-authored approval prose. The controller pauses before dispatch on
  unsupported interactive counters without resetting them.
- Adds regression coverage for retirement authorization, controller handoffs,
  example-policy omissions, case-insensitive contract guards, and byte-identical
  shared planning blocks. Updates the English and Chinese Goal guidance.

The stock protocol fingerprint has changed. Existing paused goals require the
normal identity-transition approval; installing this release does not approve new
grants, migrate fixed project caps, or reset counters. Review the narrower push
scope when adopting it. This release does not update the separately published DSH
companion package; its documented v2.15.0 artifact and compatibility evidence remain
unchanged.

# memory-bank v2.15.0

Adds required amendment milestones and deferred options so implementation discoveries
can have their own owners without continually expanding the original milestone.

- Required repairs use `amend-M53-01.md`; optional work uses `option-M53-02.md`.
  Both share a permanent child-number sequence and declare their parent. Required
  amendments retain the parent's original acceptance and review gate. Options do
  not block parent closure. External testing-tool repair is optional unless the
  owner explicitly promotes it.
- `OPTION_POLICY: confirm` consolidates options after parent closure and waits for
  an actual owner answer. `ignore` leaves them deferred throughout the goal.
  Planning refreshes preserve the resolved policy and existing authorization.
- The API controller binds child filenames in approved receipts, enforces amendment
  prerequisites for pending and resumed rows, and inherits family priority without
  adding dependency edges. A prior parent's acceptance can be reused from private
  receipts only while its specification, status, required amendments and declared
  implementation inputs remain current.
- Child retirement supports closing-row changes and subsection headings while
  preserving source and earlier evidence. Required successor owners and review
  gates still block premature parent retirement. Explicitly declined rowless
  options can retire without invented implementation tasks.
- Crash recovery verifies a resumed blocked row against its original claim,
  approved prerequisites and exact commit evidence. Option claims remain visible
  to the global ledger ownership gate. Root specifications and initialization
  checks retain their guards; record ID validation is shared across components.

The stock goal protocol has changed. Adopting its new fingerprint in an existing
paused goal requires the existing identity-transition approval; installation does
not approve that transition, migrate project rules or reset grants, attempts and
review counters. Protocol registries are regenerated from published release tags.

# memory-bank v2.14.0

Adds offline milestone reflection and run reporting, and tightens the API runner's
dangerous-command filter. v2.13.4, tagged earlier, already contained these
changes; this release is the version that names them.

New in this release, all optional and off by default:

- Offline milestone reflection: `tabilet-audit reflect` drafts suggested edits to
  `tech-stack.md` and `lessons.md` from a milestone's recorded runs, and
  `OPTIMIZE_POLICY` / `--optimize confirm|auto` runs it when a goal milestone
  closes. It needs auditing enabled and `tabilet_reflect.py` installed, spends at
  most 10% of the milestone's recorded time, and a report made without a model
  proposes no edits. The proposal is written to a Git-ignored path that
  `tabilet-audit audit enable` sets up; rerun it on a project enabled earlier.
  `reflect --check` lists the model backends it found. Agent CLI backends run from a
  temporary directory, and `--probe` starts only a project test runner.
- `--format trajectories` exports per-task trajectories to an explicit path outside
  the project or Git-ignored.
- `RUN_REPORT` makes the API runner append one JSON line per invocation to an
  absolute path outside the repository.
- The runner's dangerous-command filter also blocks `git checkout --`, its long
  options and `-f`, and `rm -rf` of `~/*`, `$HOME/*`, `"$HOME"` and `${HOME}/*`; a
  credential-free trap suite pins each case.

The goal protocol text is unchanged from v2.13.4; only its recorded version moves, so
`GOAL_IDENTITY` hashes stay valid and no paused goal needs fresh approval.

# memory-bank v2.13.4

Remediates review findings against v2.13.2 and v2.13.3, which added light
testing profiles and the standing revision envelope; neither release carried
notes, so their content is summarized here.

- v2.13.2: `--test` profiles (`browserlight`, `golight`, `rustlight`,
  `tslight`, `jslight`, `pythonlight`) and the Execution cadence, Replacement
  coverage and Acceptance readiness rules, plus a fast preflight before counted
  attempts.
- v2.13.3: an optional `standing` grant block and
  `SCOPE_POLICY: workspace-contained` revision envelope for iterative local
  verification.

Changes in this release:

- The envelope is defined once, in `GOAL.md`, and every other document points to
  it. It reaches only effective unprivileged workspace-local verification
  (`cli.local`); `sudo`, `ssh`, live browser and `git.push` grants never gain it,
  and a revised artifact there is a changed scope needing fresh approval.
  `/tmp` and `$TMPDIR` are outside the workspace unless the grant lists them.
- `standing.budget` is owner-held and persisted, reserved before each run, counts
  failed and cancelled runs, and replaces the gate's default only when a human
  approved the number. Presets decide only which explicit grants planning writes
  into launch input; the executor never infers a preset from `SCOPE_POLICY`.
- `strict` stays exact-match for scope resolution; a `standing` block is the one
  documented addition and only for local verification grants.
- The API runner prompt no longer mentions the envelope or grants, and its
  embedded twin matches the prompt copy.
- Testing standards: `standard` adds no constraints; light profiles, execution
  cadence and the 3-attempt gate read the same in the template, planning
  contracts and `AGENTS.md`.
- `check.py` parses grant fields independently of order, rejects an empty
  `scope:` before or after `standing:`, blanket booleans, wildcards, credential
  keys and unknown keys inside `standing`, a budget outside 1 to 3, undocumented
  stop conditions and a `standing` block on a privileged grant. The docs carry a
  linted `standing:` example, and each lint rule has an isolated test.
- The Simplified Chinese goal guide again states that a changed scope needs
  fresh approval.

The stock goal protocol changed, so `GOAL_IDENTITY` records a new hash and
paused goals pause for approval at resume under the existing rules. The
v2.13.2 and v2.13.3 tags are kept at their original commits.

# memory-bank v2.13.1

Upgrade now checks maintained incoming links before proposing removal or
reduction of a package-owned stock protocol. Current execution references name
the bundled protocol; historical references retain their original revision/path
and approval meaning. Frozen records remain byte-for-byte unchanged, and an
unresolved required reference preserves the file pending an approved solution.
Negative contract fixtures cover missing link inspection, lost historical
context, frozen-record rewriting and premature removal. These are instruction
guards, not runtime link-repair enforcement.

API setup guidance distinguishes plugin upgrades from separately installed
executables, documents explicit mapping of custom model/base-URL variables for
Anthropic-compatible gateways, and clarifies the obsolete `TABILET_AUDIT_DB`
setting. No provider credential, audit opt-in or execution authority changes.

The stock goal protocol bytes are unchanged from v2.13.0; a package-version
label alone does not change `GOAL_IDENTITY`. This patch makes no DSH companion
release or marketplace catalog update.

# memory-bank v2.13.0

Protocol and addendum fingerprints normalize CRLF to LF, with LF checkout rules
for bundled protocols and registries. Tagged fingerprints remain available when
a working protocol changes without a package-version bump. Identity compares
hashes, selected paths and package classifications; release-label aliases alone
do not interrupt a run. Fresh legacy launch references without identity get an
explicit resolution and missing-approval transition, preserving grants and limits.

Installation guidance now uses v2.13.0 with matching instructions and complete
bundles. Corrective suspension resumes through its authorized interactive owner;
API launchers retain their existing row and authorization gates.

Contract guards cover operative entrypoints and the extracted API instruction,
use consistent token normalization, and check delegation to the governing
protocol. These are static instruction checks, not runtime approval enforcement.

Approval email validates bounded UTF-8 worker input before reservation and
starts a waiting worker before creating an attempt record. A launch failure
can be corrected without permanently suppressing an unattempted alert; uncertain
post-dispatch outcomes still never replay automatically. Argument errors return
sanitized JSON. Email tests avoid creating bytecode in shipped bundles.

Goal and interactive Next accept opt-in `MODEL_POLICY`: users choose the models
for ordinary work and fresh read-only whole-milestone reviewers from any provider
supported by their host. Effort settings are optional and host/model-specific;
omission preserves the selected model's host default. No OpenAI model or account
is required. Omission of the entire policy preserves host settings.
Unsupported or unverifiable settings pause affected work for an explicit
replacement policy. Review lenses may be combined or batched within host
capacity; the coordinator alone records one report and applies fixes, retaining
the review counter and iteration-10 stop. This is instruction-level host
selection; Python API model selection and authorization are unchanged.

Lease cleanup now inspects ignored artifacts and preserves cited qualification
and recovery evidence before removing a clean merged worktree. Retention hashes
and maintained references are verified before freezing retirement records;
uncertain retention or frozen citations that still need the lease preserve it.

Planning refreshes launch input without requiring a package-local protocol and
preserves explicit `GOAL_PROTOCOL`, actual identity and `MODEL_POLICY`. Missing
or incompatible selection pauses refresh instead of replacing it with stock.
Legacy paused goals need approval for changed or uncertain protocol identity,
without resetting grants, denials, counters, attempts or limits. The registry
retains the published v2.12.0 stock fingerprint.

Expand–contract applies when a bounded green change or compatibility transition
needs it. Defect reproduction is preferred when safe within authority and
budget; unavailable reproduction records evidence and limitations while
preserving acceptance gates. Whole-milestone reviews include uncommitted work
and still assess acceptance when no implementation diff is required.

# memory-bank v2.12.0

v2.12.0 moves the goal protocol into the skills and adopts several ideas from a
study of `mattpocock/skills`. The seven skills and the v2 project layout are
unchanged.

**The goal protocol is plugin-level.** The stock `GOAL.md` now ships inside the
init, goal, propose, reconcile, and upgrade bundles, each with a byte-identical
`goal-protocol.json` holding its version, hash, and the fingerprints of every
released stock copy, so resolution works offline and in plain-file installs.
Projects no longer receive a copy, and `template/` carries none. A package's
optional `tabilet/GOAL.md` is now a **project addendum**: it adds rules and
narrows defaults, is combined with the stock protocol at run time, and can never
weaken the review gate, authorization, ownership, verification, or retirement
rules. A request that names `tabilet/GOAL.md` (or "the memory-bank goal protocol")
selects stock plus addendum; only `GOAL_PROTOCOL: <path>` selects a different full
protocol. A byte-identical stock copy is ignored and reported as removable, and a
modified full copy stops the run until you reduce it to the project-specific part.
Goal state and launch input record a `GOAL_IDENTITY` block (the protocol hash and
every participating package's addendum hash, `ignored-stock <version>`, or
`none`), rechecked at every resume and child dispatch; any change pauses the
affected work. Upgrade classifies an existing `tabilet/GOAL.md` and proposes
removing a stock copy or reducing a modified one; it never writes a merged
protocol. This changes goal-protocol compatibility: a modified full project
copy blocks goal execution until explicitly reconciled, while a recognized
stock copy is ignored in favor of the bundled protocol. A paused run still
requires approval for a changed or uncertain identity; installation does not
approve that transition. Ordinary project addenda remain applicable.

**Lease cleanup.** The governing protocol now removes a finished lease worktree
and its branch after recorded closure, and a resume sweep removes leftovers only
when closure and integration are recorded, ownership matches, no writer is
active, and the branch is merged with a clean worktree. A lease just created at
the integration tip, or one interrupted before closure, is preserved.

**Review and planning.** The review fan-out gains an Acceptance & Scope lens
(missing or partial requirements, behavior nobody asked for), pins the base commit
before reviewing, and groups findings by lens. Planning gains expand–contract
sequencing for wide refactors and an Out of scope register for ruled-out work.
Closure includes an environment retro: mechanical mistakes become proposed
deterministic checks, judgement calls become lessons, and environment candidates
are reported most severe first without becoming unapproved rows. Defect rows first
establish a command that goes red on the reported symptom. Delegated goals can
share one out-of-repository exploration pass through context pointers.

**Smaller template `AGENTS.md`.** The corrective-planning, email, and
authorization bullets became pointers to their authoritative sections, and the
suspend/resume mechanics moved from the status-file preamble into
`milestone.md`. `check.py` bounds the file's size and keeps each policy pinned in
one place. Downstream projects adopt the new rules through a later
memory-bank-upgrade run.

# memory-bank v2.11.0

Goal and Next support human-approved `CORRECTIVE_PLANNING: auto` for necessary
repairs within the original delivery outcome, existing grants and explicit
limits. The owner prepares and checks complete planning actions, may amend
pending work or create repair milestones, and refreshes dependency/launch/hash
state without another confirmation. Frozen history, review counts and limits
remain preserved. Nested Reconcile may use standing approval and hand execution
back; standalone Reconcile retains its gate. Init and Propose dangerous presets
propose `auto`, sandbox/least propose `confirm`, and human overrides win.

Interactive Goal/Next accept `--email ADDRESS` for approval alerts through an
optional Cloudflare REST helper, bundled without third-party Python dependencies.
Private account configuration, permitted recipients and a sending token are
required. Readiness checks are local-only; attempts are reserved before POST,
duplicates or uncertain sends never replay automatically, and provider queuing
does not prove inbox delivery. Email never approves work. This first version
covers workflow approval requests, not native host tool prompts. The Python API
runner/controller consume neither feature. Email delivery was verified with
offline fixtures; users configure the sender separately and explicitly adopt
workflow updates in existing projects.

Nested Reconcile verifies the invoking approval provenance before standing
planning writes. Corrections cannot weaken acceptance or cancel unmet work,
and repair milestones cannot evade the originating bounded review counter.
Suspended tasks use explicit `[~]` → `[!]` → `[~]` prerequisite handoffs while
preserving partial work. Interactive controls live outside the API task prompt.
The email helper now handles protocol/UTF-8 failures, rejects line/bidi controls,
resolves XDG defaults lazily, and supervises a 10-second total network deadline.
DSH preflight requires complete notification and interactive resources.

# memory-bank v2.10.3

Light `--test` profiles now separate focused tests from full regression: a
30-second focused-test target with a two-minute cap, 20 minutes for full regression,
and five minutes for applicable UI/race checks. Explicit project budgets win;
`standard` remains unconstrained. Init, Propose and Reconcile bundle the same
profile reference, preserve existing settings on update, and record compilation
separately from test execution. Go profiles allow the CGO needed for supported
race checks. Required physical coverage remains owned by the final release gate.

# memory-bank v2.10.2

v2.10.2 introduces declarative verification and testing profiles (`--test <profile>`) across planning skills and memory-bank templates to enforce bounded, fast test cycles during iterative execution:

- **Verification Profiles (`--test standard | browserlight | golight | rustlight | tslight | jslight | pythonlight`)**:
  - `standard` (Default): Standard unconstrained verification planning.
  - `browserlight`: Enforces strict offline, fast loopback testing (< 30s budget, synthetic fixtures/mocks). Prohibits heavy test ceremonies during routine tasks—no physical X11/Xvfb display servers, custom supervisor daemons, kernel process debugging, or multi-GB disk snapshots. Restricts real browser binary and physical end-to-end execution strictly to the single final release smoke test.
  - Language-specialized profiles (`golight`, `rustlight`, `tslight`, `jslight`, `pythonlight`): Inherit `browserlight` and prescribe language-native fast loopback fixtures (e.g. `httptest.Server`, `wiremock`, `msw`, `responses`, isolated temporary directories) while excluding unmocked e2e suites from default routine loops.
- **Contract & Template Injection**:
  - `memory-bank-init`, `memory-bank-propose`, and `memory-bank-reconcile` accept `--test <profile>` and inject `## Verification and testing standards` into `tabilet/memory-bank/tech-stack.md`.
  - Injects an enforcement rule into `AGENTS.md` under `## Hard Rules` when a non-standard profile is chosen, binding agent execution to the tech-stack testing budget.
- **Documentation & Asset Parity**:
  - Updated `README.md`, `docs/init.md`, and `docs/zh/init.md` (1-for-1 locale parity).
  - Synchronized `skills/memory-bank-upgrade/assets/template/` to maintain byte-identical template parity.

# memory-bank v2.10.1

v2.10.1 fixes invalid YAML front matter shipped in v2.9.0 and v2.10.0:

- **`memory-bank-init` is loadable again by strict YAML loaders.** Its
  `argument-hint` began with `[` (`[--stages] [--environment ...]`), which is not
  valid YAML. Claude Code tolerated it, but DSH and other strict loaders dropped
  the skill, so only six of the seven skills loaded. The hint is now quoted.
  `memory-bank-upgrade`'s hint, which parsed as a list instead of a string, is
  quoted too.
- **`check.py` lints front matter.** An unquoted value that starts with a YAML
  indicator character such as `[`, or contains `: `, now fails the repository
  check, with a unit test that includes the exact shipped defect.

No skill behavior, protocol or template changes. Use v2.10.1 rather than v2.9.0
or v2.10.0 with strict loaders.

# memory-bank v2.10.0

v2.10.0 adds bounded handling for expensive or protected checks. It follows a
downstream project that spent 26 counted runs on one physical qualification
row. Containment itself passed early, but each run was cut short by an unrelated
producer step, low-fidelity diagnostics and missing stop rules.

- **Bounded verification-attempt gate.** `GOAL.md` and the template
  `milestone.md` cover expensive or protected checks: privileged setup, scarce
  hardware or quota, physical or live environments, granted actions, or long
  runs. For these:
  - diagnose first in the cheapest reproducing environment;
  - run every independent case and report all failures;
  - keep raw diagnostics from synthetic fixtures in private, ignored artifacts;
  - persist the attempt count, and stop to ask after three consecutive
    same-stage failures or a failure outside the milestone's owned scope.

  `memory-bank-next` follows the same gate.
- **Expensive-check planning.** The template "Requested changes" and "New review
  intake" sections, Propose and Reconcile's `plan-update.md`, and Init's write
  contract now:
  - limit acceptance to behavior the milestone owns;
  - leave real producer or consumer pairing to the adopting milestone;
  - schedule a cheap readiness probe for needed host capabilities;
  - name an uncounted diagnostic loop.
- **Fixture browser authority.** A `browser` requirement may use `goal-policy`
  when its scope declares `environment: fixture`: disposable synthetic pages
  with no real origin, credential, saved session or user data. Every other
  browser environment still needs explicit authority. `check.py` and its tests
  enforce the distinction.
- **Current-state status records.** The status template and `GOAL.md` replace
  superseded checkpoints instead of appending dated narrative, and prune bulky
  disposable artifacts at closure.

# memory-bank v2.9.0

v2.9.0 introduces the declarative `--environment` option across planning skills and the API harness runner:

- **Declarative Planning Stance (`--environment dangerous | sandbox | least`)**: Adds `--environment` to `memory-bank-init`, `memory-bank-propose`, and `memory-bank-reconcile`, establishing the hands-free authorization stance from day one:
  - `dangerous`: Synthesizes maximal hands-free autonomous execution defaults (`SUGGESTED_UPDATE: auto`, `SCOPE_POLICY: workspace-contained`, `COMMIT_POLICY: task`, and ambient `GLOBAL:` grants with `[~]` for verification and `[+]` for git push to authorized workspace organization remotes). Destructive or privileged actions (`sudo`, `ssh`, live browser, or foreign repository remotes outside the active workspace directory) remain strictly ungranted (`[ ]` or omitted) unless an explicit modifier authorizes them. Includes recommended runner flags in launch comments (`# Recommended harness flags: ALLOW_UNSANDBOXED_SHELL=1`).
  - `sandbox` (Default): Synthesizes standard fail-safe policies (`SUGGESTED_UPDATE: confirm`, `SCOPE_POLICY: strict`, `COMMIT_POLICY: task`, and `AUTHORIZATION_GRANTS: {}` or proposed grants marked `[ ]`).
  - `least`: Synthesizes strict least privilege (`SUGGESTED_UPDATE: confirm`, `SCOPE_POLICY: strict`, and `AUTHORIZATION_GRANTS: {}`, requiring manual confirmation for all actions).
- **Natural Language Modifiers**:
  - `plus <action>` (e.g. `--environment dangerous plus sudo`): Adds explicit approval (`[+]`) for `<action>` in the milestones/tasks requiring it, and emits recommended runner flags (`ALLOW_DANGEROUS_COMMANDS=1`).
  - `minus <action>` / `deny <action>` (e.g. `--environment dangerous minus git.push`): Sets `<action>` to `[-]` (denied).
  - `but <action> in milestone <status-XNN.md | MNN>` (e.g. `--environment least but cli.local in milestone status-X00.md`): Attaches a milestone-specific policy override directly to the milestone specification in `tabilet/memory-bank/milestone.md` without polluting global launch input.
- **API Runner Integration (`harness/tackle-memory-bank-api-loop`)**: Adds `--environment {dangerous,sandbox,least}` CLI argument and `LLM_ENVIRONMENT` environment variable:
  - `--environment dangerous`: Auto-acknowledges model-controlled host shell access (`ALLOW_UNSANDBOXED_SHELL=1`), clearing exit code 14 without extra flags. The `DANGEROUS_RE` guardrail remains active unless `--allow-dangerous` is passed.
  - `--environment sandbox` (Default): Retains standard behavior (requires explicit `ALLOW_UNSANDBOXED_SHELL=1`).
  - `--environment least`: Strictly enforces sandboxing; permits execution inside verified container environments (`/.dockerenv` or `TABILET_CONTAINER`) while disallowing unsandboxed host shell access (exits code 14).
- **Cross-Repository Alignment**: Synchronized bootstrap guides (`AGENTS.md`, `template/AGENTS.md`), template milestone guidance (`template/.../milestone.md`), upgrade assets, and documentation (`README.md`, `docs/authorizations.md`, `docs/automation.md`).

# memory-bank v2.8.1

v2.8.1 refines multi-package autonomous goal execution under `GOAL.md` and provides comprehensive authorization guidance:

- **Bounded Scope Policy (`SCOPE_POLICY: workspace-contained`)**: Introduces `SCOPE_POLICY: strict | workspace-contained` in `GOAL.md`. Under `workspace-contained`, the orchestrator automatically binds `git.push` and `cli.local` to sibling repositories within the approved workspace root directory (e.g. `~/Workspace/*`) and matching authorized remote organization URLs (e.g. `OpenUdon/*`), eliminating repetitive interactive prompts when sibling repositories are integrated. Non-workspace paths, foreign public remotes, and privileged commands (`sudo`, `ssh`) remain strictly bound.
- **Milestone-Attached Policy Overrides**: Enables milestone specifications in `tabilet/memory-bank/milestone.md` to attach local policies and requirement overrides (`POLICIES:` or milestone-scoped `AUTHORIZATION_OVERRIDE`). Milestone-attached policies take precedence over global launch defaults in `suggested.txt` during that milestone's lease, allowing launch references to stay concise (~30 lines) while preserving strict local constraints.
- **Authoritative Authorization Reference**: Adds `docs/authorizations.md` documenting all 10 manual authorization cases, hands-free configuration levers, milestone override rules, multi-repo workspace examples, and the complete decision marker reference.
- **Child Brief Alignment**: Synchronizes `subagents.md` so delegated child briefs inherit `SCOPE_POLICY` and milestone-attached policy overrides while preserving worker non-expansion invariants.

# memory-bank v2.8.0

v2.8.0 introduces autonomous goal execution under `GOAL.md` and refined human authorization controls:

- **Autonomous Launch Reference Refresh (`SUGGESTED_UPDATE: auto`)**: Authorizes the orchestrator (e.g. `agy`, Claude Code, Codex) to refresh `suggested.txt` across milestone closures within the approved active horizon (pruning completed milestones, updating dependency order, activating triggered conditional milestones) and continue execution without pausing for re-confirmation. The default `SUGGESTED_UPDATE: confirm` pauses whenever `suggested.txt` changes.
- **Grant Decision Markers**: Proposed grants in launch references and `suggested.txt` use checkbox decision markers consistent with task ledger vocabulary: `[ ]` (need authorization), `[+]` (approve), `[-]` (deny), and `[~]` (auto).
- **Top-Level `GLOBAL:` Ambient Authority**: Declares common scopes (such as declared local verification or git push) applicable across all tasks in a goal, preventing repetitive milestone declarations while allowing individual milestones to narrow or reject them.
- **Launch Checksum Verification**: Mandates matching the SHA256 checksum of `suggested.txt` against human approval before activating grants.
- **Autonomous Execution Guide**: Adds `docs/automation.md` detailing the autonomous multi-milestone execution model, prerequisites, and non-bypassable human safety boundaries (secrets/credentials, 10-iteration review ceiling, ambiguity, and parallel rebase conflicts).
- **Consolidated Controller Specification**: Consolidates 10 historical draft files into `docs/api.md`, providing a unified technical specification for the Tabilet API controller, Docker sandbox limits, and the authoritative `tabilet.api.receipt/v1` schema table.

# memory-bank v2.7.1

Milestone specifications may declare optional `AUTHORIZATION_REQUIREMENTS`.
The resolved human-approved goal request may carry `AUTHORIZATION_GRANTS`
for exact milestone assignments, including package-qualified keys. Declarations
and proposed launch grants establish no permission. Effective grants require
explicit human approval of concrete scope, preserve commit and external-mutation
policies, and are narrowed for children; read-only reviewers have no mutation
authority. Missing authority pauses affected work and dependents. Required
unperformed actions prevent closure, and uncertain side effects cannot replay
automatically on resume.

Init, Propose, Reconcile, Next, Goal, and Upgrade guidance, project templates,
and public guides describe these instruction-level boundaries. Adoption is
explicit; field omission preserves legacy behavior without new authority or
automatic migration. No audit dependency or grant-consuming runtime is added.
The Python API controller continues to exclude external actions. Host/tool
permissions and credentials still apply. Contract checks guard the documented
rules and examples; they do not enforce runtime permissions.

Generated launch references always include `AUTHORIZATION_GRANTS`, using `{}`
for the default with no explicit grants. Upgrade proposes updates to existing
`tabilet/GOAL.md` and `tabilet/memory-bank/suggested.txt`, preserving custom
restrictions and explicit policies. It reconciles launch input against current
project truth, marks proposed grants as unapproved, and applies the complete
file-action proposal only after approval. Missing optional files stay absent by
default, compatible files yield a no-op, and no upgrade starts execution.

# memory-bank v2.7.0

v2.7.0 records API token usage in the optional audit. When audit is enabled, the
runner and controller write one `usage_observed` event per run, just before
`run_finished`, with total input, cached-read, cache-write, and output tokens
and the turn count. Counts only; an unreported field is `null`, and nothing gates
on it. Failed and interrupted runs keep the totals gathered so far.

The event type raises the toolkit interface from 3 to 4. Reinstall the runner,
controller, and the audit, index, host, and Explorer modules together; the runner
refuses to record against older audit modules and reports the usual
reinstall-together gap without changing any row gate. No database schema change
or migration is needed, existing databases keep working, and `prompt_cache_key`
is not sent: OpenAI documents it for Responses, not Chat Completions, and
routing is automatic on current models.

# memory-bank v2.6.2

v2.6.2 is a patch release following v2.6.1. It fixes the optional SQLite audit
and index CLI on Windows: v2.6.0 and v2.6.1 failed every `index` command with
`ModuleNotFoundError: No module named 'fcntl'`, because the CLI loads the runner
for its parsers and the runner imported `fcntl` unconditionally. The import is now
optional. Where POSIX file locking is unavailable the shared project lock refuses
cleanly, and API-runner execution remains POSIX-only. A regression test and the
Windows CI job cover it. No project, skill, or schema changes.

# memory-bank v2.6.1

v2.6.1 is a patch release following v2.6.0. Planning's remote-review fetch no
longer crashes on Python 3.9 when an HTTP redirect or error response has no body:
it closes the error only when a body exists, and still reports the redirect or
status as a planning error. The Docker endpoint unit test now stubs the `docker`
lookup instead of requiring Docker to be installed. The full unit suite passes on
Python 3.9. No project, skill, or schema changes.

# memory-bank v2.6.0

v2.6.0 keeps the seven skills and the v2 project layout. It adds project-local
SQLite audit storage, tighter goal delegation, and provider prompt caching with
normalized token reporting for the API runner and controller. Reinstall the
optional toolkit files together; updating skills alone does not update the
installed runner or controller.

Each project manually enables audit with `tabilet-audit audit enable PROJECT`.
The saved preference and audit/index data live in `tabilet/audit.sqlite3`;
registered linked worktrees share the primary checkout's file. Setup preserves
`tabilet/.gitignore` and adds `/audit.sqlite3*`. Index refresh never enables
recording. `audit disable` preserves history, while deleting the database returns
the project to disabled. Database path options and environment overrides are
removed. The Python CLI provides the same commands on Linux, macOS, and Windows.
The seven skills check the saved setting; runners preserve their row gates when
audit fails. Controller containers mount existing audit files read-only.

Goal execution now distinguishes strict `STATUS_ORDER` from dependency-ready
dispatch using `STATUS_PRIORITY`. Parallel contract checks cover reads and
writes in both directions. Fresh-agent briefs carry the resolved goal policies,
user restrictions, and actual integration branch instead of assuming `main`.
Under milestone commit policy, one unpublished aggregate checkpoint supports
lease review; the owner includes verified closure before finalizing and
fast-forwarding a single milestone commit.
Delegated execution now assigns one explicit milestone and status file to each
child. Only the orchestrator refreshes shared `suggested.txt` launch input, and
child diffs are checked for writes outside their assignment before integration.

Explorer's first "Create index" now installs the `/audit.sqlite3*` ignore rule
like the CLI, so a new database cannot be left untracked or committed. Read-only
CLI commands validate the current-directory project, so a database copied into
another checkout is rejected instead of silently read.

The API runner and controller now order requests for provider prompt caching.
The standalone first message puts the reusable instructions first and the
repository path, run counter, and lane table after them, so consecutive runs
share about 1,500 tokens of prefix. OpenAI and DeepSeek cache automatically; the
reorder is the whole change. Direct Claude (`api.anthropic.com`) now receives up
to two `cache_control` breakpoints: the end of the stable prefix and the newest
message. `LLM_PROMPT_CACHE=auto|on|off` (default `auto`, official host only) and
`LLM_PROMPT_CACHE_TTL=5m|1h` control this; an invalid value exits with code 2.
Other endpoints keep their previous payload byte for byte. Prefixes below a
model's minimum, such as Opus 4.6/4.7 and Haiku 4.5, are not cached.
Each turn prints a normalized usage line (input, cached read, cache write,
output; `unknown` when a provider does not report a field) with run totals. The
controller adds totals to its progress line and keeps four small counters in the
receipt `usage.tokens`. Nothing skips a model call or weakens a gate.

The SQLite lookup reader recognizes exact backticked historical `[x]` task
completion cells only in valid completed retirement records with passed review.
It preserves frozen source bytes, hashes, physical lines, and literal search text,
and reports each adaptation. Active parsing and execution remain strict;
uppercase `[X]` retains cancellation meaning. Projection refresh automatically
reparses older cached documents without changing the audit database schema.

# memory-bank v2.5.1

v2.5.1 is a protocol and documentation patch release following v2.5.0:

- **Protocol Specification Fix:** Resolved a contradiction in the portable
  `GOAL.md` header example where `COMMIT_POLICY: none` was shown alongside
  `PARALLELISM: 3` and `INTEGRATION: local-rebase-ff`. Tier 1 safe parallel
  execution requires `COMMIT_POLICY: task` or `milestone`; the portable example
  now specifies `COMMIT_POLICY: task` across all byte-identical copies.
- **Review Fan-Out Timing Accuracy:** Clarified review fan-out timing in
  `docs/subagents.md` and release notes to reflect measured parallel cycle times
  (~3 minutes per iteration) without unbenchmarked serial duration claims.
- **Migration Test Clarity:** Added explanatory commentary in the migration test
  suite documenting the stock v2.0 baseline goal hash invariant.

# memory-bank v2.5.0

v2.5.0 introduces the complete sub-agent execution architecture and parallel-safe
milestone modeling for multi-milestone workflows under `tabilet/GOAL.md`.

- **Tier 0 Sequential Handoff & Read-Only Parallel Fan-Out:** Ephemeral sub-agents
  receive fresh, distilled context briefs per milestone, completely bounding prompt
  growth and eliminating quadratic context inflation. Review gates fan out across
  orthogonal, read-only inspection lenses (Correctness, Security, Tests) and
  downstream reconciliation in parallel, completing review cycles in approximately
  3 minutes per iteration while catching complementary defects.
- **Tier 1 Concurrent Worktree Leases (Opt-In):** Projects can opt into concurrent
  leases executed in isolated external worktrees outside the project root
  (`../<repo>.goal/<ID>`) with `PARALLELISM: N` and `INTEGRATION: local-rebase-ff`.
  Each lease implements tasks with one `[~]` row at a time, verifies in isolation,
  rebases onto `main`, and runs its authoritative review gate inside the lease.
  Integration into `main` uses fast-forward only (`git merge --ff-only`), strictly
  preserving one commit per status row and linear Git history without merge commits.
- **Parallel-Safety Specification Fields:** Milestone specifications declare
  `Write set`, `Contracts read`, `Shared verification resources`, and
  `Parallel-safe` (defaulting to `no`). Two milestones run concurrently only when
  unconnected by dependencies, with disjoint write sets, and reading no contracts
  the other changes.
- **Documentation & Bilingual Mirror:** Shipped the Sub-Agent Milestone Execution
  guide (`docs/subagents.md`) and its complete Simplified Chinese translation
  (`docs/zh/subagents.md`) with 1-to-1 parity, explicit ASCII heading anchors, and
  strict navigation integration.

# memory-bank v2.4.0

v2.4.0 keeps the seven skills, project format, and optional controller from
v2.3.0. The optional SQLite index now reads frozen retirement records headed
`## Full status document` as well as the older `## Status` heading. This
normalization happens only while indexing: frozen Markdown keeps its original
bytes and line numbers, and the execution runner's retirement validation stays
strict. The bundled skills remain compatible with v2.3.0 projects; no project
migration or database schema change is needed.

The DSH companion v2.4.0 pins this release and adds read-only browsing of the
selected project's external SQLite audit and Markdown index in its sidebar.
Explorer installation and automatic API-runner auditing remain separate options.

# memory-bank v2.3.0

v2.3.0 combines optional stage-aware planning with the Tabilet API controller
prepared in the unreleased v2.2.0 candidate. Init can create `tabilet/stages.md`
for a medium or large project, giving later stages stable `STG-` IDs while
planning milestones only for the current stage's next verifiable outcome.
Later stages may start with tentative names and one-sentence ideas. Propose can
refine a stage or explicitly rescope pending work after approval. Projects
without `stages.md` keep the existing one-stage workflow.

The optional controller works alongside the standalone one-row runner. It uses
the canonical planning skills, shows one exact proposal and bounded local
horizon for confirmation, and executes task commands in a networkless local
Docker container. Project Markdown remains authoritative; the seven skills and
template stay usable without the controller.

- `tabilet chat`, `status`, `resume`, and `extend-limit` provide planning,
  read-only state, crash reconciliation, and separately confirmed limit changes.
  Private receipts persist approvals, cumulative caps, task and closure evidence,
  and recovery proofs outside the project.
- Host commits retain the standalone runner's shared post-commit gates and add
  controller pre-commit row and required-check validation. Docker mounts the
  project writable and `.git` read-only, disables networking, and rejects
  unsupported Git topologies, active custom filters, and command-launching Git
  configuration.
- A clean verified closure completes a horizon automatically. Dirty or
  uncertain interruptions require manual review and are never reset or replayed
  automatically. External actions remain separate from the general confirmation.
- The installer packages all seven canonical skill bundles with a generated
  SHA-256 manifest and installs the controller without requiring a source
  checkout at runtime. Credential-free fake-provider tests and a Docker
  acceptance CI job cover the command path and sandbox.
- The optional SQLite index now reads older retirement envelopes and resolves
  sibling milestone dependencies without changing frozen Markdown records.

Paid live-model acceptance must be explicitly invoked under the documented
US$10 provider budget; no paid run is implied by these notes.

# memory-bank v2.1.0

v2.1.0 adds an optional SQLite audit and Markdown lookup toolkit. Project
Markdown stays authoritative, and the v2 project layout is unchanged; no
migration is needed. Auditing is off unless `TABILET_AUDIT_DB` names a database
outside every project. Installation and read commands never create one.

- `tabilet-audit` records workflow runs, observed events, instruction
  provenance, conversation coverage, and selected visible messages. Message
  capture is metadata-only by default, and an explicit purge keeps the envelope,
  hash, and tombstone while removing content.
- A rebuildable index covers milestones, tasks, retired history, knowledge,
  evolution, and archives, with full-text search when SQLite provides FTS5 and a
  literal fallback otherwise. Sync is explicit and never writes project files.
- A loopback-only explorer shows Overview, Timeline, and an advisory To-do view.
  Follow-up buttons prepare copyable text; they never run an agent or edit
  Markdown.
- With `TABILET_AUDIT_DB` set, the API runner records its own runs. It still
  installs as one file when auditing is off, and its exit codes and gate order
  are unchanged. The seven skills gain a byte-identical optional audit
  reference; approvals and outcomes do not depend on it.

The toolkit needs Python 3.9 or later with the `sqlite3` module built against
SQLite 3.24.0 or later. Missing or older SQLite produces one clear message, and
the runner and skills record an audit gap and continue unchanged. The full test
suite passes on Python 3.9 and 3.14; Linux and macOS are the supported
platforms, and Windows is untested.

The template's milestone guide bounds historical retrieval: consult retired
records only when the current task needs them, and stop when the evidence
suffices. Existing projects adopt it through an approved Upgrade. The Medium
drafts are no longer part of the repository. The DSH companion is unchanged and
remains at its v2.0.0 release.

# memory-bank v2.0.0

New projects keep `AGENTS.md` at the root and place their goal protocol, active
memory bank, evolution snapshots, frozen archives, and retired history under
`tabilet/`. Existing v1.5.0 projects migrate only by running the explicit
preview/apply command bundled with Upgrade. The command leaves a reviewable,
uncommitted diff and preserves frozen records byte-for-byte. v2 skills and the
API runner stop on unmigrated projects. The DSH companion continues to show
v1.5.0 projects read-only with a migration warning.

The canonical repository retains `GOAL.md` at its root as the portable source;
the project template carries the identical copy at `tabilet/GOAL.md`.

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
