# Goal Invocation And Session Continuation

Read this reference when invocation syntax or optional native goal continuation
is needed. Ordinary ordered execution uses the [main skill](../SKILL.md).

**Use the form supplied by the installation.** Plugin installs use
`/memory-bank:memory-bank-goal` in Claude Code and
`$memory-bank:memory-bank-goal` in Codex. Plain-file installs use
`/memory-bank-goal` and `$memory-bank-goal`, respectively. DSH filesystem
installs use `/memory-bank-goal` or an ordinary-language request to use this
skill. **The name avoids
`goal` on purpose.** Claude Code and Codex have a built-in `/goal` for keeping a
durable objective active; see *Keeping the session going* below.

## Keeping the session going

Goal accepts optional `--email ADDRESS` in the skill request or the objective
of a native goal that explicitly invokes the installed Goal skill with the
protocol. Naming the protocol alone does not locate the email helper. Load the
complete skill bundle and pass its local sender check before relying on alerts;
report a missing bundle/helper as a notification gap. For example:

```text
$memory-bank:memory-bank-goal --email abc@def.gh STATUS_ORDER: M01 -> M02. COMMIT_POLICY: task.
```

This is a conversation request, not a shell command. The recipient and narrow
notification authority are retained for that run's resumes only; no flag on a
new run disables email. See the bundled [email reference](email-notifications.md)
for private Cloudflare setup, local checking and approval-alert delivery.
`CORRECTIVE_PLANNING: auto` may also be supplied explicitly in the request to
authorize necessary in-scope repair planning; it grants no new actions or limits.

In **Claude Code and Codex**, built-in `/goal` is an optional persistence layer
for a long run. It keeps the objective active; `tabilet/GOAL.md` still defines the
multi-milestone execution protocol. Include the complete protocol request,
commit policy, and a measurable completion condition. When the disposable
reference exists, verify that its SHA256 checksum matches human approval before
activating grants, and let the goal reconcile it first:

```text
/goal Using tabilet/GOAL.md, reconcile tabilet/memory-bank/suggested.txt against the current memory bank, then execute the resolved loop. COMMIT_POLICY: task. SUGGESTED_UPDATE: auto. Completion condition: every required status is complete, every triggered conditional status is complete, and every milestone's documented verification passes.
```

In either agent, run `/goal` with no arguments to show status and `/goal clear`
to stop. Codex also supports `/goal pause` and `/goal resume`; if `/goal` is not
listed, run `codex features enable goals`. See the official [Claude Code goal
documentation](https://code.claude.com/docs/en/goal) and [OpenAI Codex goal
guide](https://learn.chatgpt.com/use-cases/follow-goals).

If `suggested.txt` is absent, put the resolved order or priority, file map, and downstream
impacts directly in the request instead. Invoking `memory-bank-goal` directly
remains the portable non-persistent launcher: use
`/memory-bank:memory-bank-goal` or `/memory-bank-goal` in Claude Code, and
`$memory-bank:memory-bank-goal` or `$memory-bank-goal` in Codex. For DSH, use
`/memory-bank-goal` or the [resolved request block](../SKILL.md#resolve-the-request). Its optional
native goal continuation keeps the same execution owner; it never supplies
missing approval or marks a milestone accepted. For other agents, paste that resolved request block.
