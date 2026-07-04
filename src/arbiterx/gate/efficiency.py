"""Efficiency checker — detects performance anti-patterns and suggests optimizations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class EfficiencyIssue:
    """A single efficiency issue found in code."""

    severity: str  # "high", "medium", "low"
    message: str
    line: int
    suggestion: str


# String concatenation in loop patterns
_LOOP_START = re.compile(r"""^\s*(?:for|while)\s+""")
_STRING_CONCAT_ASSIGN = re.compile(r"""(\w+)\s*\+=\s*(?:['"]|f['"]|str\(|\w+\s*\+)""")
_STRING_CONCAT_REASSIGN = re.compile(r"""(\w+)\s*=\s*\1\s*\+\s*""")

# Nested list comprehension (overly complex)
_NESTED_COMPREHENSION = re.compile(
    r"""\[.*\bfor\b.*\bfor\b.*\bfor\b.*\]"""
)

# Double nested comprehension (two levels)
_DOUBLE_NESTED_COMP = re.compile(
    r"""\[.*\bfor\b.*\bfor\b.*\]"""
)

# Unnecessary list() wrapping a generator
_UNNECESSARY_LIST = re.compile(
    r"""list\(\s*(?:\w+\s*\.\s*)?(?:keys|values|items|range|map|filter|zip|enumerate)\s*\("""
)

# list() around a generator expression used in for loop
_LIST_IN_FOR = re.compile(r"""for\s+\w+\s+in\s+list\(""")


class EfficiencyChecker:
    """Checks code for performance anti-patterns using regex heuristics.

    Detects:
    - String concatenation in loops (suggest join)
    - Nested list comprehensions that could be generators
    - Repeated computation that should be cached
    - O(n^2) patterns (nested for loops over same collection)
    - Unnecessary list() calls on generators/iterables
    """

    def check(self, code: str) -> List[EfficiencyIssue]:
        """Run all efficiency checks on the given code.

        Args:
            code: Source code string to analyze.

        Returns:
            List of EfficiencyIssue instances found.
        """
        issues: List[EfficiencyIssue] = []
        lines = code.splitlines()

        issues.extend(self._check_string_concat_in_loops(lines))
        issues.extend(self._check_nested_comprehensions(lines))
        issues.extend(self._check_repeated_computation(lines))
        issues.extend(self._check_quadratic_patterns(lines))
        issues.extend(self._check_unnecessary_list(lines))

        return issues

    def _check_string_concat_in_loops(
        self, lines: list[str]
    ) -> List[EfficiencyIssue]:
        """Detect string concatenation inside loops."""
        issues: List[EfficiencyIssue] = []
        loop_stack: list[int] = []  # indent levels of active loops

        for line_num, line in enumerate(lines, start=1):
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip())

            # Pop loops that we've exited (based on indentation)
            while loop_stack and indent <= loop_stack[-1]:
                loop_stack.pop()

            # Track loop entry
            if _LOOP_START.match(line):
                loop_stack.append(indent)
                continue

            # Inside a loop — check for string concatenation
            if loop_stack:
                if _STRING_CONCAT_ASSIGN.search(line) or _STRING_CONCAT_REASSIGN.search(line):
                    # Heuristic: skip numeric-looking operations
                    if re.search(r"""\+=\s*\d""", line):
                        continue
                    # Skip counter increments
                    if re.search(r"""\+=\s*1\s*$""", line):
                        continue
                    issues.append(
                        EfficiencyIssue(
                            severity="medium",
                            message="String concatenation in loop — O(n^2) for strings",
                            line=line_num,
                            suggestion="Collect items in a list and use ''.join(items) after the loop",
                        )
                    )

        return issues

    def _check_nested_comprehensions(
        self, lines: list[str]
    ) -> List[EfficiencyIssue]:
        """Detect overly nested list comprehensions."""
        issues: List[EfficiencyIssue] = []

        for line_num, line in enumerate(lines, start=1):
            if _NESTED_COMPREHENSION.search(line):
                issues.append(
                    EfficiencyIssue(
                        severity="medium",
                        message="Triple-nested list comprehension — hard to read and potentially slow",
                        line=line_num,
                        suggestion="Break into a generator function or explicit loops for clarity",
                    )
                )
            elif _DOUBLE_NESTED_COMP.search(line):
                # Only flag if the line is very long (complex)
                if len(line.strip()) > 80:
                    issues.append(
                        EfficiencyIssue(
                            severity="low",
                            message="Complex nested list comprehension — consider a generator expression",
                            line=line_num,
                            suggestion="Use a generator expression (...) if the result is iterated only once",
                        )
                    )

        return issues

    def _check_repeated_computation(
        self, lines: list[str]
    ) -> List[EfficiencyIssue]:
        """Detect repeated expensive calls inside loops."""
        issues: List[EfficiencyIssue] = []
        loop_stack: list[int] = []
        seen_calls_in_loop: dict[str, int] = {}

        # Patterns for expensive operations
        expensive_call = re.compile(
            r"""(?:re\.compile|json\.loads|json\.dumps|sorted|list\(|open\(|\.read\(|\.readlines\()"""
        )

        for line_num, line in enumerate(lines, start=1):
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip())

            # Pop loops we've exited
            while loop_stack and indent <= loop_stack[-1]:
                loop_stack.pop()
                seen_calls_in_loop.clear()

            if _LOOP_START.match(line):
                loop_stack.append(indent)
                seen_calls_in_loop.clear()
                continue

            if loop_stack:
                match = expensive_call.search(line)
                if match:
                    call_text = match.group(0)
                    if call_text in seen_calls_in_loop:
                        # Already flagged this call in this loop
                        continue
                    # Check if it looks like the same call on a constant
                    # (e.g., re.compile with a literal pattern inside a loop)
                    if "re.compile" in call_text:
                        issues.append(
                            EfficiencyIssue(
                                severity="high",
                                message="re.compile() called inside a loop — compile once outside",
                                line=line_num,
                                suggestion="Move re.compile() outside the loop and reuse the compiled pattern",
                            )
                        )
                        seen_calls_in_loop[call_text] = line_num

        return issues

    def _check_quadratic_patterns(
        self, lines: list[str]
    ) -> List[EfficiencyIssue]:
        """Detect O(n^2) patterns: nested for loops over the same collection."""
        issues: List[EfficiencyIssue] = []

        # Track for-loop variables and their iterables
        for_pattern = re.compile(r"""^\s*for\s+(\w+)\s+in\s+(\w+)""")

        outer_loops: list[tuple[int, str, int]] = []  # (indent, iterable, line)

        for line_num, line in enumerate(lines, start=1):
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip())

            # Remove outer loops we've left
            while outer_loops and indent <= outer_loops[-1][0]:
                outer_loops.pop()

            match = for_pattern.match(line)
            if match:
                _, iterable = match.groups()

                # Check if this is a nested loop over same collection
                for outer_indent, outer_iterable, outer_line in outer_loops:
                    if iterable == outer_iterable:
                        issues.append(
                            EfficiencyIssue(
                                severity="high",
                                message=f"Nested loops over same collection '{iterable}' — O(n^2) complexity",
                                line=line_num,
                                suggestion="Consider using a set/dict for O(1) lookups, or itertools.combinations()",
                            )
                        )
                        break

                outer_loops.append((indent, iterable, line_num))

        return issues

    def _check_unnecessary_list(self, lines: list[str]) -> List[EfficiencyIssue]:
        """Detect unnecessary list() wrapping on iterables."""
        issues: List[EfficiencyIssue] = []

        for line_num, line in enumerate(lines, start=1):
            # list() around dict methods, range, map, filter, etc. in a for loop
            if _LIST_IN_FOR.search(line):
                issues.append(
                    EfficiencyIssue(
                        severity="low",
                        message="Unnecessary list() in for loop — iterables work directly",
                        line=line_num,
                        suggestion="Remove list(): 'for x in range(...)' instead of 'for x in list(range(...))'",
                    )
                )
            elif _UNNECESSARY_LIST.search(line):
                # Only flag if it's in a context where a generator would suffice
                # (not assigned to a variable that might need indexing)
                if re.match(r"""\s*for\s+""", line) or "in list(" in line:
                    issues.append(
                        EfficiencyIssue(
                            severity="low",
                            message="Potentially unnecessary list() materialization",
                            line=line_num,
                            suggestion="If only iterating, remove list() to save memory",
                        )
                    )

        return issues
