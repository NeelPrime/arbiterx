---
description: Run quality gate on generated code. Scores 0-100, checks security, robustness, efficiency.
---

# ArbiterX Gate

Run a quality gate on the last generated code or a specified file.

## Instructions

Check for these categories:

### Security (Critical — fails immediately)
- Hardcoded API keys (sk-..., AKIA..., ghp_..., xoxb-...)
- Hardcoded passwords in strings
- SQL injection (string formatting in queries)
- eval() or exec()
- subprocess with shell=True

### Robustness (High priority)
- File operations without try/except or context managers
- Network calls without timeout parameter
- Bare except clauses (catch specific exceptions)
- Database operations without transaction handling

### Efficiency (Medium priority)
- String concatenation in loops (use join())
- Nested loops over same collection (O(n²))
- re.compile() inside loops
- Unnecessary list() wrapping generators

### Completeness (Must fix)
- TODO/FIXME/HACK comments
- Placeholder implementations
- Missing error messages in exceptions

## Output Format

```
Score: XX/100
Status: PASS / FAIL

Issues:
1. [severity] file:line — description → suggested fix
2. ...
```

If FAIL: list exactly what to change to pass.
