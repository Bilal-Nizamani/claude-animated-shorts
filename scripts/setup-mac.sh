#!/usr/bin/env bash
# One-time setup on a Mac (Apple silicon or Intel). Run it from the checkout of this branch:
#   <parent>/shorts-production/first-short   <- this repo (branch first-short)
# It creates the rest of the layout next to it:
#   <parent>/claude-animated-shorts          tooling (voice scripts, templates)   [cloned from main]
#   <parent>/shorts-runtime                  Python env + model weights           [never in Git]
set -euo pipefail

SHORT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$SHORT/../.." && pwd)"
SKILL_URL="${SKILL_URL:-https://github.com/Bilal-Nizamani/claude-animated-shorts.git}"
NARRATOR="${NARRATOR:-Aiden}"
echo "layout root: $ROOT"

command -v brew >/dev/null 2>&1 || { echo "Install Homebrew first (https://brew.sh), then run this again."; exit 1; }
brew install ffmpeg node python@3.12 uv git

if ! ffmpeg -hide_banner -filters 2>/dev/null | grep -q rubberband; then
  echo "WARNING: this ffmpeg has no 'rubberband' filter. Pace/pitch edits will fall back to a lower-quality method."
fi

[ -d "$ROOT/claude-animated-shorts/.git" ] || git clone "$SKILL_URL" "$ROOT/claude-animated-shorts"
git -C "$ROOT/claude-animated-shorts" pull --ff-only || true

# Python env + Qwen3-TTS 0.6B and 1.7B models (about 6 GB, one time)
bash "$ROOT/claude-animated-shorts/templates/voice/setup-qwen.sh"
PY="$ROOT/shorts-runtime/tts-venv/bin/python"
"$PY" -B -c "import sys; sys.path.insert(0, '$ROOT/claude-animated-shorts/templates/voice'); from qwen_narrate import save_profile; save_profile('$NARRATOR', 'English', False); print('narrator saved: $NARRATOR')"

# Remotion + Three.js + GSAP, and Remotion's own headless Chrome
cd "$SHORT/remotion"
npm ci --no-audit --no-fund
node -e "import('@remotion/renderer').then(r => r.ensureBrowser()).then(() => console.log('Remotion browser ready'))"

echo
echo "Setup finished. Next:  bash scripts/make-short.sh all     (from $SHORT)"
