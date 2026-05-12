# AGENTS.md

## Purpose

Bootstrap guide for agents working on `[project-name]`. Keep this file short and
use the memory bank as the active project source of truth.

## Start Here

Before substantial changes, read these in order:

1. [memory-bank/product.md](memory-bank/product.md)
2. [memory-bank/architecture.md](memory-bank/architecture.md)
3. [memory-bank/tech-stack.md](memory-bank/tech-stack.md)
4. [memory-bank/milestone.md](memory-bank/milestone.md)
5. The matching `memory-bank/status-Mx.md` file for the current milestone.

Do not recreate duplicate root-level product, architecture, roadmap, or status
documents. Long-form references live in `docs/`; README is operator-focused.

## Boundaries

`[project-name]` owns:

- [Owned responsibility 1.]
- [Owned responsibility 2.]
- [Owned responsibility 3.]

Out of scope:

- [Out-of-scope responsibility] -> [owning project/module/person].
- [Out-of-scope responsibility] -> [owning project/module/person].

Rule of thumb: if a change [describe the boundary test], it belongs in
[owning place], not here.

## Essential Commands

```bash
[build command]
[test command]
[lint command]
[format command]
```

Tool versions, installation notes, CI, and runtime assumptions are maintained in
[memory-bank/tech-stack.md](memory-bank/tech-stack.md).

## Hard Rules

- [Hard rule 1.]
- [Hard rule 2.]
- [Hard rule 3.]
- Run the required verification before claiming a change is done.

## Work Cadence

- Update memory-bank files in the same change as the code they describe:
  product scope -> `product.md`; architecture/data flow/contracts ->
  `architecture.md`; tools/dependencies/commands -> `tech-stack.md`; milestone
  scope/acceptance -> `milestone.md`; completion state -> the matching
  `status-Mx.md` file.
- Keep one `memory-bank/status-Mx.md` file for each milestone `Mx` listed in
  [memory-bank/milestone.md](memory-bank/milestone.md).
- Treat each row in the matching `memory-bank/status-Mx.md` file as a commit
  unit. See that file for status markers and commit rules.
- Treat each section in [memory-bank/milestone.md](memory-bank/milestone.md) as a
  review unit. See that file for milestone review rules.
- After the last task in a milestone is complete, run a deep code review of the
  milestone before closing it.
- After the milestone review is complete and required verification passes, make
  a git commit for the milestone changes.
- Check [evolution/](evolution/) after a major review, milestone, or boundary
  change. Add a new version only when product direction, architecture boundary,
  milestone target, or public/private contract direction materially changes.
