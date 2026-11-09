#!/usr/bin/env bash
# Build the short step by step (or all at once):   bash scripts/make-short.sh [voice|mix|render|all]
#   voice   Qwen narration from narration.txt + delivery.json -> voice/voice.wav, word timings (words.json)
#   mix     voice + synthesized ambience / SFX / light score -> audio/mix.wav  (-14 LUFS)
#   render  Remotion 1440x2560 render, mux the mix, frame-by-frame QA -> out/okene_final.mp4
# Environment knobs:  CONC=3 (parallel render tabs)  GL=angle  REMOTION_TMP=/path/with/space  FFMPEG=...
set -euo pipefail

SHORT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$SHORT/../.." && pwd)"
SKILL="$ROOT/claude-animated-shorts"
PY="$ROOT/shorts-runtime/tts-venv/bin/python"
[ -x "$PY" ] || { echo "Run scripts/setup-mac.sh first."; exit 1; }
cd "$SHORT"
mkdir -p voice/archive out remotion/public/voice

step_voice() {
  # qwen_narrate refuses to overwrite a take: archive the old one first. Beats that did not change are reused from voice/beats/.
  if [ -f voice/voice.wav ]; then mv voice/voice.wav "voice/archive/voice-$(date +%Y%m%d-%H%M%S).wav"; fi
  "$PY" -B "$SKILL/templates/voice/qwen_narrate.py" --workspace "$SHORT"
  cp voice/voice.wav voice/archive/model-raw-current.wav
  "$PY" -B finish_voice.py                                        # clean silence cuts only (a model stumble), no stretching
  "$PY" -I align.py voice/voice.wav narration.txt voice/words_raw.json
  "$PY" -B retime.py                                              # snap word times to the real speech edges
  cp voice/voice.wav remotion/public/voice/voice.wav
}

step_mix() { "$PY" -B audio/okene_mix.py; }

step_render() {
  cd "$SHORT/remotion"
  [ -d node_modules ] || npm ci --no-audit --no-fund
  GL="${GL:-angle}" CONC="${CONC:-3}" node scripts/render.mjs ../out/video_silent.mp4 4/3
  cd "$SHORT"
  ffmpeg -v error -y -i out/video_silent.mp4 -i audio/mix.wav -map 0:v:0 -map 1:a:0 \
    -vf "scale=in_range=full:out_range=tv,format=yuv420p" -c:v libx264 -preset slow -crf 14 \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart out/okene_final.mp4
  "$PY" -B scripts/qa_shots.py > out/shots.json
  "$PY" -B remotion/scripts/short_qa.py out/okene_final.mp4 out/qa out/shots.json
  echo "Done: $SHORT/out/okene_final.mp4"
}

case "${1:-all}" in
  voice) step_voice ;;
  mix) step_mix ;;
  render) step_render ;;
  all) step_voice; step_mix; step_render ;;
  *) echo "usage: $0 [voice|mix|render|all]"; exit 1 ;;
esac
