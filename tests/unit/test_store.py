"""Tests for the MapStore module."""

from __future__ import annotations

from pathlib import Path

import pytest

from arbiterx.mapper.parser import Edge, Symbol
from arbiterx.mapper.store import MapStore


class TestMapStoreInit:
    """Tests for MapStore initialization and table creation."""

    def test_init_db_creates_database_file(self, tmp_path: Path) -> None:
        """init_db should create the SQLite database file."""
        db_path = tmp_path / "test.db"
        store = MapStore(db_path)
        store.init_db()

        assert db_path.exists()
        store.close()

    def test_init_db_creates_tables(self, tmp_path: Path) -> None:
        """init_db should create files, symbols, and edges tables."""
        db_path = tmp_path / "test.db"
        store = MapStore(db_path)
        store.init_db()

        # Query sqlite_master for table names
        cursor = store.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row["name"] for row in cursor.fetchall()}

        assert "files" in tables
        assert "symbols" in tables
        assert "edges" in tables
        store.close()

    def test_init_db_creates_parent_directories(self, tmp_path: Path) -> None:
        """init_db should create parent directories if they don't exist."""
        db_path = tmp_path / "nested" / "dir" / "test.db"
        store = MapStore(db_path)
        store.init_db()

        assert db_path.exists()
        store.close()

    def test_init_db_idempotent(self, tmp_path: Path) -> None:
        """Calling init_db multiple times should not raise errors."""
        db_path = tmp_path / "test.db"
        store = MapStore(db_path)
        store.init_db()
        store.init_db()  # Should not raise
        store.close()


class TestMapStoreFiles:
    """Tests for file upsert and hash retrieval."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> MapStore:
        """Create and initialize a MapStore with an in-memory-like temp db."""
        db_path = tmp_path / "test.db"
        s = MapStore(db_path)
        s.init_db()
        return s

    def test_upsert_file_returns_id(self, store: MapStore) -> None:
        """upsert_file should return a positive integer ID."""
        file_id = store.upsert_file("src/main.py", "abc123hash", "python")
        assert isinstance(file_id, int)
        assert file_id > 0
        store.close()

    def test_get_file_hash_returns_stored_hash(self, store: MapStore) -> None:
        """get_file_hash should return the hash stored via upsert_file."""
        store.upsert_file("src/main.py", "sha256_hash_value", "python")
        result = store.get_file_hash("src/main.py")
        assert result == "sha256_hash_value"
        store.close()

    def test_get_file_hash_returns_none_for_missing(self, store: MapStore) -> None:
        """get_file_hash should return None for a file not in the store."""
        result = store.get_file_hash("nonexistent/file.py")
        assert result is None
        store.close()

    def test_upsert_file_updates_existing(self, store: MapStore) -> None:
        """Upserting the same path should update the hash."""
        store.upsert_file("src/main.py", "hash_v1", "python")
        store.upsert_file("src/main.py", "hash_v2", "python")

        result = store.get_file_hash("src/main.py")
        assert result == "hash_v2"
        store.close()

    def test_upsert_file_preserves_same_id(self, store: MapStore) -> None:
        """Upserting the same path should return the same file ID."""
        id1 = store.upsert_file("src/main.py", "hash_v1", "python")
        id2 = store.upsert_file("src/main.py", "hash_v2", "python")
        assert id1 == id2
        store.close()


class TestMapStoreSymbols:
    """Tests for symbol storage and lookup."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> MapStore:
        db_path = tmp_path / "test.db"
        s = MapStore(db_path)
        s.init_db()
        return s

    def _make_symbol(self, name: str, kind: str = "function", **kwargs) -> Symbol:
        """Helper to create a Symbol with defaults."""
        return Symbol(
            name=name,
            kind=kind,
            file_path=kwargs.get("file_path", "src/main.py"),
            line_start=kwargs.get("line_start", 1),
            line_end=kwargs.get("line_end", 10),
            signature=kwargs.get("signature", f"def {name}():"),
            docstring=kwargs.get("docstring", ""),
            parent=kwargs.get("parent"),
        )

    def test_upsert_symbols_stores_correctly(self, store: MapStore) -> None:
        """upsert_symbols should store symbols retrievable by get_symbols_by_name."""
        file_id = store.upsert_file("src/main.py", "hash1", "python")
        symbols = [
            self._make_symbol("greet", "function"),
            self._make_symbol("Calculator", "class"),
        ]
        store.upsert_symbols(file_id, symbols)

        results = store.get_symbols_by_name("greet")
        assert len(results) == 1
        assert results[0]["name"] == "greet"
        assert results[0]["kind"] == "function"
        store.close()

    def test_get_symbols_by_name_qualified(self, store: MapStore) -> None:
        """get_symbols_by_name should match by qualified_name too."""
        file_id = store.upsert_file("src/main.py", "hash1", "python")
        sym = self._make_symbol("add", "method", parent="Calculator")
        store.upsert_symbols(file_id, [sym])

        # Search by qualified name
        results = store.get_symbols_by_name("Calculator.add")
        assert len(results) == 1
        assert results[0]["name"] == "add"
        assert results[0]["qualified_name"] == "Calculator.add"
        store.close()

    def test_upsert_symbols_replaces_on_reindex(self, store: MapStore) -> None:
        """Upserting symbols for the same file_id should replace old symbols."""
        file_id = store.upsert_file("src/main.py", "hash1", "python")

        # First index
        store.upsert_symbols(file_id, [self._make_symbol("old_func")])
        assert len(store.get_symbols_by_name("old_func")) == 1

        # Re-index with different symbols
        store.upsert_symbols(file_id, [self._make_symbol("new_func")])
        assert len(store.get_symbols_by_name("old_func")) == 0
        assert len(store.get_symbols_by_name("new_func")) == 1
        store.close()

    def test_get_symbols_by_name_returns_empty_for_missing(self, store: MapStore) -> None:
        """Searching for a non-existent symbol should return empty list."""
        results = store.get_symbols_by_name("does_not_exist")
        assert results == []
        store.close()


class TestMapStoreEdges:
    """Tests for edge storage and clearing."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> MapStore:
        db_path = tmp_path / "test.db"
        s = MapStore(db_path)
        s.init_db()
        return s

    def test_upsert_edges_stores_edges(self, store: MapStore) -> None:
        """upsert_edges should store edges retrievable via get_all_edges."""
        edges = [
            Edge(
                source="src/main.py", target="greet", kind="calls", file_path="src/main.py", line=10
            ),
            Edge(
                source="src/main.py", target="os", kind="imports", file_path="src/main.py", line=1
            ),
        ]
        store.upsert_edges(edges)

        all_edges = store.get_all_edges()
        assert len(all_edges) == 2
        targets = {e["target"] for e in all_edges}
        assert "greet" in targets
        assert "os" in targets
        store.close()

    def test_clear_edges_for_file_removes_only_target_file(self, store: MapStore) -> None:
        """clear_edges_for_file should remove edges for the given file only."""
        edges = [
            Edge(source="src/a.py", target="foo", kind="calls", file_path="src/a.py", line=5),
            Edge(source="src/b.py", target="bar", kind="calls", file_path="src/b.py", line=3),
        ]
        store.upsert_edges(edges)

        store.clear_edges_for_file("src/a.py")

        remaining = store.get_all_edges()
        assert len(remaining) == 1
        assert remaining[0]["file_path"] == "src/b.py"
        store.close()

    def test_clear_edges_for_file_no_op_when_empty(self, store: MapStore) -> None:
        """Clearing edges for a file with no edges should not raise."""
        store.clear_edges_for_file("nonexistent/file.py")  # Should not raise
        store.close()
