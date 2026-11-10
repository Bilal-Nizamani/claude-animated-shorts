#!/usr/bin/env python3
"""Compare a draft narration script with the measured style of short-form or long-form narrated videos.
usage:  python script_check.py <script.txt> --format short|long [--json]
Reads style_profiles.json (numbers only) next to this file. For every measure it says OK (inside the p10-p90 of the measured videos),
EDGE (between the measured min and max) or OUT (outside everything measured), and what to change. Pure standard library."""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NUM = re.compile(r"\d|^(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|hundred|thousand|million|billion|half|double|triple|first|second|third)$", re.I)
MECH = ["because", "that's why", "the reason", "turns out", "here's", "you see", "it's because", "which means", "so that", "thanks to", "that's how"]
clean = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())


def sentences(text):
    text = re.sub(r"\s+", " ", text.replace("…", "...")).strip()
    parts = re.split(r"(?<=[.?!])\s+(?=[\"'“(]?[A-Z0-9])", text)
    return [p.strip() for p in parts if p.strip()]


def hook_kinds(t):
    low = t.lower()
    first8 = low.split()[:8]
    k = []
    if t.endswith("?"):
        k.append("question")
    if re.match(r"^(if|imagine|picture|what if|suppose|have you|did you|do you)\b", low):
        k.append("if/imagine/you-address")
    if any(NUM.search(clean(w)) for w in first8):
        k.append("number in first 8 words")
    if re.search(r"\b(but|yet|never|only|just|despite|still|instead|without|can't|couldn't|impossible|illegal|banned)\b", low):
        k.append("paradox / tension word")
    if re.match(r"^(in|on|back in|during|by)\s+(the\s+)?(\w+\s+)?\d{3,4}", low):
        k.append("date-setting")
    if re.match(r"^(how|why|what|who|where)\b", low):
        k.append("how/why/what-led")
    if re.search(r"\b(you|your)\b", low):
        k.append("addresses 'you'")
    return k or ["plain statement"]


