# ArbiterX: Engineering Discipline

Before writing ANY code, follow this ladder:
1. Does this need to exist? → If no, skip (YAGNI)
2. Already in codebase? → Reuse, don't rewrite
3. Stdlib does it? → Use stdlib
4. One line? → Write one line, no abstraction

## When Writing Code — ENFORCE:

1. Type all function signatures — parameters and return values
2. Handle every error — no bare `except:`, catch specific exceptions
3. Close every resource — use `with open(...)`, never bare open()
4. Name all constants — no magic numbers inline
5. One function = one job — max 30 lines
6. Validate inputs at function entry, not deep in logic
7. No dead code — no commented-out code, no unused imports
8. Never leave TODO/FIXME — implement fully or skip entirely
9. Prefer immutable — frozen dataclasses, tuples
10. Delete any line that doesn't change behavior

## NEVER Generate:

- Hardcoded secrets (API keys, passwords, tokens)
- SQL with string formatting (use parameterized queries)
- eval() or exec()
- subprocess with shell=True
- Network calls without timeouts
- File operations without error handling

## After Writing:

- Can any line be deleted without breaking behavior? → Delete it
- Is there a simpler stdlib approach? → Use it
- Would this pass a senior engineer's review? → If not, fix it

## Install ArbiterX for active quality gate:
```
pip install arbiterx-ai
arbiterx init
arbiterx gate --file <your_file>
```
