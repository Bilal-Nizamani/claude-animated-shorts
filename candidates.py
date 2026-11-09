"""Generate N candidate takes of one beat with the 1.7B model, score each for stumbles (silent gaps inside a phrase), keep the best in
the per-beat cache and save all of them to voice/candidates/ so they can be compared by ear. usage: python candidates.py <beat index 1-based> <N>"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.path.join(HERE, "..", "..", "claude-animated-shorts", "templates", "voice")
sys.path.insert(0, VOICE)
import numpy as np, soundfile as sf
from qwen_narrate import load_model, narrator_synthesizer, beat_cache_path, narration_paragraphs
idx, n = int(sys.argv[1]) - 1, int(sys.argv[2])
cfg = json.load(open(os.path.join(VOICE, "qwen.json"), encoding="utf-8-sig"))
paras = narration_paragraphs(open(os.path.join(HERE, "narration.txt"), encoding="utf-8-sig").read())
beat = json.load(open(os.path.join(HERE, "delivery.json"), encoding="utf-8-sig"))[idx]
model = load_model(cfg["style_model"], cfg["style_revision"], dtype=cfg.get("style_dtype", "float32"))
syn = narrator_synthesizer(model, speaker="Aiden", language="English")
os.makedirs(os.path.join(HERE, "voice", "candidates"), exist_ok=True)


def worst_gap(x, sr, thr=0.0015):
    env = np.abs(x)
    loud = np.flatnonzero(env > 0.02)
    a, b = loud[0], loud[-1]
    quiet = np.convolve((env[a:b] < thr).astype(float), np.ones(int(0.01 * sr)), "same") >= int(0.01 * sr) * 0.99
    worst = run = 0
    for q in quiet:
        run = run + 1 if q else 0
        worst = max(worst, run)
    return worst / sr


best = None
for k in range(n):
    t0 = time.time()
    audio, sr = syn(paras[idx], beat.get("instruct"))
    x = np.asarray(audio[0], dtype=np.float32)
    gap = worst_gap(x, sr)
    path = os.path.join(HERE, "voice", "candidates", f"beat{idx + 1}_cand{k + 1}.wav")
    sf.write(path, x, sr)
    print(f"candidate {k + 1}: {len(x) / sr:.2f} s, longest silence inside the phrase {gap:.2f} s  ({time.time() - t0:.0f} s)", flush=True)
    if best is None or gap < best[0]:
        best = (gap, x, sr, k + 1)
gap, x, sr, k = best
cache = beat_cache_path(os.path.join(HERE, "voice", "beats"), paras[idx], beat.get("instruct"), "preset|Aiden|English")
np.savez(cache, audio=x, rate=sr)
print(f"kept candidate {k} (gap {gap:.2f} s) in the beat cache", flush=True)
