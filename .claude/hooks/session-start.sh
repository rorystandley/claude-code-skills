#!/bin/bash
set -euo pipefail

# Only run in remote/cloud environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install Python dependencies for all skills
find "$CLAUDE_PROJECT_DIR/skills" -name "requirements.txt" | while read -r req; do
  pip3 install -r "$req" -q
done
