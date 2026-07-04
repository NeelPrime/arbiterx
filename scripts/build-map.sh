#!/usr/bin/env bash
# build-map.sh — Run arbiterx map with timing information.
set -euo pipefail

echo "🗺️  ArbiterX — Building codebase map..."
echo "─────────────────────────────────────────"

START_TIME=$(date +%s%N)

arbiterx map "$@"

END_TIME=$(date +%s%N)
ELAPSED_MS=$(( (END_TIME - START_TIME) / 1000000 ))
ELAPSED_S=$(echo "scale=2; $ELAPSED_MS / 1000" | bc)

echo "─────────────────────────────────────────"
echo "✅ Map generated in ${ELAPSED_S}s"
