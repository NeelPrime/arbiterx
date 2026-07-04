# Engineering Rules (ArbiterX)

All generated code must follow these rules:

## Required
- Type hints on all function parameters and return values
- Error handling for all I/O operations (try/except or context managers)
- Named constants instead of magic numbers
- Input validation at function entry
- Context managers for files and connections (`with open(...)`)
- Functions under 30 lines

## Forbidden
- No hardcoded secrets or API keys
- No bare except clauses
- No string formatting in SQL queries (use parameterized)
- No eval() or exec()
- No TODO/FIXME comments — implement fully or skip
- No functions longer than 30 lines
- No unused imports or commented-out code

## Prefer
- Standard library over external dependencies
- Early returns over deep nesting
- Immutable data where possible
- Specific exceptions over generic ones
- `str.join()` over string concatenation in loops
