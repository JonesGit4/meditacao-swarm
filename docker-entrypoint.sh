#!/bin/bash
set -e

echo "=== Pre-Build Validation ==="
python3 /app/scripts/prebuild_check.py
PREBUILD_EXIT=$?

if [ $PREBUILD_EXIT -ne 0 ]; then
    echo "PREBUILD FAILED - Container will exit"
    exit 1
fi

echo ""
echo "=== Starting Meditation Swarm ==="
exec python3 -u /app/src/main.py
