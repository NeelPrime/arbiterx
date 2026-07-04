"""Engineering enforcement ladder with self-interrogation cascade.

Phase 1: 16-step decision ladder for intelligent model routing.
Phase 2: Engineering arbiterx enforcement on generated code via static analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto

from arbiterx.router.classifier import ClassifiedTask

# ─── Enums ────────────────────────────────────────────────────────────────────


class LadderAction(Enum):
    """Action to take after interrogation."""

    USE_CACHE = auto()
    USE_LOCAL = auto()
    USE_SMALL = auto()
    USE_MEDIUM = auto()
    USE_LARGE = auto()
    USE_EXPERT = auto()
    DECOMPOSE = auto()
    REJECT = auto()


class Severity(Enum):
    """Violation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ArbiterX(Enum):
    """Engineering arbiterxs that can be enforced."""

    YAGNI = "yagni"
    ERROR_HANDLING = "error_handling"
    TYPE_SAFETY = "type_safety"
    RESOURCE_CLEANUP = "resource_cleanup"
    NO_MAGIC_NUMBERS = "no_magic_numbers"
    NO_DEAD_CODE = "no_dead_code"
    SINGLE_RESPONSIBILITY = "single_responsibility"
    FAIL_FAST = "fail_fast"
    IDEMPOTENCY = "idempotency"
    PERFORMANCE = "performance"


# ─── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class LadderResult:
    """Result of the self-interrogation cascade."""

    step_reached: int
    reason: str
    action: LadderAction
    tokens_saved: int
    confidence: float = 0.0
    details: dict[str, str] = field(default_factory=dict)


@dataclass
class _StepResult:
    """Internal result of a single interrogation step."""

    passed: bool
    reason: str
    action: LadderAction | None = None
    tokens_saved: int = 0


@dataclass
class EngineeringViolation:
    """A single engineering arbiterx violation found in code."""

    arbiterx_name: str
    severity: Severity
    description: str
    line_hint: int | None
    suggested_fix: str


@dataclass
class EngineeringReport:
    """Aggregate report from engineering enforcement pass."""

    violations: list[EngineeringViolation] = field(default_factory=list)
    passed: bool = True
    summary: str = ""
    score: int = 100


@dataclass
class ArbiterXConfig:
    """Configuration for which arbiterxs are active and their severity overrides."""

    enabled: dict[ArbiterX, bool] = field(default_factory=lambda: {t: True for t in ArbiterX})
    severity_overrides: dict[ArbiterX, Severity] = field(default_factory=dict)
    max_function_lines: int = 30
    magic_number_threshold: int = 1  # Allow 0 and 1 as non-magic


# ─── Phase 1: Decision Ladder ─────────────────────────────────────────────────


