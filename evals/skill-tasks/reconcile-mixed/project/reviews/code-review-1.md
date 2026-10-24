# Code review: tasklist

Reviewer: external reviewer
Baseline: not supplied
Scope: src/tasklist.py

## R-1 (P1) complete() silently ignores an unknown task id

`complete()` in `src/tasklist.py` loops over the tasks and returns without an error when no task has the given id, so a mistyped id reports success while nothing changes. It must raise an error for an unknown id.

## R-2 (P2) Tasks cannot be saved or loaded

`src/tasklist.py` keeps tasks only in memory, so every task is lost when the program exits. It needs `save()` and `load()` functions that write and read a JSON file.

## R-3 (P3) Poor function name

`listing()` is an awkward name. Consider renaming it to `list_tasks()` when the API is next touched.

## R-4 (P2) No way to search tasks

A user with a long list cannot find a task by title. Add a search by title.
