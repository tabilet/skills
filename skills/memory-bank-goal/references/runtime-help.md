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

In **Claude Code and Codex**, built-in `/goal` is an optional persistence layer
for a long run. It keeps the objective active; `tabilet/GOAL.md` still defines the
multi-milestone execution protocol. Include the complete protocol request,
commit policy, and a measurable completion condition. When the disposable
reference exists, let the goal reconcile it first:

```text
/goal Using tabilet/GOAL.md, reconcile tabilet/memory-bank/suggested.txt against the current memory bank, then execute the resolved loop. COMMIT_POLICY: task. Completion condition: every required status is complete, every triggered conditional status is complete, and every milestone's documented verification passes.
```

In either agent, run `/goal` with no arguments to show status and `/goal clear`
to stop. Codex also supports `/goal pause` and `/goal resume`; if `/goal` is not
listed, run `codex features enable goals`. See the official [Claude Code goal
documentation](https://code.claude.com/docs/en/goal) and [OpenAI Codex goal
guide](https://learn.chatgpt.com/use-cases/follow-goals).

If `suggested.txt` is absent, put the resolved order, file map, and downstream
impacts directly in the request instead. Invoking `memory-bank-goal` directly
remains the portable non-persistent launcher: use
`/memory-bank:memory-bank-goal` or `/memory-bank-goal` in Claude Code, and
`$memory-bank:memory-bank-goal` or `$memory-bank-goal` in Codex. For DSH, use
`/memory-bank-goal` or the [resolved request block](../SKILL.md#resolve-the-request). Its optional
native goal continuation keeps the same execution owner; it never supplies
missing approval or marks a milestone accepted. For other agents, paste that resolved request block.