class SelfInterrogator:
    """16-step interrogation cascade + engineering enforcement.

    Phase 1 (Decision Ladder): Determines the minimal model needed for a task.
    Phase 2 (Engineering Enforcement): Validates generated code against arbiterxs.

    Steps 1-16:
     1. Is the answer already cached?
     2. Is this an exact repeat of a recent query?
     3. Can this be answered with a static lookup/template?
     4. Is the response a single token (yes/no, true/false)?
     5. Is this simple reformatting or translation?
     6. Can a regex or rule handle this?
     7. Is the full context already in the prompt?
     8. Is the task within a single function's scope?
     9. Does it require only local file context?
    10. Does it need cross-file understanding?
    11. Does it need repository-wide reasoning?
    12. Does it involve ambiguous requirements needing clarification?
    13. Does it require multi-step planning?
    14. Does it need domain expertise beyond code?
    15. Is this a novel architectural decision?
    16. Is the task beyond current AI capability?
    """

    def __init__(
        self,
        cache_available: bool = True,
        avg_token_cost: float = 0.003,
        arbiterx_config: ArbiterXConfig | None = None,
    ) -> None:
        self.cache_available = cache_available
        self.avg_token_cost = avg_token_cost
        self.config = arbiterx_config or ArbiterXConfig()

    def interrogate(self, task: ClassifiedTask, query: str) -> LadderResult:
        """Run the 16-step cascade on a classified task."""

        steps = [
            self._step_01_cached,
            self._step_02_repeat,
            self._step_03_template,
            self._step_04_single_token,
            self._step_05_reformatting,
            self._step_06_rule_based,
            self._step_07_self_contained,
            self._step_08_single_function,
            self._step_09_local_file,
            self._step_10_cross_file,
            self._step_11_repo_wide,
            self._step_12_ambiguous,
            self._step_13_multi_step,
            self._step_14_domain_expertise,
            self._step_15_architectural,
            self._step_16_beyond_capability,
        ]

        for i, step_fn in enumerate(steps, start=1):
            result = step_fn(task, query)
            if not result.passed:
                action = result.action or self._default_action(i)
                return LadderResult(
                    step_reached=i,
                    reason=result.reason,
                    action=action,
                    tokens_saved=result.tokens_saved,
                    confidence=self._step_confidence(i, task),
                )

        return LadderResult(
            step_reached=16,
            reason="Task requires maximum capability",
            action=LadderAction.USE_EXPERT,
            tokens_saved=0,
            confidence=task.confidence,
        )

    # ── Ladder Steps ──────────────────────────────────────────────────────────

    def _step_01_cached(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import Complexity

        if self.cache_available and task.complexity == Complexity.TRIVIAL:
            return _StepResult(
                False, "Trivial task likely cached", LadderAction.USE_CACHE, task.estimated_tokens
            )
        return _StepResult(True, "Not cached")

    def _step_02_repeat(self, task: ClassifiedTask, query: str) -> _StepResult:
        return _StepResult(True, "Not a repeat")

    def _step_03_template(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import Complexity

        keywords = ["boilerplate", "scaffold", "starter", "template"]
        if any(kw in query.lower() for kw in keywords):
            if task.complexity in (Complexity.TRIVIAL, Complexity.LOW):
                return _StepResult(
                    False,
                    "Template-based response sufficient",
                    LadderAction.USE_LOCAL,
                    task.estimated_tokens - 50,
                )
        return _StepResult(True, "Not template-able")

    def _step_04_single_token(self, task: ClassifiedTask, query: str) -> _StepResult:
        yn_patterns = ["is it", "does it", "can i", "should i", "will it"]
        q_lower = query.lower().strip()
        if any(q_lower.startswith(p) for p in yn_patterns) and len(query.split()) < 8:
            return _StepResult(
                False,
                "Yes/no question — minimal model",
                LadderAction.USE_SMALL,
                task.estimated_tokens - 10,
            )
        return _StepResult(True, "Not a yes/no question")

    def _step_05_reformatting(self, task: ClassifiedTask, query: str) -> _StepResult:
        keywords = ["format", "reformat", "prettify", "indent", "lint"]
        if any(kw in query.lower() for kw in keywords):
            return _StepResult(
                False,
                "Reformatting — local tool",
                LadderAction.USE_LOCAL,
                task.estimated_tokens - 100,
            )
        return _StepResult(True, "Not reformatting")

    def _step_06_rule_based(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import Complexity

        keywords = ["rename", "find and replace", "search", "grep"]
        if any(kw in query.lower() for kw in keywords) and task.complexity == Complexity.TRIVIAL:
            return _StepResult(
                False, "Rule-based operation", LadderAction.USE_LOCAL, task.estimated_tokens
            )
        return _StepResult(True, "Not rule-based")

    def _step_07_self_contained(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import Complexity

        if task.estimated_tokens < 200 and task.complexity == Complexity.LOW:
            return _StepResult(
                False,
                "Self-contained, small model sufficient",
                LadderAction.USE_SMALL,
                task.estimated_tokens // 2,
            )
        return _StepResult(True, "Needs external context")

    def _step_08_single_function(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import Complexity, TaskType

        if task.task_type in (TaskType.DEBUGGING, TaskType.CODE_GENERATION):
            if task.complexity.value <= Complexity.LOW.value:
                return _StepResult(
                    False,
                    "Single-function scope",
                    LadderAction.USE_SMALL,
                    task.estimated_tokens // 3,
                )
        return _StepResult(True, "Broader than single function")

    def _step_09_local_file(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import ContextScope

        if task.context_scope == ContextScope.FILE:
            return _StepResult(
                False,
                "File-scoped — medium model",
                LadderAction.USE_MEDIUM,
                task.estimated_tokens // 4,
            )
        return _StepResult(True, "Needs broader context")

    def _step_10_cross_file(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import ContextScope

        if task.context_scope == ContextScope.MODULE:
            return _StepResult(
                False,
                "Module-scoped — medium model",
                LadderAction.USE_MEDIUM,
                task.estimated_tokens // 5,
            )
        return _StepResult(True, "Needs repo-wide context")

    def _step_11_repo_wide(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import Complexity

        if task.complexity == Complexity.HIGH:
            return _StepResult(
                False, "Repo-wide reasoning — large model", LadderAction.USE_LARGE, 0
            )
        return _StepResult(True, "Even broader scope needed")

    def _step_12_ambiguous(self, task: ClassifiedTask, query: str) -> _StepResult:
        signals = ["maybe", "not sure", "could be", "possibly", "or"]
        if sum(1 for s in signals if s in query.lower()) >= 2:
            return _StepResult(
                False, "Ambiguous — large model for clarification", LadderAction.USE_LARGE, 0
            )
        return _StepResult(True, "Requirements seem clear")

    def _step_13_multi_step(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import Complexity, TaskType

        if task.complexity.value >= Complexity.HIGH.value:
            if task.task_type in (TaskType.ARCHITECTURE, TaskType.REFACTORING):
                return _StepResult(
                    False, "Multi-step planning — large model", LadderAction.USE_LARGE, 0
                )
        return _StepResult(True, "Single-step or handled")

    def _step_14_domain_expertise(self, task: ClassifiedTask, query: str) -> _StepResult:
        keywords = ["legal", "medical", "financial", "compliance", "regulation"]
        if any(kw in query.lower() for kw in keywords):
            return _StepResult(False, "Domain expertise — expert model", LadderAction.USE_EXPERT, 0)
        return _StepResult(True, "Standard code domain")

    def _step_15_architectural(self, task: ClassifiedTask, query: str) -> _StepResult:
        from arbiterx.router.classifier import Complexity, TaskType

        if task.task_type == TaskType.ARCHITECTURE and task.complexity == Complexity.EXPERT:
            return _StepResult(
                False, "Novel architecture — expert model", LadderAction.USE_EXPERT, 0
            )
        return _StepResult(True, "Not novel architecture")

    def _step_16_beyond_capability(self, task: ClassifiedTask, query: str) -> _StepResult:
        reject_signals = [
            "predict the future",
            "guarantee",
            "prove mathematically",
            "real-time data",
            "access the internet",
        ]
        if any(s in query.lower() for s in reject_signals):
            return _StepResult(
                False, "Task may exceed AI capability", LadderAction.REJECT, task.estimated_tokens
            )
        return _StepResult(True, "Within capability")

    def _default_action(self, step: int) -> LadderAction:
        if step <= 3:
            return LadderAction.USE_CACHE
        elif step <= 6:
            return LadderAction.USE_LOCAL
        elif step <= 8:
            return LadderAction.USE_SMALL
        elif step <= 11:
            return LadderAction.USE_MEDIUM
        elif step <= 14:
            return LadderAction.USE_LARGE
        return LadderAction.USE_EXPERT

    def _step_confidence(self, step: int, task: ClassifiedTask) -> float:
        step_conf = max(0.3, 1.0 - (step - 1) * 0.05)
        return min(1.0, step_conf * task.confidence * 1.2)

    # ─── Phase 2: Engineering Enforcement ─────────────────────────────────────

    def enforce(self, code: str, language: str = "python") -> EngineeringReport:
        """Run all enabled arbiterx checks against generated code.

        Args:
            code: The generated source code to analyze.
            language: Programming language of the code (default: python).

        Returns:
            EngineeringReport with violations, score, and pass/fail status.
        """
        violations: list[EngineeringViolation] = []
        lines = code.splitlines()

        checkers: list[tuple[ArbiterX, callable]] = [
            (ArbiterX.YAGNI, self._check_yagni),
            (ArbiterX.ERROR_HANDLING, self._check_error_handling),
            (ArbiterX.TYPE_SAFETY, self._check_type_safety),
            (ArbiterX.RESOURCE_CLEANUP, self._check_resource_cleanup),
            (ArbiterX.NO_MAGIC_NUMBERS, self._check_magic_numbers),
            (ArbiterX.NO_DEAD_CODE, self._check_dead_code),
            (ArbiterX.SINGLE_RESPONSIBILITY, self._check_single_responsibility),
            (ArbiterX.FAIL_FAST, self._check_fail_fast),
            (ArbiterX.IDEMPOTENCY, self._check_idempotency),
            (ArbiterX.PERFORMANCE, self._check_performance),
        ]

        for arbiterx, checker in checkers:
            if not self.config.enabled.get(arbiterx, True):
                continue
            found = checker(lines, language)
            for v in found:
                if arbiterx in self.config.severity_overrides:
                    v.severity = self.config.severity_overrides[arbiterx]
                violations.append(v)

        error_count = sum(1 for v in violations if v.severity == Severity.ERROR)
        warning_count = sum(1 for v in violations if v.severity == Severity.WARNING)
        score = max(0, 100 - (error_count * 15) - (warning_count * 5))
        passed = error_count == 0

        summary_parts: list[str] = []
        if error_count:
            summary_parts.append(f"{error_count} error(s)")
        if warning_count:
            summary_parts.append(f"{warning_count} warning(s)")
        summary = f"Engineering score: {score}/100. " + (
            ", ".join(summary_parts) if summary_parts else "All arbiterxs passed."
        )

        return EngineeringReport(violations=violations, passed=passed, summary=summary, score=score)

    def audit_plan(self, task_description: str) -> list[str]:
        """Return engineering concerns to consider BEFORE writing code.

        Args:
            task_description: What the task intends to accomplish.

        Returns:
            List of engineering concerns/reminders relevant to the task.
        """
        concerns: list[str] = []
        desc_lower = task_description.lower()

        if any(w in desc_lower for w in ["file", "read", "write", "open", "path"]):
            concerns.append("Ensure file handles are closed (use context managers).")
            concerns.append("Add error handling for FileNotFoundError, PermissionError.")

        if any(w in desc_lower for w in ["http", "request", "api", "fetch", "url"]):
            concerns.append("Handle network timeouts and connection errors.")
            concerns.append("Validate response status codes before processing.")

        if any(w in desc_lower for w in ["database", "sql", "query", "insert", "update"]):
            concerns.append("Use parameterized queries to prevent SQL injection.")
            concerns.append("Wrap DB operations in transactions for idempotency.")
            concerns.append("Close connections/cursors in finally blocks.")

        if any(w in desc_lower for w in ["loop", "iterate", "list", "array", "process all"]):
            concerns.append("Consider time complexity — avoid nested iterations if possible.")

        if any(w in desc_lower for w in ["config", "setting", "option", "flag"]):
            concerns.append("Extract magic numbers/strings into named constants.")

        if any(w in desc_lower for w in ["parse", "input", "user", "argument", "param"]):
            concerns.append("Validate inputs at function entry (fail fast).")
            concerns.append("Add type hints to all parameters and return values.")

        if any(w in desc_lower for w in ["retry", "queue", "async", "background"]):
            concerns.append("Ensure operations are idempotent — safe to retry.")

        if not concerns:
            concerns.append("Add type hints to all function signatures.")
            concerns.append("Keep functions under 30 lines (single responsibility).")
            concerns.append("No magic numbers — use named constants.")

        return concerns

    # ── ArbiterX Checkers ────────────────────────────────────────────────────────

    def _check_yagni(self, lines: list[str], language: str) -> list[EngineeringViolation]:
        """Detect over-engineering: abstract base classes with single implementations, unused params."""
        violations: list[EngineeringViolation] = []

        # Detect ABC/abstract patterns that suggest premature abstraction
        abc_pattern = re.compile(r"class\s+\w+\s*\(.*(?:ABC|Abstract|Base).*\)")
        for i, line in enumerate(lines, 1):
            if abc_pattern.search(line):
                violations.append(
                    EngineeringViolation(
                        arbiterx_name="YAGNI",
                        severity=Severity.WARNING,
                        description="Abstract base class detected — ensure it has multiple implementations",
                        line_hint=i,
                        suggested_fix="Remove abstraction unless multiple concrete classes exist now (not 'might exist later').",
                    )
                )

        # Detect *args/**kwargs without clear purpose
        catchall_pattern = re.compile(r"def\s+\w+\s*\([^)]*\*\*kwargs[^)]*\)")
        for i, line in enumerate(lines, 1):
            if catchall_pattern.search(line) and "override" not in line.lower():
                violations.append(
                    EngineeringViolation(
                        arbiterx_name="YAGNI",
                        severity=Severity.INFO,
                        description="**kwargs may indicate over-generalization",
                        line_hint=i,
                        suggested_fix="Use explicit parameters unless this is a decorator or wrapper.",
                    )
                )

        return violations

    def _check_error_handling(self, lines: list[str], language: str) -> list[EngineeringViolation]:
        """Ensure I/O, network, and file operations have try/except or context managers."""
        violations: list[EngineeringViolation] = []

        io_patterns = [
            (re.compile(r"open\s*\("), "file open"),
            (re.compile(r"requests\.\w+\s*\("), "HTTP request"),
            (re.compile(r"urllib\.request"), "URL request"),
            (re.compile(r"socket\.\w+\s*\("), "socket operation"),
            (re.compile(r"\.\s*connect\s*\("), "connection"),
            (re.compile(r"subprocess\.\w+\s*\("), "subprocess call"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, op_name in io_patterns:
                if pattern.search(line):
                    # Check if this line is inside a try block or uses `with`
                    context_start = max(0, i - 6)
                    context = "\n".join(lines[context_start:i])
                    has_try = "try:" in context or "try :" in context
                    has_with = re.search(r"\bwith\b", context) is not None
                    if not has_try and not has_with and "with " not in line:
                        violations.append(
                            EngineeringViolation(
                                arbiterx_name="ERROR_HANDLING",
                                severity=Severity.ERROR,
                                description=f"Unprotected {op_name} — no try/except or context manager",
                                line_hint=i,
                                suggested_fix=f"Wrap {op_name} in try/except or use a `with` statement.",
                            )
                        )

        return violations

    def _check_type_safety(self, lines: list[str], language: str) -> list[EngineeringViolation]:
        """Check that function definitions have type hints."""
        if language not in ("python", "py"):
            return []

        violations: list[EngineeringViolation] = []
        func_pattern = re.compile(r"^\s*def\s+(\w+)\s*\(([^)]*)\)")

        for i, line in enumerate(lines, 1):
            match = func_pattern.match(line)
            if not match:
                continue
            func_name = match.group(1)
            params = match.group(2)

            # Skip dunder methods and self/cls
            if func_name.startswith("__") and func_name.endswith("__"):
                continue

            # Check return type
            if "->" not in line:
                violations.append(
                    EngineeringViolation(
                        arbiterx_name="TYPE_SAFETY",
                        severity=Severity.WARNING,
                        description=f"Function '{func_name}' missing return type annotation",
                        line_hint=i,
                        suggested_fix=f"Add -> ReturnType to '{func_name}'.",
                    )
                )

            # Check parameter annotations
            if params.strip():
                param_list = [p.strip() for p in params.split(",")]
                for param in param_list:
                    param_name = param.split("=")[0].split(":")[0].strip()
                    if param_name in ("self", "cls", "*", "/"):
                        continue
                    if ":" not in param and param_name:
                        violations.append(
                            EngineeringViolation(
                                arbiterx_name="TYPE_SAFETY",
                                severity=Severity.WARNING,
                                description=f"Parameter '{param_name}' in '{func_name}' has no type hint",
                                line_hint=i,
                                suggested_fix=f"Add type annotation: {param_name}: Type",
                            )
                        )

        return violations

    def _check_resource_cleanup(
        self, lines: list[str], language: str
    ) -> list[EngineeringViolation]:
        """Detect resources opened without context managers."""
        violations: list[EngineeringViolation] = []

        # Pattern: variable = open(...) without `with`
        bare_open = re.compile(r"(\w+)\s*=\s*open\s*\(")
        for i, line in enumerate(lines, 1):
            if bare_open.search(line) and "with " not in line:
                violations.append(
                    EngineeringViolation(
                        arbiterx_name="RESOURCE_CLEANUP",
                        severity=Severity.ERROR,
                        description="File opened without context manager — risk of resource leak",
                        line_hint=i,
                        suggested_fix="Use `with open(...) as f:` instead of bare assignment.",
                    )
                )

        # Pattern: connection created without close in surrounding scope
        conn_patterns = re.compile(r"(\w+)\s*=\s*(?:create_connection|connect|socket\.socket)\s*\(")
        for i, line in enumerate(lines, 1):
            match = conn_patterns.search(line)
            if match and "with " not in line:
                var_name = match.group(1)
                remaining = "\n".join(lines[i : min(i + 20, len(lines))])
                if f"{var_name}.close()" not in remaining and "finally" not in remaining:
                    violations.append(
                        EngineeringViolation(
                            arbiterx_name="RESOURCE_CLEANUP",
                            severity=Severity.ERROR,
                            description=f"Connection '{var_name}' may not be closed",
                            line_hint=i,
                            suggested_fix=f"Use context manager or ensure {var_name}.close() in a finally block.",
                        )
                    )

        return violations

    def _check_magic_numbers(self, lines: list[str], language: str) -> list[EngineeringViolation]:
        """Flag numeric literals that should be named constants."""
        violations: list[EngineeringViolation] = []
        threshold = self.config.magic_number_threshold

        # Match standalone numbers in expressions (not in imports, indices 0/1, or definitions)
        magic_pattern = re.compile(r"(?<!=\s)(?<![.\[,])\b(\d+\.?\d*)\b")
        skip_contexts = re.compile(r"(range\(|import |#|__version__|sleep\(0)")
        constant_def = re.compile(r"^[A-Z_][A-Z_0-9]*\s*=")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("import"):
                continue
            if constant_def.match(stripped):
                continue
            if skip_contexts.search(line):
                continue

            for match in magic_pattern.finditer(line):
                try:
                    value = float(match.group(1))
                except ValueError:
                    continue
                if value <= threshold or value in (100, 1000):  # common benign values
                    continue
                # Skip if it's in a type hint or string
                if ":" in line[: match.start()] and "->" not in line[: match.start()]:
                    continue
                violations.append(
                    EngineeringViolation(
                        arbiterx_name="NO_MAGIC_NUMBERS",
                        severity=Severity.WARNING,
                        description=f"Magic number {match.group(1)} — use a named constant",
                        line_hint=i,
                        suggested_fix=f"Extract to: MEANINGFUL_NAME = {match.group(1)}",
                    )
                )

        return violations

    def _check_dead_code(self, lines: list[str], language: str) -> list[EngineeringViolation]:
        """Detect commented-out code, unused imports, unreachable branches."""
        violations: list[EngineeringViolation] = []

        # Commented-out code (lines starting with # that look like code)
        code_comment_pattern = re.compile(
            r"^\s*#\s*(def |class |import |from |return |if |for |while |print\()"
        )
        for i, line in enumerate(lines, 1):
            if code_comment_pattern.match(line):
                violations.append(
                    EngineeringViolation(
                        arbiterx_name="NO_DEAD_CODE",
                        severity=Severity.WARNING,
                        description="Commented-out code detected — remove or restore",
                        line_hint=i,
                        suggested_fix="Delete commented code. Use version control to recover old code.",
                    )
                )

        # Unused imports heuristic: import X where X never appears again
        import_pattern = re.compile(r"^\s*(?:from\s+\S+\s+)?import\s+(.+)")
        full_code = "\n".join(lines)
        for i, line in enumerate(lines, 1):
            match = import_pattern.match(line)
            if not match:
                continue
            imported_names = match.group(1)
            for name in imported_names.split(","):
                name = name.strip().split(" as ")[-1].strip()
                if not name or name == "*":
                    continue
                # Count occurrences beyond the import line itself
                occurrences = len(re.findall(r"\b" + re.escape(name) + r"\b", full_code))
                if occurrences <= 1:
                    violations.append(
                        EngineeringViolation(
                            arbiterx_name="NO_DEAD_CODE",
                            severity=Severity.WARNING,
                            description=f"Import '{name}' appears unused",
                            line_hint=i,
                            suggested_fix=f"Remove unused import: {name}",
                        )
                    )

        # Unreachable code after return/raise/break/continue
        terminal_pattern = re.compile(r"^\s+(return|raise|break|continue)\b")
        for i, line in enumerate(lines[:-1], 1):
            if terminal_pattern.match(line):
                next_line = lines[i].strip() if i < len(lines) else ""
                if next_line and not next_line.startswith(
                    ("#", "def ", "class ", "elif", "else", "except", "finally")
                ):
                    indent_current = len(line) - len(line.lstrip())
                    indent_next = len(lines[i]) - len(lines[i].lstrip())
                    if indent_next >= indent_current:
                        violations.append(
                            EngineeringViolation(
                                arbiterx_name="NO_DEAD_CODE",
                                severity=Severity.ERROR,
                                description="Unreachable code after terminal statement",
                                line_hint=i + 1,
                                suggested_fix="Remove unreachable code or fix control flow logic.",
                            )
                        )

        return violations

    def _check_single_responsibility(
        self, lines: list[str], language: str
    ) -> list[EngineeringViolation]:
        """Flag functions exceeding max_function_lines threshold."""
        violations: list[EngineeringViolation] = []
        max_lines = self.config.max_function_lines

        func_start_pattern = re.compile(r"^(\s*)def\s+(\w+)\s*\(")
        func_starts: list[tuple[int, str, int]] = []  # (line_num, name, indent_level)

        for i, line in enumerate(lines, 1):
            match = func_start_pattern.match(line)
            if match:
                indent = len(match.group(1))
                func_starts.append((i, match.group(2), indent))

        for idx, (start_line, func_name, _indent) in enumerate(func_starts):
            # Find function end: next line at same or lesser indent (or next function)
            if idx + 1 < len(func_starts):
                end_line = func_starts[idx + 1][0] - 1
            else:
                end_line = len(lines)

            # Count non-empty, non-comment lines in the function body
            body_lines = 0
            for line in lines[start_line:end_line]:  # skip the def line itself
                stripped = line.strip()
                if (
                    stripped
                    and not stripped.startswith("#")
                    and not stripped.startswith('"""')
                    and not stripped.startswith("'''")
                ):
                    body_lines += 1

            if body_lines > max_lines:
                violations.append(
                    EngineeringViolation(
                        arbiterx_name="SINGLE_RESPONSIBILITY",
                        severity=Severity.WARNING,
                        description=f"Function '{func_name}' is {body_lines} lines (max: {max_lines}) — likely doing too much",
                        line_hint=start_line,
                        suggested_fix=f"Extract sub-logic into helper functions. Target ≤{max_lines} lines per function.",
                    )
                )

        return violations

    def _check_fail_fast(self, lines: list[str], language: str) -> list[EngineeringViolation]:
        """Check that input validation happens at function entry, not deep in logic."""
        violations: list[EngineeringViolation] = []

        func_pattern = re.compile(r"^(\s*)def\s+(\w+)\s*\(([^)]+)\)")
        validation_pattern = re.compile(
            r"(isinstance|assert |if\s+\w+\s+is\s+None|if\s+not\s+\w+|raise\s+(?:ValueError|TypeError))"
        )

        in_function = False
        func_name = ""
        func_indent = 0
        func_body_lines = 0
        found_validation_late = False

        for i, line in enumerate(lines, 1):
            match = func_pattern.match(line)
            if match:
                # Check previous function if applicable
                in_function = True
                func_indent = len(match.group(1))
                func_name = match.group(2)
                func_body_lines = 0
                found_validation_late = False
                continue

            if not in_function:
                continue

            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            current_indent = len(line) - len(line.lstrip())
            if current_indent <= func_indent and stripped and not stripped.startswith((")", "]")):
                in_function = False
                continue

            func_body_lines += 1

            # If validation appears after 10+ lines of body, it's late
            if func_body_lines > 10 and validation_pattern.search(line):
                if not found_validation_late:
                    found_validation_late = True
                    violations.append(
                        EngineeringViolation(
                            arbiterx_name="FAIL_FAST",
                            severity=Severity.INFO,
                            description=f"Late validation in '{func_name}' — validate inputs at function entry",
                            line_hint=i,
                            suggested_fix="Move input validation (isinstance, None checks, asserts) to the top of the function.",
                        )
                    )

        return violations

    def _check_idempotency(self, lines: list[str], language: str) -> list[EngineeringViolation]:
        """Flag side-effectful operations that may not be safe to retry."""
        violations: list[EngineeringViolation] = []

        # Patterns that suggest non-idempotent operations
        append_patterns = [
            (re.compile(r"\.\s*append\s*\(.*\bopen\b"), "Appending to file may duplicate on retry"),
            (
                re.compile(r"INSERT\s+INTO", re.IGNORECASE),
                "INSERT without ON CONFLICT may duplicate rows",
            ),
            (
                re.compile(r"\bcounter\s*\+=|\bcounter\s*=\s*counter\s*\+"),
                "Counter increment is not idempotent",
            ),
            (
                re.compile(r"\.send\s*\(|send_mail|send_email"),
                "Sending messages — not safe to retry without dedup",
            ),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, desc in append_patterns:
                if pattern.search(line):
                    violations.append(
                        EngineeringViolation(
                            arbiterx_name="IDEMPOTENCY",
                            severity=Severity.INFO,
                            description=desc,
                            line_hint=i,
                            suggested_fix="Add idempotency key, use upsert, or check-before-write pattern.",
                        )
                    )

        # File writes with mode 'a' (append) without truncation check
        append_write = re.compile(r"open\s*\([^)]*['\"]a['\"]")
        for i, line in enumerate(lines, 1):
            if append_write.search(line):
                violations.append(
                    EngineeringViolation(
                        arbiterx_name="IDEMPOTENCY",
                        severity=Severity.WARNING,
                        description="File opened in append mode — retries will duplicate content",
                        line_hint=i,
                        suggested_fix="Consider write mode with full content, or add deduplication logic.",
                    )
                )

        return violations

    def _check_performance(self, lines: list[str], language: str) -> list[EngineeringViolation]:
        """Flag O(n²) patterns when O(n) alternatives likely exist."""
        violations: list[EngineeringViolation] = []

        # Detect nested loops (simple heuristic: for/while inside for/while)
        loop_pattern = re.compile(r"^\s*(for |while )")
        loop_stack: list[int] = []

        for i, line in enumerate(lines, 1):
            if loop_pattern.match(line):
                indent = len(line) - len(line.lstrip())
                # Pop loops that are at same or lesser indent
                while loop_stack and loop_stack[-1] >= indent:
                    loop_stack.pop()
                if loop_stack:
                    violations.append(
                        EngineeringViolation(
                            arbiterx_name="PERFORMANCE",
                            severity=Severity.WARNING,
                            description="Nested loop detected — potential O(n²) complexity",
                            line_hint=i,
                            suggested_fix="Consider using a set/dict for O(1) lookups, or restructure to single pass.",
                        )
                    )
                loop_stack.append(indent)
            else:
                # Pop loops we've exited based on indent
                current_indent = len(line) - len(line.lstrip()) if line.strip() else 999
                while loop_stack and loop_stack[-1] >= current_indent and line.strip():
                    loop_stack.pop()

        # Detect `in list` membership checks inside loops (should be a set)
        in_list_pattern = re.compile(r"if\s+.+\s+in\s+(\w+)")
        list_assignments = re.compile(r"(\w+)\s*=\s*\[")
        list_vars: set[str] = set()

        for line in lines:
            lm = list_assignments.search(line)
            if lm:
                list_vars.add(lm.group(1))

        in_loop = False
        for i, line in enumerate(lines, 1):
            if loop_pattern.match(line):
                in_loop = True
            elif line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                in_loop = False

            if in_loop:
                match = in_list_pattern.search(line)
                if match and match.group(1) in list_vars:
                    violations.append(
                        EngineeringViolation(
                            arbiterx_name="PERFORMANCE",
                            severity=Severity.WARNING,
                            description=f"Membership test on list '{match.group(1)}' inside loop — O(n²) total",
                            line_hint=i,
                            suggested_fix=f"Convert '{match.group(1)}' to a set for O(1) membership checks.",
                        )
                    )

        # String concatenation in loops
        concat_pattern = re.compile(r"(\w+)\s*\+=\s*['\"]|(\w+)\s*=\s*\2\s*\+\s*['\"]")
        in_loop = False
        for i, line in enumerate(lines, 1):
            if loop_pattern.match(line):
                in_loop = True
            elif line.strip() and len(line) - len(line.lstrip()) == 0:
                in_loop = False
            if in_loop and concat_pattern.search(line):
                violations.append(
                    EngineeringViolation(
                        arbiterx_name="PERFORMANCE",
                        severity=Severity.WARNING,
                        description="String concatenation in loop — O(n²) memory reallocation",
                        line_hint=i,
                        suggested_fix="Collect parts in a list and use ''.join() after the loop.",
                    )
                )

        return violations
