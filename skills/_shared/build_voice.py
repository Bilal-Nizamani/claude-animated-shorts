#!/usr/bin/env python3
"""Build the narration audio from a script and its delivery plan (made by delivery_plan.py).
usage:  python build_voice.py <workspace> [--speaker Aiden] [--candidates 2] [--stretch atempo|rubberband] [--name voice_final]
workspace/ must contain narration.txt, delivery.json, plan.json.  Needs the venv from templates/voice/setup-qwen.sh (Qwen3-TTS 1.7B CustomVoice).
Steps: generate N candidates per take with the take's instruction -> keep the one without a stumble (silence inside a phrase) ->
stretch each take to its target words/s (at most plan.max_stretch, atempo by default) -> soften a rough top end ->
set the pause after every sentence to the measured value -> push the planned words (+dB) -> voice EQ + compression ->
master to the planned loudness (limiter, true peak <= -1.2 dBTP).  Writes <name>.wav / .m4a, <name>_words.json, voice_report.md.
Never use it to imitate a real person's voice: the voice is a preset narrator (or a voice you have permission to clone, see references)."""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

import numpy as np
import soundfile as sf
from scipy import ndimage
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))


def find_repo():
    """the checkout that holds templates/voice: SHORTS_REPO, two folders up (inside the repo), or a claude-animated-shorts folder near here / in ~/shorts"""
    cands = [os.environ.get("SHORTS_REPO"), os.path.abspath(os.path.join(HERE, "..", "..")), os.path.join(os.getcwd(), "claude-animated-shorts"), os.path.join(os.path.dirname(os.getcwd()), "claude-animated-shorts"),
             os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), "claude-animated-shorts"), os.path.expanduser("~/shorts/claude-animated-shorts")]
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "templates", "voice", "qwen_narrate.py")):
            return os.path.abspath(c)
    raise SystemExit("Cannot find the claude-animated-shorts checkout (templates/voice). Set SHORTS_REPO=/path/to/claude-animated-shorts")


REPO = find_repo()
VOICE = os.path.join(REPO, "templates", "voice")
RUNTIME = os.path.join(os.path.dirname(REPO), "shorts-runtime")
sys.path.insert(0, VOICE)
sys.path.insert(0, os.path.join(REPO, "templates", "audio"))
os.environ["HF_HOME"] = os.path.join(RUNTIME, "huggingface")
os.environ["HF_HUB_CACHE"] = os.path.join(os.environ["HF_HOME"], "hub")
from qwen_narrate import load_model, narrator_synthesizer, rubberband, find_ffmpeg  # noqa: E402
from dsp import SR, ns, dbg, hp, peq, shelf, integrated, true_peak, write_wav  # noqa: E402

log = lambda *a: print(*a, flush=True)
clean = lambda w: "".join(c for c in w.lower() if c.isalnum() or c == "'")


def silent_runs(x, sr, thr=0.0015, min_len=0.10):
    """[(start_s, end_s)] of silence between the first and last sound"""
    env = np.abs(x)
    loud = np.flatnonzero(env > 0.02)
    a, b = loud[0], loud[-1]
    q = np.convolve((env[a:b] < thr).astype(float), np.ones(int(0.01 * sr)), "same") >= int(0.01 * sr) * 0.99
    runs, start = [], None
    for i, v in enumerate(list(q) + [False]):
        if v and start is None:
            start = i
        if not v and start is not None:
            if (i - start) / sr >= min_len:
                runs.append(((a + start) / sr, (a + i) / sr))
            start = None
    return runs


def stretch(x, T, how):
    if how == "rubberband":
        return rubberband(x.astype(np.float32), SR, T, 0.0).astype(np.float64)
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x.astype(np.float32), SR, subtype="FLOAT")
        subprocess.run([find_ffmpeg(), "-v", "error", "-y", "-i", a, "-af", f"atempo={T}", "-c:a", "pcm_f32le", b], check=True)
        return sf.read(b, dtype="float64")[0]


def hf_db(x):
    from scipy import signal
    f, P = signal.welch(x, SR, nperseg=4096)
    return 10 * np.log10(P[f > 6000].sum() / P.sum() + 1e-12)


