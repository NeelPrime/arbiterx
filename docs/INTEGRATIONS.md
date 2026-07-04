# ArbiterX — Integration Guide

How to integrate ArbiterX with popular AI coding assistants.

---

## Prerequisites

ArbiterX requires the Python package to be installed for full functionality (quality gate, codebase map, model routing):

```bash
pip install arbiterx-ai
arbiterx --version   # verify
arbiterx init        # initialize in your project (once)
arbiterx map         # build codebase index (optional, enables token savings)
```

> **Without `pip install arbiterx-ai`:** Plugin integrations still inject engineering rules into the AI's prompt (prompt-only mode). **With it installed:** The quality gate actively scores generated code and rejects anything below threshold.

---

## Overview: 3 Ways to Integrate

| Method | Works With | Effort | Quality Gate |
|--------|-----------|--------|--------------|
| **Plugin** (recommended) | Claude Code, Codex | 1 command | ✅ Active (requires pip install) |
| **Hooks** (powerful) | Claude Code, Codex | Copy a config | ✅ Active (requires pip install) |
| **Rules file** (universal) | Cursor, Windsurf, Copilot, Aider, Kiro, Zed | Copy a file | ❌ Prompt-only |

---

## 1. Claude Code (Plugin)

Claude Code supports plugins — packages of slash commands, hooks, and skills.

### Install

```bash
# Step 1: Install the arbiterx Python package
pip install arbiterx-ai

# Step 2: Install the plugin in Claude Code
/plugin install NeelPrime/arbiterx
```

That's it. ArbiterX is now active — the quality gate will score all generated code automatically.

### What It Does

Once installed, the plugin:
- **Installs** the `arbiterx` CLI tool via pip (if not already present)
- **Runs `arbiterx init`** to set up the `.arbiterx/` config directory
- **Injects engineering principles** into every prompt (the 10 rules)
- **Runs the quality gate** on every file the AI writes or edits (PostToolUse hook)
- **Scores code 0–100** and reports issues inline

### Slash Commands Available

| Command | Action |
|---------|--------|
| `/arbiterx` | Show current mode (lite/full/strict) |
| `/arbiterx strict` | Enable strict enforcement |
| `/arbiterx lite` | Enable lightweight mode |
| `/arbiterx off` | Disable enforcement |
| `/arbiterx-review` | Review the current diff against arbiterxs |
| `/arbiterx-gate` | Run quality gate on last generated code |

### Hooks Integration

If you prefer manual hook setup (or want to customize), add this to your Claude Code `settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "handler": {
          "type": "command",
          "command": "arbiterx --version && echo 'ArbiterX engineering mode active.'"
        }
      }
    ],
    "PostToolUse": [
      {
        "matcher": "write_to_file|edit_file|create_file",
        "handler": {
          "type": "command",
          "command": "arbiterx gate --file \"$TOOL_ARG_PATH\" --json"
        }
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "handler": {
          "type": "command",
          "command": "echo 'Run: arbiterx gate on changed files before committing.'"
        }
      }
    ]
  }
}
```

**What each hook does:**
- `SessionStart` → Verifies arbiterx is installed and activates engineering mode
- `PostToolUse` → After Claude writes/edits a file, runs the quality gate and reports score
- `Stop` → Reminds to gate-check before committing

> **Requires:** `pip install arbiterx-ai` for hooks to function. Without it, hooks silently skip.

### Manual Setup (Without Plugin)

If you don't want to use the plugin system:

1. Copy the rules file to your project:
```bash
cp /path/to/arbiterx/.claude-rules/arbiterx.md .claude/rules/arbiterx.md
```

2. Or add to `CLAUDE.md` in your project root:
```bash
cat /path/to/arbiterx/skills/arbiterx-principles.md >> CLAUDE.md
```

---

## 2. OpenAI Codex CLI (Plugin)

Codex CLI has a similar plugin system.

### Install

```bash
# Step 1: Install the arbiterx Python package
pip install arbiterx-ai

# Step 2: Install the plugin in Codex
codex plugin install NeelPrime/arbiterx
```

Then open `/plugins` in Codex, select ArbiterX, and enable it.

### Enable Hooks

Open `/hooks` in Codex, review and trust ArbiterX's lifecycle hooks:
- **Pre-turn hook** — Injects engineering principles
- **Post-turn hook** — Validates generated code

### Skills

Codex uses `@` to invoke skills:
- `@arbiterx` — Activate full engineering mode
- `@arbiterx-review` — Review current code against arbiterxs
- `@arbiterx-gate` — Run quality gate

### Manual Setup (AGENTS.md)

Codex reads `AGENTS.md` from your project root. Create one with ArbiterX's principles:

```bash
arbiterx export-rules --format agents > AGENTS.md
```

Or copy directly:
```markdown
# Engineering ArbiterXs (ArbiterX)

Before writing any code:
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

After writing code, verify:
- No hardcoded secrets (API keys, passwords)
- No SQL injection (no string formatting in queries)
- No eval/exec
- All file operations use context managers
- All network calls have timeouts
```

---

## 3. Cursor

Cursor uses `.cursor/rules/` files.

### Setup

```bash
mkdir -p .cursor/rules
```

Create `.cursor/rules/arbiterx.mdc`:

