# Code review: tasklist

Reviewer: external reviewer
Baseline: not supplied
Scope: src/tasklist.py

## R-1 (P1) complete() silently ignores an unknown task id

`complete()` in `src/tasklist.py` loops over the tasks and returns without an error when no task has the given id, so a mistyped id reports success while nothing changes. It must raise an error for an unknown id.
