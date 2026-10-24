# Code review: tasklist

Reviewer: external reviewer
Baseline: not supplied
Scope: src/tasklist.py

## R-1 (P1) add() accepts a blank title

`add()` in `src/tasklist.py` creates a task when the title is empty or only spaces, and such a task cannot be shown or found later. It must raise `ValueError` for a blank title.

## R-2 (P2) The blank-title check needs a test

Once `add()` rejects blank titles, `tests/test_tasklist.py` needs a regression test for it. This only exists because of R-1 and is not separate work.

## R-3 (P2) save() is not atomic

`save()` writes `tasks.json` in place, so a crash in the middle of the write leaves a corrupt file. It should write a temporary file and rename it over the old one.

## R-4 (P3) Poor function name

`listing()` is an awkward name. Consider renaming it to `list_tasks()` when the API is next touched.
