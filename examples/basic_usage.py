#!/usr/bin/env python3
"""Basic usage example for ArbiterX.

Demonstrates:
  1. Building a codebase map programmatically
  2. Querying symbols from the map
  3. Classifying a task using the router

Run with:
    python examples/basic_usage.py
"""

import tempfile
from pathlib import Path

# ─── Step 1: Build a codebase map ─────────────────────────────────────────────
# The mapper module provides Indexer + MapStore to parse source files into a
# SQLite-backed symbol database.

from arbiterx.mapper import Indexer, MapStore, detect_language


def demo_build_map() -> MapStore:
    """Build a codebase map from the current project."""
    print("=" * 60)
    print("STEP 1: Building a codebase map")
    print("=" * 60)

    # Create a temporary database for this demo
    db_path = Path(tempfile.mktemp(suffix=".db"))
    store = MapStore(db_path)
    store.init_db()

    # Point the indexer at the arbiterx source directory
    indexer = Indexer(store)
    project_root = Path(__file__).resolve().parent.parent / "src"

    print(f"  Indexing: {project_root}")
    stats = indexer.index_repo(project_root)

    print(f"  Files indexed:  {stats['files']}")
    print(f"  Symbols found:  {stats['symbols']}")
    print(f"  Edges (refs):   {stats['edges']}")
    print()

    return store


# ─── Step 2: Query a symbol ───────────────────────────────────────────────────
# Once the map is built, you can look up any symbol by name.

def demo_query_symbol(store: MapStore) -> None:
    """Look up a symbol in the codebase map."""
    print("=" * 60)
    print("STEP 2: Querying a symbol")
    print("=" * 60)

    symbol_name = "QualityGate"
    results = store.get_symbols_by_name(symbol_name)

    if results:
        for sym in results:
            print(f"  Found: {sym['qualified_name']}")
            print(f"    Kind:     {sym['kind']}")
            print(f"    File:     {sym['file_path']}")
            print(f"    Lines:    {sym['line_start']}-{sym['line_end']}")
            if sym.get("signature"):
                print(f"    Signature: {sym['signature']}")
    else:
        print(f"  Symbol '{symbol_name}' not found in the map.")

    print()


# ─── Step 3: Classify a task ──────────────────────────────────────────────────
# The router module provides a TaskClassifier that categorizes natural-language
# task descriptions into structured metadata (type, complexity, scope, etc.).

from arbiterx.router import TaskClassifier


def demo_classify_task() -> None:
    """Classify different tasks to show the router in action."""
    print("=" * 60)
    print("STEP 3: Classifying tasks")
    print("=" * 60)

    classifier = TaskClassifier()

    tasks = [
        "Fix the null pointer bug in auth.py",
        "Write a REST API endpoint for user registration",
        "Explain how the caching layer works",
        "Refactor the payment module to use strategy pattern",
        "Architect a distributed event system with Kafka",
    ]

    for task in tasks:
        result = classifier.classify(task)
        print(f"  Task: \"{task}\"")
        print(f"    Type:       {result.task_type.name}")
        print(f"    Complexity: {result.complexity.name}")
        print(f"    Scope:      {result.context_scope.name}")
        print(f"    Latency:    {result.latency.name}")
        print(f"    Est tokens: {result.estimated_tokens}")
        print(f"    Confidence: {result.confidence:.2f}")
        print()


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("ArbiterX — Basic Usage Demo")
    print("─" * 60)
    print()

    # Build the map and query it
    store = demo_build_map()
    demo_query_symbol(store)

    # Classify tasks
    demo_classify_task()

    # Cleanup
    store.close()
    print("Done! ✓")
