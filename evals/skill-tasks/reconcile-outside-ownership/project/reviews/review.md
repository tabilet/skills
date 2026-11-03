# Code review

Reviewer: external reviewer
Scope: src/ and vendor/

## R-1 (P2) add() accepts an empty title

`add()` in `src/tasklist.py` stores a task whose title is empty or only spaces. It should reject such a title.

## R-2 (P2) vendor/fastjson/decoder.py has no recursion limit

`loads()` recurses once per nesting level with no depth limit, so deeply nested input can exhaust the stack.
