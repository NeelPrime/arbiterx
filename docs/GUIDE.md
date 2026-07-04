# ArbiterX — Installation & Usage Guide

---

## Step 1: Install

You need Python 3.9 or newer:

```bash
python3 --version
# Should show 3.9 or higher
```

Install ArbiterX:

```bash
pip install arbiterx-gate
```

Or install from source (if you cloned the repo):

```bash
cd arbiterx
pip install -e .
```

Check it worked:

```bash
arbiterx --version
# arbiterx 0.1.0
```

---

## Step 2: Set Up Your Project

Go to any project you're working on:

```bash
cd my-project
arbiterx init
```

You'll see:

```
✓ Initialized .arbiterx/ in /path/to/my-project
```

Add to your `.gitignore`:

```bash
echo ".arbiterx/" >> .gitignore
```

---

## Step 3: Build the Map

This scans your code and creates a smart index of every function, class, and how they connect:

```bash
arbiterx map
```

Output:

```
Files indexed      34
Symbols extracted  670
Reference edges    1113
Time               0.5s
```

**Run this once.** Re-run after major code changes.

---

## Step 4: Use It

### Ask how a task should be handled

```bash
arbiterx route "fix the login bug"
```

Output:

```
Task           fix the login bug
Type           DEBUGGING
Complexity     MEDIUM
Context Scope  MODULE
Latency        INTERACTIVE
Confidence     80%
```

This means: it's a debugging task, medium difficulty, the AI needs module-level context.

### Look up any symbol

```bash
arbiterx query UserService
```

Shows where `UserService` is defined, its signature, file, and line number — without reading the whole file.

### Check what's indexed

```bash
arbiterx map --status
```

Shows how many files, symbols, and edges are in your map.

---

## Step 5: Check Code Quality

### From the command line

Use it in Python scripts or notebooks:

```python
from arbiterx.gate import QualityGate

gate = QualityGate()

code = """
def get_data(url):
    import requests
    r = requests.get(url)
    return r.json()
"""

result = gate.validate(code, "python")
print(f"Score: {result.score}/100")
print(f"Passed: {result.passed}")

for issue in result.issues:
    print(f"  ⚠ {issue.category}: {issue.message}")
```

Output:

```
Score: 60/100
Passed: False
  ⚠ robustness: Network call without timeout parameter
  ⚠ robustness: No error handling for network request
```

### Fix it based on feedback

```python
better_code = """
import httpx
from typing import Any

REQUEST_TIMEOUT = 30

def get_data(url: str) -> Any:
    try:
        response = httpx.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as err:
        raise RuntimeError(f"Request failed: {err}") from err
"""

result = gate.validate(better_code, "python")
print(f"Score: {result.score}/100")  # 100
print(f"Passed: {result.passed}")    # True
```

---

## Step 6: Enforce Engineering Rules

The enforcer checks 10 rules on any code:

```python
from arbiterx.ladder.interrogator import SelfInterrogator

enforcer = SelfInterrogator()
report = enforcer.enforce(your_code, "python")

print(f"Score: {report.score}/100")
print(f"Passed: {report.passed}")

for v in report.violations:
    print(f"  [{v.severity.value}] {v.arbiterx_name}: {v.description}")
```

### The 10 rules explained simply

| Rule | What It Means |
|------|--------------|
| YAGNI | Don't build stuff nobody asked for |
| Error Handling | If something can fail, wrap it in try/except |
| Type Safety | Tell Python what types your function takes and returns |
| Resource Cleanup | Use `with open(...)` so files always get closed |
| No Magic Numbers | Write `MAX_RETRIES = 3`, not just `3` |
| No Dead Code | Delete commented-out code and unused imports |
| Single Responsibility | One function does one thing. Keep it short. |
| Fail Fast | Check if inputs are valid at the start, not the middle |
| Idempotency | Running it twice shouldn't break things |
| Performance | Don't put a loop inside a loop if you don't have to |

---

## Step 7: Connect to Your AI Tool

### Claude Code (1 command)

```
/plugin install neelpatel/arbiterx
```

Done. ArbiterX is now active in every Claude Code session.

### Codex CLI (1 command)

```bash
codex plugin install neelpatel/arbiterx
```

### Cursor

Copy the rules file into your project:

```bash
cp .cursor/rules/arbiterx.mdc your-project/.cursor/rules/
```

### GitHub Copilot

Copy the instructions file:

```bash
cp .github/copilot-instructions.md your-project/.github/
```

### Aider

Copy `AGENTS.md` to your project root. Aider reads it automatically.

### Any Other Tool

Most AI coding tools read `AGENTS.md` from your project root:

```bash
cp AGENTS.md your-project/
```

See [docs/INTEGRATIONS.md](INTEGRATIONS.md) for every platform.

---

## Step 8: Add API Keys (Optional)

Only needed if you want ArbiterX to route tasks to real LLMs:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

Or create `arbiterx.toml`:

```toml
[models.anthropic]
api_key_env = "ANTHROPIC_API_KEY"

[models.openai]
api_key_env = "OPENAI_API_KEY"

[models.ollama]
base_url = "http://localhost:11434"
```

---

## Command Reference

| Command | What It Does |
|---------|-------------|
| `arbiterx init` | Set up ArbiterX in your project |
| `arbiterx map` | Scan and index your codebase |
| `arbiterx map --status` | See what's indexed |
| `arbiterx route "task"` | See how a task gets classified |
| `arbiterx query Symbol` | Look up a function or class |
| `arbiterx stats` | See token savings |
| `arbiterx --help` | All options |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: arbiterx` | Run `pip install -e .` and make sure pip's bin dir is in your PATH |
| `No .arbiterx/ found` | Run `arbiterx init` first |
| `No map found` | Run `arbiterx map` to build the index |
| Map is slow | Add large folders (node_modules, dist) to excludes in config |
| Score too strict | Set `min_score = 60` in `arbiterx.toml` |
| Want less rules | Use `mode = "lite"` in config (only 5 core rules) |

---

## That's It

Three commands to start:

```bash
arbiterx init
arbiterx map
arbiterx route "your task here"
```

ArbiterX handles the rest — picks the model, sends minimal context, and makes sure the code is solid.
