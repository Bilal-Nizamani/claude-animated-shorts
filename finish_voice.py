"""Clean edits on the model's raw take (no stretching, no pitch change). Raw take stays in voice/archive/.
Edits are silence cuts only (asserted): the model sometimes stumbles ("a ... huge") with a pause in the middle of a phrase."""
import os
import numpy as np
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
x, sr = sf.read(os.path.join(HERE, "voice", "archive", "model-raw-current.wav"), dtype="float32")
x = x if x.ndim == 1 else x.mean(1)
def silent_run(lo, hi, thr=0.0015, margin=0.045):
    """the longest truly silent stretch inside [lo, hi] s, shrunk by a margin on both sides so the word edges stay untouched"""
    env = np.abs(x[int(lo * sr):int(hi * sr)])
    quiet = np.convolve((env < thr).astype(float), np.ones(int(0.005 * sr)), "same") >= int(0.005 * sr) * 0.99
    best, start = (0, 0), None
    for i, q in enumerate(list(quiet) + [False]):
        if q and start is None:
            start = i
        if not q and start is not None:
            best = max(best, (i - start, start)); start = None
    n, st = best
    return lo + st / sr + margin, lo + (st + n) / sr - margin


# a stumble = a silent gap of 0.2 s+ inside the phrase "a huge swell" region (7.0-8.2 s); drop the middle of it, keep a short natural gap
CUTS = []
lo, hi = silent_run(6.9, 8.3)
if hi - lo > 0.06:
    CUTS.append((lo, hi))
keep = np.ones(len(x), bool)
for a, b in CUTS:
    assert np.abs(x[int(a * sr):int(b * sr)]).max() < 0.002, f"cut {a:.3f}-{b:.3f} is not silence"
    print(f"cutting {a:.3f}-{b:.3f} s ({b - a:.2f} s of silence)")
    keep[int(a * sr):int(b * sr)] = False
if not CUTS:
    print("no stumble found, nothing cut")
y = x[keep]
sf.write(os.path.join(HERE, "voice", "voice.wav"), y, sr, subtype="PCM_24")
print("raw", round(len(x) / sr, 2), "s -> final", round(len(y) / sr, 2), "s")
