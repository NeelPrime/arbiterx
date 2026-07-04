#!/usr/bin/env python3
"""Validate a source file using the ArbiterX quality gate.

Usage:
    python examples/validate_file.py path/to/file.py

Exits with code 0 on pass, 1 on failure.
"""

import sys
from pathlib import Path

from arbiterx.gate import QualityGate
from arbiterx.mapper.languages import detect_language

# ─── Language detection from file extension ───────────────────────────────────

EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}


def get_language(file_path: Path) -> str:
    """Detect programming language from file extension."""
    # Try arbiterx's built-in detection first
    lang = detect_language(file_path)
    if lang:
        return lang
    # Fall back to extension map
    ext = file_path.suffix.lower()
    return EXTENSION_MAP.get(ext, "python")


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python examples/validate_file.py <file_path>")
        print("Example: python examples/validate_file.py src/arbiterx/gate/validator.py")
        return 1

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return 1

    if not file_path.is_file():
        print(f"Error: Not a file: {file_path}")
        return 1

    # Read the file
    code = file_path.read_text(encoding="utf-8")
    language = get_language(file_path)

    print(f"Validating: {file_path}")
    print(f"Language:   {language}")
    print(f"Lines:      {len(code.splitlines())}")
    print("─" * 50)

    # Run the quality gate
    gate = QualityGate(passing_score=70)
    result = gate.validate(code, language=language)

    # Print results
    if result.passed:
        print(f"✅ PASSED  (score: {result.score}/100)")
    else:
        print(f"❌ FAILED  (score: {result.score}/100)")

    if result.issues:
        print(f"\nIssues ({len(result.issues)}):")
        for issue in result.issues:
            print(f"  [{issue.severity.upper():8s}] Line {issue.line:4d}: {issue.message}")
            if issue.suggestion:
                print(f"             → {issue.suggestion}")
        print()

    if result.fixed_code:
        print("ℹ️  Auto-fix available. Use the QualityGate API with auto_fix=True to retrieve it.")

    # Exit with appropriate code
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
