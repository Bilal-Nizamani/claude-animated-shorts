#!/usr/bin/env bash
# Copy the narrated-video skills and their shared tools into ~/.claude/skills (macOS / Linux).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$DEST"
for d in _shared short-form-narrative long-form-narrative; do
  rm -rf "$DEST/$d"
  cp -R "$HERE/$d" "$DEST/$d"
done
echo "Installed short-form-narrative, long-form-narrative and _shared into $DEST"
