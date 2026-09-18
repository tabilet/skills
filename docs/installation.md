# Install, update, remove

Choose the agent you already use. Install the skills once, then open that agent
in the project you want to work on. **Installation adds commands; it does not
create or upgrade a project's memory bank.**

| Your setup | Install |
|---|---|
| Claude Code | The `memory-bank` plugin from the `tabilet` marketplace |
| Codex | The same `memory-bank` plugin through the Codex CLI |
| DSH Web or headless | The `tabilet-skills` companion, or the seven source-checkout filesystem bundles |
| Manual installation | Complete skill folders in your agent's skill directory |

The canonical seven skills and the DSH companion use the same project Markdown.
Propose is prepared in unpublished v1.5.0 source; the public v1.4.0 plugin
and companion still install six skills.
Python is only required for the optional API runner.

## Claude Code

Run these **inside Claude Code**:

```text
/plugin marketplace add tabilet/skills
/plugin install memory-bank@tabilet
```

Open a fresh session in your project, then send:

```text
/memory-bank:memory-bank-init
```

Use Init only when the project has no initialized memory bank. Otherwise,
[choose the workflow](examples.md) for the work you want to do.

## Codex

Run these **in a terminal**:

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

Then open a fresh Codex session in your project and send:

```text
$memory-bank:memory-bank-init
```

