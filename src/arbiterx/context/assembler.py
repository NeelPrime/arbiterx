"""Context assembler that queries the codebase map and respects token budgets."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol


class CodebaseMap(Protocol):
    """Protocol for a codebase map that can be queried for relevant context."""

    def query(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Query the map for relevant code snippets."""
        ...

    def get_file_summary(self, path: str) -> Optional[str]:
        """Get a summary of a file's contents."""
        ...


@dataclass
class ContextChunk:
    """A single chunk of context to include in the prompt."""

    source: str
    content: str
    relevance_score: float
    token_count: int
    chunk_type: str = "code"


@dataclass
class AssembledContext:
    """The result of context assembly."""

    chunks: list[ContextChunk] = field(default_factory=list)
    total_tokens: int = 0
    budget_remaining: int = 0
    sources_consulted: int = 0
    sources_included: int = 0

    @property
    def text(self) -> str:
        """Render all chunks into a single context string."""
        parts: list[str] = []
        for chunk in self.chunks:
            header = f"# {chunk.source} ({chunk.chunk_type})"
            parts.append(f"{header}\n{chunk.content}")
        return "\n\n---\n\n".join(parts)


class ContextAssembler:
    """Queries the codebase map and assembles minimal relevant context.

    Given a task description and token budget, the assembler:
    1. Queries the codebase map for relevant files/symbols
    2. Ranks results by relevance
    3. Greedily packs context within the token budget
    4. Returns the assembled context ready for prompt insertion
    """

    def __init__(
        self,
        token_budget: int = 8000,
        min_relevance: float = 0.3,
        chars_per_token: int = 4,
    ) -> None:
        self.token_budget = token_budget
        self.min_relevance = min_relevance
        self.chars_per_token = chars_per_token

    def assemble(
        self,
        query: str,
        codebase_map: Optional[CodebaseMap] = None,
        file_paths: Optional[list[str]] = None,
        top_k: int = 20,
    ) -> AssembledContext:
        """Assemble context for a given query within the token budget."""
        candidates: list[ContextChunk] = []

        if codebase_map is not None:
            results = codebase_map.query(query, top_k=top_k)
            for result in results:
                chunk = self._result_to_chunk(result)
                if chunk.relevance_score >= self.min_relevance:
                    candidates.append(chunk)

        if file_paths:
            for path in file_paths:
                chunk = self._load_file_chunk(path)
                if chunk is not None:
                    candidates.append(chunk)

        candidates.sort(key=lambda c: c.relevance_score, reverse=True)

        assembled = AssembledContext(
            sources_consulted=len(candidates),
            budget_remaining=self.token_budget,
        )

        for chunk in candidates:
            if chunk.token_count <= assembled.budget_remaining:
                assembled.chunks.append(chunk)
                assembled.total_tokens += chunk.token_count
                assembled.budget_remaining -= chunk.token_count
                assembled.sources_included += 1

        return assembled

    def _result_to_chunk(self, result: dict[str, Any]) -> ContextChunk:
        """Convert a map query result to a ContextChunk."""
        content = result.get("content", "")
        token_count = self._estimate_tokens(content)
        return ContextChunk(
            source=result.get("path", result.get("source", "unknown")),
            content=content,
            relevance_score=result.get("score", result.get("relevance", 0.5)),
            token_count=token_count,
            chunk_type=result.get("type", "code"),
        )

    def _load_file_chunk(self, path: str) -> Optional[ContextChunk]:
        """Load a file from disk as a context chunk."""
        file_path = Path(path)
        if not file_path.exists() or not file_path.is_file():
            return None
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        token_count = self._estimate_tokens(content)
        return ContextChunk(
            source=path,
            content=content,
            relevance_score=1.0,
            token_count=token_count,
            chunk_type="code",
        )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length."""
        return max(1, len(text) // self.chars_per_token)
