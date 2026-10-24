# Code review: tasklist

Reviewer: external reviewer
Baseline: not supplied
Scope: src/tasklist.py

## R-1 (P2) load() fails on a first run

`load()` in `src/tasklist.py` raises an unhandled `FileNotFoundError` when `tasks.json` does not exist yet, so the first run of the program crashes. A missing file should load as an empty task list.
