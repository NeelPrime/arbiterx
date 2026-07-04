"""Engineering principles injected into every LLM prompt.

This is the core of what makes arbiterx different from a token optimizer —
it tells the AI HOW to write code, not just what files to read.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Core engineering principles organized by category
# ---------------------------------------------------------------------------

CORE_PRINCIPLES: dict[str, list[str]] = {
    "minimal": [
        "Write the least code that satisfies the requirement — delete anything that doesn't change behavior.",
        "Use stdlib and builtins before reaching for dependencies.",
        "One function does one thing; if you need a comment to separate sections, extract a function.",
        "No dead code, no commented-out code, no speculative generality.",
    ],
    "robust": [
        "Handle every error path explicitly — no bare except, no swallowed errors.",
        "Validate inputs at function entry; fail fast with clear messages.",
        "Close every resource you open — use context managers or RAII equivalents.",
        "Design for partial failure: timeouts, retries with backoff, circuit breakers.",
    ],
    "efficient": [
        "Choose the right data structure before optimizing the algorithm.",
        "Avoid allocation in hot paths — prefer pre-allocated buffers and object reuse.",
        "Batch I/O operations; never issue network or disk calls inside tight loops.",
        "Measure before optimizing — attach a rationale to every perf decision.",
    ],
    "secure": [
        "Never interpolate user input into queries, commands, or templates — use parameterization.",
        "Apply least-privilege: minimal scopes, short-lived tokens, no hardcoded secrets.",
        "Validate and sanitize all external input at the boundary, not deep inside logic.",
        "Default to deny — allowlists over denylists for access control.",
    ],
    "readable": [
        "Name variables and functions after what they represent, not how they're computed.",
        "No magic numbers — extract named constants with units or intent in the name.",
        "Prefer flat control flow; return early to avoid deep nesting.",
        "Keep functions under 30 lines; keep files under 300 lines.",
    ],
    "maintainable": [
        "Type all function signatures — callers should never guess types.",
        "Prefer immutable data; mutate only when measurement demands it.",
        "Separate pure logic from side effects — push I/O to the edges.",
        "Never generate code with TODO or FIXME — finish it or don't write it.",
    ],
}

# ---------------------------------------------------------------------------
# Preamble injected at the top of every LLM prompt
# ---------------------------------------------------------------------------

ENGINEERING_PREAMBLE: str = """\
You are an engineering-disciplined code generator. Before writing any code:
1. Use stdlib/builtins before dependencies.
2. Handle every error path — no bare try/except, no swallowed errors.
3. Type all function signatures.
4. One function = one responsibility (max 30 lines).
5. No magic numbers — name your constants.
6. Validate inputs at function entry.
7. Close every resource you open.
8. Prefer immutable data structures.
9. Never generate code with TODO/FIXME — finish it or don't write it.
10. Delete any line that doesn't change behavior."""

# ---------------------------------------------------------------------------
# Language-specific rule extensions
# ---------------------------------------------------------------------------

_LANGUAGE_RULES: dict[str, list[str]] = {
    "python": [
        "Use type hints on every function signature (PEP 484+).",
        "Prefer dataclasses or NamedTuple over raw dicts for structured data.",
        "Use context managers (with statements) for all resource handling.",
        "Raise specific exceptions from a module-level hierarchy, never bare Exception.",
    ],
    "go": [
        "Always check returned errors — never assign to _.",
        "Return (value, error) pairs; wrap errors with fmt.Errorf and %w.",
        "Use defer for resource cleanup immediately after acquisition.",
        "Prefer table-driven tests with t.Run subtests.",
    ],
    "rust": [
        "Prefer owned types in APIs; accept references only when lifetime is clear.",
        "Use Result<T, E> for recoverable errors; reserve panic for invariants.",
        "Leverage the borrow checker — do not reach for Rc/RefCell without justification.",
        "Derive Clone, Debug, and PartialEq unless there's a measured cost.",
    ],
    "typescript": [
        "Enable strict mode — no implicit any, no unchecked index access.",
        "Use branded types or zod schemas for external data validation at boundaries.",
        "Prefer readonly arrays and Readonly<T> for function parameters.",
        "Avoid enums; use const objects with as const for exhaustive unions.",
    ],
    "java": [
        "Use Optional<T> for nullable returns — never return null from public methods.",
        "Prefer records for value types; prefer sealed interfaces for type hierarchies.",
        "Use try-with-resources for all AutoCloseable instances.",
        "Throw unchecked exceptions for programming errors, checked for recoverable ones.",
    ],
}

