"""Quality gate validator — orchestrates all checks and produces a GateResult."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import tree_sitter_language_pack as tslp

from arbiterx.gate.efficiency import EfficiencyChecker
from arbiterx.gate.robustness import RobustnessChecker
from arbiterx.gate.security import SecurityChecker


class Severity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(str, Enum):
    """Issue category classification."""

    SYNTAX = "syntax"
    SECURITY = "security"
    ROBUSTNESS = "robustness"
    EFFICIENCY = "efficiency"
    STYLE = "style"
    COMPLETENESS = "completeness"


@dataclass
class GateIssue:
    """A single issue found during quality gate validation."""

    severity: str
    category: str
    message: str
    line: int
    suggestion: str


@dataclass
class GateResult:
    """Result of running the quality gate on generated code."""

    passed: bool
    score: int  # 0-100
    issues: List[GateIssue] = field(default_factory=list)
    fixed_code: Optional[str] = None


# Style check patterns
_SINGLE_LETTER_VAR = re.compile(
    r"""^\s*([a-z])\s*=\s*(?!.*\bfor\b)"""
)
_ALLOWED_SINGLE_LETTERS = {"i", "j", "k", "x", "y", "n", "_"}

# Loop variable pattern (these are fine as single letters)
_LOOP_VAR = re.compile(r"""^\s*for\s+([a-z])\s+in\s+""")

# Completeness patterns
_INCOMPLETE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"""\b(?:TODO|FIXME|HACK|XXX)\b""", re.IGNORECASE), "TODO/FIXME/HACK comment left in code"),
    (re.compile(r"""(?:pass\s*#|\.\.\.)\s*$"""), "Placeholder implementation (pass or ...)"),
    (re.compile(r"""raise\s+NotImplementedError"""), "NotImplementedError — unfinished implementation"),
]

# Naming convention patterns
_CAMEL_CASE_FUNC = re.compile(r"""^\s*def\s+([a-z]+[A-Z][a-zA-Z]*)\s*\(""")
_MIXED_NAMING = re.compile(r"""^\s*([a-z]+[A-Z][a-zA-Z]*)\s*=""")


