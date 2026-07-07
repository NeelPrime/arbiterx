"""Orchestrator for indexing a repository into the codebase map."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from arbiterx.mapper.hasher import FileHasher
from arbiterx.mapper.languages import detect_language
from arbiterx.mapper.parser import Edge, Symbol, TreeSitterParser
from arbiterx.mapper.store import MapStore


@dataclass
class IndexResult:
    """Result of an indexing operation."""

    files_total: int
    files_indexed: int
    files_skipped: int
    symbols: int
    edges: int


def _parse_file_worker(file_path_str: str) -> dict[str, Any]:
    """Worker function for parallel parsing. Runs in a separate process.

    Returns a dict with symbols and edges for a single file.
    """
    file_path = Path(file_path_str)
    parser = TreeSitterParser()

    try:
        symbols = parser.parse_file(file_path)
        edges = parser.parse_references(file_path)
    except OSError:
        return {"symbols": [], "edges": [], "error": True}

    # Serialize symbols and edges to dicts for cross-process transfer
    return {
        "symbols": [
            {
                "name": s.name,
                "kind": s.kind,
                "file_path": s.file_path,
                "line_start": s.line_start,
                "line_end": s.line_end,
                "signature": s.signature,
                "docstring": s.docstring,
                "parent": s.parent,
                "qualified_name": s.qualified_name,
            }
            for s in symbols
        ],
        "edges": [
            {
                "source": e.source,
                "target": e.target,
                "kind": e.kind,
                "file_path": e.file_path,
                "line": e.line,
            }
            for e in edges
        ],
        "error": False,
    }


class Indexer:
    """Orchestrates parsing, hashing, and storage for a codebase map.

    Supports incremental indexing (skip unchanged files) and parallel
    parsing across multiple CPU cores for large monorepos.
    """

    # Minimum files to trigger parallel processing (overhead not worth it below this)
    PARALLEL_THRESHOLD = 100

    def __init__(self, store: MapStore) -> None:
        """Initialize the Indexer.

        Args:
            store: The MapStore instance for database operations.
        """
        self.store = store
        self.parser = TreeSitterParser()
        self.hasher = FileHasher()

    def index_repo(
        self,
        root_path: Path,
        workers: int = 1,
        force: bool = False,
    ) -> IndexResult:
        """Index a repository with incremental and optional parallel support.

        Skips files that haven't changed since last index (hash-based).
        Optionally uses multiple processes for parsing large repos.

        Args:
            root_path: Root directory of the repository.
            workers: Number of parallel workers (1 = single-threaded).
                     Use 0 for auto-detect (cpu_count).
            force: If True, re-index all files regardless of hash.

        Returns:
            IndexResult with detailed counts.
        """
        self.store.init_db()

        # Resolve worker count
        if workers == 0:
            workers = os.cpu_count() or 4
        if workers < 1:
            workers = 1

        # Scan all supported source files
        source_files: list[Path] = []
        for file_path in sorted(root_path.rglob("*")):
            if file_path.is_file() and detect_language(file_path) is not None:
                if not self.hasher._should_skip(file_path):
                    source_files.append(file_path)

        # Determine which files need re-indexing (incremental)
        files_to_index: list[tuple[Path, str, str]] = []  # (path, relative, hash)
        files_skipped = 0

        for file_path in source_files:
            try:
                relative = str(file_path.relative_to(root_path))
                file_hash = self.hasher.hash_file(file_path)

                if not force:
                    existing_hash = self.store.get_file_hash(relative)
                    if existing_hash == file_hash:
                        files_skipped += 1
                        continue

                language = detect_language(file_path)
                if language is None:
                    continue

                files_to_index.append((file_path, relative, file_hash))
            except OSError:
                continue

        # Remove files from DB that no longer exist on disk
        self._remove_deleted_files(root_path, source_files)

        # Nothing to index
        if not files_to_index:
            return IndexResult(
                files_total=len(source_files),
                files_indexed=0,
                files_skipped=files_skipped,
                symbols=0,
                edges=0,
            )

        # Choose indexing strategy
        use_parallel = workers > 1 and len(files_to_index) >= self.PARALLEL_THRESHOLD

        if use_parallel:
            total_symbols, total_edges = self._index_parallel(files_to_index, root_path, workers)
        else:
            total_symbols, total_edges = self._index_sequential(files_to_index, root_path)

        return IndexResult(
            files_total=len(source_files),
            files_indexed=len(files_to_index),
            files_skipped=files_skipped,
            symbols=total_symbols,
            edges=total_edges,
        )

    def _index_sequential(
        self,
        files_to_index: list[tuple[Path, str, str]],
        root_path: Path,
    ) -> tuple[int, int]:
        """Index files one by one (single-threaded)."""
        total_symbols = 0
        total_edges = 0

        for file_path, relative, file_hash in files_to_index:
            try:
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
                continue

        return total_symbols, total_edges

    def _index_parallel(
        self,
        files_to_index: list[tuple[Path, str, str]],
        root_path: Path,
        workers: int,
    ) -> tuple[int, int]:
        """Index files using multiple processes for parsing."""
        total_symbols = 0
        total_edges = 0

        # Submit parsing work to process pool
        file_map: dict[str, tuple[str, str]] = {}  # path_str -> (relative, hash)
        for file_path, relative, file_hash in files_to_index:
            file_map[str(file_path)] = (relative, file_hash)

        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(_parse_file_worker, str(fp)): str(fp) for fp, _, _ in files_to_index
            }

            for future in as_completed(futures):
                file_path_str = futures[future]
                relative, file_hash = file_map[file_path_str]

                try:
                    result = future.result()
                except Exception:
                    continue

                if result["error"]:
                    continue

                language = detect_language(Path(file_path_str))
                if language is None:
                    continue

                # Write to DB (single writer — sequential)
                file_id = self.store.upsert_file(relative, file_hash, language)

                # Reconstruct Symbol objects
                symbols = [
                    Symbol(
                        name=s["name"],
                        kind=s["kind"],
                        file_path=s["file_path"],
                        line_start=s["line_start"],
                        line_end=s["line_end"],
                        signature=s["signature"],
                        docstring=s["docstring"],
                        parent=s["parent"],
                        qualified_name=s["qualified_name"],
                    )
                    for s in result["symbols"]
                ]
                self.store.upsert_symbols(file_id, symbols)
                total_symbols += len(symbols)

                # Reconstruct Edge objects
                edges = [
                    Edge(
                        source=e["source"],
                        target=e["target"],
                        kind=e["kind"],
                        file_path=e["file_path"],
                        line=e["line"],
                    )
                    for e in result["edges"]
                ]
                self.store.clear_edges_for_file(relative)
                self.store.upsert_edges(edges)
                total_edges += len(edges)

        return total_symbols, total_edges

    def _remove_deleted_files(self, root_path: Path, current_files: list[Path]) -> None:
        """Remove database entries for files that no longer exist on disk."""
        current_paths = {str(f.relative_to(root_path)) for f in current_files}
        stored_files = self.store.get_all_files()

        for stored in stored_files:
            if stored["path"] not in current_paths:
                self.store.conn.execute("DELETE FROM files WHERE path = ?", (stored["path"],))

        self.store.conn.commit()

    def incremental_update(self, changed_files: list[str]) -> IndexResult:
        """Re-index only the files that have changed.

        Args:
            changed_files: List of relative file paths that were modified.

        Returns:
            IndexResult with counts of re-indexed items.
        """
        total_symbols = 0
        total_edges = 0
        indexed = 0

        for relative in changed_files:
            file_path = Path(relative)
            if not file_path.exists():
                # File was deleted — remove from DB
                self.store.conn.execute("DELETE FROM files WHERE path = ?", (relative,))
                self.store.conn.commit()
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
                indexed += 1
            except OSError:
                continue

        return IndexResult(
            files_total=len(changed_files),
            files_indexed=indexed,
            files_skipped=0,
            symbols=total_symbols,
            edges=total_edges,
        )
