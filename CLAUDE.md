# ArbiterX Engineering Rules

This project uses ArbiterX for code quality enforcement.

## Setup
```bash
pip install arbiterx-gate
arbiterx init
arbiterx map
```

## Rules (always enforced)

1. Type all function signatures — parameters and return values
2. Handle every error — no bare `except:`, catch specific exceptions
3. Close every resource — use `with open(...)`, never bare open()
4. Name all constants — no magic numbers inline
5. One function = one job — max 30 lines
6. Validate inputs at function entry
7. No dead code — no commented-out code, no unused imports
8. Never leave TODO/FIXME — implement or skip
9. Prefer immutable — frozen dataclasses, tuples
10. Delete any line that doesn't change behavior

## Never generate
- Hardcoded secrets
- SQL with string formatting
- eval() or exec()
- subprocess with shell=True
- Network calls without timeouts

## Quality gate
Run `arbiterx gate --file <file>` on any changed file. Minimum score: 70/100.
