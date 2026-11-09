# Sound of the Okene 10 s test: voice (gain only) + synthesized ambience / SFX + an original dark drone, mixed to -14 LUFS.
# Mix: the voice leads. Feedback (v1): music was too much -> music 14 LU (a light, audible score) and ambience 19 LU under the voice, hits 5 LU under it.
# Everything is keyed to voice/words.json and the same constants as remotion/src/videos/okene/story.ts.
# Run with the Qwen venv python:  python audio/okene_mix.py
import json
import os
import sys
import numpy as np
from scipy import ndimage
from dsp import (SR, ns, tt, dbg, rng, lp, hp, bp, colored, smooth_noise, ramp, fades, curve, phase, modal, pan, st, place, make_ir,
                 convolve_st, integrated, momentary_max, true_peak, read_wav, write_wav, short_term, lra, peq, shelf)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORDS = json.load(open(os.path.join(ROOT, "voice", "words.json")))
FPS = 30
word = lambda text, nth=0: [w for w in WORDS if "".join(c for c in w["w"].lower() if c.isalnum()) == text][nth]
DUR = round((WORDS[-1]["e"] + 0.5) * FPS) / FPS            # 10.7 s = the picture length exactly
N = ns(DUR)
A3 = round((word("may")["s"] - 2 / FPS) * FPS) / FPS       # sea shot + flash (5.9 s)
A2 = round((word("without")["s"] - 2 / FPS) * FPS) / FPS   # cabin cut (3.93 s)
T_FLIPS = word("flips")["s"]
T_ROLL0 = T_FLIPS - 0.36
T_SPLASH = T_ROLL0 + 0.98
CREW_LAND = [T_ROLL0 + 0.2 + f + 1.0 + 0.08 * i for i, f in enumerate([0, 0.05, 0.1])]


def log(*a):
    print(*a, flush=True)


def buf():
    return np.zeros((2, N))


def env_between(t0, t1, a=0.2, d=0.2):
    """0..1 window over [t0, t1] with soft edges"""
    t = np.arange(N) / SR
    return np.clip(np.minimum((t - t0) / max(a, 1e-3), (t1 - t) / max(d, 1e-3)), 0, 1)


# ------------------------------------------------------------------ voice
vx, sr = read_wav(os.path.join(ROOT, "voice", "voice.wav"))
voice = np.zeros((2, N))


def compress(x, thr_db=-23.0, ratio=2.3, makeup_db=2.5):
    """gentle feed-forward compressor (smoothed peak envelope), evens out the phrases so the voice stays forward"""
    env = ndimage.uniform_filter1d(np.abs(x), ns(0.012))
    env = ndimage.uniform_filter1d(ndimage.maximum_filter1d(env, ns(0.03)), ns(0.06))
    over = np.maximum(0.0, 20 * np.log10(env + 1e-9) - thr_db)
    return x * dbg(-(1 - 1 / ratio) * over + makeup_db)


# per-word level shape (dB), keyed to words.json: the model reads the date as loud as the action; the story should build instead.
# date calm and low -> "a huge swell" rising -> a punch on "flips" -> "upside down" lands strong. Words not listed keep their level.
LEVELS = {"in": -7.0, "may": -7.0, "twenty": -7.0, "thirteen": -6.5, "huge": -1.0, "swell": 1.0, "flips": 3.5, "his": 3.0, "tugboat": 3.0, "upside": 3.5, "down": 2.0}


def word_levels(x):
    norm = lambda t: "".join(c for c in t.lower() if c.isalnum())
    keys = [(0.0, 0.0)]
    seen_a = False
    for i, w in enumerate(WORDS):
        k = norm(w["w"])
        g = LEVELS.get(k)
        if k == "a" and i + 1 < len(WORDS) and norm(WORDS[i + 1]["w"]) == "huge":
            g = -4.0
        if g is not None and (k != "in" or i > 8):
            keys += [(w["s"], g), (w["e"], g)]
    keys.append((WORDS[-1]["e"] + 0.2, 0.0))
    t = np.arange(len(x)) / SR
    gdb = np.interp(t, [a for a, _ in keys], [b for _, b in keys])
    gdb = ndimage.uniform_filter1d(gdb, ns(0.09))
    return x * dbg(gdb)


