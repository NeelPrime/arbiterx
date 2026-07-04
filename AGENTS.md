# Tenet — Engineering Discipline for AI Code Generation

## Before Writing Code

Run this ladder. Stop at the first "yes":

1. Does this need to exist? → No → skip (YAGNI)
2. Already in this codebase? → Reuse it
3. Stdlib does it? → Use stdlib
4. Installed dep does it? → Use it
5. One-liner? → One line, no abstraction
6. Only then → write the minimum that works

## The 10 Tenets (Always Enforce)

1. Type all function signatures (params + return)
2. Handle every error path (no bare except, no swallowed errors)
3. Close every resource (use `with`, never bare open)
4. Name all constants (no magic numbers)
5. One function = one job (max 30 lines)
6. Validate inputs at function entry
7. No dead code (no commented code, no unused imports)
8. Finish everything (no TODO/FIXME — implement or skip)
9. Prefer immutable (frozen dataclasses, tuples)
10. Every line earns its place (delete what doesn't change behavior)

## Never Generate

- Hardcoded secrets (API keys, passwords, tokens)
- SQL with string formatting (use parameterized queries)
- eval() or exec()
- subprocess with shell=True
- Network calls without timeouts
- File ops without error handling

## After Writing

- Can any line be deleted without breaking behavior? → Delete it
- Is there a simpler stdlib approach? → Use it
- Would this pass review by the strictest engineer you know? → If not, fix it
