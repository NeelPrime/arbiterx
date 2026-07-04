#!/usr/bin/env python3
"""Quality check example for ArbiterX.

Demonstrates the QualityGate and SelfInterrogator (engineering enforcement)
running against code snippets of varying quality.

Run with:
    python examples/quality_check.py
"""

from arbiterx.gate import GateResult, QualityGate
from arbiterx.ladder.interrogator import EngineeringReport, SelfInterrogator

# ─── Code Snippets ────────────────────────────────────────────────────────────

BAD_CODE = """\
import os, sys, json, re, hashlib, base64

def f(x):
    PASSWORD = "admin123"
    a = x + 1
    b = a * 3.14159
    c = b / 2.71828
    # TODO: implement properly
    data = eval(x)
    return c
"""

MEDIUM_CODE = '''\
import json
from pathlib import Path


def load_config(config_path: str) -> dict:
    """Load configuration from a JSON file."""
    with open(config_path, "r") as f:
        data = json.load(f)
    threshold = 42
    if data.get("debug"):
        print("Debug mode enabled")
    return data


def process_items(items: list) -> list:
    results = []
    for item in items:
        if item > 0:
            results.append(item * 2)
    return results
'''

GOOD_CODE = '''\
"""User service — handles user CRUD operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class User:
    """Immutable user record."""

    user_id: str
    email: str
    display_name: str


class UserRepository:
    """In-memory user store for demonstration purposes."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def get(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID, or None if not found."""
        return self._users.get(user_id)

    def create(self, user_id: str, email: str, display_name: str) -> User:
        """Create and store a new user.

        Raises:
            ValueError: If user_id already exists.
        """
        if user_id in self._users:
            raise ValueError(f"User {user_id!r} already exists")
        user = User(user_id=user_id, email=email, display_name=display_name)
        self._users[user_id] = user
        return user

    def delete(self, user_id: str) -> bool:
        """Remove a user. Returns True if deleted, False if not found."""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False
'''


# ─── Helpers ──────────────────────────────────────────────────────────────────


def print_gate_result(label: str, result: GateResult) -> None:
    """Pretty-print a QualityGate result."""
    status = "✅ PASS" if result.passed else "❌ FAIL"
    print(f"  {status}  Score: {result.score}/100")
    if result.issues:
        print(f"  Issues ({len(result.issues)}):")
        for issue in result.issues[:5]:  # Show first 5
            print(f"    [{issue.severity.upper():8s}] L{issue.line:3d}: {issue.message}")
        if len(result.issues) > 5:
            print(f"    ... and {len(result.issues) - 5} more")
    print()


def print_enforcement_report(label: str, report: EngineeringReport) -> None:
    """Pretty-print a SelfInterrogator enforcement report."""
    status = "✅ PASS" if report.passed else "❌ FAIL"
    print(f"  {status}  Score: {report.score}/100")
    if report.violations:
        print(f"  Violations ({len(report.violations)}):")
        for v in report.violations[:5]:
            line_info = f"L{v.line_hint}" if v.line_hint else "—"
            print(
                f"    [{v.severity.value.upper():7s}] {v.arbiterx_name:20s} {line_info}: {v.description}"
            )
        if len(report.violations) > 5:
            print(f"    ... and {len(report.violations) - 5} more")
    if report.summary:
        print(f"  Summary: {report.summary}")
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("ArbiterX — Quality Check Demo")
    print("─" * 60)
    print()

    # Initialize the gate and enforcer
    gate = QualityGate(passing_score=70)
    enforcer = SelfInterrogator()

    snippets = [
        ("BAD CODE", BAD_CODE),
        ("MEDIUM CODE", MEDIUM_CODE),
        ("GOOD CODE", GOOD_CODE),
    ]

    for label, code in snippets:
        print("=" * 60)
        print(f"  {label}")
        print("=" * 60)
        print()

        # Run QualityGate
        print("  ── QualityGate ──")
        gate_result = gate.validate(code, language="python")
        print_gate_result(label, gate_result)

        # Run SelfInterrogator engineering enforcement
        print("  ── Engineering Tenets (SelfInterrogator) ──")
        report = enforcer.enforce(code, language="python")
        print_enforcement_report(label, report)

        print()

    print("Done! ✓")
