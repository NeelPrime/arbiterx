#!/bin/bash
# ArbiterX Terminal Demo
# Record with: asciinema rec demo.cast
# Convert to GIF with: agg demo.cast assets/demo.gif
#
# Or just run this script to see ArbiterX in action:
#   bash scripts/demo.sh

set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

type_slow() {
    echo -ne "${CYAN}\$ ${NC}"
    for ((i=0; i<${#1}; i++)); do
        echo -n "${1:$i:1}"
        sleep 0.03
    done
    echo ""
    sleep 0.5
}

print_header() {
    echo ""
    echo -e "${BOLD}${YELLOW}━━━ $1 ━━━${NC}"
    echo ""
    sleep 1
}

clear
echo -e "${BOLD}"
echo "    _         _     _ _            __  __"
echo "   / \   _ __| |__ (_) |_ ___ _ __\ \/ /"
echo "  / _ \ | '__| '_ \| | __/ _ \ '__|\  / "
echo " / ___ \| |  | |_) | | ||  __/ |   /  \ "
echo "/_/   \_\_|  |_.__/|_|\__\___|_|  /_/\_\\"
echo ""
echo -e "${NC}${CYAN}  Engineering discipline for AI code generation${NC}"
echo ""
sleep 2

# --- INIT ---
print_header "Step 1: Initialize"
type_slow "arbiterx init"
echo -e "  ${GREEN}✓ Initialized .arbiterx/ in /home/dev/my-project${NC}"
sleep 1

# --- MAP ---
print_header "Step 2: Build the codebase map"
type_slow "arbiterx map"
echo ""
echo "  ┌──────────────────┬─────────┐"
echo "  │ Files indexed     │ 127     │"
echo "  │ Symbols extracted │ 3,842   │"
echo "  │ Reference edges   │ 8,291   │"
echo "  │ Time              │ 1.2s    │"
echo "  └──────────────────┴─────────┘"
sleep 2

# --- ROUTE ---
print_header "Step 3: Smart routing"
type_slow 'arbiterx route "fix the authentication bypass in JWT validation"'
echo ""
echo "  ┌───────────────┬──────────────────────────────────────┐"
echo "  │ Type          │ DEBUGGING                            │"
echo "  │ Complexity    │ HIGH                                 │"
echo "  │ Context Scope │ MODULE                               │"
echo -e "  │ ${GREEN}→ Model${NC}       │ ${GREEN}opus (needs deep security reasoning)${NC} │"
echo "  └───────────────┴──────────────────────────────────────┘"
sleep 2

type_slow 'arbiterx route "rename getUserName to getUsername"'
echo ""
echo "  ┌───────────────┬──────────────────────────────────────┐"
echo "  │ Type          │ REFACTORING                          │"
echo "  │ Complexity    │ TRIVIAL                              │"
echo "  │ Context Scope │ FILE                                 │"
echo -e "  │ ${GREEN}→ Model${NC}       │ ${GREEN}haiku (cheap — simple rename)${NC}       │"
echo "  └───────────────┴──────────────────────────────────────┘"
sleep 2

# --- QUERY ---
print_header "Step 4: Query symbols"
type_slow "arbiterx query QualityGate"
echo ""
echo "  ┌────────────────────────────────┬───────┬─────────────────────────┬──────┐"
echo "  │ Name                           │ Kind  │ File                    │ Line │"
echo "  ├────────────────────────────────┼───────┼─────────────────────────┼──────┤"
echo "  │ QualityGate                    │ class │ src/arbiterx/gate/val.. │ 42   │"
echo "  └────────────────────────────────┴───────┴─────────────────────────┴──────┘"
sleep 2

# --- GATE ---
print_header "Step 5: Quality gate"
echo -e "${CYAN}\$ ${NC}python3 -c \"
from arbiterx.gate import QualityGate
gate = QualityGate()

bad_code = '''
def get_data(url):
    f = open('cache.txt')
    data = eval(f.read())
    return data
'''

result = gate.validate(bad_code, 'python')
print(f'Score: {result.score}/100')
print(f'Passed: {result.passed}')
\""
echo ""
sleep 0.5
echo -e "  Score: ${RED}35/100${NC}"
echo -e "  Passed: ${RED}False${NC}"
echo ""
echo -e "  ${RED}❌ [high] security: Use of eval() is a security risk${NC}"
echo -e "  ${RED}❌ [medium] robustness: File operation without error handling${NC}"
echo -e "  ${YELLOW}⚠  [low] style: Single-letter variable 'f'${NC}"
sleep 2

# --- EXPORT ---
print_header "Step 6: Export rules to your AI tool"
type_slow "arbiterx export-rules --format cursor"
echo -e "  ${GREEN}✓ Rules written to .cursor/rules/arbiterx.mdc${NC}"
sleep 1

type_slow "arbiterx export-rules --format copilot"
echo -e "  ${GREEN}✓ Rules written to .github/copilot-instructions.md${NC}"
sleep 1

# --- DONE ---
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${GREEN}  ArbiterX: Your AI writes code. You decide if it ships.${NC}"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${CYAN}pip install arbiterx${NC}"
echo -e "  ${CYAN}arbiterx init && arbiterx map${NC}"
echo ""
