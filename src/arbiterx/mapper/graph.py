"""Symbol graph construction and PageRank-based ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx

from arbiterx.mapper.parser import Edge, Symbol


@dataclass
class RankedSymbol:
    """A symbol with its computed rank score and metadata."""

    name: str
    qualified_name: str
    kind: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    score: float
    token_estimate: int = 0

    @property
    def display(self) -> str:
        """Human-readable display string."""
        return f"{self.qualified_name} ({self.kind}) @ {self.file_path}:{self.line_start}"


class SymbolGraph:
    """Directed graph of symbol relationships with PageRank ranking.

    Uses NetworkX for graph operations and PageRank computation to determine
    the most important symbols for context inclusion.
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._symbol_map: dict[str, Symbol] = {}

    @property
    def graph(self) -> nx.DiGraph:
        """Access the underlying NetworkX directed graph."""
        return self._graph

    def build_graph(
        self,
        files: list[dict[str, Any]],
        symbols: list[Symbol],
        edges: list[Edge],
    ) -> None:
        """Build the symbol graph from indexed data.

        Args:
            files: List of file records.
            symbols: All extracted symbols.
            edges: All reference edges between symbols.
        """
        self._graph.clear()
        self._symbol_map.clear()

        for sym in symbols:
            qn = sym.qualified_name
            self._symbol_map[qn] = sym
            self._graph.add_node(
                qn,
                kind=sym.kind,
                file_path=sym.file_path,
                line_start=sym.line_start,
                line_end=sym.line_end,
                signature=sym.signature,
            )

        for edge in edges:
            if edge.source in self._symbol_map and edge.target in self._symbol_map:
                self._graph.add_edge(
                    edge.source,
                    edge.target,
                    kind=edge.kind,
                    file_path=edge.file_path,
                    line=edge.line,
                )

    def compute_pagerank(self, personalization: dict[str, float] | None = None) -> dict[str, float]:
        """Compute PageRank scores for all symbols in the graph.

        Args:
            personalization: Optional bias weights toward specific nodes.

        Returns:
            Dict mapping qualified symbol names to PageRank scores.
        """
        if len(self._graph) == 0:
            return {}

        try:
            scores: dict[str, float] = nx.pagerank(
                self._graph,
                alpha=0.85,
                personalization=personalization,
                max_iter=100,
                tol=1.0e-6,
            )
        except nx.PowerIterationFailedConvergence:
            n = len(self._graph)
            scores = {node: 1.0 / n for node in self._graph.nodes()}

        return scores

    def get_ranked_symbols(
        self,
        token_budget: int,
        chat_files: list[str] | None = None,
    ) -> list[RankedSymbol]:
        """Get top-ranked symbols that fit within a token budget.

        Args:
            token_budget: Maximum number of tokens to allocate.
            chat_files: File paths relevant to the chat, used to bias ranking.

        Returns:
            List of RankedSymbol sorted by descending score within budget.
        """
        personalization: dict[str, float] | None = None
        if chat_files:
            personalization = {
                node: (1.0 if data.get("file_path") in chat_files else 0.0)
                for node, data in self._graph.nodes(data=True)
            }
            if not any(v > 0 for v in personalization.values()):
                personalization = None

        scores = self.compute_pagerank(personalization)
        ranked_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        result: list[RankedSymbol] = []
        tokens_used = 0

        for qname, score in ranked_items:
            sym = self._symbol_map.get(qname)
            if sym is None:
                continue

            token_estimate = max(
                len(sym.signature) // 4,
                (sym.line_end - sym.line_start + 1) * 10,
            )

            if tokens_used + token_estimate > token_budget:
                continue

            result.append(
                RankedSymbol(
                    name=sym.name,
                    qualified_name=qname,
                    kind=sym.kind,
                    file_path=sym.file_path,
                    line_start=sym.line_start,
                    line_end=sym.line_end,
                    signature=sym.signature,
                    score=score,
                    token_estimate=token_estimate,
                )
            )
            tokens_used += token_estimate

        return result
