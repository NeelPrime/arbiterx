"""ArbiterX MCP Server — exposes codebase intelligence as tools for Claude Code.

Runs as a local stdio MCP server. Claude Code calls these tools instead of
reading raw files, reducing token usage by 97%.

Usage:
    arbiterx mcp-serve
"""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "arbiterx",
    instructions=(
        "ArbiterX provides codebase intelligence tools. "
        "Use arbiterx_query to find relevant functions/classes before reading files. "
        "Use arbiterx_overview to understand project structure. "
        "Use arbiterx_gate to score code quality. "
        "These tools are faster and cheaper than reading raw files."
    ),
)


def _get_project_dir() -> Path:
    """Get the project directory from environment or current working directory."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def _get_store():
    """Get the MapStore for the current project."""
    from arbiterx.mapper.store import MapStore

    project_dir = _get_project_dir()
    db_path = project_dir / ".arbiterx" / "map.db"

    if not db_path.exists():
        return None

    store = MapStore(db_path)
    store.init_db()
    return store


@mcp.tool()
def arbiterx_query(query: str) -> str:
    """Search the codebase map for functions, classes, and symbols matching a query.

    Use this BEFORE reading files — it returns only the relevant signatures,
    saving 97% of tokens compared to reading full files.

    Args:
        query: Search term (function name, class name, keyword like "payment" or "auth")

    Returns:
        Matching symbol signatures with file locations and relationships.
    """
    store = _get_store()
    if store is None:
        return (
            "Error: No ArbiterX map found. Run 'arbiterx init && arbiterx map' in the project root."
        )

    # Search by name (exact and partial match)
    results = store.get_symbols_by_name(query)

    # Also search by partial match if no exact results
    if not results:
        all_symbols = store.conn.execute(
            "SELECT s.*, f.path as file_path FROM symbols s "
            "JOIN files f ON s.file_id = f.id "
            "WHERE s.name LIKE ? OR s.qualified_name LIKE ? "
            "ORDER BY s.name LIMIT 20",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        results = [dict(row) for row in all_symbols]

    if not results:
        return f"No symbols found matching '{query}'. Try a different search term."

    output_lines = []
    for sym in results[:15]:
        sig = sym.get("signature", "")
        file_path = sym.get("file_path", "")
        kind = sym.get("kind", "")
        line = sym.get("line_start", 0)
        parent = sym.get("parent", "")

        header = f"{kind}: {sym['name']}"
        if parent:
            header = f"{kind}: {parent}.{sym['name']}"

        output_lines.append(f"{header}")
        if sig:
            output_lines.append(f"  Signature: {sig}")
        output_lines.append(f"  File: {file_path}:{line}")
        output_lines.append("")

    store.close()
    return "\n".join(output_lines)


@mcp.tool()
def arbiterx_overview() -> str:
    """Get a high-level overview of the codebase — languages, file counts, top symbols.

    Use this to understand project structure before diving into specifics.

    Returns:
        Language breakdown, file counts, and top-ranked symbols.
    """
    store = _get_store()
    if store is None:
        return (
            "Error: No ArbiterX map found. Run 'arbiterx init && arbiterx map' in the project root."
        )

    # Language breakdown
    langs = store.conn.execute(
        "SELECT language, COUNT(*) as count FROM files GROUP BY language ORDER BY count DESC"
    ).fetchall()

    # Total counts
    total_files = store.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    total_symbols = store.conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
    total_edges = store.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    # Top symbols (most referenced)
    top_symbols = store.conn.execute(
        "SELECT target as name, COUNT(*) as refs FROM edges "
        "GROUP BY target ORDER BY refs DESC LIMIT 15"
    ).fetchall()

    output = []
    output.append(
        f"Codebase: {total_files} files, {total_symbols} symbols, {total_edges} references"
    )
    output.append("")
    output.append("Languages:")
    for row in langs:
        output.append(f"  {row['language']}: {row['count']} files")

    if top_symbols:
        output.append("")
        output.append("Most referenced symbols:")
        for row in top_symbols:
            output.append(f"  {row['name']} ({row['refs']} refs)")

    store.close()
    return "\n".join(output)


@mcp.tool()
def arbiterx_gate(code: str, language: str = "python") -> str:
    """Score code quality 0-100. Checks security, robustness, efficiency, types.

    Use this to validate AI-generated code before presenting it to the user.

    Args:
        code: The source code to validate.
        language: Programming language (default: python).

    Returns:
        Score, pass/fail status, and list of issues with suggested fixes.
    """
    from arbiterx.gate.validator import QualityGate

    gate = QualityGate()
    result = gate.validate(code, language)

    output = []
    output.append(f"Score: {result.score}/100 — {'PASSED' if result.passed else 'FAILED'}")

    if result.issues:
        output.append("")
        output.append("Issues:")
        for issue in result.issues:
            output.append(f"  [{issue.severity}] {issue.message}")
            if issue.suggestion:
                output.append(f"    Fix: {issue.suggestion}")

    return "\n".join(output)


@mcp.tool()
def arbiterx_file_symbols(file_path: str) -> str:
    """Get all symbols (functions, classes, methods) defined in a specific file.

    Use this instead of reading the full file when you only need to know
    what's defined there.

    Args:
        file_path: Relative path to the file (e.g., "src/auth/service.py")

    Returns:
        All symbols in the file with their signatures.
    """
    store = _get_store()
    if store is None:
        return (
            "Error: No ArbiterX map found. Run 'arbiterx init && arbiterx map' in the project root."
        )

    # Find file by path (partial match)
    rows = store.conn.execute(
        "SELECT id, path FROM files WHERE path LIKE ?",
        (f"%{file_path}%",),
    ).fetchall()

    if not rows:
        return f"File '{file_path}' not found in the map. Run 'arbiterx map' to index."

    output = []
    for file_row in rows[:3]:
        file_id = file_row["id"]
        output.append(f"File: {file_row['path']}")
        output.append("")

        symbols = store.get_file_symbols(file_id)
        for sym in symbols:
            sig = sym.get("signature", "")
            kind = sym.get("kind", "")
            parent = sym.get("parent", "")

            name = sym["name"]
            if parent:
                name = f"{parent}.{name}"

            output.append(f"  {kind}: {name} (line {sym['line_start']})")
            if sig:
                output.append(f"    {sig}")

        output.append("")

    store.close()
    return "\n".join(output)


def run_server() -> None:
    """Start the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