def set_pauses(x, wanted, tol=0.04):
    """inside one take, bring the silences between sentences to the planned lengths (only when the number of silences matches)"""
    runs = [r for r in silent_runs(x, SR, min_len=0.08)]
    if len(runs) != len(wanted):
        return x, False
    out, last = [], 0
    for (s, e), w in zip(runs, wanted):
        out.append(x[last:int(s * SR)])
        out.append(np.zeros(int(round(w * SR))))
        last = int(e * SR)
    out.append(x[last:])
    return np.concatenate(out), True


def compress(x, thr_db, ratio, makeup_db=2.5):
    env = ndimage.uniform_filter1d(np.abs(x), ns(0.012))
    env = ndimage.uniform_filter1d(ndimage.maximum_filter1d(env, ns(0.03)), ns(0.06))
    over = np.maximum(0.0, 20 * np.log10(env + 1e-9) - thr_db)
    return x * dbg(-(1 - 1 / ratio) * over + makeup_db)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("--speaker", default="Aiden")
    ap.add_argument("--candidates", type=int, default=2)
    ap.add_argument("--stretch", choices=["atempo", "rubberband"], default="atempo")
    ap.add_argument("--name", default="voice_final")
    a = ap.parse_args()
    W = os.path.abspath(a.workspace)
    paras = [p.strip() for p in open(os.path.join(W, "narration.txt"), encoding="utf-8-sig").read().strip().split("\n\n") if p.strip()]
    delivery = json.load(open(os.path.join(W, "delivery.json"), encoding="utf-8-sig"))
    plan = json.load(open(os.path.join(W, "plan.json")))
    meta, takes = plan["meta"], plan["takes"]
    assert len(paras) == len(delivery) == len(takes), "narration.txt, delivery.json and plan.json do not describe the same takes"
    os.makedirs(os.path.join(W, "takes"), exist_ok=True)
    cfg = json.load(open(os.path.join(VOICE, "qwen.json"), encoding="utf-8-sig"))
    t0 = time.time()
    model = load_model(cfg["style_model"], cfg["style_revision"], dtype=cfg.get("style_dtype", "float32"))
    log(f"model loaded in {time.time() - t0:.0f} s")
    syn = narrator_synthesizer(model, speaker=a.speaker, language="English")
    chosen = []
    for i, (text, d) in enumerate(zip(paras, delivery)):
        cands = []
        for c in range(a.candidates):
            cache = os.path.join(W, "takes", f"take{i + 1}_cand{c + 1}.wav")
            if os.path.exists(cache):
                x, sr = sf.read(cache, dtype="float32")
            else:
                t1 = time.time()
                audio, sr = syn(text, d["instruct"])
                x = np.asarray(audio[0], dtype=np.float32)
                sf.write(cache, x, sr)
                log(f"take {i + 1} candidate {c + 1}: {len(x) / sr:.1f} s speech in {time.time() - t1:.0f} s")
            n_sent = len(takes[i]["sentences"])
            runs = silent_runs(x, sr, min_len=0.12)
            inner = [e - s for s, e in runs]
            # a clean take has about one silence per sentence boundary and none longer than 0.7 s
            score = abs(len(inner) - (n_sent - 1)) * 1.0 + sum(max(0, g - 0.7) for g in inner)
            cands.append((score, x, sr, c + 1))
        best = min(cands, key=lambda k: k[0])
        log(f"  take {i + 1}: keeping candidate {best[3]} (score {best[0]:.2f})")
        chosen.append(best)
    del model
    parts, report = [], []
    for i, (score, x, sr, c) in enumerate(chosen):
        y = resample_poly(x.astype(np.float64), SR, sr) if sr != SR else x.astype(np.float64)
        idx = np.flatnonzero(np.abs(y) > 0.01)
        y = y[max(0, idx[0] - ns(0.06)):idx[-1] + ns(0.08)]
        sil = sum(e - s for s, e in silent_runs(y, SR, min_len=0.2))
        rate = takes[i]["words"] / max(0.5, len(y) / SR - sil)
        T = float(min(meta["max_stretch"], max(1.0, takes[i]["target_wps"] / rate)))
        if T > 1.01:
            y = stretch(y, T, a.stretch)
        if hf_db(y) > -24.0:
            y = shelf(y, 5500, -4.5, "high")
            y = peq(y, 7500, -3.0, 1.2)
        wanted = [takes[i]["inner_pauses_s"][str(s)] for s in takes[i]["sentences"][:-1]]
        y, ok = set_pauses(y, wanted)
        report.append(f"take {i + 1}: model {rate:.2f} words/s -> x{T:.2f} -> target {takes[i]['target_wps']}; sentence pauses {'set to the plan' if ok else 'left as generated (silence count differs)'}")
        parts.append(y)
    t = meta["lead_in_s"]
    total = t + sum(len(p) / SR for p in parts) + sum(tk["pause_after_s"] for tk in takes[:-1]) + meta["tail_s"]
    v = np.zeros(ns(total))
    starts = []
    for p, tk in zip(parts, takes):
        v[ns(t):ns(t) + len(p)] = p
        starts.append((t, t + len(p) / SR))
        t += len(p) / SR + tk["pause_after_s"]
    # whisper word times (also the output used to sync pictures) and the planned pushes
    from faster_whisper import WhisperModel
    seg, _ = WhisperModel("base.en", device="cpu", compute_type="int8").transcribe(resample_poly(v, 1, 3).astype(np.float32), word_timestamps=True, language="en", beam_size=5)
    words = [(w.word.strip(), w.start, w.end) for s_ in seg for w in s_.words]
    keys, used = [(0.0, 0.0)], set()
    for g in plan["word_gains"]:
        a0, b0 = starts[g["take"] - 1]
        for j, (w, s, e) in enumerate(words):
            if a0 - 0.2 <= s <= b0 and clean(w) == clean(g["word"]) and (g["take"], j) not in used:
                used.add((g["take"], j))
                keys += [(s, g["gain_db"]), (e, g["gain_db"])]
                break
    keys.append((total, 0.0))
    keys.sort()
    v = v * dbg(ndimage.uniform_filter1d(np.interp(np.arange(len(v)) / SR, [k[0] for k in keys], [k[1] for k in keys]), ns(0.09)))
    short = meta["format"] == "short"
    x = hp(v, 90, 2)
    x = peq(x, 260, -4.0, 0.9)
    x = peq(x, 480, -1.0, 1.0)
    x = peq(x, 3500, 3.0, 0.8)
    x = shelf(x, 7000, 1.0, "high")
    x = compress(x, -26.0 if short else -24.0, 2.8 if short else 2.2)
    st = np.stack([x, x])
    st *= dbg(meta["loudness_lufs"] - integrated(st))
    ceil = -1.8
    for _ in range(6):
        pk = ndimage.maximum_filter1d(np.abs(st).max(0), ns(0.008))
        out = st * ndimage.uniform_filter1d(np.minimum(1.0, 10 ** (ceil / 20) / np.maximum(pk, 1e-9)), ns(0.005))
        if true_peak(out) <= -1.2:
            break
        ceil -= 0.6
    out[:, -ns(0.05):] *= np.linspace(1, 0, ns(0.05))
    wav = os.path.join(W, a.name + ".wav")
    write_wav(wav, out)
    subprocess.run([find_ffmpeg(), "-v", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "256k", wav.replace(".wav", ".m4a")], check=True)
    json.dump([dict(w=w, s=round(s, 3), e=round(e, 3)) for w, s, e in words], open(os.path.join(W, a.name + "_words.json"), "w"), indent=1)
    rep = ["# Voice report", "", f"length {len(x) / SR:.1f} s (plan expected {meta['expected_seconds']} s), {integrated(out):.1f} LUFS (target {meta['loudness_lufs']}), true peak {true_peak(out):.2f} dBTP", ""] + report
    open(os.path.join(W, "voice_report.md"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    log("\n".join(rep))
    log("DONE", wav)


if __name__ == "__main__":
    main()
