"""Task classifier using keyword heuristics and regex patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class TaskType(Enum):
    """Categorizes the kind of work a task represents."""

    CODE_GENERATION = auto()
    CODE_REVIEW = auto()
    DEBUGGING = auto()
    REFACTORING = auto()
    EXPLANATION = auto()
    DOCUMENTATION = auto()
    TESTING = auto()
    ARCHITECTURE = auto()
    CONFIGURATION = auto()
    CONVERSATION = auto()
    RESEARCH = auto()
    TRANSLATION = auto()
    UNKNOWN = auto()


class Complexity(Enum):
    """Estimated cognitive complexity of a task."""

    TRIVIAL = auto()   # One-liner, simple lookup
    LOW = auto()       # Single function, straightforward
    MEDIUM = auto()    # Multi-function, moderate reasoning
    HIGH = auto()      # Multi-file, significant reasoning
    EXPERT = auto()    # Architectural, cross-system


class ContextScope(Enum):
    """How much codebase context is needed."""

    FILE = auto()      # Single file is sufficient
    MODULE = auto()    # Need surrounding module/package
    REPO = auto()      # Need broad repository context


class Latency(Enum):
    """Expected latency tolerance."""

    INTERACTIVE = auto()  # User waiting, sub-5s ideal
    BATCH = auto()        # Async acceptable, quality over speed


@dataclass(frozen=True)
class ClassifiedTask:
    """Result of classifying a task string."""

    task_type: TaskType
    complexity: Complexity
    context_scope: ContextScope
    latency: Latency
    estimated_tokens: int
    confidence: float  # 0.0 to 1.0


# --- Heuristic pattern tables ---

_TYPE_PATTERNS: list[tuple[re.Pattern, TaskType]] = [
    (re.compile(r"\b(write|create|generate|implement|build|add)\b.*\b(function|class|method|module|api|endpoint|component|system|feature|service|handler|page|route|view)", re.I), TaskType.CODE_GENERATION),
    (re.compile(r"\b(write|create|generate|implement|build|add)\b.*\b(a|an|the|new)\b", re.I), TaskType.CODE_GENERATION),
    (re.compile(r"\b(review|critique|check|audit)\b.*\b(code|pr|pull request|diff|changes)", re.I), TaskType.CODE_REVIEW),
    (re.compile(r"\b(debug|fix|error|bug|issue|broken|crash|traceback|exception)\b", re.I), TaskType.DEBUGGING),
    (re.compile(r"\b(refactor|restructure|clean\s*up|simplify|extract|rename|move)\b", re.I), TaskType.REFACTORING),
    (re.compile(r"\b(explain|what\s+(is|does|are)|how\s+(does|do|is)|why\s+(does|is|do)|describe|clarify|walk\s+(me\s+)?through|tell\s+me\s+about)\b", re.I), TaskType.EXPLANATION),
    (re.compile(r"\b(document|docstring|readme|jsdoc|comment|annotate)\b", re.I), TaskType.DOCUMENTATION),
    (re.compile(r"\b(tests?|spec|unittest|pytest|jest|coverage|assert|mock)\b", re.I), TaskType.TESTING),
    (re.compile(r"\b(architect|design|system\s*design|scalab|microservice|schema|database\s*design|infrastructure)\b", re.I), TaskType.ARCHITECTURE),
    (re.compile(r"\b(config|configure|setup|install|deploy|ci|cd|docker|yaml|toml|env)\b", re.I), TaskType.CONFIGURATION),
    (re.compile(r"\b(research|compare|evaluate|survey|benchmark|pros\s*and\s*cons|alternatives)\b", re.I), TaskType.RESEARCH),
    (re.compile(r"\b(translate|convert|port|migrate)\b.*\b(to|from|into)\b", re.I), TaskType.TRANSLATION),
]

_COMPLEXITY_SIGNALS: dict[Complexity, list[re.Pattern]] = {
    Complexity.TRIVIAL: [
        re.compile(r"\b(one.?liner|simple|quick|trivial|just|only)\b", re.I),
        re.compile(r"\b(rename|typo|import|constant)\b", re.I),
    ],
    Complexity.LOW: [
        re.compile(r"\b(single\s*function|small|minor|basic|straightforward)\b", re.I),
    ],
    Complexity.MEDIUM: [
        re.compile(r"\b(multiple|several|moderate|feature|endpoint|handler)\b", re.I),
    ],
    Complexity.HIGH: [
        re.compile(r"\b(complex|multi.?file|significant|large|rewrite|overhaul)\b", re.I),
        re.compile(r"\b(across|entire|whole)\s+(codebase|project|repo)", re.I),
    ],
    Complexity.EXPERT: [
        re.compile(r"\b(architect|system\s*design|distributed|scalab|migration\s*strategy)\b", re.I),
        re.compile(r"\b(security\s*audit|performance\s*optimization|consensus|protocol)\b", re.I),
    ],
}

_SCOPE_PATTERNS: list[tuple[re.Pattern, ContextScope]] = [
    (re.compile(r"\b(repo|project|codebase|entire|all\s*files|cross.?module)\b", re.I), ContextScope.REPO),
    (re.compile(r"\b(module|package|directory|folder|namespace)\b", re.I), ContextScope.MODULE),
    (re.compile(r"\b(file|function|class|method|line|snippet)\b", re.I), ContextScope.FILE),
]

# Plugin extension point: custom classifier functions
_CUSTOM_CLASSIFIERS: dict[str, Any] = {}

class TaskClassifier:
    """Analyzes a task string and produces a structured classification.

    Uses keyword heuristics and regex pattern matching to infer task type,
    complexity, scope, latency requirements, and estimated token usage.

    Example:
        >>> classifier = TaskClassifier()
        >>> result = classifier.classify("Fix the null pointer bug in auth.py")
        >>> result.task_type
        TaskType.DEBUGGING
    """

    def __init__(self, token_multiplier: float = 1.5) -> None:
        """Initialize the classifier.

        Args:
            token_multiplier: Multiplier applied to word count for token estimation.
        """
        self._token_multiplier = token_multiplier

    def classify(self, task: str) -> ClassifiedTask:
        """Classify a task string into structured metadata.

        Args:
            task: Natural language description of the task.

        Returns:
            A ClassifiedTask with all inferred fields.
        """
        task_type = self._infer_type(task)
        complexity = self._infer_complexity(task, task_type)
        context_scope = self._infer_scope(task, complexity)
        latency = self._infer_latency(complexity, task_type)
        estimated_tokens = self._estimate_tokens(task, complexity, task_type)
        confidence = self._compute_confidence(task, task_type, complexity)

        return ClassifiedTask(
            task_type=task_type,
            complexity=complexity,
            context_scope=context_scope,
            latency=latency,
            estimated_tokens=estimated_tokens,
            confidence=confidence,
        )

    def _infer_type(self, task: str) -> TaskType:
        """Match task against type patterns, return best match."""
        matches: list[tuple[TaskType, int]] = []
        for pattern, task_type in _TYPE_PATTERNS:
            match = pattern.search(task)
            if match:
                # Score by match span length (more specific = better)
                matches.append((task_type, match.end() - match.start()))

        if not matches:
            # Fallback: short inputs are likely conversation
            if len(task.split()) <= 5:
                return TaskType.CONVERSATION
            return TaskType.UNKNOWN

        # Return the match with longest span
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0]

    def _infer_complexity(self, task: str, task_type: TaskType) -> Complexity:
        """Infer complexity from explicit signals and type-based defaults."""
        scores: dict[Complexity, int] = {c: 0 for c in Complexity}

        for complexity, patterns in _COMPLEXITY_SIGNALS.items():
            for pattern in patterns:
                if pattern.search(task):
                    scores[complexity] += 1

        # If explicit signals found, use highest scoring
        max_score = max(scores.values())
        if max_score > 0:
            for complexity in [Complexity.EXPERT, Complexity.HIGH, Complexity.MEDIUM, Complexity.LOW, Complexity.TRIVIAL]:
                if scores[complexity] == max_score:
                    return complexity

        # Type-based defaults when no explicit signals
        type_defaults: dict[TaskType, Complexity] = {
            TaskType.CODE_GENERATION: Complexity.MEDIUM,
            TaskType.CODE_REVIEW: Complexity.MEDIUM,
            TaskType.DEBUGGING: Complexity.MEDIUM,
            TaskType.REFACTORING: Complexity.MEDIUM,
            TaskType.EXPLANATION: Complexity.LOW,
            TaskType.DOCUMENTATION: Complexity.LOW,
            TaskType.TESTING: Complexity.MEDIUM,
            TaskType.ARCHITECTURE: Complexity.HIGH,
            TaskType.CONFIGURATION: Complexity.LOW,
            TaskType.CONVERSATION: Complexity.TRIVIAL,
            TaskType.RESEARCH: Complexity.MEDIUM,
            TaskType.TRANSLATION: Complexity.MEDIUM,
            TaskType.UNKNOWN: Complexity.MEDIUM,
        }
        return type_defaults.get(task_type, Complexity.MEDIUM)

    def _infer_scope(self, task: str, complexity: Complexity) -> ContextScope:
        """Infer context scope from patterns and complexity."""
        for pattern, scope in _SCOPE_PATTERNS:
            if pattern.search(task):
                return scope

        # Complexity-based fallback
        scope_map: dict[Complexity, ContextScope] = {
            Complexity.TRIVIAL: ContextScope.FILE,
            Complexity.LOW: ContextScope.FILE,
            Complexity.MEDIUM: ContextScope.MODULE,
            Complexity.HIGH: ContextScope.REPO,
            Complexity.EXPERT: ContextScope.REPO,
        }
        return scope_map[complexity]

    def _infer_latency(self, complexity: Complexity, task_type: TaskType) -> Latency:
        """Determine latency tolerance based on complexity and type."""
        # Trivial/low complexity tasks and explanations should be interactive
        if complexity in (Complexity.TRIVIAL, Complexity.LOW):
            return Latency.INTERACTIVE

        # Conversations and explanations are always interactive
        if task_type in (TaskType.CONVERSATION, TaskType.EXPLANATION):
            return Latency.INTERACTIVE

        # High/expert tasks can tolerate batch latency
        if complexity in (Complexity.HIGH, Complexity.EXPERT):
            return Latency.BATCH

        return Latency.INTERACTIVE

    def _estimate_tokens(self, task: str, complexity: Complexity, task_type: TaskType) -> int:
        """Estimate output tokens based on task characteristics.

        This estimates the expected *response* size, not prompt size.
        """
        # Base estimate from task description length
        word_count = len(task.split())
        base = int(word_count * self._token_multiplier)

        # Complexity multipliers for expected output
        complexity_multipliers: dict[Complexity, int] = {
            Complexity.TRIVIAL: 50,
            Complexity.LOW: 200,
            Complexity.MEDIUM: 800,
            Complexity.HIGH: 2000,
            Complexity.EXPERT: 4000,
        }

        # Type adjustments (code gen produces more tokens than explanation)
        type_multipliers: dict[TaskType, float] = {
            TaskType.CODE_GENERATION: 1.5,
            TaskType.CODE_REVIEW: 1.0,
            TaskType.DEBUGGING: 1.2,
            TaskType.REFACTORING: 1.4,
            TaskType.EXPLANATION: 0.8,
            TaskType.DOCUMENTATION: 1.2,
            TaskType.TESTING: 1.4,
            TaskType.ARCHITECTURE: 1.3,
            TaskType.CONFIGURATION: 0.8,
            TaskType.CONVERSATION: 0.5,
            TaskType.RESEARCH: 1.1,
            TaskType.TRANSLATION: 1.3,
            TaskType.UNKNOWN: 1.0,
        }

        estimated = complexity_multipliers[complexity] * type_multipliers.get(task_type, 1.0)
        return max(int(estimated), base + 50)

    def _compute_confidence(self, task: str, task_type: TaskType, complexity: Complexity) -> float:
        """Compute classification confidence (0.0 to 1.0)."""
        confidence = 0.5

        # Boost if type matched explicitly
        if task_type != TaskType.UNKNOWN:
            confidence += 0.2

        # Boost if complexity matched explicitly
        for patterns in _COMPLEXITY_SIGNALS.values():
            for p in patterns:
                if p.search(task):
                    confidence += 0.1
                    break
            if confidence >= 1.0:
                break

        # Penalize very short inputs
        if len(task.split()) < 3:
            confidence -= 0.2

        return max(0.1, min(1.0, confidence))
