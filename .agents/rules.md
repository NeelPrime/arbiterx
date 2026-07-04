# Agent Rules — ArbiterX

## Project Overview

ArbiterX is a CLI tool that generates token-efficient codebase maps for AI-assisted development. It parses source code via AST analysis, extracts structural information (functions, classes, imports, dependencies), and compresses it into a compact representation that fits within LLM context windows. The tool supports incremental updates via content hashing and task-aware context prioritization.

## Tech Stack

- **Language:** Python 3.11+
- **CLI Framework:** Click
- **AST Parsing:** tree-sitter (multi-language), ast (Python stdlib fallback)
- **Hashing:** hashlib (SHA-256)
- **Configuration:** tomllib / tomli
- **AI Integration:** litellm (multi-provider)
- **Testing:** pytest, pytest-cov
- **Linting/Formatting:** ruff
- **Packaging:** hatchling / pyproject.toml

## Coding Conventions

- **Python version:** 3.11+ minimum. Use modern syntax (match statements, `type` aliases, ExceptionGroups where appropriate).
- **Type hints:** Required on all public functions and methods. Use `from __future__ import annotations` in every module.
- **Line length:** 100 characters max.
- **Formatter/Linter:** ruff (format + check). Configuration lives in `pyproject.toml`.
- **Imports:** Group as stdlib → third-party → local. Use absolute imports.
- **Docstrings:** Google style. Required on all public classes and functions.
- **Naming:** snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for constants.
- **Error handling:** Use custom exception classes in `src/arbiterx/exceptions.py`. Never catch bare `Exception` in library code.
- **No global mutable state.** Pass dependencies explicitly or use dependency injection.

## Project Structure

```
src/arbiterx/
├── __init__.py
├── cli.py              # Click CLI entry points
├── mapper.py           # Core map generation logic
├── hasher.py           # File content hashing (SHA-256)
├── classifier.py       # Task classification for relevance ranking
├── parser/             # Language-specific AST parsers
├── output/             # Formatters (markdown, json, prompt)
├── config.py           # Configuration loading
├── exceptions.py       # Custom exceptions
└── models.py           # Data classes / types
```

## Testing Approach

- **Framework:** pytest
- **Structure:** `tests/unit/` for isolated logic, `tests/integration/` for CLI and end-to-end flows.
- **Naming:** Test files mirror source: `src/arbiterx/hasher.py` → `tests/unit/test_hasher.py`
- **Fixtures:** Use `conftest.py` for shared fixtures. Prefer `tmp_path` for filesystem tests.
- **Coverage:** Aim for 80%+ on core modules (mapper, hasher, classifier, parser).
- **Mocking:** Mock external I/O (filesystem, network, LLM calls). Never mock the unit under test.
- **Run tests:** `pytest` from project root. CI runs against Python 3.11 and 3.12.

## Key Decisions

- Maps are deterministic — same input always produces same output (for caching).
- The tool must work fully offline (no network calls during `map`).
- Token counting uses tiktoken with cl100k_base encoding.
- File hashing uses SHA-256 for cache invalidation.
- Configuration is optional — sensible defaults work out of the box.

## Common Tasks

- **Add a new language parser:** Create a module in `src/arbiterx/parser/`, implement the `Parser` protocol, register in `parser/__init__.py`.
- **Add a CLI command:** Add to `src/arbiterx/cli.py` using Click decorators.
- **Update output format:** Modify or add a formatter in `src/arbiterx/output/`.
