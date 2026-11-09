"""Word timings for the Okene short: Whisper words (voice/words_raw.json, mapped onto the script) snapped to the real speech edges
found in the audio energy. Whisper starts words 0.1-0.4 s early after a pause; the energy says when sound really begins / ends.
Every cut, cue and sound effect is keyed to these numbers.  usage: python retime.py"""
import json
import os
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(HERE, *a)
x, sr = sf.read(P("voice", "voice.wav"), dtype="float32")
x = x if x.ndim == 1 else x.mean(1)
words = json.load(open(P("voice", "words_raw.json")))
hop = int(sr * 0.01)
rms = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
on = rms > 0.0175 * np.abs(x).max()
fr = lambda t: min(len(on) - 1, max(0, int(round(t / 0.01))))
out, prev_end = [], 0.0
for w in words:
    s, e = w["s"], w["e"]
    a, b = fr(s), fr(e)
    if not on[a]:                                   # word "starts" in silence: move to the first sound inside the word
        hit = np.flatnonzero(on[a:b + 1])
        if len(hit):
            s = (a + hit[0]) * 0.01
    if not on[b]:                                   # word "ends" in silence: back to the last sound inside the word
        hit = np.flatnonzero(on[fr(s):b + 1])
        if len(hit):
            e = (fr(s) + hit[-1] + 1) * 0.01
    s = max(s, prev_end); e = max(e, s + 0.04); prev_end = e
    out.append({"w": w["w"], "s": round(s, 3), "e": round(e, 3)})
json.dump(out, open(P("voice", "words.json"), "w"), indent=1)
json.dump(out, open(P("remotion", "src", "videos", "okene", "words.json"), "w"))
print("duration", round(len(x) / sr, 2))
for w in out:
    print(f"{w['s']:6.2f} {w['e']:6.2f}  {w['w']}")
