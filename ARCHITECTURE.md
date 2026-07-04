# ArbiterX — Architecture

> Engineering discipline for AI code generation.
> Smart routing + 97% token reduction + unbreakable code by default.

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DEVELOPER / IDE                              │
│   (Claude Code, Codex, Cursor, Aider, Copilot, etc.)               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ task + context
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ARBITERX MIDDLEWARE                          │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐     │
│  │ Principles  │  │ Self-Check   │  │ Codebase Map           │     │
│  │ Injection   │→ │ Ladder &     │→ │ Engine                 │     │
│  │ (arbiterxs)    │  │ Enforcer     │  │ (tree-sitter+PageRank) │     │
│  └─────────────┘  └──────┬───────┘  └────────────┬───────────┘     │
│                           │                        │                │
│  ┌────────────────────────┴────────────────────────┴─────────────┐  │
│  │              Task Classifier & Smart Router                    │  │
│  │    (type → complexity → model → token budget → context)       │  │
│  └────────────────────────────────┬──────────────────────────────┘  │
│                                   │                                 │
│  ┌────────────────────────────────┴──────────────────────────────┐  │
│  │                    Model Adapters                              │  │
│  │  Anthropic │ OpenAI │ Google │ Ollama │ OpenRouter │ Plugin   │  │
│  └────────────────────────────────┬──────────────────────────────┘  │
│                                   │                                 │
│  ┌────────────────────────────────┴──────────────────────────────┐  │
│  │              ENGINEERING QUALITY GATE                          │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐   │  │
│  │  │ Security │ │Robustness│ │Efficiency│ │ 10 ArbiterX Score │   │  │
│  │  │ Checker  │ │ Checker  │ │ Checker  │ │ (pass ≥ 70)    │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │
                                   ▼
                    Minimal, Correct, Robust Code
