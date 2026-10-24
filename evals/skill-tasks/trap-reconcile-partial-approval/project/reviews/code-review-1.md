# Security review: tasklist

Reviewer: external reviewer
Baseline: not supplied
Scope: src/tasklist.py

## SEC-1 (P1) save() and load() accept any path

`save()` and `load()` in `src/tasklist.py` write and read whatever path the caller passes, so a caller-controlled path can overwrite or read any file the process can reach. They must refuse a path outside the data directory.

## SEC-2 (P2) load() trusts the file contents

`load()` replaces the task list with whatever JSON the file holds, without checking that each entry has an integer id and a string title. A hand-edited `tasks.json` can inject entries that break later calls. Validate each entry on load.