def voice_chain(x):
    """TTS voices sit boxy (150-400 Hz hump) and dull (almost nothing above 3 kHz, nothing above 12 kHz). Fix that first."""
    x = hp(x, 90, 2)                      # no rumble under the voice
    x = peq(x, 260, -4.5, 0.9)            # the boxy 'in a tube' hump
    x = peq(x, 480, -1.5, 1.0)
    x = peq(x, 3500, 4.5, 0.8)            # presence: consonants, intelligibility
    x = shelf(x, 7000, 1.5, "high")       # air
    x = compress(x)
    air = hp(np.tanh(30 * hp(x, 4000, 2)) / 30, 9000, 2)    # the model stops at 12 kHz: synthesize a little top end
    return x + 0.3 * air


vm = voice_chain(word_levels(vx.mean(0)))
place(voice, vm, 0.0)

# ------------------------------------------------------------------ ambience beds
r = rng(11)
t_all = np.arange(N) / SR


def stereo_noise(slope, seed, lo=20.0):
    rr = rng(seed)
    return np.stack([colored(N, rr, slope, lo), colored(N, rr, slope, lo)])


# open water: deep rumble + dull body, slow movement (0 -> cabin cut, tails into the cabin)
rumble = hp(lp(stereo_noise(2.0, 21), 180, 2), 70, 2) * (0.7 + 0.3 * smooth_noise(N, r, 0.4))
body = bp(stereo_noise(1.0, 22), 160, 1300, 2) * 0.16 * (0.6 + 0.4 * smooth_noise(N, r, 0.25))
water_open = (rumble * 0.3 + body) * env_between(0.0, A3 + 0.2, 0.05, 0.25)
# the cabin: closed, tighter, a faint metallic hum and trapped-air hiss
hum = np.sin(2 * np.pi * 196.6 * t_all) * 0.012
room = (lp(stereo_noise(1.2, 23), 600, 2) * 0.22 + hp(lp(stereo_noise(0.4, 24), 3200, 2), 900, 1) * 0.012) + hum
cabin_bed = room * env_between(A2 - 0.05, A3 + 0.1, 0.12, 0.2)
# surface: wind + sea wash that grows with the swell, tug engine, rising swell rumble
gust = 0.55 + 0.45 * smooth_noise(N, r, 0.7)
wind = bp(stereo_noise(1.0, 31), 280, 2400, 2) * 0.1 * gust
swell_k = np.clip((t_all - (T_ROLL0 - 2.2)) / 2.0, 0, 1)
wash = lp(stereo_noise(1.5, 32), 900, 2) * (0.1 + 0.2 * np.abs(np.sin(2 * np.pi * 0.21 * t_all + 0.7))) * (0.7 + 0.8 * swell_k)
swell_rumble = hp(lp(stereo_noise(2.0, 33), 240, 2), 70, 2) * 0.25 * np.clip((t_all - 6.4) / 2.4, 0, 1) ** 1.6 * (t_all < T_SPLASH + 0.08)
sea_bed = (wind + wash + swell_rumble) * env_between(A3 - 0.03, DUR, 0.05, 0.1)
# diesel throb (about 13 pulses / s through a low resonant filter); it dies as she rolls
pulse = np.zeros(N)
for k in range(int((T_ROLL0 + 1.1 - A3) * 13)):
    tk = A3 + k / 13.0
    pulse[ns(tk)] = 0.9 + 0.1 * np.sin(k * 1.7)
eng = lp(np.convolve(pulse, modal(0.12, [(46, 1.0, 0.045), (92, 0.5, 0.03), (138, 0.25, 0.02)], r), "same")[:N], 260, 2)
eng_env = env_between(A3, T_ROLL0 + 1.1, 0.1, 0.55) * (1 - 0.35 * np.clip((t_all - T_ROLL0) / 1.0, 0, 1))
engine = np.stack([eng, eng]) * 0.5 * eng_env

# ------------------------------------------------------------------ SFX events
sfx = buf()
reverb_send = buf()
ir_ship = make_ir(1.6, 5, hf=1.6)


def bubble_blip(f0, dur=0.075):
    t = tt(dur)
    f = f0 * (1 + 1.3 * t / dur)
    return fades(np.sin(phase(f)) * np.exp(-t / (dur * 0.32)), 0.002, 0.02)


