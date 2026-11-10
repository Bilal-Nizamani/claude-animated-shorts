#!/usr/bin/env python3
"""Mark up a finished script with HOW TO SAY IT, from the measured delivery of short-form / long-form narrated videos.
usage:  python delivery_plan.py <script.txt> --format short|long --out <workspace folder>
Writes into the workspace folder:
  narration.txt   the script grouped into takes (blank line = new take): sentences of one mood that should flow together
  delivery.json   one entry per take for templates/voice/qwen_narrate.py: {"instruct": ..., "pause_ms": ...}
  plan.json       everything else the voice builder needs: target words/s per take, pause after every sentence, words to push (+dB), loudness target
  delivery_plan.md  a table you can read: speed, level, pitch, pause and pushed words for every sentence
Rules come from style_profiles.json (numbers measured from real videos). Sentence-type effects are shrunk toward "no change" when
the measured sample was small. Pitch cannot be set on the voice model: it is written down as guidance and goes into the instruction text."""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_check import NUM, clean, sentences  # noqa: E402

EXTREMES = {"only", "every", "first", "last", "ever", "never", "whole", "entire", "most", "least", "biggest", "best", "worst", "always", "nobody", "nothing", "everything", "everyone"}
PHASE_INSTRUCT = {
    "short": [
        "Confident and engaging, like telling a surprising true story to a friend. Clear, direct and brisk.",
        "Steady and curious, brisk, keeping the listener hooked.",
        "A little more serious and tense. Steady and brisk, weight on the numbers.",
        "Clear and matter-of-fact, explaining how it works, with a light confident touch.",
        "Settled and a little wry. Slightly slower, the last line lands low and final.",
    ],
    "long": [
        "Warm, direct and conversational, speaking to one person. Calm and unhurried.",
        "Curious and thoughtful, steady pace, explaining step by step.",
        "Engaged and a little more serious, steady pace, weight on the key facts.",
        "Clear and explanatory, friendly, making the idea easy to follow.",
        "Reflective and settled, slower, the final lines land low and calm.",
    ],
}
SHRINK_N = 30        # categories measured on fewer sentences are pulled toward "no change" in proportion


def load():
    return json.load(open(os.path.join(HERE, "style_profiles.json")))


def shrink(value, n, neutral):
    w = min(1.0, (n or 0) / SHRINK_N)
    return neutral + (value - neutral) * w


def categories(i, S, total):
    s = S[i]
    low = s.lower()
    n = len(s.split())
    c = []
    if i == 0:
        c.append("first sentence (the hook)")
    if i == 1:
        c.append("second sentence")
    if i == total - 1:
        c.append("last sentence")
    if i == total - 2:
        c.append("second to last")
    if s.endswith("?"):
        c.append("question")
    if s.endswith("!"):
        c.append("exclamation")
    if any(NUM.search(clean(w)) for w in s.split()):
        c.append("contains a number")
    if re.search(r"\b(but|yet|however)\b", low):
        c.append("contains but / yet / however")
    if re.match(r"^(but|however|yet)\b", low):
        c.append("starts with but / however / yet")
    if re.match(r"^(so|and)\b", low):
        c.append("starts with so / and")
    if re.search(r"\b(because|that's why|turns out|you see|here's)\b", low):
        c.append("explanation (because / turns out / you see)")
    if re.search(r"\b(you|your)\b", low):
        c.append("addresses you")
    if n <= 6:
        c.append("short (<= 6 words)")
    if n >= 20:
        c.append("long (>= 20 words)")
    if i > 0 and len(S[i - 1].split()) >= 16 and n <= 7:
        c.append("short punch after a long sentence")
    return c


def arc_at(arcs, frac, key):
    pos = min(9.0, max(0.0, frac * 10 - 0.5))
    a, b = int(pos), min(9, int(pos) + 1)
    va, vb = arcs[a][key], arcs[b][key]
    if va is None or vb is None:
        return 0.0
    return va + (vb - va) * (pos - a)


