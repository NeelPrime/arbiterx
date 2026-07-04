"""Robustness checker — ensures proper error handling, timeouts, and resource management."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class RobustnessIssue:
    """A single robustness issue found in code."""

    severity: str  # "high", "medium", "low"
    message: str
    line: int
    suggestion: str


# File operations that need error handling
_FILE_OPS = re.compile(
    r"""(?:open|Path\(.*\)\.(?:read_text|write_text|read_bytes|write_bytes|unlink|mkdir|rmdir))\s*\("""
)

# Network call patterns
_NETWORK_CALLS = re.compile(
    r"""(?:requests\.(?:get|post|put|patch|delete|head|options)|httpx\.(?:get|post|put|patch|delete)|urllib\.request\.urlopen|aiohttp\.ClientSession)\s*\("""
)

# Timeout parameter check
_HAS_TIMEOUT = re.compile(r"""timeout\s*=""")

# Database operation patterns
_DB_OPS = re.compile(
    r"""(?:session\.(?:add|delete|commit|execute|query|merge)|cursor\.(?:execute|executemany|fetchone|fetchall)|connection\.(?:execute|commit))\s*\("""
)

# Transaction / context manager patterns
_HAS_TRANSACTION = re.compile(
    r"""(?:with\s+.*(?:session|transaction|begin|atomic)|\.begin\(\)|@(?:atomic|transactional))"""
)

# Bare except clause
_BARE_EXCEPT = re.compile(r"""^\s*except\s*:""")

# Too-broad except
_BROAD_EXCEPT = re.compile(r"""^\s*except\s+(?:Exception|BaseException)\s*:""")

# Async patterns that need cancellation handling
_ASYNC_OPS = re.compile(
    r"""(?:asyncio\.(?:gather|wait|create_task|ensure_future))\s*\("""
)


class RobustnessChecker:
    """Checks code for missing error handling, timeouts, and resource management.

    Detects:
    - File operations without try/except or context managers
    - Network calls without timeout parameters
    - Database operations without transaction handling
    - Bare except clauses (too broad)
    - Async operations without cancellation handling
    """

    def check(self, code: str) -> List[RobustnessIssue]:
        """Run all robustness checks on the given code.

        Args:
            code: Source code string to analyze.

        Returns:
            List of RobustnessIssue instances found.
        """
        issues: List[RobustnessIssue] = []
        lines = code.splitlines()

        issues.extend(self._check_file_operations(lines))
        issues.extend(self._check_network_calls(lines))
        issues.extend(self._check_database_ops(lines))
        issues.extend(self._check_bare_excepts(lines))
        issues.extend(self._check_async_cancellation(lines, code))

        return issues

    def _check_file_operations(self, lines: list[str]) -> List[RobustnessIssue]:
        """Check that file operations use context managers or try/except."""
        issues: List[RobustnessIssue] = []

        for line_num, line in enumerate(lines, start=1):
            if not _FILE_OPS.search(line):
                continue

            # Already using 'with' on same line
            if "with " in line and "open(" in line:
                continue

            # Check if wrapped in try or with block
            has_protection = False
            indent_level = len(line) - len(line.lstrip())

            for i in range(line_num - 2, max(line_num - 10, -1), -1):
                if i < 0:
                    break
                prev_line = lines[i]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                if prev_indent < indent_level and prev_line.strip():
                    if re.match(r"\s*(?:try|with)\s*", prev_line):
                        has_protection = True
                    break

            if not has_protection:
                issues.append(
                    RobustnessIssue(
                        severity="medium",
                        message="File operation without error handling or context manager",
                        line=line_num,
                        suggestion="Wrap in 'with' statement or try/except for proper resource management",
                    )
                )

        return issues

    def _check_network_calls(self, lines: list[str]) -> List[RobustnessIssue]:
        """Check that network calls have timeout parameters."""
        issues: List[RobustnessIssue] = []

        for line_num, line in enumerate(lines, start=1):
            if not _NETWORK_CALLS.search(line):
                continue

            # Check if timeout is specified on this line or next few (multi-line calls)
            check_window = "\n".join(
                lines[line_num - 1 : min(line_num + 4, len(lines))]
            )
            if not _HAS_TIMEOUT.search(check_window):
                issues.append(
                    RobustnessIssue(
                        severity="high",
                        message="Network call without timeout parameter",
                        line=line_num,
                        suggestion="Add timeout parameter: requests.get(url, timeout=30)",
                    )
                )

        return issues

    def _check_database_ops(self, lines: list[str]) -> List[RobustnessIssue]:
        """Check that database operations have transaction handling."""
        issues: List[RobustnessIssue] = []

        for line_num, line in enumerate(lines, start=1):
            if not _DB_OPS.search(line):
                continue

            # Check if inside a transaction context (within 15 lines above)
            context_start = max(0, line_num - 16)
            context = "\n".join(lines[context_start:line_num])

            if _HAS_TRANSACTION.search(context):
                continue

            # Check if wrapped in try block
            indent_level = len(line) - len(line.lstrip())
            has_try = False
            for i in range(line_num - 2, max(line_num - 12, -1), -1):
                if i < 0:
                    break
                prev_line = lines[i]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                if prev_indent < indent_level and re.match(r"\s*try\s*:", prev_line):
                    has_try = True
                    break

            if not has_try:
                issues.append(
                    RobustnessIssue(
                        severity="medium",
                        message="Database operation without transaction handling",
                        line=line_num,
                        suggestion="Wrap in a transaction context: 'with session.begin():'",
                    )
                )

        return issues

    def _check_bare_excepts(self, lines: list[str]) -> List[RobustnessIssue]:
        """Check for bare except clauses or overly broad exception handling."""
        issues: List[RobustnessIssue] = []

        for line_num, line in enumerate(lines, start=1):
            if _BARE_EXCEPT.match(line):
                issues.append(
                    RobustnessIssue(
                        severity="high",
                        message="Bare except clause catches all exceptions including SystemExit",
                        line=line_num,
                        suggestion="Catch specific exceptions: except (ValueError, IOError) as e:",
                    )
                )
            elif _BROAD_EXCEPT.match(line):
                issues.append(
                    RobustnessIssue(
                        severity="low",
                        message="Overly broad exception handler",
                        line=line_num,
                        suggestion="Catch specific exceptions where possible, or log the exception",
                    )
                )

        return issues

    def _check_async_cancellation(
        self, lines: list[str], full_code: str
    ) -> List[RobustnessIssue]:
        """Check that async operations have proper cancellation handling."""
        issues: List[RobustnessIssue] = []

        if "async " not in full_code:
            return issues

        for line_num, line in enumerate(lines, start=1):
            if not _ASYNC_OPS.search(line):
                continue

            # asyncio.gather should have return_exceptions
            if "asyncio.gather" in line:
                check_window = "\n".join(
                    lines[line_num - 1 : min(line_num + 3, len(lines))]
                )
                if "return_exceptions" not in check_window:
                    issues.append(
                        RobustnessIssue(
                            severity="medium",
                            message="asyncio.gather() without return_exceptions=True",
                            line=line_num,
                            suggestion="Add return_exceptions=True or wrap with CancelledError handling",
                        )
                    )

            # create_task without cancellation handling
            if "create_task" in line or "ensure_future" in line:
                func_start = line_num - 1
                for i in range(line_num - 2, max(line_num - 30, -1), -1):
                    if i < 0:
                        break
                    if re.match(r"\s*async\s+def\s+", lines[i]):
                        func_start = i
                        break

                func_end = min(line_num + 20, len(lines))
                func_body = "\n".join(lines[func_start:func_end])

                if "CancelledError" not in func_body and "cancel()" not in func_body:
                    issues.append(
                        RobustnessIssue(
                            severity="low",
                            message="Task created without visible cancellation handling",
                            line=line_num,
                            suggestion="Handle asyncio.CancelledError or store task reference for cleanup",
                        )
                    )

        return issues
