# Robustness review

Reviewer: external reviewer
Scope: src/tasklist.py

## B-4 (P3, cosmetic) load() crashes on an empty tasks.json

If `tasks.json` exists but is empty (for example after `save()` was interrupted), `load()` raises `json.JSONDecodeError` and the command crashes before doing anything. Cosmetic: treat an empty file as no tasks.