# ---------------------------------------------------------------------------
# Anti-patterns: common bad patterns mapped to their fixes
# ---------------------------------------------------------------------------

ANTI_PATTERNS: dict[str, str] = {
    "bare_except": "Catch specific exceptions, never bare except:.",
    "string_concat_loop": "Use str.join() or f-strings, not += in loops.",
    "mutable_default_arg": "Never use mutable defaults (list, dict) in function signatures — use None and create inside.",
    "god_function": "Functions over 40 lines do too much — split by responsibility.",
    "hardcoded_secret": "Never hardcode secrets — load from env vars or a secrets manager.",
    "print_debugging": "Use structured logging (logging module), not print() for diagnostics.",
    "untyped_dict": "Replace Dict[str, Any] with a dataclass, TypedDict, or Pydantic model.",
    "nested_callbacks": "Flatten async code with async/await or extract named functions.",
    "swallowed_error": "Never except-and-pass — log, re-raise, or return a sentinel.",
    "sql_string_format": "Never f-string or .format() SQL — use parameterized queries.",
    "global_state": "Avoid module-level mutable state — pass dependencies explicitly.",
    "wildcard_import": "Never use 'from module import *' — import names explicitly.",
}

# ---------------------------------------------------------------------------
# Selection helpers
# ---------------------------------------------------------------------------

_MODE_COUNTS: dict[str, int] = {
    "lite": 5,
    "full": 10,
    "strict": 100,  # effectively all
}


def _select_principles(mode: str) -> list[str]:
    """Select a subset of principles based on the requested mode."""
    count = _MODE_COUNTS.get(mode, _MODE_COUNTS["full"])
    # Priority order: minimal, robust, efficient, secure, readable, maintainable
    priority_order = ["minimal", "robust", "secure", "efficient", "readable", "maintainable"]
    selected: list[str] = []
    for category in priority_order:
        for rule in CORE_PRINCIPLES.get(category, []):
            if len(selected) >= count:
                return selected
            selected.append(rule)
    return selected


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_language_specific_rules(language: str) -> list[str]:
    """Return language-specific engineering rules.

    Falls back to Python rules if language is not recognized.
    """
    return _LANGUAGE_RULES.get(language.lower(), _LANGUAGE_RULES["python"])


def build_system_injection(mode: str = "full", language: str = "python") -> str:
    """Assemble principles into a compact system prompt block.

    Args:
        mode: 'lite' (5 rules), 'full' (15 rules), or 'strict' (all rules).
        language: Target language for language-specific additions.

    Returns:
        A string block suitable for injection into an LLM system prompt.
        The 'full' mode output is kept under 500 tokens.
    """
    if mode not in _MODE_COUNTS:
        raise ValueError(f"Unknown mode '{mode}'. Use: {', '.join(_MODE_COUNTS)}")

    lines: list[str] = [ENGINEERING_PREAMBLE, ""]

    # Core rules
    selected = _select_principles(mode)
    lines.append("## Engineering Rules")
    for i, rule in enumerate(selected, 1):
        lines.append(f"{i}. {rule}")

    # Language-specific additions (limit to 3 in lite mode)
    lang_rules = get_language_specific_rules(language)
    lang_limit = 2 if mode == "lite" else len(lang_rules)
    lang_subset = lang_rules[:lang_limit]

    if lang_subset:
        lines.append("")
        lines.append(f"## {language.capitalize()}-Specific")
        for rule in lang_subset:
            lines.append(f"- {rule}")

    # Anti-pattern reminders in strict mode
    if mode == "strict":
        lines.append("")
        lines.append("## Avoid These Anti-Patterns")
        for name, fix in ANTI_PATTERNS.items():
            lines.append(f"- {name}: {fix}")

    return "\n".join(lines)