```markdown
---
description: Engineering discipline rules for code generation
globs: ["**/*.py", "**/*.ts", "**/*.js", "**/*.go", "**/*.rs"]
alwaysApply: true
---

# ArbiterX: Engineering Discipline

Before writing ANY code, follow this ladder:
1. Does this need to exist? → If no, skip (YAGNI)
2. Already in codebase? → Reuse, don't rewrite
3. Stdlib does it? → Use stdlib
4. One line? → Write one line, no abstraction

When writing code, ENFORCE:
- Type all function parameters and return values
- Handle every error — no bare except, no swallowed errors
- Use context managers for files/connections (with open...)
- Name all constants — no magic numbers
- One function = one job (max 30 lines)
- Validate inputs at function entry, not deep in logic
- Never leave TODO/FIXME — finish it or don't write it

REJECT if:
- Hardcoded secrets present
- SQL built with string formatting
- eval() or exec() used
- File operations without error handling
- String concatenation in loops
```

### Auto-generate from ArbiterX

```bash
arbiterx export-rules --format cursor > .cursor/rules/arbiterx.mdc
```

---

## 4. Windsurf

Windsurf uses `.windsurf/rules/` files.

```bash
mkdir -p .windsurf/rules
arbiterx export-rules --format windsurf > .windsurf/rules/arbiterx.md
```

Or manually create `.windsurf/rules/arbiterx.md` with the same content as the Cursor rules above (without the YAML frontmatter).

---

## 5. GitHub Copilot

Copilot reads `.github/copilot-instructions.md` from your project.

```bash
mkdir -p .github
arbiterx export-rules --format copilot > .github/copilot-instructions.md
```

Or create `.github/copilot-instructions.md`:

```markdown
# Code Generation Rules

Follow these engineering principles for all generated code:

## Must-Have
- Type hints on all function signatures
- Error handling for all I/O operations (try/except or context managers)
- Named constants instead of magic numbers
- Input validation at function entry

## Must-Not
- No hardcoded secrets or API keys
- No bare except clauses
- No string formatting in SQL queries
- No eval() or exec()
- No TODO/FIXME comments in generated code
- No functions longer than 30 lines

## Prefer
- Standard library over external dependencies
- Context managers (with) over manual open/close
- Immutable data structures where possible
- Early returns over deep nesting
```

---

## 6. Aider

Aider reads `CONVENTIONS.md` or can be configured with `--read` flag.

### Option A: Conventions file

Create `CONVENTIONS.md` in your project root:

```bash
arbiterx export-rules --format aider > CONVENTIONS.md
```

Aider automatically reads this and applies it to all generations.

### Option B: CLI flag

```bash
aider --read /path/to/arbiterx/skills/arbiterx-principles.md
```

### Option C: .aider.conf.yml

```yaml
read:
  - .arbiterx/principles.md
```

---

## 7. Kiro

Kiro reads `.kiro/steering/` files.

```bash
mkdir -p .kiro/steering
arbiterx export-rules --format kiro > .kiro/steering/arbiterx.md
```

---

## 8. Zed

Zed reads `.zed/assistant/rules.md`.

```bash
mkdir -p .zed/assistant
arbiterx export-rules --format zed > .zed/assistant/rules.md
```

---

## 9. Any CLI (Universal — AGENTS.md)

Most modern AI coding tools read `AGENTS.md` from the project root. This is the universal integration:

```bash
arbiterx export-rules --format agents > AGENTS.md
```

This works with: Codex, Claude Code, CodeWhale, Swival, OpenCode, and others.

---

## 10. As a Git Hook (Automatic)

Requires `pip install arbiterx-ai`. Rejects commits with code scoring below 70/100:

```bash
# .git/hooks/pre-commit
#!/bin/bash
set -e

if ! command -v arbiterx &>/dev/null; then
    echo "⚠️  ArbiterX not installed. Run: pip install arbiterx-ai"
    exit 0
fi

changed_files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|ts|js|go|rs)$' || true)

if [ -z "$changed_files" ]; then
    exit 0
fi

for file in $changed_files; do
    result=$(arbiterx gate --file "$file" --json 2>/dev/null)
    score=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('score',100))" 2>/dev/null || echo "100")
    if [ "$score" -lt 70 ]; then
        echo "❌ ArbiterX: $file scored $score/100 (minimum 70)"
        echo "$result" | python3 -c "import sys,json; [print(f'   • {i}') for i in json.load(sys.stdin).get('issues',[])]" 2>/dev/null
        exit 1
    fi
done
echo "✓ ArbiterX: all files pass quality gate"
```

Install it:
```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## Quick Export Command

ArbiterX includes a built-in export command for generating rules files:

```bash
# Generate for any platform
arbiterx export-rules --format claude     # → .claude/rules/arbiterx.md
arbiterx export-rules --format codex      # → AGENTS.md
arbiterx export-rules --format cursor     # → .cursor/rules/arbiterx.mdc
arbiterx export-rules --format copilot    # → .github/copilot-instructions.md
arbiterx export-rules --format aider      # → CONVENTIONS.md
arbiterx export-rules --format agents     # → AGENTS.md (universal)

# Or print to stdout
arbiterx export-rules --format cursor --stdout
```

---

## Summary: Which to Use?

| Your Tool | Best Integration | File to Create |
|-----------|-----------------|----------------|
| Claude Code | Plugin (`/plugin install`) | Automatic |
| Codex CLI | Plugin (`codex plugin install`) | Automatic |
| Cursor | Rules file | `.cursor/rules/arbiterx.mdc` |
| Windsurf | Rules file | `.windsurf/rules/arbiterx.md` |
| GitHub Copilot | Instructions | `.github/copilot-instructions.md` |
| Aider | Conventions | `CONVENTIONS.md` |
| Kiro | Steering | `.kiro/steering/arbiterx.md` |
| Zed | Rules | `.zed/assistant/rules.md` |
| Any tool | AGENTS.md | `AGENTS.md` |
| CI/CD | Git hook | `.git/hooks/pre-commit` |