def pick_pushes(s):
    words = s.split()
    if len(words) < 6:
        return []
    cand = []
    for j, w in enumerate(words):
        c = clean(w)
        if NUM.search(c) and c not in {"first", "second", "third"}:
            cand.append((0, j, w, "number", 3.5))
        elif c in EXTREMES:
            cand.append((1, j, w, "extreme", 3.5))
        elif w[:1].isupper() and j > 0 and c not in {"i", "i'm", "i've", "i'll"}:
            cand.append((2, j, w, "name", 2.5))
    cand.sort()
    return [dict(word=re.sub(r"[^\w'-]", "", w), index=j, kind=k, gain_db=g) for _, j, w, k, g in cand[:1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--format", choices=["short", "long"], required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    P = load()[a.format]
    D = P["delivery"]
    kinds = D["sentence_kinds"]
    text = open(a.script, encoding="utf-8-sig").read()
    S = sentences(text)
    total = len(S)
    words_total = sum(len(s.split()) for s in S)
    base_wps = D["sentence_speed_wps"]["median"]
    pause_sentence = D["pauses"]["sentence"]["median"]
    pause_q = D["pause_positions"].get("after a question", dict(median=pause_sentence))["median"]
    pause_but = D["pause_positions"].get("before but / yet / however", dict(median=pause_sentence))["median"]
    pause_hook = D["pause_after_hook_s"]
    plan, acc = [], 0
    for i, s in enumerate(S):
        n = len(s.split())
        frac = (acc + n / 2) / words_total
        acc += n
        cats = categories(i, S, total)
        rate_f = [shrink(kinds[c]["rate"], kinds[c]["n"], 1.0) for c in cats if c in kinds and kinds[c]["rate"]]
        lvl = [shrink(kinds[c]["level"], kinds[c]["n"], 0.0) for c in cats if c in kinds and kinds[c]["level"] is not None]
        pit = [shrink(kinds[c]["pitch"], kinds[c]["n"], 0.0) for c in cats if c in kinds and kinds[c]["pitch"] is not None]
        slope = [shrink(kinds[c]["pitch_slope"], kinds[c]["n"], 0.0) for c in cats if c in kinds and kinds[c]["pitch_slope"] is not None]
        f = (sum(rate_f) / len(rate_f) if rate_f else 1.0) * arc_at(D["arcs"], frac, "rate")
        f = max(0.88, min(1.25, f))
        level = (sum(lvl) / len(lvl) if lvl else 0.0) + arc_at(D["arcs"], frac, "level")
        pitch = (sum(pit) / len(pit) if pit else 0.0) + arc_at(D["arcs"], frac, "pitch")
        end_fall = sum(slope) / len(slope) if slope else D["sentence_kinds"]["all"]["pitch_slope"]
        nxt = S[i + 1] if i + 1 < total else ""
        if i == total - 1:
            pause = D["tail_s"]["median"]
        elif i == 0:
            pause = pause_hook
        elif s.endswith("?"):
            pause = pause_q
        elif re.match(r"^(but|however|yet)\b", nxt.lower()):
            pause = pause_but
        else:
            pause = pause_sentence
        plan.append(dict(i=i, text=s, words=n, kinds=cats, speed=round(f, 2), target_wps=round(base_wps * f, 2), level_db=round(level, 1), pitch_st=round(pitch, 1), end_fall_st=round(end_fall, 1),
                         pause_after_s=round(pause, 2), push=pick_pushes(s), phase=min(4, int(frac * 5))))
    # takes: sentences of one phase that should flow together
    max_sent = 3 if a.format == "short" else 4
    takes, cur = [], []
    for p in plan:
        if cur and (p["phase"] != cur[-1]["phase"] or len(cur) >= max_sent or sum(x["words"] for x in cur) + p["words"] > (45 if a.format == "short" else 70)):
            takes.append(cur)
            cur = []
        cur.append(p)
    if cur:
        takes.append(cur)
    os.makedirs(a.out, exist_ok=True)
    narration = "\n\n".join(" ".join(x["text"] for x in t) for t in takes) + "\n"
    delivery, plan_takes = [], []
    for k, t in enumerate(takes):
        w = sum(x["words"] for x in t)
        tw = sum(x["words"] * x["target_wps"] for x in t) / w
        fall = sum(x["end_fall_st"] for x in t) / len(t)
        inst = PHASE_INSTRUCT[a.format][t[0]["phase"]] + f" Each sentence ends by falling in pitch, about {abs(fall):.0f} semitones."
        delivery.append(dict(instruct=inst, pause_ms=int(round(1000 * t[-1]["pause_after_s"]))))
        plan_takes.append(dict(take=k + 1, sentences=[x["i"] for x in t], words=w, target_wps=round(tw, 2), pause_after_s=t[-1]["pause_after_s"],
                               inner_pauses_s={str(x["i"]): x["pause_after_s"] for x in t[:-1]}))
    for t in takes:
        for x in t:
            x["take"] = takes.index(t) + 1
    gains = [dict(word=pu["word"], sentence=p["i"], take=p["take"], gain_db=pu["gain_db"], kind=pu["kind"]) for p in plan for pu in p["push"]]
    lufs = D["lufs"]["median"]
    meta = dict(format=a.format, profile_videos=P["videos"], loudness_lufs=round(lufs, 1), lead_in_s=round(D["lead_in_s"]["median"], 2), tail_s=round(D["tail_s"]["median"], 2) if a.format == "short" else 1.5,
                max_stretch=1.35, expected_seconds=round(sum(p["words"] / p["target_wps"] for p in plan) + sum(p["pause_after_s"] for p in plan[:-1]), 1))
    open(os.path.join(a.out, "narration.txt"), "w", encoding="utf-8").write(narration)
    json.dump(delivery, open(os.path.join(a.out, "delivery.json"), "w"), indent=2)
    json.dump(dict(meta=meta, takes=plan_takes, sentences=plan, word_gains=gains), open(os.path.join(a.out, "plan.json"), "w"), indent=1)
    md = [f"# Delivery plan ({a.format}-form, from {P['videos']} measured videos)", "",
          f"Expected spoken length about {meta['expected_seconds']} s. Loudness target {meta['loudness_lufs']} LUFS. Lead-in {meta['lead_in_s']} s.", "",
          "Speed is relative to the typical sentence; target is words per second (the voice builder stretches each take to it, at most 1.35x). Level in dB and pitch in semitones are relative to the video's average; the voice model cannot set pitch, so pitch is guidance.", "",
          "| # | take | sentence | speed x | words/s | level dB | pitch st | end falls st | pause after s | push |", "|---|---|---|---|---|---|---|---|---|---|"]
    for p in plan:
        md.append(f"| {p['i'] + 1} | {p['take']} | {p['text'][:70]} | {p['speed']} | {p['target_wps']} | {p['level_db']:+} | {p['pitch_st']:+} | {p['end_fall_st']} | {p['pause_after_s']} | " + ", ".join(f"{x['word']} (+{x['gain_db']} dB)" for x in p["push"]) + " |")
    md += ["", "## Takes", ""] + [f"{t['take']}. {len(t['sentences'])} sentences, {t['words']} words, target {t['target_wps']} words/s, then {t['pause_after_s']} s. Instruction: {delivery[t['take'] - 1]['instruct']}" for t in plan_takes]
    open(os.path.join(a.out, "delivery_plan.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"{total} sentences in {len(takes)} takes; expected {meta['expected_seconds']} s; files written to {a.out}")


if __name__ == "__main__":
    main()
