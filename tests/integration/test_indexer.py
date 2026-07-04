"""Integration tests for the Indexer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from arbiterx.mapper.indexer import Indexer
from arbiterx.mapper.store import MapStore


class TestIndexerIntegration:
    """Integration tests: indexer parses files, stores symbols and edges."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> MapStore:
        """Create and initialize a MapStore for testing."""
        db_path = tmp_path / "map.db"
        s = MapStore(db_path)
        s.init_db()
        return s

    @pytest.fixture
    def sample_repo(self, tmp_path: Path) -> Path:
        """Create a temporary repository with several Python files."""
        repo = tmp_path / "repo"
        repo.mkdir()

        # Create a simple module structure
        (repo / "main.py").write_text('''\
"""Main entry point."""

from utils import helper
from calculator import Calculator


def main():
    """Run the app."""
    calc = Calculator()
    result = calc.add(1, 2)
    msg = helper("world")
    print(msg, result)


if __name__ == "__main__":
    main()
''')

        (repo / "utils.py").write_text('''\
"""Utility functions."""


def helper(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"


def format_number(n: int) -> str:
    """Format a number with commas."""
    return f"{n:,}"
''')

        (repo / "calculator.py").write_text('''\
"""Calculator module."""


class Calculator:
    """A basic calculator."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtract b from a."""
        return a - b

    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
''')

        return repo

    def test_index_repo_returns_counts(self, store: MapStore, sample_repo: Path) -> None:
        """index_repo should return a dict with file, symbol, and edge counts."""
        indexer = Indexer(store)
        result = indexer.index_repo(sample_repo)

        assert "files" in result
        assert "symbols" in result
        assert "edges" in result
        assert result["files"] == 3
        assert result["symbols"] > 0
        assert result["edges"] > 0
        store.close()

    def test_index_repo_stores_files(self, store: MapStore, sample_repo: Path) -> None:
        """All source files should be stored in the database."""
        indexer = Indexer(store)
        indexer.index_repo(sample_repo)

        all_files = store.get_all_files()
        file_paths = {f["path"] for f in all_files}

        assert "main.py" in file_paths
        assert "utils.py" in file_paths
        assert "calculator.py" in file_paths
        store.close()

    def test_index_repo_stores_symbols(self, store: MapStore, sample_repo: Path) -> None:
        """Expected symbols should be stored and retrievable by name."""
        indexer = Indexer(store)
        indexer.index_repo(sample_repo)

        # Check function symbols
        main_results = store.get_symbols_by_name("main")
        assert len(main_results) >= 1
        assert main_results[0]["kind"] == "function"

        helper_results = store.get_symbols_by_name("helper")
        assert len(helper_results) >= 1
        assert helper_results[0]["kind"] == "function"

        # Check class symbol
        calc_results = store.get_symbols_by_name("Calculator")
        assert len(calc_results) >= 1
        assert calc_results[0]["kind"] == "class"
        store.close()

    def test_index_repo_stores_edges(self, store: MapStore, sample_repo: Path) -> None:
        """Reference edges (calls, imports) should be stored."""
        indexer = Indexer(store)
        indexer.index_repo(sample_repo)

        all_edges = store.get_all_edges()
        assert len(all_edges) > 0

        # Check that import edges exist
        import_edges = [e for e in all_edges if e["kind"] == "imports"]
        assert len(import_edges) > 0

        # Check that call edges exist
        call_edges = [e for e in all_edges if e["kind"] == "calls"]
        assert len(call_edges) > 0
        store.close()

    def test_reindex_does_not_duplicate_files(
        self, store: MapStore, sample_repo: Path
    ) -> None:
        """Running index_repo twice should not create duplicate file entries."""
        indexer = Indexer(store)
        indexer.index_repo(sample_repo)
        indexer.index_repo(sample_repo)

        all_files = store.get_all_files()
        # Should still have exactly 3 files, not 6
        assert len(all_files) == 3
        store.close()

    def test_reindex_does_not_duplicate_symbols(
        self, store: MapStore, sample_repo: Path
    ) -> None:
        """Running index_repo twice should not create duplicate symbols."""
        indexer = Indexer(store)
        first_result = indexer.index_repo(sample_repo)
        second_result = indexer.index_repo(sample_repo)

        # Symbol counts should be the same both times
        assert first_result["symbols"] == second_result["symbols"]

        # Verify by querying: each symbol name should appear once per file
        main_results = store.get_symbols_by_name("main")
        assert len(main_results) == 1
        store.close()

    def test_reindex_updates_changed_hash(
        self, store: MapStore, sample_repo: Path
    ) -> None:
        """After modifying a file, re-indexing should update the stored hash."""
        indexer = Indexer(store)
        indexer.index_repo(sample_repo)

        hash_before = store.get_file_hash("utils.py")

        # Modify the file
        (sample_repo / "utils.py").write_text('''\
"""Modified utilities."""


def helper(name: str) -> str:
    """Improved greeting."""
    return f"Hi, {name}! Welcome."
''')

        indexer.index_repo(sample_repo)
        hash_after = store.get_file_hash("utils.py")

        assert hash_before != hash_after
        store.close()

    def test_index_skips_unsupported_files(
        self, store: MapStore, sample_repo: Path
    ) -> None:
        """Non-source files should not be indexed."""
        # Add non-source files
        (sample_repo / "README.md").write_text("# README")
        (sample_repo / "data.json").write_text('{"key": "value"}')
        (sample_repo / "image.png").write_bytes(b"\x89PNG\r\n")

        indexer = Indexer(store)
        result = indexer.index_repo(sample_repo)

        # Should only have 3 Python files
        assert result["files"] == 3
        all_files = store.get_all_files()
        for f in all_files:
            assert f["path"].endswith(".py")
        store.close()
