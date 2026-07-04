<p align="center">
  <img src="assets/arbiterx-logo.svg" alt="ArbiterX Logo" width="120" />
</p>

<h1 align="center">ArbiterX</h1>

<p align="center">
  <strong>Your AI writes code. ArbiterX decides if it's good enough.</strong>
</p>

<p align="center">
  <em>The intelligent middleware that makes AI coding assistants write like senior engineers — minimal, robust, unbreakable.</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square" alt="License"></a>
  <a href="https://pypi.org/project/arbiterx-gate/"><img src="https://img.shields.io/badge/pypi-arbiterx--gate-orange?style=flat-square" alt="PyPI"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square" alt="Python"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/tests-109%20passing-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="#benchmarks"><img src="https://img.shields.io/badge/token%20savings-97%25-purple?style=flat-square" alt="Token Savings"></a>
  <a href="#"><img src="https://img.shields.io/badge/works%20with-10%2B%20AI%20tools-black?style=flat-square" alt="Integrations"></a>
</p>

<p align="center">
  <a href="#install">Install</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#examples">Examples</a> •
  <a href="#integrations">Integrations</a> •
  <a href="docs/GUIDE.md">Full Guide</a>
</p>

---

<br>

## 💀 The Problem

Your AI assistant just wrote this:

```python
def get_user(id):
    try:
        conn = psycopg2.connect("postgresql://admin:password123@localhost/db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = " + str(id))
        return cursor.fetchone()
    except:
        return None
```

**5 security vulnerabilities. 3 resource leaks. 0 type hints. Your code review just got longer.**

---

## ✅ The Fix

With ArbiterX active, the AI writes this instead:

```python
from typing import Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    id: int
    name: str
    email: str

def get_user(user_id: int, conn: Connection) -> Optional[User]:
    """Fetch a user by ID. Returns None if not found."""
    row = conn.execute(
        "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return User(**row._asdict()) if row else None
```

**Typed. Parameterized. No hardcoded secrets. No resource leak. Ships on first review.**

---

<br>

## 🏗️ What ArbiterX Does

```
┌────────────────────────────────────────────────────────────────┐
│                       YOUR AI TOOL                             │
│  Claude Code • Codex • Cursor • Copilot • Aider • Windsurf   │
└───────────────────────────────┬────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────┐
│                         ARBITERX                               │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ ① DECIDE     │  │ ② COMPRESS   │  │ ③ ENFORCE            │ │
│  │              │  │              │  │                      │ │
│  │ Route to     │  │ Send 2KB     │  │ Score output 0-100   │ │
│  │ right model  │  │ not 200KB    │  │ Reject if below 70   │ │
│  │              │  │              │  │                      │ │
│  │ trivial→     │  │ symbols +    │  │ ✓ security           │ │
│  │   haiku      │  │ signatures   │  │ ✓ robustness         │ │
│  │ hard→opus    │  │ only         │  │ ✓ efficiency         │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                  Clean, Minimal, Unbreakable Code
```

---

<br>

## 📊 Numbers That Matter

<table>
<tr>
<td align="center"><strong>97.1%</strong><br><sub>Token Reduction</sub></td>
<td align="center"><strong>0.25s</strong><br><sub>Map Build Time</sub></td>
<td align="center"><strong>0.5ms</strong><br><sub>Query Latency</sub></td>
<td align="center"><strong>109</strong><br><sub>Tests Passing</sub></td>
</tr>
<tr>
<td align="center"><strong>10</strong><br><sub>Engineering Rules</sub></td>
<td align="center"><strong>6</strong><br><sub>Quality Checks</sub></td>
<td align="center"><strong>22</strong><br><sub>Languages</sub></td>
<td align="center"><strong>5</strong><br><sub>LLM Providers</sub></td>
</tr>
</table>

> **196,247 tokens → 5,639 tokens.** That's what your AI actually needs to see.

---

<br>

<a name="install"></a>
## 📦 Install

```bash
pip install arbiterx-gate
```

**Using Python 3 specifically:**

```bash
pip3 install arbiterx-gate
```

**Permission issues? Install for your user:**

```bash
pip install --user arbiterx-gate
```