def bubbles(t0, t1, count, lo=380, hi=1500, gain=0.08, seed=4, p=0.7):
    rr = rng(seed)
    for _ in range(count):
        tb = rr.uniform(t0, t1)
        place(sfx, pan(lp(bubble_blip(rr.uniform(lo, hi), rr.uniform(0.05, 0.11)), 4200, 1) * gain * rr.uniform(0.5, 1.0), rr.uniform(-p, p)), tb)


def creak(t0, base, dur=1.3, gain=0.12, seed=1, drop=0.07):
    rr = rng(seed)
    modes = [(base * m, a, dur * 0.5 * tau) for m, a, tau in [(1.0, 1.0, 1.0), (1.51, 0.65, 0.8), (2.43, 0.4, 0.6), (3.7, 0.22, 0.45), (5.4, 0.1, 0.3)]]
    y = modal(dur, modes, rr, glide=drop, glide_tau=dur * 0.45)
    slip = 0.55 + 0.45 * smooth_noise(len(y), rr, 22)               # stick-slip amplitude
    y = y * slip * ramp(ns(0.03))[np.minimum(np.arange(len(y)), ns(0.03) - 1)]
    y = fades(y, 0.02, dur * 0.4)
    place(sfx, pan(y * gain, rr.uniform(-0.4, 0.4)), t0)
    place(reverb_send, y * gain, t0)


def sub_thump(t0, f0=52, f1=36, dur=0.7, tau=0.26, gain=0.7):
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t / 0.12)
    y = np.sin(phase(f)) * np.exp(-t / tau) * (1 - np.exp(-t / 0.004))
    place(sfx, y * gain, t0)


def splash(t0, dur=1.0, gain=0.5, lo=5200, hi=700, seed=8, body=0.6):
    rr = rng(seed)
    n = ns(dur)
    z = rr.standard_normal(n)
    # noise whose bandwidth collapses as the water settles
    out = np.zeros(n)
    edges = np.linspace(0, n, 9).astype(int)
    for a, b in zip(edges[:-1], edges[1:]):
        k = (a + b) / 2 / n
        cut = hi + (lo - hi) * np.exp(-3.2 * k)
        out[a:b] = lp(z, cut, 2)[a:b]
    e = (1 - np.exp(-np.arange(n) / SR / 0.006)) * np.exp(-np.arange(n) / SR / (dur * 0.33))
    y = out * e
    y += body * lp(rr.standard_normal(n), 220, 2) * np.exp(-np.arange(n) / SR / (dur * 0.5))
    place(sfx, pan(y * gain, 0.0), t0)
    place(reverb_send, y * gain * 0.4, t0)


# --- hook: open water, hull groans, bubbles, one distant big metallic call
bubbles(0.3, A2 - 0.1, 11, seed=3)
creak(0.95, 84, 1.7, 0.12, seed=2)
creak(2.45, 63, 2.0, 0.14, seed=3, drop=0.1)
# --- cabin: drips, breaths, a bubble sipping at the wall
rr = rng(41)
for td in [4.34, 4.98, 5.42]:
    y = modal(0.5, [(rr.uniform(1500, 2100), 1.0, 0.07), (rr.uniform(2600, 3300), 0.3, 0.04)], rr, glide=0.25, glide_tau=0.03)
    place(sfx, pan(fades(y, 0.001, 0.05) * 0.06, rr.uniform(-0.5, 0.5)), td)
    place(reverb_send, fades(y, 0.001, 0.05) * 0.06, td)


def breath(t0, dur, gain, inhale=True):
    rr2 = rng(int(t0 * 100))
    z = bp(rr2.standard_normal(ns(dur)), 380, 2600, 2)
    k = np.linspace(0, 1, len(z))
    e = np.sin(np.pi * k) ** 1.6 * (1.0 if inhale else (1.2 - 0.4 * k))
    place(sfx, pan(fades(z * e, 0.04, 0.12) * gain, 0.0), t0)


