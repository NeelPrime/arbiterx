# How ArbiterX Works — Deep Dive

A technical explanation of how ArbiterX reduces tokens, routes models, scores code, and integrates with AI tools.

---

## Table of Contents

- [How Token Reduction Works](#how-token-reduction-works)
- [How It Works in a Monorepo](#how-it-works-in-a-monorepo)
- [How the Plugin System Works](#how-the-plugin-system-works)
- [How Incremental Indexing Works](#how-incremental-indexing-works)
- [How Parallel Indexing Works](#how-parallel-indexing-works)
- [How Context Saving Will Work](#how-context-saving-will-work)
- [How the AI Knows What to Read](#how-the-ai-knows-what-to-read)

---

## How Token Reduction Works

### The Problem

When you ask your AI "fix the login bug", it needs to understand your codebase. Without ArbiterX:

```
AI reads entire files:
  auth.py          → 500 lines (2,000 tokens)
  user_model.py    → 300 lines (1,200 tokens)
  database.py      → 400 lines (1,600 tokens)
  routes.py        → 600 lines (2,400 tokens)
  middleware.py    → 200 lines (800 tokens)
  ... 35 more files → 160,000 tokens

Total sent to AI: ~168,000 tokens 💸
```

Most of that is irrelevant — the AI didn't need to see your payment code to fix a login bug.

### The Solution

ArbiterX builds a **map** of your codebase — just function names, signatures, and relationships. Like a table of contents instead of the full book.

```bash
$ arbiterx map

Indexed 40 files → 1,364 symbols → stored in SQLite
```

Now when you ask "fix the login bug", ArbiterX queries the map and sends ONLY:

```python
# auth.py
def authenticate(username: str, password: str) -> Optional[User]: ...
def verify_token(token: str) -> bool: ...
def hash_password(raw: str) -> str: ...

# user_model.py
class User(id: int, username: str, email: str, password_hash: str): ...
def get_user_by_username(username: str) -> Optional[User]: ...

# middleware.py
def require_auth(request: Request) -> User: ...
```

**Total sent to AI: ~400 tokens** ✅ (99.7% reduction)

### How It Builds the Map

1. **tree-sitter** parses every file into an AST (Abstract Syntax Tree)
2. Extracts every function, class, interface — just the **signature**, not the body
3. **PageRank** ranks which symbols are most important (most referenced = most important)
4. Stores everything in SQLite (`.arbiterx/map.db`)
5. When you ask a question, ArbiterX matches keywords to relevant symbols
6. Sends only those signatures to the AI

### The Math

| Scenario | Without ArbiterX | With ArbiterX | Saved |
|----------|-----------------|---------------|-------|
| Small project (40 files) | 196K tokens | 5K tokens | 97% |
| Medium project (150 files) | 500K tokens | 8K tokens | 98% |
| Monorepo (300 files) | 800K+ tokens | 12K tokens | 98.5% |

At $3/million tokens (Claude Sonnet), a monorepo query costs:
- Without: $2.40 per query
- With ArbiterX: $0.04 per query (60x cheaper)

---

## How It Works in a Monorepo

### Example Structure

```
/enterprise-monorepo
├── backend/
│   ├── UserService/        (C#, 50 files)
│   ├── OrderService/       (C#, 40 files)
│   └── PaymentService/     (C#, 35 files)
├── frontend/
│   ├── angular-app/        (TypeScript, 80 files)
│   └── react-dashboard/    (JSX, 30 files)
├── services/
│   ├── ml-pipeline/        (Python, 20 files)
│   └── go-gateway/         (Go, 15 files)
└── legacy-api/             (PHP, 25 files)
```

### What ArbiterX Does

```bash
$ arbiterx map
  Files: 295
  Symbols: 4,200
  Time: 0.8s
```

You ask: "Add a discount field to OrderService"

ArbiterX knows from the map that only these symbols matter:

```csharp
// OrderService/Controllers/OrderController.cs
class OrderController : GetAll(), GetById(int id), Create(OrderDto data)

// OrderService/Models/Order.cs
class Order(id, userId, items, total, createdAt)

// OrderService/Services/PricingService.cs
class PricingService : CalculateTotal(List<Item> items) -> decimal
```

**Sent to AI: ~600 tokens** instead of 800,000.

### What Gets Skipped Automatically

ArbiterX skips 60+ directories of non-source files:

| Ecosystem | Skipped Directories |
|-----------|-------------------|
| .NET/C# | `bin/`, `obj/` |
| PHP | `vendor/` |
| JavaScript | `node_modules/`, `bower_components/`, `.next/` |
| Python | `__pycache__/`, `.venv/`, `.eggs/` |
| Rust | `target/`, `.cargo/` |
| Go | (builds in-place, no skip needed) |
| Java | `.gradle/` |
| Swift/iOS | `Pods/`, `DerivedData/` |
| IDEs | `.idea/`, `.vs/`, `.vscode/` |
| All | `dist/`, `build/`, `coverage/`, `tmp/`, `logs/` |

Only actual source code gets indexed.

---

## How the Plugin System Works

### Two Ways to Install

**Full install (quality gate active):**
```bash
pip install arbiterx-gate
/plugin install NeelPrime/arbiterx
```

**Direct plugin (rules only, no pip):**
```bash
/plugin marketplace add NeelPrime/arbiterx
/plugin install arbiterx@arbiterx-marketplace
```

### What the Plugin Does

The plugin injects three things into your AI tool:

1. **Skills** (always-on rules) — The 10 engineering rules are prepended to every prompt
2. **Hooks** — Lifecycle events that run ArbiterX CLI commands:
   - `SessionStart` → checks if arbiterx is installed
   - `PostToolUse` → runs `arbiterx gate --file` on every file the AI writes
   - `Stop` → reminds to check quality before committing
3. **Quality gate** (requires pip install) — Actively scores code 0-100

### With vs Without pip install

| Feature | Plugin only | Plugin + pip install |
|---------|------------|---------------------|
| 10 engineering rules in prompt | ✅ | ✅ |
| AI follows discipline | ✅ | ✅ |
| Active quality gate scoring | ❌ | ✅ |
| Codebase map (token reduction) | ❌ | ✅ |
| Smart model routing | ❌ | ✅ |

---

## How Incremental Indexing Works

### The Problem

Without incremental indexing:
```bash
$ arbiterx map        # First run: indexes 300 files (3s)
# Edit 2 files...
$ arbiterx map        # Re-indexes ALL 300 files (3s) — wasteful
```

### The Solution

ArbiterX stores a content hash for each file. On subsequent runs:

```bash
$ arbiterx map        # First run: indexes 300 files (3s)
# Edit 2 files...
$ arbiterx map        # Checks hashes: skips 298, re-indexes 2 (0.1s)
```

### How It Works

```
For each file:
  1. Compute SHA-256 hash of content
  2. Compare to hash stored in database
  3. Same hash? → skip (already indexed correctly)
  4. Different hash? → re-parse, update symbols and edges
  5. File deleted? → remove from database
  6. New file? → parse and add
```

### Crash Recovery

If `arbiterx map` crashes at file 150/300:
```bash
$ arbiterx map        # Resumes: skips 150 already-indexed, processes remaining 150
```

No checkpoint file needed — the hash-based skip gives crash recovery for free.

### CLI

```bash
arbiterx map            # Incremental (default)
arbiterx map --force    # Full re-index (ignore hashes)
```

---

## How Parallel Indexing Works

### The Problem

For very large monorepos (100K+ files), single-threaded indexing is slow:
- 1M files × 5ms/file = 83 minutes

### The Solution

```bash
arbiterx map --workers 8      # Use 8 CPU cores
arbiterx map --workers 0      # Auto-detect cores
```

### Architecture

```
┌──────────────────────────────────────────┐
│  COORDINATOR (main process)              │
│  1. Scan all files                       │
│  2. Check hashes (incremental skip)      │
│  3. Split remaining into chunks          │
│  4. Distribute to workers                │
│  5. Merge results into SQLite            │
└──────────┬───────────────────────────────┘
           │
    ┌──────┼──────┬──────────┐
    ▼      ▼      ▼          ▼
 Worker1  Worker2  Worker3  Worker4
   │        │        │        │
   ▼        ▼        ▼        ▼
 parse    parse    parse    parse
   │        │        │        │
   └────────┴────────┴────────┘
           │
           ▼
    SQLite (single writer)
```

### Key Design Decisions

- **Each worker gets its own TreeSitterParser** — no shared state during parsing
- **Single writer for SQLite** — coordinator serializes all DB writes (no locking issues)
- **Only activates for 100+ files** — overhead not worth it for small repos
- **Incremental + parallel** — hash check is single-threaded (fast), only parsing is parallelized

### Performance

| Files | Single-thread | 8 workers |
|-------|--------------|-----------|
| 10K | 50s | 8s |
| 100K | 8 min | 1.5 min |
| 1M | 83 min | 12 min |

---

## How Context Saving Will Work

> ⚠️ This feature is planned (see [Issue #8](https://github.com/NeelPrime/arbiterx/issues/8))

### The Problem

Today, every time you ask about the same feature, the AI re-reads the codebase:

```
Day 1: "How does payment retry work?"  → AI reads map (5K tokens)
Day 2: "Add max retry limit"           → AI reads map again (5K tokens)
Day 3: "Fix retry timeout bug"         → AI reads map again (5K tokens)
```

### The Solution

After the first explanation, ArbiterX saves it:

```
Day 1: "How does payment retry work?"  → AI reads map (5K tokens)
        → ArbiterX SAVES the explanation to .arbiterx/context/payment-retry.md

Day 2: "Add max retry limit"           → Loads saved context (600 tokens)
Day 3: "Fix retry timeout bug"         → Loads saved context (600 tokens)
```

### Storage

```
.arbiterx/
├── map.db                    (symbols — existing)
└── context/
    ├── payment-retry.md      (saved feature understanding)
    ├── auth-flow.md
    └── database-pool.md
```

### Invalidation

When relevant source files change (detected via content hash):
- Saved context is marked stale
- Next query regenerates it from updated code

---

## How the AI Knows What to Read

**It doesn't.** The AI never decides what to read. ArbiterX decides and injects the right context before the AI sees anything.

### The Flow

```
┌─────────────────────────────────────┐
│  YOU                                │
│  "Add max retry to payment flow"    │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  ARBITERX (runs first via hooks)    │
│                                     │
│  1. Extract keywords from prompt    │
│     → ["retry", "payment"]          │
│  2. Check saved contexts            │
│     → Found: payment-retry.md       │
│  3. Query symbol map                │
│     → PaymentService, RetryHandler  │
│  4. Build context package           │
│     → saved note + symbols          │
│  5. Inject into AI prompt           │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  AI RECEIVES:                       │
│                                     │
│  [Context from ArbiterX - 600 tok]  │
│  PaymentService.charge() calls      │
│  StripeClient with retry in         │
│  RetryHandler.execute(). Max set    │
│  by PAYMENT_MAX_RETRIES in config.  │
│                                     │
│  [Your question]                    │
│  "Add max retry to payment flow"    │
│                                     │
│  AI works with 600 tokens total.    │
│  Never reads 50 files.              │
│  Doesn't know ArbiterX exists.      │
└─────────────────────────────────────┘
```

### Analogy

| Without ArbiterX | With ArbiterX |
|-----------------|---------------|
| Hand someone a 500-page book and say "answer my question" | Hand them a 2-page summary and say "answer my question" |

The AI never chose the summary. ArbiterX gave it the summary instead of the book. The AI doesn't know the book exists.

### This is the Same Pattern as Existing Hooks

```json
// hooks.json — runs automatically, AI doesn't decide
{
  "SessionStart": "inject engineering rules",
  "PostToolUse": "run quality gate on written file",
  "BeforePrompt": "inject relevant context from map + saved notes"
}
```

The quality gate doesn't ask the AI "should I check your code?" — it just runs. Context injection works the same way.
