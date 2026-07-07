"""Language detection and grammar registry for supported source languages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
    "csharp": [".cs"],
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

# Mapping from our language identifiers to tree-sitter-language-pack grammar names
# (when they differ)
_GRAMMAR_NAME_MAP: dict[str, str] = {
    "jsx": "javascript",  # JSX is parsed by the javascript grammar
}


def detect_language(path: Path | str) -> str | None:
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
        The tree-sitter Language object, or None if grammar is unavailable.

    Raises:
        ValueError: If the language is not supported.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language!r}. Supported: {sorted(SUPPORTED_LANGUAGES.keys())}"
        )
    grammar_name = _GRAMMAR_NAME_MAP.get(language, language)
    try:
        return tslp.get_language(grammar_name)
    except Exception:
        # Grammar unavailable at runtime (DownloadError, LookupError, etc.)
        return None