```

## Design Principles

1. **Enforce, don't suggest** — Bad code is rejected, not flagged
2. **Map, don't re-read** — Build once, query forever, update incrementally
3. **Route, don't overspend** — Match task complexity to model capability
4. **Compress, don't truncate** — Send symbols + signatures, not raw files
5. **Validate, don't trust** — Every output passes the quality gate
6. **Log, don't ask** — All decisions auditable, never bother the user

---

## Part 2 — Codebase Mapping Engine

The core value proposition. Builds a persistent, queryable map of any codebase.

### Algorithm (Hybrid: tree-sitter + PageRank + Merkle)

```
                    ┌──────────────────┐
                    │  File Watcher /  │
                    │  Git Hook        │
                    └────────┬─────────┘
                             │ changed files
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   INCREMENTAL INDEXER                      │
│                                                          │
│  1. Merkle-hash each file (SHA256 of content)            │
│  2. Compare against stored hashes in map.db              │
│  3. Only re-parse files whose hash changed               │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Tree-sitter AST Parser                            │  │
│  │  ─────────────────────────────────────────────     │  │
│  │  • Load grammar for file's language                │  │
│  │  • Parse → AST                                     │  │
│  │  • Run .scm queries to extract:                    │  │
│  │    - Definitions (class, function, method, var)    │  │
│  │    - References (calls, imports, type usage)       │  │
│  │    - Signatures (params, return types, docstrings) │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Symbol Graph Builder                              │  │
│  │  ─────────────────────────────────────────────     │  │
│  │  • Nodes = files                                   │  │
│  │  • Edges = file_A references symbol defined in B   │  │
│  │  • Edge weight = f(ref_count, identifier_quality,  │  │
│  │                     recency, user_mentions)        │  │
│  │  • Stored in SQLite (not in-memory NetworkX)       │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │  PageRank Ranker                                   │  │
│  │  ─────────────────────────────────────────────     │  │
│  │  • Personalization: boost files in active context  │  │
│  │  • Damping factor: 0.85 (standard)                 │  │
│  │  • Output: ranked list of (file, symbol) pairs     │  │
│  │  • Binary search to fit token budget               │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    .arbiterx/ STORE                      │
│                                                          │
│  map.db          — SQLite: symbols, files, edges, hashes │
│  embeddings.bin  — FAISS vector index (optional Phase 2) │
│  summaries.md    — Human-readable, git-friendly          │
│  manifest.json   — Version, build metadata               │
└──────────────────────────────────────────────────────────┘
```

### Storage Schema (SQLite — `map.db`)

```sql
CREATE TABLE files (
    id          INTEGER PRIMARY KEY,
    path        TEXT UNIQUE NOT NULL,
    language    TEXT,
    hash        TEXT NOT NULL,          -- SHA256 of content
    size_bytes  INTEGER,
    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE symbols (
    id          INTEGER PRIMARY KEY,
    file_id     INTEGER REFERENCES files(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    kind        TEXT NOT NULL,          -- function, class, method, variable, type
    signature   TEXT,                   -- full signature with params/return type
    docstring   TEXT,                   -- first docstring/comment
    line_start  INTEGER,
    line_end    INTEGER,
    parent_id   INTEGER REFERENCES symbols(id)  -- for nested (method in class)
);

CREATE TABLE edges (
    id          INTEGER PRIMARY KEY,
    src_file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    dst_file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    symbol_name TEXT NOT NULL,
    weight      REAL DEFAULT 1.0,
    ref_count   INTEGER DEFAULT 1
);

CREATE TABLE summaries (
    id          INTEGER PRIMARY KEY,
    scope       TEXT NOT NULL,          -- file, module, or repo
    path        TEXT,                   -- file/dir path (NULL for repo)
    content     TEXT NOT NULL,
    token_count INTEGER,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_symbols_file ON symbols(file_id);
CREATE INDEX idx_edges_src ON edges(src_file_id);
CREATE INDEX idx_edges_dst ON edges(dst_file_id);
CREATE INDEX idx_files_path ON files(path);
```

### Supported Languages (Phase 1)

| Language   | Grammar Source             | Status  |
|-----------|---------------------------|---------|
| Python    | tree-sitter-python         | Core    |
| TypeScript| tree-sitter-typescript     | Core    |
| JavaScript| tree-sitter-javascript     | Core    |
| Go        | tree-sitter-go             | Core    |
| Rust      | tree-sitter-rust           | Core    |
| Java      | tree-sitter-java           | Core    |
| C/C++     | tree-sitter-c/cpp          | Core    |
| Ruby      | tree-sitter-ruby           | Phase 2 |
| C#        | tree-sitter-c-sharp        | Phase 2 |
| PHP       | tree-sitter-php            | Phase 2 |

### Performance Targets

| Metric                    | Target          | How                              |
|--------------------------|-----------------|----------------------------------|
| Initial map build (100k LOC) | < 60s        | Parallel parsing, batch SQLite   |
| Incremental update        | < 2s           | Merkle-hash diff, parse only Δ   |
| Query latency             | < 50ms         | SQLite indexed, in-process       |
| Map size on disk          | < 10MB/100k LOC| Signatures only, no bodies       |

---

## Part 1 — Task Classifier & Model Router

### Classification Pipeline

```
User Task (natural language + file refs)
         │
         ▼
┌─────────────────────────────────────────┐
│         TASK CLASSIFIER                  │
│                                         │
│  Extracts:                              │
│  ├─ task_type: enum (20+ types)         │
│  ├─ complexity: trivial/low/med/hi/exp  │
│  ├─ context_scope: file/module/repo     │
│  ├─ latency: interactive/batch          │
│  └─ estimated_tokens: int               │
│                                         │
│  Method: keyword heuristics + optional  │
│  lightweight classifier (regex → rules  │
│  → small LLM fallback)                  │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│         ROUTING TABLE                    │
│         (arbiterx.toml)               │
│                                         │
│  [[routes]]                             │
│  match = {complexity = "trivial"}       │
│  model = "haiku"                        │
│  fallback = "gpt-4o-mini"              │
│                                         │
│  [[routes]]                             │
│  match = {type = "architecture"}        │
│  model = "opus"                         │
│  fallback = "o1"                        │
│                                         │
│  [[routes]]                             │
│  match = {context_scope = "repo"}       │
│  model = "gemini-2.0-pro"             │
│  fallback = "opus"                      │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│         CONTEXT HANDOFF                  │
│                                         │
│  Serialize:                             │
│  ├─ conversation_history (compressed)   │
│  ├─ active_file_refs → map pointers     │
│  ├─ tool_call_history + results         │
│  ├─ user_intent_stack                   │
│  └─ working_memory (KV store)           │
│                                         │
│  Re-hydrate into target format:         │
│  ├─ Anthropic Messages API              │
│  ├─ OpenAI Chat Completions             │
│  ├─ Google Gemini format                │
│  └─ Ollama /api/chat                    │
└─────────────────────────────────────────┘
```

### Task Types

| Type          | Examples                               | Default Model |
|--------------|----------------------------------------|---------------|
| `rename`      | Rename variable, file, class           | haiku         |
| `format`      | Fix formatting, lint                   | local/haiku   |
| `oneliner`    | One-line fix, typo, config change      | haiku         |
| `bugfix`      | Fix specific bug with stack trace      | sonnet        |
| `refactor`    | Extract method, restructure            | sonnet        |
| `feature`     | New feature implementation             | sonnet        |
| `test`        | Write tests for existing code          | sonnet        |
| `docs`        | Documentation, comments                | haiku         |
| `review`      | Code review, PR feedback               | sonnet        |
| `explain`     | Explain code behavior                  | sonnet        |
| `debug`       | Complex debugging, race conditions     | opus          |
| `architecture`| System design, major refactors         | opus          |
| `security`    | Security audit, vulnerability fix      | opus          |
| `performance` | Optimization, profiling analysis       | opus          |
| `migration`   | Framework/language migration           | opus          |
| `regex`       | Write/explain regex                    | haiku         |
| `sql`         | Write/optimize SQL                     | sonnet        |
| `config`      | Config files, env setup                | haiku         |
| `devops`      | CI/CD, Docker, deployment              | sonnet        |
| `data`        | Data processing, ETL                   | sonnet        |

### Complexity Scoring

```python
def score_complexity(task) -> Complexity:
    signals = {
        "file_count": len(task.referenced_files),
        "symbol_count": len(task.referenced_symbols),
        "cross_module": task.spans_multiple_modules,
        "requires_reasoning": task.has_ambiguity or task.has_constraints,
        "has_tests": task.mentions_testing,
        "estimated_changes": task.estimated_line_changes,
    }
    
    score = weighted_sum(signals)
    
    if score < 2:   return Complexity.TRIVIAL
    if score < 5:   return Complexity.LOW
    if score < 10:  return Complexity.MEDIUM
    if score < 20:  return Complexity.HIGH
    return Complexity.EXPERT
```

---

## Part 3 — Self-Interrogation Ladder

Runs automatically before any code generation. Never prompts the user.
Each step is logged to `.arbiterx/decisions.log` for auditability.

```
┌─────────────────────────────────────────────────────┐
│  SELF-INTERROGATION CASCADE                          │
│  (stop at first "yes" — short-circuit)              │
│                                                     │
│   1. Does this need to exist?        → SKIP (YAGNI)│
│   2. Already in this codebase?       → REUSE       │
│   3. Stdlib does it?                 → USE STDLIB   │
│   4. Native platform feature?        → USE NATIVE  │
│   5. Installed dep does it?          → USE DEP     │
│   6. Well-maintained lib available?  → ADD DEP     │
│   7. Can it be a one-liner?          → ONE LINE    │
│   8. Cached answer from prior run?   → RETURN CACHE│
│   9. Map answers without LLM?        → SKIP LLM   │
│  10. Smaller model handles it?       → DOWNGRADE   │
│  11. Prompt can be shortened?        → COMPRESS    │
│  12. Can batch with pending tasks?   → BATCH       │
│  13. Prompt caching applicable?      → CACHE MARK  │
│  14. Can stream + early-exit?        → STREAM      │
│  15. Write minimum code              → GENERATE    │
│  16. Can any line be deleted?        → DELETE IT   │
└─────────────────────────────────────────────────────┘
```

### Decision Log Format

```json
{
  "timestamp": "2026-07-03T14:30:00Z",
  "task_id": "abc123",
  "ladder_result": {
    "step_reached": 9,
    "reason": "codebase map contains full signature for requested function",
    "action": "SKIP_LLM",
    "tokens_saved": 4200,
    "time_saved_ms": 1800
  }
}
```

---

## Part 4 — Token-Saving Tactics

### Implemented Strategies

| Strategy                    | Reduction | When Applied                    |
|----------------------------|-----------|--------------------------------|
| Symbol-level context        | 80-95%   | Always (core map query)         |
| Semantic diff prompts       | 60-80%   | File modifications              |
| Response caching            | 100%     | Identical prompt+model+temp     |
| Prompt compression          | 30-50%   | Large context windows           |
| Deduplication               | 20-40%   | Repeated imports/boilerplate    |
| Sliding-window summarize    | 50-70%   | Long conversations              |
| Tool-result truncation      | 40-60%   | Large command outputs           |
| Skeleton extraction         | 70-90%   | File overview requests          |

### Context Assembly Pipeline

```
Query: "fix the auth bug in login handler"
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│  1. SYMBOL LOOKUP                                    │
│     map.query("login", "auth") → 3 relevant symbols │
│     (signatures + docstrings only = ~500 tokens)     │
│     vs naive: read 5 full files = ~12,000 tokens    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  2. EXPAND ON DEMAND                                 │
│     If LLM needs more: fetch function body           │
│     Only the specific function, not the whole file   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  3. DIFF MODE                                        │
│     For edits: send unified diff, not full file      │
│     Before: 800 lines × 2 = 1600 lines              │
│     After: 20-line diff                              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  4. CACHE CHECK                                      │
│     Hash(prompt + model + temperature)               │
│     Hit? → return cached response (0 new tokens)     │
└─────────────────────────────────────────────────────┘
```

---

## CLI Interface

```
arbiterx init          Initialize .arbiterx/ in current repo
arbiterx map           Build/update the codebase map
arbiterx map --status  Show map freshness and coverage
arbiterx route <task>  Classify task and show routing decision
arbiterx chat          Interactive session with smart routing
arbiterx stats         Token savings dashboard
arbiterx query <sym>   Query the map for a symbol
```

---

## Configuration (`arbiterx.toml`)

```toml
[project]
name = "my-project"
languages = ["python", "typescript", "go"]
exclude = ["node_modules", "dist", ".git", "__pycache__", "*.min.js"]

[map]
store_dir = ".arbiterx"
max_file_size_kb = 500
parallel_workers = 4
watch = true                    # fs-watcher for auto-update

[router]
default_model = "sonnet"
cost_budget_daily = 5.00        # USD
latency_mode = "interactive"    # or "batch"

[[router.rules]]
match = { complexity = "trivial" }
model = "haiku"
fallback = "gpt-4o-mini"

[[router.rules]]
match = { complexity = "expert", type = ["architecture", "security"] }
model = "opus"
fallback = "o1"

[[router.rules]]
match = { context_scope = "repo" }
model = "gemini-2.0-pro"
fallback = "opus"

[models.anthropic]
api_key_env = "ANTHROPIC_API_KEY"

[models.openai]
api_key_env = "OPENAI_API_KEY"

[models.ollama]
base_url = "http://localhost:11434"
default_model = "qwen2.5-coder:7b"

[models.openrouter]
api_key_env = "OPENROUTER_API_KEY"

[cache]
enabled = true
ttl_hours = 24
max_size_mb = 100

[telemetry]
enabled = false                 # zero telemetry by default
```

---

## Project Structure

```
arbiterx/
├── .agents/                    # Agent instruction files
├── .github/workflows/          # CI configuration
├── assets/                     # Images, diagrams
├── benchmarks/                 # Token reduction benchmark suite
├── commands/                   # CLI command implementations
├── docs/                       # Extended documentation
├── examples/                   # Usage examples
├── hooks/                      # Git hooks for auto-update
├── scripts/                    # Build/release scripts
├── skills/                     # Agent skill definitions
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── src/
│   └── arbiterx/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI entry point
│       ├── mapper/
│       │   ├── __init__.py
│       │   ├── parser.py       # Tree-sitter AST parsing
│       │   ├── graph.py        # Symbol graph + PageRank
│       │   ├── hasher.py       # Merkle-tree file hashing
│       │   ├── store.py        # SQLite storage layer
│       │   ├── indexer.py      # Orchestrates incremental indexing
│       │   └── languages.py    # Language detection + grammar loading
│       ├── router/
│       │   ├── __init__.py
│       │   ├── classifier.py   # Task type + complexity scoring
│       │   ├── table.py        # Declarative routing rules
│       │   └── handoff.py      # Context serialization for model switch
│       ├── context/
│       │   ├── __init__.py
│       │   ├── assembler.py    # Token-budget-aware context building
│       │   ├── compressor.py   # Prompt compression
│       │   └── cache.py        # Response caching layer
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract adapter interface
│       │   ├── anthropic.py
│       │   ├── openai.py
│       │   ├── google.py
│       │   ├── ollama.py
│       │   └── openrouter.py
│       ├── ladder/
│       │   ├── __init__.py
│       │   └── interrogator.py # Self-interrogation cascade
│       └── plugins/
│           ├── __init__.py
│           └── loader.py       # Plugin discovery + loading
├── ARCHITECTURE.md
├── README.md
├── LICENSE
├── pyproject.toml
├── arbiterx.toml.example
└── .gitignore
```

---

## Technology Choices

| Component        | Choice                    | Justification                                     |
|-----------------|---------------------------|---------------------------------------------------|
| Language         | Python 3.11+              | Best tree-sitter bindings, ML ecosystem, Aider-proven |
| AST Parsing      | py-tree-sitter + language-pack | First-class, all grammars pre-built          |
| Graph/PageRank   | NetworkX (compute) → SQLite (store) | Compute in memory, persist to disk    |
| Storage          | SQLite (via sqlite3 stdlib) | Zero-dep, fast, single-file, battle-tested     |
| CLI              | Typer                     | Modern, type-safe, auto-generated help            |
| Config           | TOML (tomllib stdlib)     | Human-readable, well-supported                    |
| Async            | asyncio + aiofiles        | Concurrent file I/O for indexing                  |
| HTTP             | httpx                     | Async-first, modern Python HTTP                   |
| Embeddings       | FAISS (optional)          | Phase 2, only if user opts in                     |
| Hashing          | hashlib (stdlib)          | SHA256, zero dependencies                         |
| Testing          | pytest + pytest-asyncio   | Standard, fast, good fixtures                     |

---

## License

Apache-2.0

---

## Part 5 — Engineering Quality Gate (NEW)

Every piece of AI-generated code passes through this gate BEFORE being shown to the user.

```
Generated Code
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│              ENGINEERING QUALITY GATE                         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. SYNTAX CHECK (tree-sitter parse)                  │  │
│  │     → Rejects syntactically invalid code              │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  2. SECURITY CHECK                                    │  │
│  │     → Hardcoded keys (sk-..., AKIA..., ghp_...)       │  │
│  │     → SQL injection (string formatting in queries)    │  │
│  │     → eval/exec, subprocess shell=True                │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  3. ROBUSTNESS CHECK                                  │  │
│  │     → File ops without try/except or context mgr      │  │
│  │     → Network calls without timeouts                  │  │
│  │     → Bare except clauses                             │  │
│  │     → Missing transaction handling                    │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  4. EFFICIENCY CHECK                                  │  │
│  │     → String concat in loops (suggest join)           │  │
│  │     → O(n²) nested loops over same collection         │  │
│  │     → Unnecessary list() on generators                │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  5. ARBITERX SCORE (0-100)                             │  │
│  │     → 10 engineering arbiterxs scored independently      │  │
│  │     → Each violation reduces score                    │  │
│  │     → Pass threshold: 70/100 (configurable)           │  │
│  │     → Failed code gets regenerated with feedback      │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  6. AUTO-FIX (optional)                               │  │
│  │     → Remove TODO/FIXME comments                      │  │
│  │     → Add missing error handling wrappers             │  │
│  │     → Remove unused imports                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
  Score ≥ 70? → PASS → output to user
  Score < 70? → FAIL → regenerate with violation feedback
```

### The 10 Engineering ArbiterXs

| ArbiterX | Severity | What It Checks |
|-------|----------|----------------|
| YAGNI | error | Premature abstractions, ABC classes without need |
| ERROR_HANDLING | error | Unprotected I/O, network, file, subprocess ops |
| TYPE_SAFETY | warning | Missing param/return type annotations |
| RESOURCE_CLEANUP | error | open() without context manager |
| NO_MAGIC_NUMBERS | warning | Inline numeric literals > 1 |
| NO_DEAD_CODE | warning | Commented code, unused imports |
| SINGLE_RESPONSIBILITY | warning | Functions > 30 lines |
| FAIL_FAST | info | Validation logic > 10 lines into function |
| IDEMPOTENCY | info | Non-retryable patterns (INSERT, send_mail) |
| PERFORMANCE | warning | O(n²) patterns, string += in loops |

---

## Part 6 — Principles Injection

Every LLM call includes an engineering preamble:

```
You are an engineering-disciplined code generator. Before writing any code:
1. Use stdlib/builtins before dependencies
2. Handle every error path — no bare try/except, no swallowed errors
3. Type all function signatures
4. One function = one responsibility (max 30 lines)
5. No magic numbers — name your constants
6. Validate inputs at function entry
7. Close every resource you open
8. Prefer immutable data structures
9. Never generate code with TODO/FIXME — finish it or don't write it
10. Delete any line that doesn't change behavior
```

Modes: `lite` (5 rules), `full` (10 rules), `strict` (all + anti-patterns)

Language-specific additions are injected per target language.
