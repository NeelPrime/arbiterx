# Contributing to ArbiterX

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

### Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/arbiterx.git
cd arbiterx
```

### Set Up Development Environment

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Verify Setup

```bash
ruff check .
ruff format --check .
pytest
```

## Development Workflow

### 1. Create a Branch

Branch from `main` with a descriptive name:

```bash
git checkout -b feat/add-rust-parser
git checkout -b fix/hasher-symlink-handling
git checkout -b docs/update-cli-reference
```

Use prefixes: `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`.

### 2. Write Code

Follow the project's coding conventions:

- **Python 3.11+** with type hints on all public APIs
- **100 character** line length
- **Google-style** docstrings on public classes and functions
- **ruff** for linting and formatting (config in `pyproject.toml`)
- Run `ruff check . --fix` and `ruff format .` before committing

### 3. Write Tests

- All new features require tests
- Bug fixes should include a regression test
- Place unit tests in `tests/unit/`, integration tests in `tests/integration/`
- Use `tmp_path` for filesystem operations, mock external I/O

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/arbiterx --cov-report=term-missing

# Run a specific test file
pytest tests/unit/test_hasher.py -v
```

### 4. Commit

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Go language parser
fix: handle symlinks in file walker
docs: add configuration examples
test: add integration tests for CLI map command
refactor: extract token counter into separate module
```

Keep commits focused — one logical change per commit.

### 5. Open a Pull Request

- Push your branch and open a PR against `main`
- Fill in the PR template (what changed, why, how to test)
- Ensure CI passes (ruff check, ruff format, pytest on 3.11 + 3.12)
- Request review from a maintainer

## Code Review

PRs need at least one approving review before merge. Reviewers will check:

- Correctness and test coverage
- Adherence to coding conventions
- Documentation for public APIs
- No unintended side effects or breaking changes

## Reporting Issues

Open a GitHub issue with:

- Clear title describing the problem
- Steps to reproduce
- Expected vs. actual behavior
- Python version, OS, and ArbiterX version

## Code of Conduct

Be respectful, constructive, and inclusive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
