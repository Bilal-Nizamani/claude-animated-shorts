#!/usr/bin/env bash
# macOS / Linux launcher for the Narration Studio (the Windows twin is "Open Narration Studio.cmd").
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(cd "$HERE/../../.." && pwd)/shorts-runtime/tts-venv/bin/python"
[ -x "$PYTHON" ] || { echo "Run templates/voice/setup-qwen.sh first. See references/PRODUCTION.md."; exit 1; }
exec "$PYTHON" -B "$HERE/qwen_studio.py" "$@"