**In a virtual environment (recommended):**

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install arbiterx-gate
```

**From source:**

```bash
git clone https://github.com/NeelPrime/arbiterx.git
cd arbiterx
pip install -e .
```

**Verify:**

```bash
arbiterx --version
# arbiterx 0.2.0
```

> **Requirements:** Python 3.9+ · No system dependencies · Works offline for local models

---

<br>

<a name="quick-start"></a>
## 🚀 Quick Start

```bash
# Install
pip install arbiterx-gate

# Set up (once per project)
arbiterx init
arbiterx map            # Index your codebase (30 seconds)

# Use
arbiterx route "task"   # See how any task gets classified
arbiterx query Symbol   # Find any function instantly
arbiterx gate --file main.py  # Score any file 0-100
```

**That's it. You're running.**

**Using with an AI tool?** After `pip install arbiterx-gate`:
```bash
# Claude Code
/plugin install NeelPrime/arbiterx

# Codex CLI
codex plugin install NeelPrime/arbiterx
```

<p align="center">
  <img src="assets/demo.svg" alt="ArbiterX terminal demo" width="700" />
  <br>
  <sub>↑ <code>pip install arbiterx-gate && arbiterx init && arbiterx map</code></sub>
</p>

---

<br>

<a name="how-it-works"></a>
## ⚙️ How It Works

### 1. Codebase Map (the 97% saver)

ArbiterX parses your code with [tree-sitter](https://tree-sitter.github.io/), builds a graph of every function/class/import, ranks them with PageRank, and stores it in SQLite.

When the AI needs context, it queries the map:
- ❌ **Without ArbiterX:** Read 40 files → 200,000 tokens
- ✅ **With ArbiterX:** Query relevant signatures → 5,000 tokens

### 2. Smart Router (the cost saver)

Every task gets classified:

| Task | Type | Model |
|------|------|-------|
| "rename this variable" | TRIVIAL | Haiku / GPT-4o-mini |
| "fix the auth bug" | DEBUGGING | Sonnet / GPT-4o |
| "redesign the caching layer" | ARCHITECTURE | Opus / o1 |

### 3. Quality Gate (the code saver)

Every AI output gets scored:

```
┌───────────────────────────────────────────┐
│  QUALITY GATE                             │
│                                           │
│  Security ·····  ✓ No hardcoded secrets   │
│  Robustness ···  ✓ Errors handled         │
│  Efficiency ···  ✓ No O(n²) patterns      │
│  Types ········  ✓ All functions typed     │
│  Style ········  ✓ Clean naming           │
│  Complete ·····  ✓ No TODOs left          │
│                                           │
│  Score: 100/100  ✓ PASSED                 │
└───────────────────────────────────────────┘
```

---

<br>

## 🛡️ The 10 Engineering Rules

> *These run on every piece of generated code. No exceptions.*

| # | Rule | What Gets Rejected |
|---|------|-------------------|
| 1 | **YAGNI** | Building features nobody asked for |
| 2 | **Error Handling** | `open("file")` without try/except |
| 3 | **Type Safety** | `def process(x, y):` with no types |
| 4 | **Resource Cleanup** | `f = open(...)` without `with` |
| 5 | **No Magic Numbers** | `if retries > 3:` → name it |
| 6 | **No Dead Code** | Commented-out code, unused imports |
| 7 | **Single Responsibility** | 50-line functions that do 3 things |
| 8 | **Fail Fast** | Validating inputs on line 47 |
| 9 | **Idempotency** | Unsafe-to-retry operations |
| 10 | **Performance** | Nested loops when unnecessary |

---

<br>

<a name="examples"></a>
## 🎬 Real-World Examples

### Example 1: Using with Claude Code

Install the package and plugin, then start coding. ArbiterX scores all generated code automatically.

```
> pip install arbiterx-gate
> /plugin install NeelPrime/arbiterx

✓ ArbiterX installed. Engineering mode active.
✓ Quality gate will score all generated code.

> Build a REST endpoint to create users

Claude (with ArbiterX active):
```

```python
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

router = APIRouter()