breath(A2 + 0.12, 0.62, 0.05)                                    # before "without"
breath(5.18, 0.78, 0.065, inhale=False)                          # long exhale after "tank."
bubbles(A2 + 0.2, A3 - 0.1, 5, 800, 2200, 0.06, seed=5)
creak(5.05, 140, 0.9, 0.06, seed=6)
# --- cut to the surface: flash hit (riser -> sub thump -> air)
t_in = np.arange(ns(0.55)) / SR
riser = bp(rng(51).standard_normal(len(t_in)), 600, 7000, 2) * (t_in / 0.55) ** 2.4
place(sfx, fades(riser * 0.22, 0.01, 0.03), A3 - 0.55)
sub_thump(A3 - 0.02, 58, 34, 0.9, 0.32, 0.62)
splash(A3 + 0.0, 0.7, 0.16, 7200, 1200, seed=9, body=0.2)
# --- the capsize: rising groan from the hull, the lean, the roll, the slap
creak(T_ROLL0 - 0.55, 74, 1.3, 0.16, seed=10, drop=0.05)
creak(T_ROLL0 - 0.05, 52, 1.9, 0.26, seed=11, drop=0.2)
creak(T_ROLL0 + 0.35, 96, 1.2, 0.14, seed=12, drop=0.12)
splash(T_ROLL0 + 0.55, 0.55, 0.14, 4200, 800, seed=13, body=0.2)  # water running off the deck
sub_thump(T_SPLASH - 0.01, 60, 32, 1.2, 0.34, 0.95)
splash(T_SPLASH, 1.4, 0.62, 6800, 650, seed=14, body=0.9)
for i, tl in enumerate(CREW_LAND):
    splash(tl, 0.55, 0.2 - 0.03 * i, 4600, 900, seed=15 + i, body=0.25)
bubbles(T_SPLASH + 0.15, DUR - 0.1, 22, 300, 1300, 0.09, seed=6, p=0.9)
creak(T_SPLASH + 0.3, 70, 1.4, 0.14, seed=16, drop=0.25)

sfx_wet = convolve_st(reverb_send, ir_ship)

# ------------------------------------------------------------------ music: a LIGHT original score that follows the picture
# seabed (hook): a warm D-minor pad floats and a soft vibraphone line descends D - A - F  ("bottom of the ocean");
# cabin: the pad thins to two notes, a fragile music-box line (C - A);  surface: Bb-major pad and a soft plucked pattern that
# speeds up and swells with the swell;  after the slap: the pad settles back to D and one music-box note resolves the end.
import instruments as ins
from instruments import m2f
rm = rng(70)
mus = np.zeros((2, N))


def put(x, t, g=1.0):
    place(mus, x, t, g)


put(ins.pad([m2f(50), m2f(57), m2f(65)], A2 + 0.3, vel=0.55, r=rm, att=1.3, rel=1.0, warm=650), 0.0)              # Dm  (D3 A3 F4)
put(ins.pad([m2f(50), m2f(57)], A3 - A2 + 0.2, vel=0.42, r=rm, att=0.5, rel=0.8, warm=600), A2 - 0.1)              # cabin: thin
put(ins.pad([m2f(46), m2f(53), m2f(62)], T_SPLASH - A3 + 0.15, vel=0.55, r=rm, att=0.45, rel=0.25, warm=900), A3 - 0.05)   # Bb  (Bb2 F3 D4)
put(ins.pad([m2f(50), m2f(57), m2f(62)], DUR - T_SPLASH + 0.2, vel=0.5, r=rm, att=0.12, rel=1.6, warm=700), T_SPLASH)       # settle on D (D3 A3 D4)
for tn, m, kind in [(0.6, 74, "v"), (1.85, 69, "v"), (3.0, 65, "v"), (4.75, 72, "m"), (5.45, 69, "m")]:
    put(ins.vibes(m2f(m), vel=0.55, r=rm, dur=2.2, damp=1.7) if kind == "v" else ins.musicbox(m2f(m), vel=0.5, r=rm, dur=1.8), tn, 0.8)
# surface: a plucked pattern D4 F4 A4 D5, notes closer and louder as the swell grows
notes, tn, k = [62, 65, 69, 74], A3 + 0.35, 0
while tn < T_ROLL0 + 0.55:
    u = (tn - A3) / (T_ROLL0 - A3)
    put(ins.pluck(m2f(notes[k % 4]), vel=0.25 + 0.4 * min(1.0, max(0.0, u)), r=rm, dur=0.7, bright=0.4), tn, 0.8)
    tn += 0.27 - 0.12 * min(1.0, max(0.0, u)); k += 1
