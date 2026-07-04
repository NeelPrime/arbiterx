#!/usr/bin/env python3
"""Benchmark script proving ≥90% token reduction via codebase mapping.

Compares naive file-reading baseline against arbiterx symbol-level queries.

Usage:
    python benchmarks/run_benchmark.py --repo .
    python benchmarks/run_benchmark.py --repo /path/to/repo --output results.md
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from arbiterx.mapper.hasher import FileHasher
from arbiterx.mapper.indexer import Indexer
from arbiterx.mapper.languages import detect_language
from arbiterx.mapper.store import MapStore


# --- Benchmark queries ---

SAMPLE_QUERIES = [
    "How does the TaskClassifier work?",
    "Fix a bug in the file hasher",
    "Add a new adapter for Mistral",
    "Explain the SQLite schema",
    "Refactor the parser to support Ruby",
    "What does the ContextAssembler do?",
    "How is PageRank used in the symbol graph?",
    "Fix the authentication bug in adapters",
    "Write tests for the plugin loader",
    "How does incremental indexing work?",
]


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token)."""
    return max(1, len(text) // 4)


def extract_keywords(query: str) -> list[str]:
    """Extract meaningful keywords from a query string."""
    stop_words = {
        "how", "does", "the", "what", "is", "a", "an", "in", "to", "for",
        "of", "and", "or", "with", "this", "that", "it", "be", "do", "fix",
        "add", "new", "write", "explain", "refactor", "work", "works",
    }
    words = re.findall(r"\b[a-zA-Z_][a-zA-Z_0-9]*\b", query.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]


def naive_baseline(repo_path: Path, query: str) -> tuple[int, int]:
    """Simulate naive approach: read all files matching query keywords.

    Returns:
        (total_tokens, files_read)
    """
    keywords = extract_keywords(query)
    hasher = FileHasher()
    total_tokens = 0
    files_read = 0

    for file_path in sorted(repo_path.rglob("*")):
        if not file_path.is_file():
            continue
        if hasher._should_skip(file_path):
            continue
        if detect_language(file_path) is None:
            continue

        # Check if filename or content matches any keyword
        name_lower = file_path.name.lower()
        matches_name = any(kw in name_lower for kw in keywords)

        if not matches_name:
            try:
                content = file_path.read_text(errors="ignore")
                content_lower = content.lower()
                matches_content = any(kw in content_lower for kw in keywords)
            except (OSError, UnicodeDecodeError):
                continue
        else:
            try:
                content = file_path.read_text(errors="ignore")
                matches_content = True
            except (OSError, UnicodeDecodeError):
                continue

        if matches_name or matches_content:
            total_tokens += estimate_tokens(content)
            files_read += 1

    return total_tokens, files_read


def arbiterx_query(store: MapStore, query: str) -> tuple[int, int]:
    """Query the arbiterx map for relevant symbols.

    Returns:
        (total_tokens, symbols_found)
    """
    keywords = extract_keywords(query)
    total_tokens = 0
    symbols_found = 0

    for keyword in keywords:
        # Fuzzy search in symbols
        rows = store.conn.execute(
            "SELECT s.name, s.kind, s.signature, s.docstring, f.path "
            "FROM symbols s JOIN files f ON s.file_id = f.id "
            "WHERE s.name LIKE ? OR s.qualified_name LIKE ? "
            "LIMIT 20",
            (f"%{keyword}%", f"%{keyword}%"),
        ).fetchall()

        for row in rows:
            # Build minimal context: signature + docstring
            context_parts = []
            file_path = dict(row).get("path", "")
            signature = dict(row).get("signature", "")
            docstring = dict(row).get("docstring", "")

            if file_path:
                context_parts.append(f"# {file_path}")
            if signature:
                context_parts.append(signature)
            if docstring:
                context_parts.append(f'  """{docstring}"""')

            context = "\n".join(context_parts)
            total_tokens += estimate_tokens(context)
            symbols_found += 1

    return total_tokens, symbols_found


def run_benchmark(repo_path: Path, output_path: Path | None = None) -> None:
    """Run the full benchmark suite."""
    print(f"\n{'='*70}")
    print(f"  CARTOGRAPH BENCHMARK — Token Reduction Analysis")
    print(f"  Repository: {repo_path.resolve()}")
    print(f"{'='*70}\n")

    # Step 1: Build the map
    print("Building codebase map...")
    db_path = repo_path / ".arbiterx" / "map.db"
    (repo_path / ".arbiterx").mkdir(parents=True, exist_ok=True)

    store = MapStore(db_path)
    indexer = Indexer(store)

    start = time.time()
    result = indexer.index_repo(repo_path.resolve())
    build_time = time.time() - start

    print(f"  Map built: {result['files']} files, {result['symbols']} symbols, "
          f"{result['edges']} edges in {build_time:.2f}s\n")

    # Step 2: Run queries
    results = []
    total_naive = 0
    total_arbiterx = 0

    print(f"{'Query':<45} {'Naive':>8} {'Carto':>8} {'Reduction':>10} {'Files':>6}")
    print(f"{'-'*45} {'-'*8} {'-'*8} {'-'*10} {'-'*6}")

    for query in SAMPLE_QUERIES:
        # Naive baseline
        naive_tokens, files_read = naive_baseline(repo_path, query)

        # ArbiterX query
        start = time.time()
        carto_tokens, symbols_found = arbiterx_query(store, query)
        query_time_ms = (time.time() - start) * 1000

        # Calculate reduction
        if naive_tokens > 0:
            reduction = (1 - carto_tokens / naive_tokens) * 100
        else:
            reduction = 0.0

        total_naive += naive_tokens
        total_arbiterx += carto_tokens

        results.append({
            "query": query,
            "naive_tokens": naive_tokens,
            "arbiterx_tokens": carto_tokens,
            "reduction_pct": reduction,
            "files_read": files_read,
            "symbols_found": symbols_found,
            "query_time_ms": query_time_ms,
        })

        # Print row
        query_short = query[:43] + ".." if len(query) > 45 else query
        print(f"{query_short:<45} {naive_tokens:>8} {carto_tokens:>8} "
              f"{reduction:>8.1f}% {files_read:>6}")

    # Summary
    overall_reduction = (1 - total_arbiterx / total_naive) * 100 if total_naive > 0 else 0
    avg_query_time = sum(r["query_time_ms"] for r in results) / len(results)

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  Total naive tokens:       {total_naive:>10,}")
    print(f"  Total arbiterx tokens:  {total_arbiterx:>10,}")
    print(f"  Overall token reduction:  {overall_reduction:>10.1f}%")
    print(f"  Map build time:           {build_time:>10.2f}s")
    print(f"  Avg query time:           {avg_query_time:>10.1f}ms")
    print(f"  {'✓ PASS' if overall_reduction >= 90 else '✗ FAIL'}: "
          f"{'≥90% reduction achieved!' if overall_reduction >= 90 else 'Below 90% target'}")
    print(f"{'='*70}\n")

    # Write results if output path provided
    if output_path:
        _write_results(output_path, repo_path, results, overall_reduction, build_time, avg_query_time)
        print(f"Results saved to: {output_path}")

    store.close()

    # Exit with non-zero if benchmark fails
    if overall_reduction < 90:
        sys.exit(1)


def _write_results(
    output_path: Path,
    repo_path: Path,
    results: list[dict],
    overall_reduction: float,
    build_time: float,
    avg_query_time: float,
) -> None:
    """Write benchmark results as markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Benchmark Results — {repo_path.resolve().name}",
        "",
        f"**Overall token reduction: {overall_reduction:.1f}%**",
        f"- Map build time: {build_time:.2f}s",
        f"- Avg query time: {avg_query_time:.1f}ms",
        "",
        "## Per-Query Results",
        "",
        "| Query | Naive Tokens | ArbiterX Tokens | Reduction | Files |",
        "|-------|-------------|------------------|-----------|-------|",
    ]

    for r in results:
        lines.append(
            f"| {r['query'][:40]} | {r['naive_tokens']:,} | "
            f"{r['arbiterx_tokens']:,} | {r['reduction_pct']:.1f}% | {r['files_read']} |"
        )

    lines.extend(["", f"---", f"", f"Generated by `arbiterx` benchmark suite."])
    output_path.write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ArbiterX token reduction benchmark")
    parser.add_argument("--repo", type=Path, default=Path("."), help="Repository to benchmark")
    parser.add_argument("--output", type=Path, default=None, help="Output markdown file")
    args = parser.parse_args()

    if not args.repo.exists():
        print(f"Error: Repository path '{args.repo}' does not exist.")
        sys.exit(1)

    run_benchmark(args.repo, args.output)