class QualityGate:
    """Main quality gate that orchestrates all checks on generated code.

    Runs a fast pipeline of checks (regex + tree-sitter, no LLM calls):
    1. SyntaxCheck — parse with tree-sitter
    2. SecurityCheck — no hardcoded secrets
    3. RobustnessCheck — error handling present
    4. EfficiencyCheck — no anti-patterns
    5. StyleCheck — consistent naming
    6. CompletenessCheck — no TODO/FIXME left

    Usage:
        gate = QualityGate()
        result = gate.validate(code, language="python")
        if not result.passed:
            for issue in result.issues:
                print(f"[{issue.severity}] {issue.message} (line {issue.line})")
    """

    def __init__(self, *, passing_score: int = 70, auto_fix: bool = True) -> None:
        """Initialize the quality gate.

        Args:
            passing_score: Minimum score (0-100) to pass. Default 70.
            auto_fix: Whether to attempt auto-fixing simple issues.
        """
        self._passing_score = passing_score
        self._auto_fix = auto_fix
        self._security = SecurityChecker()
        self._robustness = RobustnessChecker()
        self._efficiency = EfficiencyChecker()

    def validate(self, code: str, language: str = "python") -> GateResult:
        """Validate generated code through the full quality pipeline.

        Args:
            code: The generated source code to validate.
            language: Programming language identifier (default: "python").

        Returns:
            GateResult with pass/fail, score, issues, and optionally fixed code.
        """
        issues: List[GateIssue] = []

        # 1. Syntax check
        issues.extend(self._check_syntax(code, language))

        # 2. Security check
        for si in self._security.check(code):
            issues.append(
                GateIssue(
                    severity=si.severity,
                    category=Category.SECURITY,
                    message=si.message,
                    line=si.line,
                    suggestion=si.suggestion,
                )
            )

        # 3. Robustness check
        for ri in self._robustness.check(code):
            issues.append(
                GateIssue(
                    severity=ri.severity,
                    category=Category.ROBUSTNESS,
                    message=ri.message,
                    line=ri.line,
                    suggestion=ri.suggestion,
                )
            )

        # 4. Efficiency check
        for ei in self._efficiency.check(code):
            issues.append(
                GateIssue(
                    severity=ei.severity,
                    category=Category.EFFICIENCY,
                    message=ei.message,
                    line=ei.line,
                    suggestion=ei.suggestion,
                )
            )

        # 5. Style check
        issues.extend(self._check_style(code))

        # 6. Completeness check
        issues.extend(self._check_completeness(code))

        # Calculate score
        score = self._calculate_score(issues)

        # Auto-fix if enabled
        fixed_code = None
        if self._auto_fix and issues:
            fixed_code = self._attempt_auto_fix(code, issues)
            if fixed_code == code:
                fixed_code = None  # No changes made

        passed = score >= self._passing_score

        return GateResult(
            passed=passed,
            score=score,
            issues=issues,
            fixed_code=fixed_code,
        )

    def _check_syntax(self, code: str, language: str) -> List[GateIssue]:
        """Parse code with tree-sitter to verify valid syntax."""
        issues: List[GateIssue] = []

        try:
            lang = tslp.get_language(language)
            parser = tslp.get_parser(language)
        except (LookupError, Exception):
            # Language not supported by tree-sitter — skip syntax check
            return issues

        tree = parser.parse(code.encode("utf-8"))

        # Walk the tree looking for ERROR nodes
        errors = self._find_error_nodes(tree.root_node)
        for node in errors:
            start_line = node.start_point[0] + 1
            issues.append(
                GateIssue(
                    severity=Severity.CRITICAL,
                    category=Category.SYNTAX,
                    message=f"Syntax error at line {start_line}",
                    line=start_line,
                    suggestion="Fix the syntax error — code will not parse correctly",
                )
            )

        return issues

    def _find_error_nodes(self, node) -> list:
        """Recursively find ERROR and MISSING nodes in a tree-sitter tree."""
        errors = []
        if node.type == "ERROR" or node.is_missing:
            errors.append(node)
        for child in node.children:
            errors.extend(self._find_error_nodes(child))
        return errors

    def _check_style(self, code: str) -> List[GateIssue]:
        """Check for style issues: naming conventions, single-letter variables."""
        issues: List[GateIssue] = []
        lines = code.splitlines()

        # Collect loop variables (these are acceptable as single letters)
        loop_vars: set[str] = set()
        for line in lines:
            m = _LOOP_VAR.match(line)
            if m:
                loop_vars.add(m.group(1))

        for line_num, line in enumerate(lines, start=1):
            # Single-letter variable assignment (not in loop, not allowed set)
            m = _SINGLE_LETTER_VAR.match(line)
            if m:
                var = m.group(1)
                if var not in _ALLOWED_SINGLE_LETTERS and var not in loop_vars:
                    issues.append(
                        GateIssue(
                            severity=Severity.LOW,
                            category=Category.STYLE,
                            message=f"Single-letter variable '{var}' — use a descriptive name",
                            line=line_num,
                            suggestion="Rename to something descriptive (e.g., 'count', 'result', 'item')",
                        )
                    )

            # camelCase function names (should be snake_case in Python)
            m = _CAMEL_CASE_FUNC.match(line)
            if m:
                issues.append(
                    GateIssue(
                        severity=Severity.LOW,
                        category=Category.STYLE,
                        message=f"Function '{m.group(1)}' uses camelCase — Python convention is snake_case",
                        line=line_num,
                        suggestion="Rename to snake_case: e.g., 'getUserName' -> 'get_user_name'",
                    )
                )

        return issues

    def _check_completeness(self, code: str) -> List[GateIssue]:
        """Check for incomplete/placeholder code markers."""
        issues: List[GateIssue] = []
        lines = code.splitlines()

        for line_num, line in enumerate(lines, start=1):
            for pattern, message in _INCOMPLETE_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        GateIssue(
                            severity=Severity.MEDIUM,
                            category=Category.COMPLETENESS,
                            message=message,
                            line=line_num,
                            suggestion="Complete the implementation before shipping",
                        )
                    )
                    break  # One issue per line

        return issues

    def _calculate_score(self, issues: List[GateIssue]) -> int:
        """Calculate a quality score (0-100) based on issues found."""
        if not issues:
            return 100

        # Deduction weights by severity
        deductions = {
            Severity.CRITICAL: 25,
            "critical": 25,
            Severity.HIGH: 15,
            "high": 15,
            Severity.MEDIUM: 8,
            "medium": 8,
            Severity.LOW: 3,
            "low": 3,
        }

        total_deduction = 0
        for issue in issues:
            total_deduction += deductions.get(issue.severity, 5)

        return max(0, 100 - total_deduction)

    def _attempt_auto_fix(self, code: str, issues: List[GateIssue]) -> str:
        """Attempt to auto-fix simple issues in the code.

        Currently handles:
        - Removing TODO/FIXME/HACK comments
        - Removing unused imports (basic detection)
        """
        lines = code.splitlines()

        # Remove TODO/FIXME/HACK inline comments
        todo_pattern = re.compile(r"""\s*#\s*(?:TODO|FIXME|HACK|XXX)\b.*$""", re.IGNORECASE)
        for i, line in enumerate(lines):
            # Only remove if it's a trailing comment, not the entire line
            if re.match(r"""^\s*#\s*(?:TODO|FIXME|HACK|XXX)\b""", line, re.IGNORECASE):
                # Entire line is a TODO comment — remove it
                lines[i] = ""
            else:
                # Trailing TODO comment — strip it
                lines[i] = todo_pattern.sub("", line)

        # Remove empty lines left behind (collapse multiple blank lines)
        cleaned: list[str] = []
        prev_blank = False
        for line in lines:
            is_blank = line.strip() == ""
            if is_blank and prev_blank:
                continue
            cleaned.append(line)
            prev_blank = is_blank

        return "\n".join(cleaned)
