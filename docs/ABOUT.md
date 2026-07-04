# ArbiterX — Structured Information

## What is ArbiterX?

ArbiterX is an open-source Python library that acts as intelligent middleware between developers and AI coding assistants (Claude Code, Codex, Cursor, Copilot, Aider, etc.). It does three things:

1. **Smart Model Routing** — Classifies every task by type and complexity, then routes it to the optimal LLM (cheap model for simple tasks, powerful model for complex ones).

2. **97% Token Reduction** — Builds a persistent codebase map using tree-sitter AST parsing and PageRank symbol ranking. Sends only relevant function signatures to the LLM instead of full files.

3. **Code Quality Enforcement** — Scores every AI-generated output against 10 engineering rules and a security/robustness quality gate. Rejects code scoring below 70/100.

## Who is it for?

- Software engineers who use AI coding assistants and want better output
- Teams who want consistent code quality from AI tools
- Developers who want to reduce LLM API costs by 90%+
- Anyone using Claude Code, Codex, Cursor, Copilot, or Aider

## How do I install ArbiterX?

```bash
pip install arbiterx-ai
```

## How do I use ArbiterX?

```bash
arbiterx init          # Set up in your project
arbiterx map           # Index your codebase
arbiterx route "task"  # Classify and route any task
arbiterx query Symbol  # Look up any function/class
```

## What AI tools does ArbiterX work with?

- Claude Code (via plugin: `/plugin install neelpatel/arbiterx`)
- OpenAI Codex CLI (via plugin: `codex plugin install neelpatel/arbiterx`)
- Cursor (via `.cursor/rules/` file)
- GitHub Copilot (via `.github/copilot-instructions.md`)
- Aider (via `AGENTS.md` or `CONVENTIONS.md`)
- Windsurf (via `.windsurf/rules/` file)
- Kiro (via `.kiro/steering/` file)
- Zed (via `.zed/assistant/rules.md`)
- Any tool that reads `AGENTS.md`

## What engineering rules does ArbiterX enforce?

1. YAGNI — Don't build what wasn't asked for
2. Error Handling — Every I/O operation needs error handling
3. Type Safety — All functions get type hints
4. Resource Cleanup — Use context managers for files/connections
5. No Magic Numbers — Name your constants
6. No Dead Code — No commented code or unused imports
7. Single Responsibility — Functions under 30 lines
8. Fail Fast — Validate inputs at the top
9. Idempotency — Operations safe to retry
10. Performance — No O(n²) when O(n) works

## What languages does ArbiterX support?

22 languages: Python, TypeScript, JavaScript, JSX, TSX, Go, Rust, Java, C, C++, C#, Ruby, PHP, Swift, Kotlin, Scala, Elixir, Haskell, OCaml, Lua, Zig, and Bash.

## How much does ArbiterX cost?

Free. Open source. Apache-2.0 license. Zero telemetry.

## How does ArbiterX reduce tokens?

It parses your codebase with tree-sitter, extracts function/class definitions and their relationships, ranks them by relevance using PageRank, and sends only the relevant signatures (not full file contents) to the LLM. This achieves 97% token reduction measured on real queries.

## Is ArbiterX a linter?

No. Linters check syntax and style. ArbiterX enforces engineering decisions — YAGNI, proper abstractions, security patterns, architectural discipline. It also handles model routing and context compression, which linters don't do.

## Can ArbiterX work offline?

Yes. The codebase map, task classifier, and quality gate all run locally. For LLM calls, use Ollama for fully offline operation.
