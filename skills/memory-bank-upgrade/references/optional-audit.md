# Optional local audit

Use this reference only when the user explicitly enabled `TABILET_AUDIT_DB` for
interactive skill runs. It names an external SQLite file. The independently
installed `tabilet-audit` command is optional; do not install it or create project
files to make logging work. If enabled but unavailable, report an audit gap and
continue the authorized workflow. The API runner owns its own lifecycle; do not
submit a duplicate run for work already being recorded by that runner.

The database records observations, never authorization. All project write,
review-fetch, commit, and external-action approval rules still apply. Installing
or invoking this skill without audit configuration never creates a database.

## Lifecycle

1. After the layout gate passes, start one run with the operation matching the
   skill suffix (`init`, `archive`, `propose`, `reconcile`, `next`, `goal`, or
   `upgrade`). Use the absolute project root. Generate a run ID once and retain
   it in the conversation for retries. The command returns the workspace ID:

   ```bash
   tabilet-audit audit begin /absolute/project next --run-id RUN_ID
   ```

   Capture defaults to metadata. Use `--capture relevant` only when selected
   message capture was explicitly enabled. A child operation in a recorded goal
   uses `--parent-run-id PARENT_RUN_ID`; both must belong to the same workspace.

2. Submit observed actions with `tabilet-audit audit event --input -`, sending
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

   Use `task_observed` for planning observations, with request/proposal/approval
   summaries and proposed or approved file actions in details. Record approval
   only after receiving it. Use `task_transition` with observed `old_state` and
   `new_state`, `verification_observed`, and `commit_observed` with the actual
   successful commit SHA. `milestone_accepted`, `milestone_retired`, `cancelled`,
   and `superseded` require their corresponding evidence; a terminal task alone
   does not establish acceptance. Never fabricate a timestamp: omit `occurred_at`
   when the observation time is unknown. The recorder supplies its own timestamp.

3. For explicitly enabled relevant capture, submit selected messages with
   `tabilet-audit audit message --input -`. Fields are `run_id`, `message_id`,
   `role`, `text`, `capture_source`, and `fidelity`; optionally include
   `redaction_note`. Agent-authored request/output summaries use source `agent`
   and fidelity `summarized` or `incomplete`. Exact raw user/output text requires
   capture supplied by the host, with source `host`. Do not reconstruct a raw
   transcript, include hidden reasoning, or submit credentials and unrelated text.

4. Finish with `tabilet-audit audit finish RUN_ID RESULT`. Results are
   `completed`, `blocked`, `failed`, `cancelled`, `interrupted`, or `unknown`.
   Choose from observed evidence, independently of process exit or a commit.
   Finish refreshes the current Markdown index; failures are reported as gaps.
   Waiting for user approval is not successful completion. Retain the run while
   waiting, or close it as blocked and start a new run when work resumes. Abrupt
   interruption may leave a run unfinished; never infer that it completed.

Logging failure never undoes work, changes status, retries a task, or changes the
commit policy. Report gaps in the final handoff. Before execution or a planning
write, reread the live Markdown even if an index lookup helped locate it.

## Explorer

The optional local explorer reads the same external database and never grants
write or execution authority. Install the server and browser assets, then run:

```bash
tabilet-audit explorer /absolute/project --port 8000
```

It provides Overview, Timeline, and To-do views. Refresh is explicit; current
Markdown remains authoritative. A follow-up action only prepares a prompt for
copying after live source validation. It does not launch an agent or edit the
project. For a remote host, tunnel with `ssh -N -L 8000:127.0.0.1:8000 user@host`.
