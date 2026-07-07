"""File hashing utilities for incremental indexing."""

from __future__ import annotations

import hashlib
from pathlib import Path


class FileHasher:
    """Computes content hashes for files to detect changes.

    Uses SHA-256 for content hashing to support incremental re-indexing.
    """

    BUFFER_SIZE = 65536  # 64 KB read chunks

    SKIP_DIRS = frozenset(
        {
            # Version control
            ".git",
            ".svn",
            ".hg",
            # ArbiterX
            ".arbiterx",
            # JavaScript / Node
            "node_modules",
            "bower_components",
            ".next",
            ".nuxt",
            ".angular",
            ".cache",
            # Python
            "__pycache__",
            ".venv",
            "venv",
            ".tox",
            ".mypy_cache",
            ".pytest_cache",
            ".eggs",
            "egg-info",
            "wheels",
            # Build outputs
            "dist",
            "build",
            "_build",
            "out",
            # .NET / C#
            "bin",
            "obj",
            # Java / Kotlin / Gradle
            ".gradle",
            # Rust
            "target",
            ".cargo",
            # Go (no common skip needed — go builds in-place)
            # Zig
            "zig-cache",
            "zig-out",
            # PHP
            "vendor",
            # Ruby
            ".bundle",
            # Elixir
            "deps",
            # Swift / iOS
            "Pods",
            "DerivedData",
            # Dart / Flutter
            ".dart_tool",
            ".pub-cache",
            # Terraform
            ".terraform",
            # IDE / Editor
            ".idea",
            ".vs",
            ".vscode",
            # Coverage / Testing
            "coverage",
            ".nyc_output",
            # Misc
            "tmp",
            "logs",
            "packages",
        }
    )

    def hash_file(self, path: Path) -> str:
        """Compute the SHA-256 hash of a file's contents.

        Args:
            path: Path to the file.

        Returns:
            Hex-encoded SHA-256 digest.
        """
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                data = f.read(self.BUFFER_SIZE)
                if not data:
                    break
                sha.update(data)
        return sha.hexdigest()

    def hash_directory(self, path: Path) -> dict[str, str]:
        """Compute hashes for all files in a directory (recursively).

        Args:
            path: Root directory path.

        Returns:
            Dictionary mapping relative file paths to their SHA-256 hashes.
        """
        hashes: dict[str, str] = {}
        if not path.is_dir():
            return hashes

        for file_path in sorted(path.rglob("*")):
            if file_path.is_file() and not self._should_skip(file_path):
                relative = str(file_path.relative_to(path))
                hashes[relative] = self.hash_file(file_path)

        return hashes

    def get_changed_files(
        self, stored_hashes: dict[str, str], current_hashes: dict[str, str]
    ) -> list[str]:
        """Determine which files have changed between stored and current states.

        Args:
            stored_hashes: Previously stored path->hash mapping.
            current_hashes: Current path->hash mapping.

        Returns:
            List of relative paths that are new, modified, or deleted.
        """
        changed: list[str] = []

        for path, current_hash in current_hashes.items():
            if path not in stored_hashes or stored_hashes[path] != current_hash:
                changed.append(path)

        for path in stored_hashes:
            if path not in current_hashes:
                changed.append(path)

        return changed

    def _should_skip(self, path: Path) -> bool:
        """Check whether a file path should be skipped during hashing."""
        return any(part in self.SKIP_DIRS for part in path.parts)
