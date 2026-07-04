# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-03

### Added

- Codebase mapping engine with tree-sitter parsing and SQLite-backed symbol store
- Task classifier with heuristic-based type, complexity, and scope inference
- 5 model adapters: OpenAI, Anthropic, Ollama, Google Gemini, and local fallback
- Quality gate with syntax, security, robustness, efficiency, style, and completeness checks
- 10 engineering tenets enforced via static analysis (YAGNI, error handling, type safety, resource cleanup, no magic numbers, no dead code, single responsibility, fail fast, idempotency, performance)
- CLI commands: `arbiterx map`, `arbiterx gate`, `arbiterx classify`, `arbiterx query`
- Plugin system with manifest-based loading for custom adapters and classifiers
- 10+ tool integrations: VS Code, Cursor, Windsurf, GitHub Copilot, Codex CLI, Claude Code, Kiro, JetBrains, Neovim, Emacs
- Self-interrogation ladder (16-step cascade) for intelligent model routing
- Incremental indexing with content-hash change detection
- Pre-commit hook for automated quality enforcement
- Routing table with configurable model-to-task mappings
- Context handoff protocol for multi-model conversations

[0.1.0]: https://github.com/neelpatel/arbiterx/releases/tag/v0.1.0
