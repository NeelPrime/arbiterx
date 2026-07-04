#!/bin/bash
# Scripted demo for recording
set -e
cd /Users/neelpatel/Drive/Github/arbiterx
source .venv/bin/activate

echo ""
echo "  ╔═══════════════════════════════════════════════╗"
echo "  ║            ArbiterX Demo v0.1.0               ║"
echo "  ║  Engineering discipline for AI code generation ║"
echo "  ╚═══════════════════════════════════════════════╝"
echo ""

echo "━━━ Step 1: Initialize ━━━"
echo ""
echo "$ arbiterx init"
rm -rf /tmp/demo-project && mkdir -p /tmp/demo-project && cd /tmp/demo-project
arbiterx init
echo ""

echo "━━━ Step 2: Build codebase map ━━━"
echo ""
echo "$ arbiterx map"
cd /Users/neelpatel/Drive/Github/arbiterx
rm -rf .arbiterx && arbiterx init 2>/dev/null
arbiterx map
echo ""

echo "━━━ Step 3: Route a task ━━━"
echo ""
echo '$ arbiterx route "fix the authentication bypass bug"'
arbiterx route "fix the authentication bypass bug"
echo ""
echo '$ arbiterx route "rename getUserName to getUsername"'
arbiterx route "rename getUserName to getUsername"
echo ""

echo "━━━ Step 4: Query a symbol ━━━"
echo ""
echo "$ arbiterx query QualityGate"
arbiterx query QualityGate
echo ""

echo "━━━ Step 5: Quality gate ━━━"
echo ""
echo '$ python3 -c "from arbiterx.gate import QualityGate; ..."'
python3 -c "
from arbiterx.gate import QualityGate
gate = QualityGate()
bad = '''def f(x):
    eval(x)
    f = open(\"a\")
    return f.read()
'''
r = gate.validate(bad, 'python')
print(f'  Bad code  → Score: {r.score}/100  Passed: {r.passed}')
for i in r.issues:
    print(f'    ❌ [{i.severity}] {i.message}')
print()

good = '''from pathlib import Path
from typing import Optional

def read_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    with open(path) as f:
        return f.read()
'''
r2 = gate.validate(good, 'python')
print(f'  Good code → Score: {r2.score}/100  Passed: {r2.passed}')
"
echo ""

echo "━━━ Step 6: Export rules ━━━"
echo ""
echo "$ arbiterx export-rules --format cursor --stdout | head -5"
arbiterx export-rules --format cursor --stdout 2>&1 | head -5
echo "  ..."
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✓ Done. pip install arbiterx && arbiterx init"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
