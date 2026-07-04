"""Response cache using SQLite, keyed by hash(prompt + model + temperature)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CacheEntry:
    """A cached response entry."""

    key: str
    response: str
    model: str
    temperature: float
    created_at: float
    ttl: float
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if this entry has exceeded its TTL."""
        if self.ttl <= 0:
            return False
        return (time.time() - self.created_at) > self.ttl


class ResponseCache:
    """SQLite-backed response cache for LLM completions.

    Caches responses keyed by hash of (prompt + model + temperature) to
    avoid redundant API calls for identical requests.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        default_ttl: float = 3600.0,
        max_entries: int = 10000,
    ) -> None:
        if db_path is None:
            cache_dir = Path.home() / ".arbiterx"
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(cache_dir / "cache.db")

        self.db_path = db_path
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        """Create the cache table if it doesn't exist."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                key TEXT PRIMARY KEY,
                response TEXT NOT NULL,
                model TEXT NOT NULL,
                temperature REAL NOT NULL,
                created_at REAL NOT NULL,
                ttl REAL NOT NULL,
                hit_count INTEGER DEFAULT 0,
                last_accessed REAL NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_last_accessed
            ON response_cache(last_accessed)
        """)
        self._conn.commit()

    @staticmethod
    def _make_key(prompt: str, model: str, temperature: float) -> str:
        """Generate a cache key from prompt + model + temperature."""
        payload = json.dumps(
            {"prompt": prompt, "model": model, "temperature": temperature},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, prompt: str, model: str, temperature: float) -> Optional[CacheEntry]:
        """Look up a cached response."""
        key = self._make_key(prompt, model, temperature)
        assert self._conn is not None

        cursor = self._conn.execute(
            "SELECT key, response, model, temperature, created_at, ttl, hit_count "
            "FROM response_cache WHERE key = ?",
            (key,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        entry = CacheEntry(
            key=row[0], response=row[1], model=row[2],
            temperature=row[3], created_at=row[4], ttl=row[5], hit_count=row[6],
        )

        if entry.is_expired:
            self._conn.execute("DELETE FROM response_cache WHERE key = ?", (key,))
            self._conn.commit()
            return None

        self._conn.execute(
            "UPDATE response_cache SET hit_count = hit_count + 1, last_accessed = ? WHERE key = ?",
            (time.time(), key),
        )
        self._conn.commit()
        entry.hit_count += 1
        return entry

    def put(
        self,
        prompt: str,
        model: str,
        temperature: float,
        response: str,
        ttl: Optional[float] = None,
    ) -> str:
        """Store a response in the cache. Returns the cache key."""
        key = self._make_key(prompt, model, temperature)
        ttl = ttl if ttl is not None else self.default_ttl
        now = time.time()
        assert self._conn is not None

        self._conn.execute(
            "INSERT OR REPLACE INTO response_cache "
            "(key, response, model, temperature, created_at, ttl, hit_count, last_accessed) "
            "VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
            (key, response, model, temperature, now, ttl, now),
        )
        self._conn.commit()
        self._evict_if_needed()
        return key

    def invalidate(self, prompt: str, model: str, temperature: float) -> bool:
        """Remove a specific cache entry. Returns True if removed."""
        key = self._make_key(prompt, model, temperature)
        assert self._conn is not None
        cursor = self._conn.execute("DELETE FROM response_cache WHERE key = ?", (key,))
        self._conn.commit()
        return cursor.rowcount > 0

    def clear(self) -> int:
        """Remove all entries. Returns count removed."""
        assert self._conn is not None
        cursor = self._conn.execute("DELETE FROM response_cache")
        self._conn.commit()
        return cursor.rowcount

    def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        assert self._conn is not None
        cursor = self._conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(hit_count), 0) FROM response_cache"
        )
        row = cursor.fetchone()
        return {"entries": row[0], "total_hits": row[1], "max_entries": self.max_entries}

    def _evict_if_needed(self) -> None:
        """Evict oldest entries if cache exceeds max size."""
        assert self._conn is not None
        cursor = self._conn.execute("SELECT COUNT(*) FROM response_cache")
        count = cursor.fetchone()[0]
        if count > self.max_entries:
            overage = count - self.max_entries
            self._conn.execute(
                "DELETE FROM response_cache WHERE key IN ("
                "SELECT key FROM response_cache ORDER BY last_accessed ASC LIMIT ?)",
                (overage,),
            )
            self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __del__(self) -> None:
        self.close()
