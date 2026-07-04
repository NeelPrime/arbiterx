"""Prompt compressor with deduplication, truncation, and summarization."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass
class CompressionResult:
    """Result of prompt compression."""

    text: str
    original_tokens: int
    compressed_tokens: int
    techniques_applied: list[str]

    @property
    def ratio(self) -> float:
        """Compression ratio (0.0 = none, 1.0 = fully removed)."""
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.compressed_tokens / self.original_tokens)

    @property
    def tokens_saved(self) -> int:
        """Number of tokens saved."""
        return self.original_tokens - self.compressed_tokens


class PromptCompressor:
    """Compresses prompt content to fit within token budgets.

    Applies a pipeline of compression techniques:
    1. Deduplication — remove repeated content
    2. Truncation — cut content exceeding budget
    3. Summarization — structural summary as last resort
    """

    def __init__(
        self,
        target_tokens: int = 4000,
        chars_per_token: int = 4,
        preserve_structure: bool = True,
    ) -> None:
        self.target_tokens = target_tokens
        self.chars_per_token = chars_per_token
        self.preserve_structure = preserve_structure

    def compress(self, text: str, budget: int | None = None) -> CompressionResult:
        """Apply full compression pipeline to text."""
        budget = budget or self.target_tokens
        original_tokens = self._estimate_tokens(text)
        techniques: list[str] = []

        if original_tokens <= budget:
            return CompressionResult(
                text=text,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                techniques_applied=[],
            )

        # Stage 1: Deduplication
        text = self.deduplicate(text)
        current_tokens = self._estimate_tokens(text)
        if current_tokens < original_tokens:
            techniques.append("deduplication")
        if current_tokens <= budget:
            return CompressionResult(
                text=text,
                original_tokens=original_tokens,
                compressed_tokens=current_tokens,
                techniques_applied=techniques,
            )

        # Stage 2: Truncation
        text = self.truncate(text, budget)
        current_tokens = self._estimate_tokens(text)
        techniques.append("truncation")
        if current_tokens <= budget:
            return CompressionResult(
                text=text,
                original_tokens=original_tokens,
                compressed_tokens=current_tokens,
                techniques_applied=techniques,
            )

        # Stage 3: Summarization
        text = self.summarize(text, budget)
        current_tokens = self._estimate_tokens(text)
        techniques.append("summarization")

        return CompressionResult(
            text=text,
            original_tokens=original_tokens,
            compressed_tokens=current_tokens,
            techniques_applied=techniques,
        )

    def deduplicate(self, text: str) -> str:
        """Remove duplicate lines, preserving first occurrence."""
        lines = text.split("\n")
        seen_hashes: set[str] = set()
        result: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped in ("{", "}", ")", "];", "};"):
                result.append(line)
                continue
            line_hash = hashlib.md5(stripped.encode()).hexdigest()
            if line_hash not in seen_hashes:
                seen_hashes.add(line_hash)
                result.append(line)

        return "\n".join(result)

    def truncate(self, text: str, budget: int) -> str:
        """Truncate text to fit within token budget."""
        target_chars = budget * self.chars_per_token
        if len(text) <= target_chars:
            return text

        if not self.preserve_structure:
            return text[:target_chars] + "\n\n... [truncated]"

        lines = text.split("\n")
        char_count = 0
        break_line = len(lines)

        for i, line in enumerate(lines):
            char_count += len(line) + 1
            if char_count >= target_chars:
                break_line = i
                break

        # Search backward for a logical break point
        for i in range(break_line, max(0, break_line - 20), -1):
            if i < len(lines):
                stripped = lines[i].strip()
                if not stripped or stripped.startswith(("class ", "def ", "function ")):
                    break_line = i
                    break

        truncated = "\n".join(lines[:break_line])
        return truncated + "\n\n... [truncated]"

    def summarize(self, text: str, budget: int) -> str:
        """Structural summarization: keep signatures, remove bodies."""
        lines = text.split("\n")
        result: list[str] = []
        in_body = False
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            if stripped.startswith(("import ", "from ", "#!", "//")):
                result.append(line)
                in_body = False
                continue

            if re.match(r"^\s*(class |def |async def )", line):
                result.append(line)
                indent_level = len(line) - len(line.lstrip())
                in_body = True
                result.append(" " * (indent_level + 4) + "...")
                continue

            if stripped.startswith("@"):
                result.append(line)
                in_body = False
                continue

            if in_body:
                current_indent = len(line) - len(line.lstrip()) if stripped else indent_level + 4
                if stripped and current_indent <= indent_level:
                    in_body = False
                    result.append(line)
                continue

            if not stripped:
                result.append(line)
                continue

            result.append(line)

        summarized = "\n".join(result)
        target_chars = budget * self.chars_per_token
        if len(summarized) > target_chars:
            summarized = summarized[:target_chars] + "\n... [summarized]"

        return summarized

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from character length."""
        return max(1, len(text) // self.chars_per_token)
