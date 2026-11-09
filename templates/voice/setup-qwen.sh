#!/usr/bin/env bash
# One-time Qwen3-TTS setup for macOS / Linux (the Windows twin is setup-qwen.ps1).
#   bash templates/voice/setup-qwen.sh [--no-clone]
# Creates ../shorts-runtime/tts-venv (Python 3.12) next to this checkout, installs the dependencies and downloads the Qwen3-TTS 1.7B CustomVoice and 1.7B Base models (about 9 GB).
# Nothing here is committed to Git: shorts-runtime/ is outside the checkout.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
RUNTIME="$(cd "$REPO/.." && pwd)/shorts-runtime"
PYTHON="$RUNTIME/tts-venv/bin/python"
mkdir -p "$RUNTIME"

if ! command -v uv >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then brew install uv; else curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"; fi
fi

export UV_CACHE_DIR="$RUNTIME/uv-cache"
if [ ! -x "$PYTHON" ]; then
  uv venv --python 3.12 --managed-python "$RUNTIME/tts-venv"
fi
uv pip install --python "$PYTHON" -r "$HERE/requirements.txt"
"$PYTHON" "$HERE/download_models.py" "$@"
"$PYTHON" "$HERE/qwen_narrate.py" --check

echo
echo "Qwen3-TTS is ready. Apple silicon: the default runs on the CPU (works everywhere)."
echo "To try the Apple GPU for generation:  export QWEN_DEVICE=mps PYTORCH_ENABLE_MPS_FALLBACK=1   (untested here)"
