"""ArbiterX CLI — command-line interface for codebase mapping and AI routing."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from arbiterx import __version__

app = typer.Typer(
    name="arbiterx",
    help="Intelligent codebase mapping for AI-assisted development.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"arbiterx {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """ArbiterX — intelligent codebase mapping for AI-assisted development."""


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Root path of the repository to initialize."),
) -> None:
    """Initialize .arbiterx/ in the current repository.

    Creates the .arbiterx/ directory with configuration files and an empty
    SQLite map database.
    """
    arbiterx_dir = path / ".arbiterx"
    if arbiterx_dir.exists():
        console.print(Panel("[yellow]⚠ .arbiterx/ already exists.[/yellow]", title="Warning"))
        raise typer.Exit(code=1)

    arbiterx_dir.mkdir(parents=True, exist_ok=True)
    (arbiterx_dir / "config.toml").write_text("# ArbiterX configuration\n[mapper]\nexclude = []\n")
    console.print(
        Panel(f"[green]✓ Initialized .arbiterx/ in {path.resolve()}[/green]", title="ArbiterX")
    )


@app.command(name="map")
def build_map(
    status: bool = typer.Option(
        False, "--status", "-s", help="Show current map status instead of rebuilding."
    ),
    root: Path = typer.Argument(Path("."), help="Root path of the repository."),
) -> None:
    """Build or update the codebase map.

    Parses all supported source files, extracts symbols and references,
    and stores them in the local SQLite map database.
    """
    import time

    from arbiterx.mapper.indexer import Indexer
    from arbiterx.mapper.store import MapStore

    arbiterx_dir = root / ".arbiterx"
    db_path = arbiterx_dir / "map.db"

    if status:
        if not db_path.exists():
            console.print("[yellow]No map found. Run 'arbiterx map' to build one.[/yellow]")
            raise typer.Exit(code=1)
        store = MapStore(db_path)
        store.init_db()
        files = store.get_all_files()
        table = Table(title="Map Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Indexed files", str(len(files)))
        # Count symbols
        total_syms = store.conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        total_edges = store.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        table.add_row("Total symbols", str(total_syms))
        table.add_row("Total edges", str(total_edges))
        table.add_row("Database size", f"{db_path.stat().st_size / 1024:.1f} KB")
        console.print(table)
        store.close()
        return

    if not arbiterx_dir.exists():
        console.print("[yellow]No .arbiterx/ found. Running 'init' first...[/yellow]")
        arbiterx_dir.mkdir(parents=True, exist_ok=True)

    console.print("[bold]Building codebase map...[/bold]")
    start = time.time()

    store = MapStore(db_path)
    indexer = Indexer(store)
    result = indexer.index_repo(root.resolve())

    elapsed = time.time() - start
    store.close()

    table = Table(title="Map Built Successfully")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Files indexed", str(result["files"]))
    table.add_row("Symbols extracted", str(result["symbols"]))
    table.add_row("Reference edges", str(result["edges"]))
    table.add_row("Time", f"{elapsed:.2f}s")
    table.add_row("Database size", f"{db_path.stat().st_size / 1024:.1f} KB")
    console.print(table)


@app.command()
def route(
    task: str = typer.Argument(..., help="Description of the task to classify."),
) -> None:
    """Classify a task and show the routing decision.

    Determines task type, complexity, and which model should handle it.
    """
    from arbiterx.router.classifier import TaskClassifier

    classifier = TaskClassifier()
    result = classifier.classify(task)

    table = Table(title="Routing Decision")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Task", task[:80])
    table.add_row("Type", result.task_type.name)
    table.add_row("Complexity", result.complexity.name)
    table.add_row("Context Scope", result.context_scope.name)
    table.add_row("Latency", result.latency.name)
    table.add_row("Est. Tokens", str(result.estimated_tokens))
    table.add_row("Confidence", f"{result.confidence:.0%}")
    console.print(table)


@app.command()
def chat(
    model: str = typer.Option("auto", "--model", "-m", help="LLM model to use."),
) -> None:
    """Start an interactive session with smart context routing.

    Opens a REPL that accepts questions about your codebase and routes
    context intelligently based on the codebase map.
    """
    console.print(
        Panel(
            f"[bold green]ArbiterX Chat[/bold green] (model={model})\nType 'exit' or Ctrl+C to quit.",
            title="Chat",
        )
    )
    raise NotImplementedError("Chat not yet implemented.")


@app.command()
def stats() -> None:
    """Display the token savings dashboard.

    Shows statistics on how much context was trimmed by smart routing,
    tokens saved, and cache hit rates.
    """
    table = Table(title="Token Savings Dashboard")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Total queries", "0")
    table.add_row("Tokens saved", "0")
    table.add_row("Cache hit rate", "0%")
    console.print(table)


@app.command()
def query(
    symbol: str = typer.Argument(..., help="Symbol name to look up in the map."),
    exact: bool = typer.Option(False, "--exact", "-e", help="Exact match only."),
    root: Path = typer.Argument(Path("."), help="Root path of the repository."),
) -> None:
    """Query the codebase map for a symbol.

    Searches the map database for definitions and references of the given
    symbol name and displays the results.
    """
    from arbiterx.mapper.store import MapStore

    db_path = root / ".arbiterx" / "map.db"
    if not db_path.exists():
        console.print("[red]No map found. Run 'arbiterx map' first.[/red]")
        raise typer.Exit(code=1)

    store = MapStore(db_path)
    store.init_db()

    results = store.get_symbols_by_name(symbol)
    if not results:
        # Try fuzzy match
        if not exact:
            rows = store.conn.execute(
                "SELECT s.*, f.path as file_path FROM symbols s "
                "JOIN files f ON s.file_id = f.id "
                "WHERE s.name LIKE ? OR s.qualified_name LIKE ? LIMIT 20",
                (f"%{symbol}%", f"%{symbol}%"),
            ).fetchall()
            results = [dict(r) for r in rows]

    if not results:
        console.print(f"[yellow]No symbols matching '{symbol}' found in map.[/yellow]")
        store.close()
        raise typer.Exit(code=1)

    table = Table(title=f"Symbols matching '{symbol}'")
    table.add_column("Name", style="cyan")
    table.add_column("Kind", style="green")
    table.add_column("File", style="blue")
    table.add_column("Line")
    table.add_column("Signature", max_width=50)

    for r in results:
        table.add_row(
            r.get("qualified_name", r.get("name", "")),
            r.get("kind", ""),
            r.get("file_path", ""),
            str(r.get("line_start", "")),
            (r.get("signature", "") or "")[:50],
        )

    console.print(table)
    store.close()


@app.command(name="export-rules")
def export_rules(
    format: str = typer.Option(
        "agents",
        "--format",
        "-f",
        help="Target format: agents, claude, cursor, copilot, aider, kiro, windsurf, zed",
    ),
    stdout: bool = typer.Option(False, "--stdout", help="Print to stdout instead of writing file"),
    root: Path = typer.Argument(Path("."), help="Project root"),
) -> None:
    """Export engineering principles as rules files for AI coding tools."""
    from arbiterx.principles import ENGINEERING_PREAMBLE

    # Build compact content: preamble rules + NEVER list + self-check
    lines: list[str] = ["# ArbiterX Engineering Rules", ""]
    # Numbered rules from preamble
    for line in ENGINEERING_PREAMBLE.strip().splitlines()[1:]:
        if line.strip():
            lines.append(line.strip())
    lines.append("")
    # NEVER GENERATE list
    lines.append("## NEVER Generate")
    lines.append("- Code with TODO/FIXME placeholders")
    lines.append("- Bare try/except or swallowed errors")
    lines.append("- Magic numbers without named constants")
    lines.append("- Functions longer than 30 lines")
    lines.append("- Untyped function signatures")
    lines.append("- Hardcoded secrets or credentials")
    lines.append("- SQL via string interpolation")
    lines.append("- Mutable default arguments")
    lines.append("- Wildcard imports")
    lines.append("- Dead or commented-out code")
    lines.append("")
    # Self-check questions
    lines.append("## Self-Check Before Responding")
    lines.append("1. Does every function have type annotations?")
    lines.append("2. Are all error paths handled explicitly?")
    lines.append("3. Is there any line that doesn't change behavior?")
    lines.append("4. Are all resources properly closed?")
    lines.append("5. Could this be simpler with stdlib?")

    content = "\n".join(lines) + "\n"

    # Format-specific output paths and wrapping
    format_map: dict[str, str] = {
        "agents": "AGENTS.md",
        "claude": ".claude/rules/arbiterx.md",
        "cursor": ".cursor/rules/arbiterx.mdc",
        "copilot": ".github/copilot-instructions.md",
        "aider": "CONVENTIONS.md",
        "kiro": ".kiro/steering/arbiterx.md",
        "windsurf": ".windsurf/rules/arbiterx.md",
        "zed": ".zed/assistant/rules.md",
    }

    if format not in format_map:
        console.print(f"[red]Unknown format '{format}'. Use one of: {', '.join(format_map)}[/red]")
        raise typer.Exit(code=1)

    # Cursor needs YAML frontmatter
    if format == "cursor":
        frontmatter = '---\ndescription: ArbiterX engineering principles\nglobs: "**/*"\nalwaysApply: true\n---\n\n'
        content = frontmatter + content

    if stdout:
        console.print(content)
        return

    out_path = root / format_map[format]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content)
    console.print(Panel(f"[green]✓ Exported rules to {out_path}[/green]", title="ArbiterX Export"))


if __name__ == "__main__":
    app()