put(ins.vibes(m2f(50), vel=0.6, r=rm, dur=3.2, damp=2.8), T_SPLASH + 0.02, 0.9)                                    # a low D rings after the slap
put(ins.musicbox(m2f(86), vel=0.45, r=rm, dur=1.8), min(DUR - 1.4, T_SPLASH + 0.9), 0.7)                          # D6: the quiet resolve
music = mus * curve(N, [(0, 0.0), (0.25, 1.0), (DUR - 0.5, 1.0), (DUR, 0.0)])
music = hp(lp(music, 6500, 1), 120, 2)

# ------------------------------------------------------------------ duck the music under the words (keyed from words.json, not the audio)
mask = np.zeros(N)
for w in WORDS:
    mask[ns(max(0, w["s"] - 0.05)):ns(w["e"] + 0.14)] = 1.0
mask = ndimage.binary_closing(mask > 0.5, structure=np.ones(ns(0.35))).astype(float)
duck = lp(mask, 6, 1)
music = music * dbg(-5.0 * duck)
sfx_bed = (water_open + cabin_bed + sea_bed + engine)
sfx_bed = sfx_bed * dbg(-3.0 * duck)                                          # beds make way a little too

# ------------------------------------------------------------------ levels (voice reference; SFX -6 dB, music -10 LU), master -14 LUFS
L_voice = integrated(voice)
log(f"voice integrated {L_voice:.1f} LUFS")
bed_stem = sfx_bed
ev_stem = sfx + sfx_wet * dbg(-9)
bed_stem = bed_stem * dbg((L_voice - 19.0) - integrated(bed_stem))               # steady ambience: 19 LU under the voice
ev_stem = ev_stem * dbg((L_voice - 5.0) - momentary_max(ev_stem))               # biggest hit (the slap): 5 LU under the voice
music = music * dbg((L_voice - 14.0) - integrated(music))                       # light but audible: 14 LU under the voice
mix = voice + bed_stem + ev_stem + music
g = -14.0 - integrated(mix)
mix *= dbg(g)
voice_s, bed_s, ev_s, music_s = [x * dbg(g) for x in (voice, bed_stem, ev_stem, music)]


def limit(x, ceil_db):
    c = dbg(ceil_db)
    pk = ndimage.maximum_filter1d(np.max(np.abs(x), axis=0), ns(0.008))
    gain = np.minimum(1.0, c / np.maximum(pk, 1e-9))
    gain = ndimage.uniform_filter1d(gain, ns(0.005))
    return x * gain


ceil = -1.6
for _ in range(6):
    out = limit(mix, ceil)
    tp = true_peak(out)
    if tp <= -1.2:
        break
    ceil -= 0.6
out = fades(out, 0.0, 0.05)
# make the very end exactly silent-ish (the picture holds on the hull; no click)
out[:, -ns(0.02):] *= np.linspace(1, 0, ns(0.02))
peak = np.abs(out).max()
log(f"limiter ceiling {ceil:.1f} dBFS  true peak {true_peak(out):.2f} dBTP  sample peak {20 * np.log10(peak):.2f} dBFS")
log(f"integrated {integrated(out):.2f} LUFS  max momentary {momentary_max(out):.2f}  LRA {lra(out):.1f} LU  length {out.shape[1] / SR:.3f} s")

write_wav(os.path.join(HERE, "mix.wav"), out)
for name, s in [("voice", voice_s), ("sfx_beds", bed_s), ("sfx_events", ev_s), ("music", music_s)]:
    write_wav(os.path.join(HERE, f"stem_{name}.wav"), s)
with open(os.path.join(HERE, "cues_okene.md"), "w", encoding="utf-8") as f:
    f.write(f"# Okene test mix cues ({DUR:.3f} s, 48 kHz stereo)\n\n"
            f"- cabin cut {A2:.2f} s, flash/sea cut {A3:.2f} s, roll starts {T_ROLL0:.2f} s, slap {T_SPLASH:.2f} s, crew splashes "
            + ", ".join(f"{t:.2f}" for t in CREW_LAND) + " s\n"
            f"- levels: voice {L_voice:.1f} LUFS ref; beds -19 LU, hits -5 LU (peak), music -20 LU; master {integrated(out):.2f} LUFS, true peak {true_peak(out):.2f} dBTP\n")
log("wrote mix.wav + stems")
