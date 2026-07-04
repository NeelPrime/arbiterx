"""SQLite-backed storage for the codebase map."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from arbiterx.mapper.parser import Edge, Symbol


@dataclass
class StoredFile:
    """A file record from the map database."""

    id: int
    path: str
    hash: str
    language: str
    last_indexed: str


CREATE_TABLES_SQL = """\
CREATE TABLE IF NOT EXISTS files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT UNIQUE NOT NULL,
    hash        TEXT NOT NULL,
    language    TEXT NOT NULL,
    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS symbols (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id     INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    kind        TEXT NOT NULL,
    line_start  INTEGER NOT NULL,
    line_end    INTEGER NOT NULL,
    signature   TEXT DEFAULT '',
    docstring   TEXT DEFAULT '',
    parent      TEXT,
    qualified_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    target      TEXT NOT NULL,
    kind        TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    line        INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_symbols_qualified ON symbols(qualified_name);
CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target);
CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
"""


class MapStore:
    """SQLite-backed storage for the codebase symbol map."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Lazy connection accessor."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init_db(self) -> None:
        """Create database tables if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn.executescript(CREATE_TABLES_SQL)
        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def get_file_hash(self, path: str) -> str | None:
        """Get the stored hash for a file path."""
        row = self.conn.execute("SELECT hash FROM files WHERE path = ?", (path,)).fetchone()
        return row["hash"] if row else None

    def upsert_file(self, path: str, hash: str, language: str) -> int:
        """Insert or update a file record. Returns the file row ID."""
        self.conn.execute(
            """INSERT INTO files (path, hash, language, last_indexed)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(path) DO UPDATE SET
                hash = excluded.hash,
                language = excluded.language,
                last_indexed = CURRENT_TIMESTAMP""",
            (path, hash, language),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT id FROM files WHERE path = ?", (path,)).fetchone()
        return row["id"]

    def upsert_symbols(self, file_id: int, symbols: list[Symbol]) -> None:
        """Replace all symbols for a given file."""
        self.conn.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
        self.conn.executemany(
            """INSERT INTO symbols
            (file_id, name, kind, line_start, line_end, signature, docstring, parent, qualified_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    file_id,
                    s.name,
                    s.kind,
                    s.line_start,
                    s.line_end,
                    s.signature,
                    s.docstring,
                    s.parent,
                    s.qualified_name,
                )
                for s in symbols
            ],
        )
        self.conn.commit()

    def upsert_edges(self, edges: list[Edge]) -> None:
        """Insert reference edges."""
        self.conn.executemany(
            "INSERT INTO edges (source, target, kind, file_path, line) VALUES (?, ?, ?, ?, ?)",
            [(e.source, e.target, e.kind, e.file_path, e.line) for e in edges],
        )
        self.conn.commit()

    def clear_edges_for_file(self, file_path: str) -> None:
        """Remove all edges originating from a given file."""
        self.conn.execute("DELETE FROM edges WHERE file_path = ?", (file_path,))
        self.conn.commit()

    def get_symbols_by_name(self, name: str) -> list[dict]:
        """Look up symbols by name."""
        rows = self.conn.execute(
            """SELECT s.*, f.path as file_path FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.name = ? OR s.qualified_name = ?""",
            (name, name),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_file_symbols(self, file_id: int) -> list[dict]:
        """Get all symbols for a file."""
        rows = self.conn.execute("SELECT * FROM symbols WHERE file_id = ?", (file_id,)).fetchall()
        return [dict(row) for row in rows]

    def get_all_files(self) -> list[dict]:
        """Get all indexed file records."""
        rows = self.conn.execute("SELECT * FROM files").fetchall()
        return [dict(row) for row in rows]

    def get_all_edges(self) -> list[dict]:
        """Get all edges."""
        rows = self.conn.execute("SELECT * FROM edges").fetchall()
        return [dict(row) for row in rows]
