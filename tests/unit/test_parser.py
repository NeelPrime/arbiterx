"""Tests for the TreeSitterParser module."""

from __future__ import annotations

from pathlib import Path

import pytest

from arbiterx.mapper.languages import detect_language
from arbiterx.mapper.parser import Edge, Symbol, TreeSitterParser


class TestTreeSitterParser:
    """Tests for TreeSitterParser symbol and reference extraction."""

    @pytest.fixture
    def parser(self) -> TreeSitterParser:
        """Create a TreeSitterParser instance."""
        return TreeSitterParser()

    @pytest.fixture
    def sample_python_file(self, tmp_path: Path) -> Path:
        """Create a temporary Python file with a class and function."""
        content = '''\
"""Sample module docstring."""

import os
from pathlib import Path


def greet(name: str) -> str:
    """Return a greeting string."""
    return f"Hello, {name}!"


class Calculator:
    """A simple calculator class."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b


def main():
    calc = Calculator()
    result = calc.add(2, 3)
    print(greet("world"))
'''
        filepath = tmp_path / "sample.py"
        filepath.write_text(content)
        return filepath

    def test_parse_simple_python_file(
        self, parser: TreeSitterParser, sample_python_file: Path
    ) -> None:
        """Parsing a Python file should return a non-empty list of symbols."""
        symbols = parser.parse_file(sample_python_file)
        assert len(symbols) > 0
        assert all(isinstance(s, Symbol) for s in symbols)

    def test_symbols_have_correct_kinds(
        self, parser: TreeSitterParser, sample_python_file: Path
    ) -> None:
        """Extracted symbols should have correct kind values."""
        symbols = parser.parse_file(sample_python_file)
        names_and_kinds = {s.name: s.kind for s in symbols}

        assert "greet" in names_and_kinds
        assert names_and_kinds["greet"] == "function"

        assert "Calculator" in names_and_kinds
        assert names_and_kinds["Calculator"] == "class"

        assert "main" in names_and_kinds
        assert names_and_kinds["main"] == "function"

    def test_symbols_have_correct_names(
        self, parser: TreeSitterParser, sample_python_file: Path
    ) -> None:
        """All expected symbol names should be present in parsed output."""
        symbols = parser.parse_file(sample_python_file)
        symbol_names = {s.name for s in symbols}

        assert "greet" in symbol_names
        assert "Calculator" in symbol_names
        assert "main" in symbol_names

    def test_symbols_have_valid_line_numbers(
        self, parser: TreeSitterParser, sample_python_file: Path
    ) -> None:
        """Symbols should have positive line numbers with end >= start."""
        symbols = parser.parse_file(sample_python_file)

        for symbol in symbols:
            assert symbol.line_start > 0
            assert symbol.line_end >= symbol.line_start

    def test_symbols_have_file_path(
        self, parser: TreeSitterParser, sample_python_file: Path
    ) -> None:
        """Every symbol should reference the file it was parsed from."""
        symbols = parser.parse_file(sample_python_file)

        for symbol in symbols:
            assert symbol.file_path == str(sample_python_file)

    def test_references_extracted_calls(
        self, parser: TreeSitterParser, sample_python_file: Path
    ) -> None:
        """parse_references should detect function calls."""
        edges = parser.parse_references(sample_python_file)
        assert len(edges) > 0
        assert all(isinstance(e, Edge) for e in edges)

        call_targets = {e.target for e in edges if e.kind == "calls"}
        # The main() function calls Calculator(), calc.add(), greet(), print()
        assert any("print" in t for t in call_targets) or any("greet" in t for t in call_targets)

    def test_references_extracted_imports(
        self, parser: TreeSitterParser, sample_python_file: Path
    ) -> None:
        """parse_references should detect import statements."""
        edges = parser.parse_references(sample_python_file)

        import_targets = {e.target for e in edges if e.kind == "imports"}
        assert "os" in import_targets or "Path" in import_targets

    def test_references_have_valid_line_numbers(
        self, parser: TreeSitterParser, sample_python_file: Path
    ) -> None:
        """All reference edges should have positive line numbers."""
        edges = parser.parse_references(sample_python_file)

        for edge in edges:
            assert edge.line > 0

    def test_references_have_correct_file_path(
        self, parser: TreeSitterParser, sample_python_file: Path
    ) -> None:
        """All edges should reference the correct source file."""
        edges = parser.parse_references(sample_python_file)

        for edge in edges:
            assert edge.file_path == str(sample_python_file)
            assert edge.source == str(sample_python_file)


class TestLanguageDetection:
    """Tests for language detection from file extensions."""

    @pytest.mark.parametrize(
        ("filename", "expected_language"),
        [
            ("main.py", "python"),
            ("types.pyi", "python"),
            ("index.ts", "typescript"),
            ("app.tsx", "tsx"),
            ("script.js", "javascript"),
            ("component.jsx", "jsx"),
            ("lib.rs", "rust"),
            ("main.go", "go"),
            ("App.java", "java"),
            ("util.c", "c"),
            ("util.cpp", "cpp"),
        ],
    )
    def test_detect_language_known_extensions(
        self, filename: str, expected_language: str
    ) -> None:
        """Known file extensions should map to the correct language."""
        result = detect_language(Path(filename))
        assert result == expected_language

    @pytest.mark.parametrize(
        "filename",
        [
            "README.md",
            "data.json",
            "config.yaml",
            "image.png",
            "file.txt",
            "Makefile",
        ],
    )
    def test_detect_language_unsupported_returns_none(self, filename: str) -> None:
        """Unsupported file extensions should return None."""
        result = detect_language(Path(filename))
        assert result is None

    def test_detect_language_case_insensitive(self) -> None:
        """Extension detection should be case-insensitive."""
        result = detect_language(Path("FILE.PY"))
        assert result == "python"


class TestParserUnsupportedFiles:
    """Tests for parser behavior with unsupported file types."""

    @pytest.fixture
    def parser(self) -> TreeSitterParser:
        return TreeSitterParser()

    def test_parse_unsupported_returns_empty_symbols(
        self, parser: TreeSitterParser, tmp_path: Path
    ) -> None:
        """Parsing an unsupported file type should return an empty list."""
        md_file = tmp_path / "readme.md"
        md_file.write_text("# Hello\n\nThis is markdown.")

        symbols = parser.parse_file(md_file)
        assert symbols == []

    def test_parse_unsupported_returns_empty_edges(
        self, parser: TreeSitterParser, tmp_path: Path
    ) -> None:
        """Parsing references in an unsupported file should return an empty list."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')

        edges = parser.parse_references(json_file)
        assert edges == []
