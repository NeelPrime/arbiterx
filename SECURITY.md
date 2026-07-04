# Security Policy

## Privacy by Design

ArbiterX runs **entirely locally** on your machine. There is:

- **Zero telemetry** — no usage data, analytics, or crash reports are collected
- **No network calls** — the core library never phones home
- **No data exfiltration** — your code stays on your filesystem

Model adapter calls (OpenAI, Anthropic, etc.) are initiated only by explicit user action and go directly to the provider's API. ArbiterX does not proxy, log, or retain any request/response data.

## Reporting a Vulnerability

If you discover a security vulnerability in ArbiterX, please report it responsibly:

**Email:** security@arbiterx.dev

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**Do not** open a public GitHub issue for security vulnerabilities.

## Scope

The following are in scope for security reports:

- The `arbiterx` Python library (everything under `src/arbiterx/`)
- CLI commands and their behavior
- Plugin loading and execution
- Pre-commit hook scripts
- Build and CI scripts

Out of scope:
- Third-party dependencies (report to their maintainers directly)
- Issues in the user's own code being analyzed
- Model provider API security (report to OpenAI, Anthropic, etc.)

## Response Commitment

- **Acknowledgment:** Within 48 hours of receipt
- **Initial assessment:** Within 5 business days
- **Fix timeline:** Critical issues patched within 7 days; others within 30 days
- **Disclosure:** Coordinated disclosure after fix is released

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Active |

We only provide security fixes for the latest minor release.
