"""Language detection and grammar registry for supported source languages."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import tree_sitter_language_pack as tslp

# Mapping of language identifier -> file extensions
SUPPORTED_LANGUAGES: dict[str, list[str]] = {
    "python": [".py", ".pyi"],
    "typescript": [".ts", ".mts", ".cts"],
    "tsx": [".tsx"],
    "javascript": [".js", ".mjs", ".cjs"],
    "jsx": [".jsx"],
    "rust": [".rs"],
    "go": [".go"],
    "java": [".java"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"],
    "c_sharp": [".cs"],
    "ruby": [".rb"],
    "php": [".php"],
    "swift": [".swift"],
    "kotlin": [".kt", ".kts"],
    "scala": [".scala"],
    "zig": [".zig"],
    "lua": [".lua"],
    "elixir": [".ex", ".exs"],
    "haskell": [".hs"],
    "ocaml": [".ml", ".mli"],
    "bash": [".sh", ".bash"],
}

# Reverse lookup: extension -> language
_EXT_TO_LANGUAGE: dict[str, str] = {}
for _lang, _exts in SUPPORTED_LANGUAGES.items():
    for _ext in _exts:
        _EXT_TO_LANGUAGE[_ext] = _lang


def detect_language(path: Path | str) -> Optional[str]:
    """Detect the programming language of a file based on its extension.

    Args:
        path: File path to inspect.

    Returns:
        Language identifier string, or None if unsupported.
    """
    ext = Path(path).suffix.lower()
    return _EXT_TO_LANGUAGE.get(ext)


def get_grammar(language: str) -> Any:
    """Get the tree-sitter grammar for a language.

    Args:
        language: Language identifier (must be in SUPPORTED_LANGUAGES).

    Returns:
        The tree-sitter Language object.

    Raises:
        ValueError: If the language is not supported.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language!r}. "
            f"Supported: {sorted(SUPPORTED_LANGUAGES.keys())}"
        )
    return tslp.get_language(language)
