"""Security checker — detects hardcoded secrets, injection risks, and dangerous calls."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class SecurityIssue:
    """A single security issue found in code."""

    severity: str  # "critical", "high", "medium", "low"
    message: str
    line: int
    suggestion: str


# Patterns for hardcoded API keys / secrets
_SECRET_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"""['"]sk-[A-Za-z0-9]{20,}['"]"""),
        "Hardcoded OpenAI API key detected",
        "Use environment variable: os.environ['OPENAI_API_KEY']",
    ),
    (
        re.compile(r"""['"]AKIA[0-9A-Z]{16}['"]"""),
        "Hardcoded AWS Access Key ID detected",
        "Use environment variable or AWS credentials file",
    ),
    (
        re.compile(r"""['"]ghp_[A-Za-z0-9]{36,}['"]"""),
        "Hardcoded GitHub personal access token detected",
        "Use environment variable: os.environ['GITHUB_TOKEN']",
    ),
    (
        re.compile(r"""['"]github_pat_[A-Za-z0-9_]{50,}['"]"""),
        "Hardcoded GitHub fine-grained token detected",
        "Use environment variable: os.environ['GITHUB_TOKEN']",
    ),
    (
        re.compile(
            r"""(?:api[_-]?key|secret[_-]?key|auth[_-]?token|access[_-]?token)\s*=\s*['"][A-Za-z0-9+/=_\-]{20,}['"]""",
            re.IGNORECASE,
        ),
        "Potential hardcoded secret in variable assignment",
        "Load secrets from environment variables or a secrets manager",
    ),
    (
        re.compile(r"""['"]xox[baprs]-[A-Za-z0-9\-]{10,}['"]"""),
        "Hardcoded Slack token detected",
        "Use environment variable for Slack tokens",
    ),
    (
        re.compile(r"""['"](?:sk|pk)_(?:live|test)_[A-Za-z0-9]{20,}['"]"""),
        "Hardcoded Stripe key detected",
        "Use environment variable: os.environ['STRIPE_SECRET_KEY']",
    ),
]

# Password patterns
_PASSWORD_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"""(?:password|passwd|pwd)\s*=\s*['"][^'"]{3,}['"]""",
            re.IGNORECASE,
        ),
        "Hardcoded password detected",
        "Use environment variable or secrets manager for passwords",
    ),
    (
        re.compile(
            r"""(?:password|passwd|pwd)\s*:\s*['"][^'"]{3,}['"]""",
            re.IGNORECASE,
        ),
        "Hardcoded password in dictionary/config",
        "Load passwords from environment variables at runtime",
    ),
]

# SQL injection patterns
_SQL_INJECTION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"""(?:execute|cursor\.execute|query)\s*\(\s*f['"].*\{""",
            re.IGNORECASE,
        ),
        "Potential SQL injection: f-string in SQL query",
        "Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id = %s', (id,))",
    ),
    (
        re.compile(
            r"""(?:execute|cursor\.execute|query)\s*\(\s*['"].*['"]\.format\(""",
            re.IGNORECASE,
        ),
        "Potential SQL injection: .format() in SQL query",
        "Use parameterized queries instead of string formatting",
    ),
    (
        re.compile(
            r"""(?:execute|cursor\.execute|query)\s*\(\s*['"].*['"\s]*\+""",
            re.IGNORECASE,
        ),
        "Potential SQL injection: string concatenation in SQL query",
        "Use parameterized queries instead of string concatenation",
    ),
]

# Dangerous function patterns
_DANGEROUS_CALLS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"""\beval\s*\("""),
        "Use of eval() is a security risk — arbitrary code execution",
        "Use ast.literal_eval() for safe parsing, or refactor to avoid eval entirely",
    ),
    (
        re.compile(r"""\bexec\s*\("""),
        "Use of exec() is a security risk — arbitrary code execution",
        "Refactor to avoid exec(); use a proper dispatch mechanism or plugin system",
    ),
    (
        re.compile(r"""subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True"""),
        "subprocess with shell=True is a command injection risk",
        "Use shell=False with a list of arguments: subprocess.run(['cmd', 'arg1'])",
    ),
    (
        re.compile(r"""os\.system\s*\("""),
        "os.system() is a command injection risk",
        "Use subprocess.run() with shell=False and a list of arguments",
    ),
    (
        re.compile(r"""os\.popen\s*\("""),
        "os.popen() is a command injection risk",
        "Use subprocess.run() with shell=False and capture_output=True",
    ),
]


class SecurityChecker:
    """Checks code for security vulnerabilities using regex pattern matching.

    Detects:
    - Hardcoded API keys (OpenAI, AWS, GitHub, Slack, Stripe)
    - Hardcoded passwords
    - SQL injection risks (string formatting in queries)
    - Dangerous eval/exec usage
    - subprocess with shell=True
    """

    def check(self, code: str) -> List[SecurityIssue]:
        """Run all security checks on the given code.

        Args:
            code: Source code string to analyze.

        Returns:
            List of SecurityIssue instances found.
        """
        issues: List[SecurityIssue] = []
        lines = code.splitlines()

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            for pattern, message, suggestion in _SECRET_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        SecurityIssue(
                            severity="critical",
                            message=message,
                            line=line_num,
                            suggestion=suggestion,
                        )
                    )

            for pattern, message, suggestion in _PASSWORD_PATTERNS:
                if pattern.search(line):
                    if re.search(
                        r"""['"](?:password|your[_-]?password|changeme|xxx|\*+|<[^>]+>)['"]""",
                        line,
                        re.IGNORECASE,
                    ):
                        continue
                    issues.append(
                        SecurityIssue(
                            severity="high",
                            message=message,
                            line=line_num,
                            suggestion=suggestion,
                        )
                    )

            for pattern, message, suggestion in _SQL_INJECTION_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        SecurityIssue(
                            severity="critical",
                            message=message,
                            line=line_num,
                            suggestion=suggestion,
                        )
                    )

            for pattern, message, suggestion in _DANGEROUS_CALLS:
                if pattern.search(line):
                    issues.append(
                        SecurityIssue(
                            severity="high",
                            message=message,
                            line=line_num,
                            suggestion=suggestion,
                        )
                    )

        return issues
