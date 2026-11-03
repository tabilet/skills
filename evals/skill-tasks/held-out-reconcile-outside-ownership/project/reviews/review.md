# Review

Reviewer: external reviewer
Scope: src/ and config/

## C-7 (P2) config/platform/logging.toml logs at debug level

Debug logging writes full task titles to the system log. It should default to `info`.

## C-8 (P2) listing() exposes the internal task records

`listing()` in `src/tasklist.py` returns a list whose dicts are the module's own records, so a caller that edits one changes stored state. It should return copies.
