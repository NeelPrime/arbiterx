"""Orchestrator for indexing a repository into the codebase map."""

from __future__ import annotations

from pathlib import Path

from arbiterx.mapper.hasher import FileHasher
from arbiterx.mapper.languages import detect_language
from arbiterx.mapper.parser import TreeSitterParser
from arbiterx.mapper.store import MapStore


class Indexer:
    """Orchestrates parsing, hashing, and storage for a codebase map.

    Coordinates between TreeSitterParser, FileHasher, and MapStore to
    build and incrementally update the symbol database.
    """

    def __init__(self, store: MapStore) -> None:
        """Initialize the Indexer.

        Args:
            store: The MapStore instance for database operations.
        """
        self.store = store
        self.parser = TreeSitterParser()
        self.hasher = FileHasher()

    def index_repo(self, root_path: Path) -> dict[str, int]:
        """Index an entire repository from scratch.

        Scans all supported source files, parses symbols and references,
        and stores them in the map database.

        Args:
            root_path: Root directory of the repository.

        Returns:
            Dict with counts: {"files": N, "symbols": M, "edges": E}
        """
        self.store.init_db()

        # Collect all supported source files
        source_files: list[Path] = []
        for file_path in sorted(root_path.rglob("*")):
            if file_path.is_file() and detect_language(file_path) is not None:
                if not self.hasher._should_skip(file_path):
                    source_files.append(file_path)

        total_symbols = 0
        total_edges = 0

        for file_path in source_files:
            try:
                relative = str(file_path.relative_to(root_path))
                file_hash = self.hasher.hash_file(file_path)
                language = detect_language(file_path)
                if language is None:
                    continue

                file_id = self.store.upsert_file(relative, file_hash, language)

                symbols = self.parser.parse_file(file_path)
                self.store.upsert_symbols(file_id, symbols)
                total_symbols += len(symbols)

                edges = self.parser.parse_references(file_path)
                self.store.clear_edges_for_file(relative)
                self.store.upsert_edges(edges)
                total_edges += len(edges)
            except OSError:
                # File was deleted, moved, or became unreadable during indexing — skip
                continue

        return {"files": len(source_files), "symbols": total_symbols, "edges": total_edges}

    def incremental_update(self, changed_files: list[str]) -> dict[str, int]:
        """Re-index only the files that have changed.

        Args:
            changed_files: List of relative file paths that were modified.

        Returns:
            Dict with counts of re-indexed items.
        """
        total_symbols = 0
        total_edges = 0

        for relative in changed_files:
            file_path = Path(relative)
            if not file_path.exists():
                # File was deleted — handled by store cascade
                continue

            try:
                language = detect_language(file_path)
                if language is None:
                    continue

                file_hash = self.hasher.hash_file(file_path)
                file_id = self.store.upsert_file(relative, file_hash, language)

                symbols = self.parser.parse_file(file_path)
                self.store.upsert_symbols(file_id, symbols)
                total_symbols += len(symbols)

                edges = self.parser.parse_references(file_path)
                self.store.clear_edges_for_file(relative)
                self.store.upsert_edges(edges)
                total_edges += len(edges)
            except OSError:
                # File became unreadable during indexing — skip
                continue

        return {"files": len(changed_files), "symbols": total_symbols, "edges": total_edges}

    def full_reindex(self) -> dict[str, int]:
        """Drop all data and re-index from scratch.

        Returns:
            Dict with counts from the fresh index pass.
        """
        self.store.conn.executescript("DELETE FROM edges; DELETE FROM symbols; DELETE FROM files;")
        self.store.conn.commit()

        raise NotImplementedError("full_reindex requires the root_path to be stored or passed.")
