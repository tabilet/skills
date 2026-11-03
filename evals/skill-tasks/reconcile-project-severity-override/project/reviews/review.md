# Storage review

Reviewer: external reviewer
Scope: src/tasklist.py

## S-1 (P3, minor) save() overwrites tasks.json in place

`save()` writes `tasks.json` directly. A write interrupted part-way (a crash, a full disk) leaves a truncated file and every saved task is lost on the next `load()`. Low priority: write to a temporary file and rename it over `tasks.json`.
