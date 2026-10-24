# AGENTS.md

## Purpose

Bootstrap guide for agents working on `tasklist`. Keep this file short and use the memory bank as the active project source of truth.

## Start Here

Before substantial changes, read these in order:

1. `tabilet/memory-bank/product.md`
2. `tabilet/memory-bank/architecture.md`
3. `tabilet/memory-bank/milestone.md`
4. The matching `tabilet/memory-bank/status-<LANE><NN>.md` file for the current milestone.

## Boundaries

`tasklist` owns a single-user command-line task tracker. Sync and multi-user features are out of scope.

## Essential Commands

```bash
python3 -m unittest
```

## Hard Rules

- Never deploy on Fridays; the release manager signs off every deploy.
- Keep the public function names in `src/tasklist.py` stable.
- Run `python3 -m unittest` before claiming a change is done.