The `@tabilet` qualifier identifies the marketplace. If your Codex build does
not expose plugin commands, use the [plain-file route](#as-plain-files-you-own).

## DeepSeek Harness

For the **Memory Bank sidebar and all six skills**, install the prebuilt v1.4.0
companion in your Web profile. Run this in a terminal on the machine running DSH:

```bash
dsh plugin --profile web add \
  https://github.com/tabilet/tabilet-skills/releases/download/v1.4.0/tabilet-skills-1.4.0.tgz \
  --ignore-scripts
```

For headless use, replace `--profile web` with `--profile headless`. Install only
in the profiles where you want it. This GitHub release route needs no npm account.

Restart DSH, select a session for your project, and open **Memory Bank** in the
right sidebar. Expand **Prepare a workflow request**, choose a skill, review the
preview, and insert it into an empty draft. **You send the request yourself.**
If the draft already contains text or attachments, copy the preview instead.
Headless profiles load the skills without a sidebar.

The companion was verified on Linux with Node **24.14.1** and locked DSH
**0.1.5-rc.2** components, plus an isolated rc.1 launcher using rc.2 components.

For **skills without the dashboard**, use the [plain-file route](#as-plain-files-you-own)
below after v1.5.0 is published, or from a trusted local v1.5.0 checkout now.
Copy all seven complete folders to `$DSH_HOME/skills`, normally
`~/.dsh/skills`. That route retains its separately tested all-rc.1 compatibility.

### Using the Memory Bank panel

The panel follows the selected session's project. **Overview** shows active
milestones and task counts; **Tasks** provides filters, search, and full notes.
**Acceptance** shows recorded verification and review evidence. **Memory** holds
current project facts, and **History** opens preserved records on demand.
**Compatibility** reports missing files, unsupported formats, conflicting task
states, and which installed skill source takes precedence.

External file edits appear through change notifications and a five-second
refresh cycle while the panel is visible. It also refreshes on focus and offers
manual refresh. Incomplete or denied reads remain visible as warnings.

Browsing and preparing requests make no model calls and do not write project
files. A preview is not execution or approval: you send it in the conversation,
and the chosen skill retains its approval boundaries. Completed task markers
alone do not establish milestone acceptance. For older project formats, prepare
an [Upgrade](upgrade.md) request and include the displayed warnings.

## Invoke a skill

Skill requests go in the **agent conversation**, not your shell. The prefix
depends on how you installed them:

| Installation | Example conversation request |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-next` |
| Codex plugin | `$memory-bank:memory-bank-next` |
| DSH companion or filesystem | `/memory-bank-next` |
| Claude Code plain files | `/memory-bank-next` |
| Codex plain files | `$memory-bank-next` |

Substitute `init`, `archive`, `propose`, `reconcile`, `upgrade`, or `goal` for `next` as
needed. The [skill guides](init.md) explain each input and approval boundary.
For Goal, include an explicit order and [commit policy](goal.md).

## As plain files you own

Clone the released source into a separate directory:

```bash
git clone --branch v1.4.0 --depth 1 https://github.com/tabilet/skills.git
```

Copy each `memory-bank-*` folder from the chosen release's `skills/` directory into
the destination for your agent:

| Agent | Personal skill directory |
|---|---|
| Codex | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` |
| DSH | `$DSH_HOME/skills/`, normally `~/.dsh/skills/` |

Copy **complete folders**, including their bundled templates and references.
Copying only `SKILL.md` leaves some workflows incomplete. Inspect and back up an
existing folder with the same name before replacing it; leave unrelated skills
alone. Start a fresh session after changing an installation.

## The project files

[Init](init.md) prepares project-specific files after you approve its proposal.
If you prefer to set them up by hand, copy `template/` from the release checkout
into a new project:

```bash
cp -R /path/to/skills/template/. /path/to/new-project/
```

The bracketed placeholders are intentional: fill them with your project's facts,
plan, and verification commands. For an existing project, merge applicable rules
and preserve its instructions; do not copy the template over its current state.
Before execution, record a concrete delivery boundary, milestone acceptance,
task rows, and verification commands. Keep `AGENTS.md` as the entry point; if
your agent reads another instruction filename, make that file point to
`AGENTS.md`. The [first-project walkthrough](examples.md#a-new-project) shows
what to check before selecting a task.

## The optional API harness

The separate API runner needs **Python 3 and Git**, plus credentials for your
chosen model provider. It uses the Python standard library only.

```bash
mkdir -p ~/.local/bin
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

You can skip the runner when using your existing coding agent. To use it, start
with an initialized project at its Git worktree root, a clean committed
baseline, and one approved actionable task. Run it inside a disposable sandbox:
the runner itself executes model commands in a host shell and does not supply
isolation. `ALLOW_UNSANDBOXED_SHELL=1` acknowledges that access.

With `OPENAI_API_KEY` already set in your environment, replace the model and
project placeholders and run:

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_PROVIDER=openai LLM_MODEL=your-model MAX_RUNS=1 \
  ~/.local/bin/tackle-memory-bank-api-loop /absolute/path/to/project
```

For Anthropic, set `ANTHROPIC_API_KEY` and use `LLM_PROVIDER=anthropic` with a
compatible model. Provider requests may incur charges. Use the executable's
`--help` for endpoint settings, timeouts, retries, and additional limits.

The API runner requires a commit for each run and stops on dirty state, missing
commits, invalid task transitions, or multiple in-progress rows. Exit `7` means
the requested run limit was reached; exit `3` means only blocked work remains.
Exit `0` means no actionable rows remain, not that every milestone passed its
review. Check the recorded verification and closure evidence afterward. Do not
run another agent against the same active ledger at the same time.

## Update

For Claude Code, use its `/plugin` manager to update the installed plugin.
For Codex, refresh the marketplace snapshot and reinstall the plugin:

```bash
codex plugin marketplace upgrade tabilet
codex plugin add memory-bank@tabilet
```

For the DSH companion, install the chosen published release archive in each
applicable profile, then restart it. For filesystem installs, stop sessions
using the bundles, inspect and back up the installed folders, then replace them
with complete folders from the chosen release. Preserve unrelated skills and
review project or user overrides that may take precedence over the new bundles.

**Updating installed skills does not migrate project rules.** Use
[Upgrade](upgrade.md) to inspect an existing project and approve specific rule
merges. Keep task state, permanent IDs, local policies, and history intact.

## Remove

Use the uninstall command for your installation:

| Installation | Command and where to run it |
|---|---|
| Claude Code plugin | `/plugin uninstall memory-bank@tabilet` in Claude Code |
| Codex plugin | `codex plugin remove memory-bank@tabilet` in a terminal |
| DSH Web companion | `dsh plugin --profile web remove tabilet-skills` in a terminal |

Remove the DSH headless installation separately if you installed it there.
For plain-file installs, remove only the identified memory-bank skill folders.
Project Markdown remains in the project and is still usable after removal.

## If a skill or dashboard is missing

- Confirm the selected session points at the project you intended.
- Start a fresh session after installation. Restart DSH after changing a profile.
- Check the invocation prefix above. A DSH Web installation does not install the
  companion in the headless profile.
- In DSH's **Compatibility** view, inspect the winning skill source. An existing
  project or user copy can take precedence over the bundled one.
- The `skills` repository itself contains a sample at `template/memory-bank/`;
  it has no active project memory bank for the dashboard to display.
