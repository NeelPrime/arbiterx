---
description: Engineering discipline rules — always active. Enforces 10 rules for minimal, robust code. Provides codebase intelligence via MCP tools.
---

# ArbiterX: Engineering Discipline

## Before Reading Code — Use ArbiterX Tools First

When you need to understand the codebase, use these tools BEFORE reading files:

- **arbiterx_query("search term")** — Find relevant functions/classes instantly (97% fewer tokens than reading files)
- **arbiterx_overview()** — Understand project structure, languages, top symbols
- **arbiterx_file_symbols("path/to/file.py")** — See what's defined in a file without reading the full source
- **arbiterx_gate(code, language)** — Score code quality 0-100 before presenting it

Only read full files when you need the implementation body AFTER querying the map.

## Before Writing Code — Decision Ladder

1. Does this need to exist? → No: skip it (YAGNI)
2. Already in this codebase? → Yes: reuse it, don't rewrite
3. Stdlib does it? → Yes: use stdlib
4. Native platform feature? → Yes: use it
5. Installed dependency does it? → Yes: use it
6. Can it be a one-liner? → Yes: one line, no abstraction
7. Only then: write the minimum that works

## When Writing Code — ENFORCE These Rules:

1. **Type all signatures** — Every function parameter and return value gets a type hint
2. **Handle every error** — No bare `except:`, no swallowed errors. Catch specific exceptions.
3. **Close every resource** — Use `with open(...)`, never bare `open()`. Same for connections, sockets.
4. **Name constants** — No magic numbers. `MAX_RETRIES = 3`, not `3`.
5. **One function = one job** — If it's over 30 lines, split it.
6. **Validate inputs first** — Check at function entry, not deep in logic.
7. **No dead code** — No commented-out code, no unused imports.
8. **Finish it** — Never write TODO/FIXME. Either implement it or don't.
9. **Prefer immutable** — Use frozen dataclasses, tuples over lists when possible.
10. **Delete what doesn't change behavior** — Every line earns its place.

## NEVER Generate:

- Hardcoded secrets (API keys, passwords, tokens in code)
- SQL built with f-strings or .format() (use parameterized queries)
- `eval()` or `exec()`
- `subprocess` with `shell=True`
- Network calls without timeouts
- File operations without error handling

## After Writing — Self-Check:

- Can any line be deleted without breaking behavior? → Delete it.
- Is there a simpler way using stdlib? → Use it.
- Would this pass a senior engineer's code review? → If not, fix it.

Lazy about the solution. Never about reading or error handling.
