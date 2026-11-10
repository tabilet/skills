# Optional local audit

The user manually enables each project with `tabilet-audit audit enable PROJECT`.
The saved opt-in lives in that project's `tabilet/audit.sqlite3`; absent or
index-only storage leaves auditing disabled. Linked worktrees share their
repository's database and setting. Its location is fixed; environment variables
do not enable auditing or select another database.

If the optional `tabilet-audit` command is installed, inspect the current setting:

```bash
tabilet-audit audit status /absolute/project
```

Continue this reference only if the returned `enabled` is true. A disabled or
missing database creates no audit run. Never enable auditing, change `.gitignore`,
install the toolkit, or create storage to make logging work. If explicitly enabled
storage is unavailable or invalid, report an audit gap and continue the authorized
workflow. The API runner owns its own lifecycle; do not submit a duplicate run
for work already being recorded by that runner.

The database records observations, never authorization. All project write,
review-fetch, commit, and external-action approval rules still apply. Installing
or invoking this skill without a saved opt-in never creates a database.

## Lifecycle

1. After the layout gate passes, start one run with the operation matching the
   skill suffix (`init`, `archive`, `propose`, `reconcile`, `next`, `goal`, or
   `upgrade`). Use the absolute project root. Generate a run ID once and retain
   it in the conversation for retries. The command returns the workspace ID and
   resolved database path. For later commands, retain the project selector even
   if the shell's current directory changes:

   ```bash
   tabilet-audit audit begin /absolute/project next --run-id RUN_ID
   ```

   SQLite 13 records instruction provenance separately from the workflow
   operation. An interactive skill may declare its logical instruction set, but
   must not search for `SKILL.md` or installation paths. Unless the host supplies
   every loaded-resource hash, use unavailable fingerprint fidelity. Replace
   `INVOKED_INSTRUCTION_SET` with this invocation's logical skill name (for
   example, `memory-bank-archive`), never with a discovered file path:

   ```bash
   tabilet-audit audit begin /absolute/project next --run-id RUN_ID \
     --provenance - <<'JSON'
   {"invocation_kind":"interactive_skill","instruction_set_name":"INVOKED_INSTRUCTION_SET","capture_method":"instruction_driven","fingerprint_fidelity":"unavailable"}
   JSON
   ```

   Capture defaults to metadata. Use `--capture relevant` only when selected
   message capture was explicitly enabled. A child operation in a recorded goal
   uses `--parent-run-id PARENT_RUN_ID`; both must belong to the same project
   database, including registered linked worktree operations.

2. Submit observed actions with `tabilet-audit --project /absolute/project audit event --input -`, sending
   a JSON object on stdin using the host's structured input mechanism or a
   safely quoted heredoc. Retain each event ID for retries. Never interpolate
   user text into executable shell syntax. A minimal event is:

   ```json
   {
     "schema": "tabilet.audit.event/v1",
     "event_id": "EVENT_ID",
     "run_id": "RUN_ID",
     "workspace_id": "WORKSPACE_ID",
     "operation": "next",
     "event_type": "task_observed",
     "subject": {
       "milestone_id": "M01",
       "task_label": "Observed task label",
       "status_path": "tabilet/memory-bank/status-M01.md"
     },
     "details": {
       "schema": "tabilet.audit.details/v1",
       "capture_source": "agent",
       "fidelity": "summarized"
     }
   }
   ```

For explorer-ready records, add the optional `details.explorer` object to the
same event. It is a typed observation extension, not an authorization signal:

```json
"explorer": {
  "schema": "tabilet.audit.explorer/v1",
  "phase": "request",
  "summary": "User requested the next SQLite task",
  "message_refs": [{"message_id": "MSG_ID", "purpose": "request"}],
  "artifact_refs": [{"namespace": "task", "identifier": "M01/T01", "relationship": "observed", "path": "tabilet/memory-bank/status-M01.md", "line": 12}]
}
```

Use `request`, `proposal`, `approval`, and `applied` for the observed phase.
Artifact relationships `created`, `changed`, and `retired` describe completed
effects and are valid only in the `applied` phase. Use `proposed` before then;
a proposal is never evidence that a file or task changed.
Message references must belong to the same run; artifact references name only
observed or explicitly proposed files and rows. Do not put hidden reasoning,
credentials, or claims of a write that was not observed in this extension.

   Use `task_observed` for planning observations, with request/proposal/approval
   summaries and proposed or approved file actions in details. Record approval
   only after receiving it. Use `task_transition` with observed `old_state` and
   `new_state`, `verification_observed`, and `commit_observed` with the actual
   successful commit SHA. `milestone_accepted`, `milestone_retired`, `cancelled`,
   and `superseded` require their corresponding evidence; a terminal task alone
   does not establish acceptance. Never fabricate a timestamp: omit `occurred_at`
   when the observation time is unknown. The recorder supplies its own timestamp.