def measure(text):
    S = sentences(text)
    words = [w for s in S for w in s.split()]
    cw = [clean(w) for w in words]
    n = max(1, len(words))
    lens = [len(s.split()) for s in S]
    per100 = lambda c: 100 * c / n
    perS = lambda c: 100 * c / max(1, len(S))
    cum, acc = [], 0
    for l in lens:
        cum.append(acc / n)
        acc += l
    first = lambda test: next((cum[i] for i, s in enumerate(S) if test(s)), None)
    m = dict(words=len(words), sentences=len(S), len_mean=sum(lens) / len(lens), len_median=sorted(lens)[len(lens) // 2],
             short_share=100 * sum(l <= 6 for l in lens) / len(lens), long_share=100 * sum(l >= 20 for l in lens) / len(lens),
             you=per100(sum(c in {"you", "your", "you're", "you'll", "you've", "yours"} for c in cw)), me=per100(sum(c in {"i", "my", "me", "i'm", "i've", "i'll", "we", "our", "we're"} for c in cw)),
             questions=perS(sum(s.endswith("?") for s in S)), numbers=per100(sum(bool(NUM.search(c)) for c in cw)),
             contrast=perS(sum(bool(re.search(r"\b(but|however|yet|although|except|instead|actually)\b", s.lower())) for s in S)), because=perS(sum("because" in s.lower() for s in S)),
             contractions=per100(sum("'" in c for c in cw)), and_so_starts=perS(sum(clean(s.split()[0]) in {"and", "so"} for s in S)),
             word_len=sum(len(c) for c in cw) / n, hook_words=lens[0], last_words=lens[-1], hook=hook_kinds(S[0]),
             pos=dict(but=first(lambda s: re.search(r"\b(but|however|yet)\b", s.lower())), question=first(lambda s: s.endswith("?")), you=first(lambda s: re.search(r"\b(you|your)\b", s.lower())),
                      number=first(lambda s: any(NUM.search(clean(w)) for w in s.split())), mech=first(lambda s: any(m_ in s.lower() for m_ in MECH))))
    return m, S


def verdict(v, sp):
    if sp is None or v is None:
        return "-"
    if sp["p10"] <= v <= sp["p90"]:
        return "OK"
    if sp["min"] <= v <= sp["max"]:
        return "EDGE"
    return "OUT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--format", choices=["short", "long"], required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    prof = json.load(open(os.path.join(HERE, "style_profiles.json")))[a.format]
    W = prof["writing"]
    m, S = measure(open(a.script, encoding="utf-8-sig").read())
    est_s = m["words"] / prof["delivery"]["whole_video_wps"]["median"]
    rows = []
    add = lambda name, v, key, fix_low, fix_high, fmt="{:.1f}": rows.append((name, fmt.format(v) if v is not None else "-", W[key], verdict(v, W[key]), fix_low, fix_high))
    add("words", m["words"], "words", "add facts or steps until the spoken length fits", "cut: fewer beats, shorter setup", "{:.0f}")
    add("words per sentence (mean)", m["len_mean"], "len_mean", "sentences are choppy: join some", "sentences are long: split some, add short punch lines")
    add("% sentences <= 6 words (punch lines)", m["short_share"], "short_share", "add a few very short lines after long ones", "too many fragments: merge some", "{:.0f}")
    add("% sentences >= 20 words", m["long_share"], "long_share", "add the occasional long explaining sentence", "break up the longest sentences", "{:.0f}")
    add("'you / your' per 100 words", m["you"], "you", "address the viewer more", "less 'you'")
    add("'I / we' per 100 words", m["me"], "me", "-", "this format is mostly third-person narration: reduce I / we")
    add("% questions", m["questions"], "questions", "-", "fewer questions")
    add("numbers per 100 words", m["numbers"], "numbers", "add concrete numbers (dates, counts, amounts)", "too many numbers")
    add("% sentences with but / yet / however", m["contrast"], "contrast", "add turns: 'But ...'", "too many reversals")
    add("contractions per 100 words", m["contractions"], "contractions", "use more contractions (spoken English)", "-")
    add("hook length (words)", m["hook_words"], "hook_words", "hook is too thin: state the surprising fact with a detail", "hook is too long: one clean fact, 9-15 words", "{:.0f}")
    add("last sentence (words)", m["last_words"], "last_words", "-", "ending is long", "{:.0f}")
    out = [f"format: {a.format}   words: {m['words']}   sentences: {m['sentences']}   estimated spoken length: {est_s:.0f} s ({est_s / 60:.1f} min) at {prof['delivery']['whole_video_wps']['median']} words/s",
           f"measured videos: {prof['videos']} ({prof['minutes']} min). Length in the measured videos: {W['duration']['p10']:.0f}-{W['duration']['p90']:.0f} s (median {W['duration']['median']:.0f} s)", ""]
    out.append(f"{'measure':44s} {'yours':>8s}  {'measured p10-p90':>18s}  verdict")
    issues = []
    for name, val, sp, ver, lo, hi in rows:
        rng = f"{sp['p10']:.1f}-{sp['p90']:.1f}" if sp else "-"
        out.append(f"{name:44s} {val:>8s}  {rng:>18s}  {ver}")
        if ver in ("EDGE", "OUT") and sp:
            issues.append(f"- {name}: yours {val}, measured {rng}. " + (lo if float(val) < sp["p10"] else hi))
    out.append("")
    out.append("hook kinds in your first sentence: " + ", ".join(m["hook"]) + "   (measured videos: " + ", ".join(f"{k} {int(100 * v)}%" for k, v in W["hook_kinds"].items()) + ")")
    out.append("")
    out.append("where devices land (fraction of the script)   yours   measured average (range, used by)")
    nm = dict(but="first but / yet / however", question="first question", you="first 'you'", number="first number", mech="first explanation marker")
    for k in ["but", "question", "you", "number", "mech"]:
        d = W["device_position"][k]
        y = m["pos"][k]
        out.append(f"  {nm[k]:42s} {('-' if y is None else f'{y:.2f}'):>6s}   {d['mean']} ({d['min']}-{d['max']}, {int(d['used_by'] * 100)}% of videos)")
        if y is None and d["used_by"] >= 0.85:
            issues.append(f"- no {nm[k]}: {int(d['used_by'] * 100)}% of the measured videos use it (average at {d['mean']} of the video).")
        elif y is not None and d["mean"] is not None and (y < d["min"] - 0.05 or y > d["max"] + 0.05):
            issues.append(f"- {nm[k]} at {y:.2f}: measured range {d['min']}-{d['max']} (average {d['mean']}).")
    if a.format == "short" and not any(k in m["hook"] for k in ("number in first 8 words", "paradox / tension word", "addresses 'you'", "question")):
        issues.append("- hook is a plain statement with no number, tension word, question or 'you': it can work (8 of 16 measured hooks did) but the others add one of those.")
    out.append("")
    out.append("fix list:" if issues else "no issues against the measured style.")
    out += issues
    print("\n".join(out))
    if a.json:
        print(json.dumps(dict(measured=m, issues=issues), indent=1, default=str))


if __name__ == "__main__":
    main()