class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    request: CreateUserRequest,
    db: Annotated[Database, Depends(get_db)],
) -> UserResponse:
    """Create a new user. Returns 409 if email already exists."""
    existing = await db.execute(
        "SELECT id FROM users WHERE email = ?", (request.email,)
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    result = await db.execute(
        "INSERT INTO users (name, email) VALUES (?, ?) RETURNING id",
        (request.name, request.email),
    )
    user_id = result.fetchone()["id"]
    return UserResponse(id=user_id, name=request.name, email=request.email)
```

> **What ArbiterX enforced:** Typed params ✓ | Parameterized SQL ✓ | Proper HTTP codes ✓ | No magic strings ✓ | Validation via Pydantic ✓ | Error case handled ✓

---

### Example 2: Using with Codex CLI

```
> pip install arbiterx-gate
> codex plugin install NeelPrime/arbiterx
> codex

You: Write a file downloader with retry logic

Codex (with ArbiterX active):
```

```python
from pathlib import Path
from typing import Optional
import httpx

MAX_RETRIES = 3
DOWNLOAD_TIMEOUT = 30
CHUNK_SIZE = 8192

class DownloadError(Exception):
    """Raised when a download fails after all retries."""

def download_file(
    url: str,
    destination: Path,
    retries: int = MAX_RETRIES,
) -> Path:
    """Download a file with retry logic. Returns the saved path."""
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL scheme: {url}")

    last_error: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            with httpx.stream("GET", url, timeout=DOWNLOAD_TIMEOUT) as response:
                response.raise_for_status()
                with open(destination, "wb") as out_file:
                    for chunk in response.iter_bytes(CHUNK_SIZE):
                        out_file.write(chunk)
            return destination
        except httpx.HTTPError as err:
            last_error = err
            if attempt == retries:
                break

    raise DownloadError(
        f"Failed after {retries} attempts: {last_error}"
    ) from last_error
```

> **What ArbiterX enforced:** Named constants ✓ | Type hints ✓ | Input validation (fail fast) ✓ | Error handling with retries ✓ | Context manager for file ✓ | Custom exception ✓ | No bare except ✓

---

### Example 3: Using with Cursor (Rules File)

Drop `.cursor/rules/arbiterx.mdc` into your project. Now every Cursor generation follows the rules.

```
You (in Cursor): Add caching to the database queries

Cursor (with ArbiterX rules):
```

```python
from functools import lru_cache
from typing import Optional
from dataclasses import dataclass
from time import monotonic

CACHE_TTL_SECONDS = 300
MAX_CACHE_SIZE = 128

@dataclass(frozen=True)
class CacheEntry:
    value: object
    expires_at: float

class QueryCache:
    """Simple TTL cache for database query results."""

    def __init__(self, ttl: int = CACHE_TTL_SECONDS, max_size: int = MAX_CACHE_SIZE) -> None:
        self._store: dict[str, CacheEntry] = {}
        self._ttl = ttl
        self._max_size = max_size

    def get(self, key: str) -> Optional[object]:
        """Get a cached value. Returns None if missing or expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if monotonic() > entry.expires_at:
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: object) -> None:
        """Store a value with TTL. Evicts oldest if at capacity."""
        if len(self._store) >= self._max_size:
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]
        self._store[key] = CacheEntry(value=value, expires_at=monotonic() + self._ttl)
```

> **What ArbiterX enforced:** Frozen dataclass (immutable) ✓ | Named constants ✓ | Typed everything ✓ | Docstrings ✓ | Single responsibility ✓ | No over-engineering (stdlib only) ✓

---

### Example 4: Checking code with the Python API

```python
from arbiterx.gate import QualityGate
from arbiterx.ladder.interrogator import SelfInterrogator

# Check any code snippet
gate = QualityGate()
enforcer = SelfInterrogator()

code = """
def send_email(to, subject, body):
    import smtplib
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.login('admin@company.com', 'password123')
    server.sendmail('admin@company.com', to, body)
"""

# Quality Gate
result = gate.validate(code, "python")
print(f"Score: {result.score}/100")  # 25/100
print(f"Passed: {result.passed}")    # False

for issue in result.issues:
    print(f"  ❌ [{issue.severity}] {issue.message}")

# Output:
#   ❌ [high] Hardcoded password detected
#   ❌ [medium] No error handling for network operation
#   ❌ [low] Single-letter variable names
```

**The fix (what ArbiterX would guide the AI to write):**

```python
import smtplib
import os
from typing import Optional
from dataclasses import dataclass

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

@dataclass(frozen=True)
class EmailConfig:
    host: str = SMTP_HOST
    port: int = SMTP_PORT
    username: str = ""
    password: str = ""

def send_email(
    recipient: str,
    subject: str,
    body: str,
    config: Optional[EmailConfig] = None,
) -> bool:
    """Send an email. Returns True on success, False on failure."""
    if config is None:
        config = EmailConfig(
            username=os.environ.get("SMTP_USER", ""),
            password=os.environ.get("SMTP_PASS", ""),
        )

    if not config.username or not config.password:
        raise ValueError("SMTP credentials not configured")

    try:
        with smtplib.SMTP(config.host, config.port) as server:
            server.starttls()
            server.login(config.username, config.password)
            server.sendmail(config.username, recipient, body)
        return True
    except smtplib.SMTPException as err:
        raise RuntimeError(f"Failed to send email: {err}") from err
```

> **Score: 100/100 ✓** — Secrets from env ✓ | Context manager ✓ | Error handling ✓ | Typed ✓ | Named constants ✓ | Input validation ✓

---

### Example 5: Using the routing decision

```bash
$ arbiterx route "rename the getUserName function to getUsername"

  Task           rename the getUserName function to getUsername
  Type           REFACTORING
  Complexity     TRIVIAL
  Context Scope  FILE
  Latency        INTERACTIVE
  Est. Tokens    50
  → Model:       haiku (cheapest — this is a trivial rename)

$ arbiterx route "redesign the authentication system to support OAuth2 and SAML"

  Task           redesign the authentication system to support OAuth2 and SAML
  Type           ARCHITECTURE
  Complexity     EXPERT
  Context Scope  REPO
  Latency        BATCH
  Est. Tokens    4000
  → Model:       opus (needs deep reasoning across the whole repo)
```

---

<br>

<a name="integrations"></a>
## 🔌 Integrations

### Plugin Install (recommended)

| Tool | Install |
|------|---------|
| **Claude Code** | `pip install arbiterx-gate` then `/plugin install NeelPrime/arbiterx` |
| **Codex CLI** | `pip install arbiterx-gate` then `codex plugin install NeelPrime/arbiterx` |

> **Why two steps?** The plugin injects engineering rules. The pip package provides the quality gate that actively scores and rejects bad code.

### Direct Plugin (no pip, rules only)

Don't want to install anything? Add the marketplace directly in Claude Code:

```bash
/plugin marketplace add NeelPrime/arbiterx
/plugin install arbiterx@arbiterx-marketplace
```

This gives you the 10 engineering rules in your prompt — no quality gate scoring, but your AI will still follow the discipline.

### Copy a File (prompt-only, no quality gate)

| Tool | File to Copy |
|------|-------------|
| **Cursor** | `.cursor/rules/arbiterx.mdc` |
| **Windsurf** | `.windsurf/rules/arbiterx.md` |
| **GitHub Copilot** | `.github/copilot-instructions.md` |
| **Aider** | `AGENTS.md` |
| **Kiro** | `.kiro/steering/arbiterx.md` |
| **Zed** | `.zed/assistant/rules.md` |
| **Any tool** | `AGENTS.md` (universal) |

### As a Git Hook

```bash
pip install arbiterx-gate  # required
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
# Now rejects commits scoring below 70/100
```

📖 **[Full integration guide →](docs/INTEGRATIONS.md)**

---

<br>

<a name="benchmarks"></a>
## 📈 Benchmarks

Tested on 10 real queries against its own codebase (46 files, 1364 symbols):

| Query | Naive (full files) | ArbiterX (map) | Saved |
|-------|-------------------|----------------|-------|
| "How does TaskClassifier work?" | 9,938 | 600 | **94%** |
| "Fix bug in file hasher" | 35,581 | 1,062 | **97%** |
| "Add new adapter for Mistral" | 14,263 | 643 | **95%** |
| "How is PageRank used?" | 45,300 | 1,034 | **97%** |
| **Total (10 queries)** | **196,247** | **5,639** | **97.1%** |

---

<br>

## 🧰 Supported Languages (22)

| Language | Status | Language | Status | Language | Status |
|----------|--------|----------|--------|----------|--------|
| Python | ✅ | TypeScript | ✅ | JavaScript | ✅ |
| Go | ✅ | Rust | ✅ | Java | ✅ |
| C / C++ | ✅ | C# | ✅ | Ruby | ✅ |
| PHP | ✅ | Swift | ✅ | Kotlin | ✅ |
| Scala | ✅ | Elixir | ✅ | Haskell | ✅ |
| OCaml | ✅ | Lua | ✅ | Zig | ✅ |
| Bash | ✅ | JSX | ✅ | TSX | ✅ |

---

<br>

## 🤝 LLM Providers

| Provider | Models | Local? |
|----------|--------|--------|
| Anthropic | Claude Opus, Sonnet, Haiku | No |
| OpenAI | GPT-4o, o1, o3 | No |
| Google | Gemini 2.0 Pro/Flash | No |
| Ollama | Any model (Qwen, Llama, Mistral) | **Yes** |
| OpenRouter | All models (unified) | No |

---

<br>

## 💬 FAQ

<details>
<summary><strong>Does it slow down my workflow?</strong></summary>

No. Map builds in <1 second. Queries take 0.5ms. The quality gate runs regex — no LLM calls.
</details>

<details>
<summary><strong>Does it work offline?</strong></summary>

Yes. The map, router, and quality gate all run locally. Only the LLM adapters need internet (use Ollama for fully offline).
</details>

<details>
<summary><strong>What if my code fails the gate?</strong></summary>

You get a score and specific issues with suggested fixes. Fix them or lower the threshold in config.
</details>

<details>
<summary><strong>Is it free?</strong></summary>

Yes. Apache-2.0 license. Zero telemetry. Your code never leaves your machine.
</details>

<details>
<summary><strong>How is this different from a linter?</strong></summary>

Linters check syntax. ArbiterX enforces engineering decisions — YAGNI, proper abstractions, security patterns, and architectural discipline. It also handles context compression and model routing, which linters don't touch.
</details>

---

<br>

## ⭐ Why Developers Star This

- **Saves money** — 97% fewer tokens = 97% lower API bills
- **Saves time** — No more reviewing AI slop in PRs
- **Works everywhere** — Claude Code, Codex, Cursor, Copilot, Aider + 5 more
- **Zero config** — `pip install arbiterx-gate && arbiterx init` and you're done
- **Runs locally** — Your code never leaves your machine
- **Actually tested** — 109 tests, benchmarked on real code, not vaporware

```bash
pip install arbiterx-gate && arbiterx init && arbiterx map
```

If it saves you from one bad AI-generated commit, **[⭐ give it a star](https://github.com/NeelPrime/arbiterx).**

---

<br>

## 🔬 Built With

| Component | Technology | Why |
|-----------|-----------|-----|
| AST Parsing | [tree-sitter](https://tree-sitter.github.io/) | Fast, accurate, 22 grammars |
| Symbol Ranking | PageRank (NetworkX) | Surfaces what matters |
| Storage | SQLite | Zero-config, fast, portable |
| CLI | [Typer](https://typer.tiangolo.com/) + Rich | Beautiful terminal output |
| HTTP | httpx (async) | Modern, streaming-capable |
| Config | TOML | Human-readable |

---

<br>

## 📄 License

[Apache-2.0](LICENSE) — Use it anywhere. No strings attached.

---

<p align="center">
  <strong>Stop reviewing AI slop. Let ArbiterX be the gatekeeper.</strong>
</p>

<p align="center">
  <a href="#install">Install Now</a> •
  <a href="docs/GUIDE.md">Read the Guide</a> •
  <a href="docs/INTEGRATIONS.md">Integrations</a> •
  <a href="ARCHITECTURE.md">Architecture</a>
</p>

<!-- 
SEO / AIO / GEO / AEO Keywords (invisible to users, visible to crawlers & AI):

arbiterx, ai code quality, ai coding assistant middleware, llm code validation,
ai code review tool, ai generated code checker, code quality gate,
smart model routing, token reduction, codebase mapping, tree-sitter,
claude code plugin, codex plugin, cursor rules, copilot instructions,
ai engineering discipline, yagni enforcer, ai code security checker,
reduce llm tokens, ai coding best practices, code generation rules,
ai pair programming, intelligent code routing, multi-model ai,
python code quality, typescript code quality, open source ai tools,
developer productivity, ai middleware, code scoring, llm optimization,
aider integration, windsurf rules, kiro steering, zed assistant,
software engineering principles, clean code ai, robust code generation,
automated code review, static analysis ai, pagerank code symbols,
incremental code indexing, codebase intelligence, context compression,
prompt engineering, ai code efficiency, reduce ai costs, llm middleware
-->
