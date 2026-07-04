"""Tests for the FileHasher module."""

from __future__ import annotations

import hashlib
from pathlib import Path

from arbiterx.mapper.hasher import FileHasher


class TestFileHasher:
    """Tests for FileHasher SHA-256 content hashing."""

    def test_hash_file_returns_correct_sha256(self, tmp_path: Path) -> None:
        """Hashing a file should return its SHA-256 hex digest."""
        content = b"hello, arbiterx!\n"
        test_file = tmp_path / "sample.py"
        test_file.write_bytes(content)

        hasher = FileHasher()
        result = hasher.hash_file(test_file)

        expected = hashlib.sha256(content).hexdigest()
        assert result == expected

    def test_hash_file_deterministic(self, tmp_path: Path) -> None:
        """Hashing the same file twice should produce identical results."""
        test_file = tmp_path / "deterministic.txt"
        test_file.write_text("same content every time")

        hasher = FileHasher()
        first = hasher.hash_file(test_file)
        second = hasher.hash_file(test_file)

        assert first == second

    def test_hash_file_changes_with_content(self, tmp_path: Path) -> None:
        """Modifying file content should produce a different hash."""
        test_file = tmp_path / "mutable.txt"
        test_file.write_text("version 1")

        hasher = FileHasher()
        hash_v1 = hasher.hash_file(test_file)

        test_file.write_text("version 2")
        hash_v2 = hasher.hash_file(test_file)

        assert hash_v1 != hash_v2

    def test_hash_empty_file(self, tmp_path: Path) -> None:
        """Hashing an empty file should return SHA-256 of empty bytes."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        hasher = FileHasher()
        result = hasher.hash_file(test_file)

        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected
