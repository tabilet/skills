# Interactive model policy

Read only when the human-approved Goal or direct Next request selects
`MODEL_POLICY`. This reference binds the policy to host capabilities; it adds
no execution engine, action grants or host configuration files. The Python
API runner/controller do not consume this field.

## Selection and scope

Omission preserves the host's existing model settings. The user chooses both
role models from any provider supported by the host; no provider or model is
required. Planning skills propose a policy only when requested, and refreshes
preserve an explicit policy instead of inserting, changing or activating one.
The following shape contains placeholders, not selected models:

```yaml
MODEL_POLICY:
  DEFAULT:
    model: "<your implementation model>"
    reasoning_effort: "<optional host-supported effort>"
  WHOLE_MILESTONE_REVIEW:
    model: "<your review model>"
    reasoning_effort: "<optional host-supported effort>"
```

Resolve both role models and any requested effort from the human-approved
request, preserving project restrictions. Missing role models or conflicting
policies need clarification. `reasoning_effort` is optional: use only values
supported by the selected host/model, with no universal effort scale. Omit it
for models without this control or to retain the selected model's host default.
Record omitted effort as `host-default`, without claiming a specific effort
level. Resolve all template placeholders before execution or omit optional
effort; never activate a literal placeholder as a model or effort setting.
`DEFAULT` covers coordination, implementation, focused verification, task
reviews, downstream analysis and review fixes. `WHOLE_MILESTONE_REVIEW` covers
each authoritative bounded whole-milestone review iteration, including the
initial pass and every required re-review. It does not change task or release
reviews into milestone reviews. Direct Next uses the same distinction when it
closes a milestone, without requiring adoption of a goal protocol.

## Check capabilities before work

Materialize the policy with the resolved request in the conversation and keep
it in existing trusted host state where supported. Check the coordinator and
each dispatch using host-reported settings or supported explicit launch
controls for the selected model and any explicitly requested effort. Omitted
effort requires no unsupported effort control. A role name, prompt instruction, or an
agent's assertion alone does not establish the settings actually selected.

A running coordinator cannot reliably change its own model or effort in
place. If it does not meet `DEFAULT`, pause affected work and explain the
needed session configuration or relaunch; do not edit account configuration
or pretend a differently configured coordinator meets the policy. For fresh
children, explicitly select the user's model and any requested effort using
available host controls; omit effort overrides when `host-default` was selected.
Where the host requires a fresh context to apply overrides, use that mode with
a complete distilled brief rather than inheriting the conversation.

If the model, explicitly requested effort, fresh-agent capability or reliable configuration evidence
is unavailable, pause affected work and dependents and request an explicit
replacement policy. Never silently fall back to a different model or effort. Independent authorized work may continue only if its policy is met.
Host permission controls, action grants, operational limits and thread capacity
still apply. These instructions do not provide tool or operating-system
enforcement. No provider-specific setting is required.

## Review dispatch and resume

For each whole-milestone iteration, launch fresh read-only reviewers using
`WHOLE_MILESTONE_REVIEW`. Cover all five lenses: correctness/reliability,
security/privacy, compatibility/contracts, tests/documentation, and
acceptance/scope. A reviewer may cover several lenses; run batches when host
capacity is limited. Give each reviewer:

- The full governing request, approval context and resolved `MODEL_POLICY`.
- Its exact assignment and effective authorization subset: no mutation authority.
- Governing protocol/addendum identities when applicable, project instructions,
  acceptance criteria, required evidence and the pinned milestone baseline.
- The complete implementation to review, including uncommitted work under
  `COMMIT_POLICY: none`, prior findings and persisted review iteration.
- Required lens coverage and the return condition: findings to the owner only.

The `DEFAULT` coordinator remains the sole ledger writer, consolidates one
iteration report and applies fixes under `DEFAULT`. Each later whole review
uses fresh review agents; an interrupted review resumes its existing iteration
with fresh reviewers as needed. Preserve counters and the iteration-10 stop.
Missing configuration or incomplete lens coverage cannot yield a clean pass.
An empty implementation diff still needs acceptance review; never manufacture
a change just to satisfy review setup.

On resume, preserve the approved policy and recheck host capability and settings
before work or dispatch. A changed policy needs explicit human approval. Legacy
requests without this field continue with host settings, and installing or
upgrading skills never opts a paused run into model routing.
