"""Routing table that maps classified tasks to model names via configurable rules."""

from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]
from dataclasses import dataclass, field
from pathlib import Path

from arbiterx.router.classifier import ClassifiedTask, Complexity, ContextScope, Latency, TaskType


@dataclass
class RoutingRule:
    """A single routing rule loaded from configuration."""

    name: str
    model: str
    fallback: list[str] = field(default_factory=list)

    # Match conditions (None = match any)
    task_types: list[TaskType] | None = None
    min_complexity: Complexity | None = None
    max_complexity: Complexity | None = None
    context_scopes: list[ContextScope] | None = None
    latency: Latency | None = None
    max_tokens: int | None = None

    def matches(self, task: ClassifiedTask) -> bool:
        """Check if this rule matches the given classified task."""
        if self.task_types and task.task_type not in self.task_types:
            return False

        if self.min_complexity is not None:
            if task.complexity.value < self.min_complexity.value:
                return False

        if self.max_complexity is not None:
            if task.complexity.value > self.max_complexity.value:
                return False

        if self.context_scopes and task.context_scope not in self.context_scopes:
            return False

        if self.latency is not None and task.latency != self.latency:
            return False

        if self.max_tokens is not None and task.estimated_tokens > self.max_tokens:
            return False

        return True


@dataclass
class RoutingResult:
    """The result of routing: a primary model plus fallback chain."""

    model: str
    fallbacks: list[str]
    rule_name: str
    confidence: float


# Plugin extension point: custom routing rules added at runtime
_CUSTOM_RULES: list[dict] = []


class RoutingTable:
    """Loads routing rules from arbiterx.toml and matches tasks to models.

    The TOML config is expected to have a `[routing]` section with an array
    of `[[routing.rules]]` entries. Each rule specifies match conditions and
    a target model with optional fallbacks.

    Example arbiterx.toml:
        [routing]
        default_model = "claude-sonnet-4-20250514"

        [[routing.rules]]
        name = "trivial_fast"
        model = "claude-haiku"
        fallback = ["gpt-4o-mini"]
        max_complexity = "LOW"
        latency = "INTERACTIVE"

        [[routing.rules]]
        name = "expert_tasks"
        model = "claude-opus"
        fallback = ["gpt-4o", "claude-sonnet-4-20250514"]
        min_complexity = "EXPERT"
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the routing table.

        Args:
            config_path: Path to arbiterx.toml. If None, searches common
                locations (cwd, ~/.config/arbiterx/, etc.).
        """
        self._rules: list[RoutingRule] = []
        self._default_model: str = "claude-sonnet-4-20250514"
        self._default_fallbacks: list[str] = ["gpt-4o", "claude-haiku"]

        if config_path is None:
            config_path = self._find_config()

        if config_path and config_path.exists():
            self._load(config_path)

    def _find_config(self) -> Path | None:
        """Search common locations for arbiterx.toml."""
        candidates = [
            Path.cwd() / "arbiterx.toml",
            Path.home() / ".config" / "arbiterx" / "arbiterx.toml",
            Path("/etc/arbiterx/arbiterx.toml"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _load(self, path: Path) -> None:
        """Parse TOML config and populate routing rules."""
        if tomllib is None:
            raise ImportError(
                "TOML parsing requires Python 3.11+ or the 'tomli' package. "
                "Install it with: pip install tomli"
            )
        with open(path, "rb") as f:
            data = tomllib.load(f)

        routing = data.get("routing", {})
        self._default_model = routing.get("default_model", self._default_model)
        self._default_fallbacks = routing.get("default_fallbacks", self._default_fallbacks)

        for rule_data in routing.get("rules", []):
            rule = self._parse_rule(rule_data)
            self._rules.append(rule)

    def _parse_rule(self, data: dict) -> RoutingRule:
        """Parse a single rule dictionary into a RoutingRule."""
        task_types = None
        if "task_types" in data:
            task_types = [TaskType[t.upper()] for t in data["task_types"]]

        min_complexity = None
        if "min_complexity" in data:
            min_complexity = Complexity[data["min_complexity"].upper()]

        max_complexity = None
        if "max_complexity" in data:
            max_complexity = Complexity[data["max_complexity"].upper()]

        context_scopes = None
        if "context_scopes" in data:
            context_scopes = [ContextScope[s.upper()] for s in data["context_scopes"]]

        latency = None
        if "latency" in data:
            latency = Latency[data["latency"].upper()]

        return RoutingRule(
            name=data.get("name", "unnamed"),
            model=data["model"],
            fallback=data.get("fallback", []),
            task_types=task_types,
            min_complexity=min_complexity,
            max_complexity=max_complexity,
            context_scopes=context_scopes,
            latency=latency,
            max_tokens=data.get("max_tokens"),
        )

    def route(self, task: ClassifiedTask) -> RoutingResult:
        """Match a classified task to a model using the rule table.

        Rules are evaluated in order; the first match wins.
        If no rule matches, the default model is returned.

        Args:
            task: A ClassifiedTask produced by TaskClassifier.

        Returns:
            RoutingResult with model name, fallback chain, and metadata.
        """
        for rule in self._rules:
            if rule.matches(task):
                return RoutingResult(
                    model=rule.model,
                    fallbacks=rule.fallback,
                    rule_name=rule.name,
                    confidence=task.confidence,
                )

        return RoutingResult(
            model=self._default_model,
            fallbacks=self._default_fallbacks,
            rule_name="default",
            confidence=task.confidence,
        )

    @property
    def rules(self) -> list[RoutingRule]:
        """Return loaded routing rules (read-only view)."""
        return list(self._rules)

    @property
    def default_model(self) -> str:
        """Return the default model name."""
        return self._default_model
