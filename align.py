"""Word-level alignment of voice/voice.wav -> voice/words.json ([{w, s, e}] in seconds), mapped onto the script words."""
import difflib, json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))   # parent of shorts-production/
os.environ["HF_HOME"] = os.path.join(ROOT, "shorts-runtime", "huggingface")
os.environ["HF_HUB_CACHE"] = os.path.join(os.environ["HF_HOME"], "hub")
from faster_whisper import WhisperModel
wav = sys.argv[1]
script = open(sys.argv[2], encoding="utf-8-sig").read().split()
model = WhisperModel("base.en", device="cpu", compute_type="int8")
import soundfile, numpy as np
from scipy.signal import resample_poly
sig, sr = soundfile.read(wav, dtype="float32")
sig = sig if sig.ndim == 1 else sig.mean(1)
sig = resample_poly(sig, 16000, sr).astype(np.float32)
segs, _ = model.transcribe(sig, word_timestamps=True, language="en", beam_size=5, vad_filter=False)
heard = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
print("heard :", " ".join(h[0] for h in heard))
a, b = [norm(x) for x in script], [norm(h[0]) for h in heard]
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
out = [None] * len(script)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1): out[i1 + k] = (heard[j1 + k][1], heard[j1 + k][2])
    elif tag in ("replace",):
        n, m = i2 - i1, j2 - j1                       # spread the heard span over the script words
        s0, e0 = heard[j1][1], heard[j2 - 1][2]
        for k in range(n): out[i1 + k] = (s0 + (e0 - s0) * k / n, s0 + (e0 - s0) * (k + 1) / n)
# fill gaps (script words nobody heard) by interpolation
for i, v in enumerate(out):
    if v is None:
        l = next((j for j in range(i - 1, -1, -1) if out[j]), None); r = next((j for j in range(i + 1, len(out)) if out[j]), None)
        s0 = out[l][1] if l is not None else 0.0; e0 = out[r][0] if r is not None else heard[-1][2]
        out[i] = (s0, max(s0 + 0.05, min(e0, s0 + 0.3)))
words = [{"w": w, "s": round(s, 3), "e": round(e, 3)} for w, (s, e) in zip(script, out)]
json.dump(words, open(sys.argv[3], "w"), indent=1)
for x in words: print(f'{x["s"]:6.2f} {x["e"]:6.2f}  {x["w"]}')
