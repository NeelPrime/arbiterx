# Tenet: Engineering Discipline

Enforce these principles on all generated code:

1. Use stdlib before dependencies. Does it need to exist? YAGNI.
2. Type all function signatures — parameters and return values.
3. Handle every error path. No bare `except:`. Catch specific exceptions.
4. Close every resource. Use `with open(...)`, never bare open().
5. Name constants. No magic numbers inline.
6. One function = one responsibility. Max 30 lines.
7. Validate inputs at function entry, not buried in logic.
8. No dead code. No commented-out code. No unused imports.
9. Never leave TODO/FIXME. Implement fully or skip entirely.
10. Delete any line that doesn't change behavior.

Never generate: hardcoded secrets, SQL with string formatting, eval/exec, subprocess shell=True, network calls without timeouts.
