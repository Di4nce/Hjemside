#!/bin/bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCK="/tmp/lerseth-deploy.lock"

exec 200>"$LOCK"
flock -n 200 || exit 0   # a previous run is still going — skip this one

cd "$REPO"

BEFORE=$(git rev-parse HEAD)
git pull --quiet
AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" != "$AFTER" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): New commits pulled ($BEFORE -> $AFTER), rebuilding..."
    "$REPO/venv/bin/python3" build.py
else
    echo "$(date '+%Y-%m-%d %H:%M:%S'): No changes."
fi