3. For explicitly enabled relevant capture, submit selected messages with
   `tabilet-audit --project /absolute/project audit message --input -`. Fields are `run_id`, `message_id`,
   `role`, `text`, `capture_source`, and `fidelity`; optionally include
   `redaction_note`. Agent-authored request/output summaries use source `agent`
   and fidelity `summarized` or `incomplete`. Exact raw user/output text requires
   capture supplied by the host, with source `host`. Do not reconstruct a raw
   transcript, include hidden reasoning, or submit credentials and unrelated text.

   Every recorded `text` value is limited to 1,024 characters. For a longer
   visible message, first write a <=1,024-character, evidence-focused summary:
   identify the request or decision, the relevant scope/constraint, and the
   observed approval, block, or outcome. Submit it as agent-authored
   `summarized` evidence. Use `incomplete` for a deliberately bounded excerpt
   or when the omitted text could change the meaning. The recorder rejects
   oversized text rather than silently truncating it or calling an excerpt exact.

   Record the observed coverage separately, including missing evidence. Use
   `skill_conversation` and `instruction_driven`; `complete` is valid only when
   all permitted visible messages were supplied. A host-provided record submitted
   afterward uses `imported` and retains its original fidelity:

   ```bash
   tabilet-audit --project /absolute/project audit coverage --input - <<'JSON'
   {"coverage_id":"RUN_ID:coverage","run_id":"RUN_ID","scope":"skill_conversation","coverage":"missing","content_state":"none","capture_method":"instruction_driven","reason":"host did not provide visible message text"}
   JSON
   ```

4. Finish with `tabilet-audit --project /absolute/project audit finish RUN_ID RESULT --reason "observed outcome"`. Results are
   `completed`, `blocked`, `failed`, `cancelled`, `interrupted`, or `unknown`.
   Choose from observed evidence, independently of process exit or a commit.
   Supply the observed reason, especially for a non-completed result. Legacy
   calls without a reason are accepted and explicitly marked as missing it.
   Finish refreshes the current Markdown index; failures are reported as gaps.
   Waiting for user approval is not successful completion. Retain the run while
   waiting, or close it as blocked and start a new run when work resumes. Abrupt
   interruption may leave a run unfinished; never infer that it completed.

Logging failure never undoes work, changes status, retries a task, or changes the
commit policy. Report gaps in the final handoff. Before execution or a planning
write, reread the live Markdown even if an index lookup helped locate it.

### Typed task, verification and review observations

When auditing is enabled, prefer the typed commands below to free-form event
details. They record observations only: they do not execute tests, update
Markdown, advance a review counter or grant authority. Keep the event and
attempt IDs for retries. Identical retries are idempotent; conflicting reuse
fails. A missing event remains a recording gap.

All four commands accept a JSON object through `--input -`, with
`schema: "tabilet.audit.observation/v1"`, `event_id`, `run_id`,
`milestone_id`, `capture_source` and `fidelity`. Agent observations use
source `agent` and fidelity `summarized` or `incomplete`; exact host
observations require host provenance.

| Command | Additional fields |
|---|---|
| `audit task-start --input -` | `attempt_id`, `task_label`, `status_path` |
| `audit task-finish --input -` | The same attempt and task identity, observed `old_state` and `new_state`, `result` and optional `reason` |
| `audit verification --input -` | `command`, `result`; optional task identity, `runner` and `source_identity` |
| `audit review --input -` | `round` (positive integer), `result` and `findings` (priority-to-count object) |

At an observed task boundary, pass `live: true` to record that boundary's
time. For a known earlier boundary supply `occurred_at` instead. Omit both
when its time is unknown; never reconstruct timestamps from memory. A task
finish requires its matching start. Finish an attempt when work blocks or
waits; resume with a new attempt ID. Task results use the run-result vocabulary
above. Completed, blocked and cancelled results must agree with the observed
new state.

Verification and review results are `passed`, `failed`, `blocked` or
`unknown`. Record available elapsed time as `duration_sec` with
`timing_basis` of `monotonic`, `recorded_boundary` or `reported`.
Unknown timing uses `unknown` and no duration. An available interval supplies
both `started_at` and `finished_at` in UTC. Record the actual command and
source identity when known; never infer equivalent test coverage from counts.

Task identity is the milestone ID, original status path and exact row label.
A review observation records the authoritative round after reading Markdown;
it cannot increment that counter. Recording failure remains nonfatal and must
be reported as a gap. These commands need a consistently installed toolkit
interface 5; legacy generic events and old recordings remain supported.

## Explorer

The optional local explorer reads the same project database and never grants
write or execution authority. Install the server and browser assets, then run:

```bash
tabilet-audit explorer /absolute/project --port 8000
```

It provides Overview, Timeline, and To-do views. Refresh is explicit; current
Markdown remains authoritative. A follow-up action only prepares a prompt for
copying after live source validation. It does not launch an agent or edit the
project. For a remote host, tunnel with `ssh -N -L 8000:127.0.0.1:8000 user@host`.
