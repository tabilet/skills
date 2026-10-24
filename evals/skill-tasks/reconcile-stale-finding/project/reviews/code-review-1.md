# Code review: tasklist

Reviewer: external reviewer
Baseline: not supplied
Scope: src/tasklist.py

## R-1 (P2) Tasks cannot be saved or loaded

`src/tasklist.py` keeps tasks only in memory, so every task is lost when the program exits. It needs `save()` and `load()` functions that write and read a JSON file.
