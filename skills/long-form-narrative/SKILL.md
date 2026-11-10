---
name: long-form-narrative
description: Write, voice and score a long narrated video (3-20 minutes, essay / explainer / personal-story style) from a topic and facts, using numbers measured from 4 real long-form narrations - the script structure, a sentence-by-sentence delivery plan (speed, pauses, pushed words, instruction text for the voice model), section pacing and the music bed. Also expands a short-form concept into a long video. Use when asked to create a long-form video, a long script, a video essay, or to use the "long-form style" for any topic.
---

# Long-form narrative: script, voice, music

Measured from **4 long-form narrations** (47.9 min, 7,297 words, 473 sentences: 3.6, 12.0, 14.9 and 17.5 minutes). Four videos is a **small sample, possibly from different creators**: treat every number as a starting point, and widen the tolerance where the sample is thin. Only numbers and structure were kept. No script, wording or voice was copied, and none may be: topics, wording and characters are your own, and a voice is a preset narrator or one you have permission to clone.

Full tables: [references/LONG_FORM_DATA.md](references/LONG_FORM_DATA.md). Numbers for the tools: [../_shared/style_profiles.json](../_shared/style_profiles.json). Short-form counterpart: [../short-form-narrative/SKILL.md](../short-form-narrative/SKILL.md).

> **Paths.** `_shared` is the folder next to this skill: `skills/_shared` in the repo, `~/.claude/skills/_shared` when installed. `build_voice.py` also needs the tooling checkout (`claude-animated-shorts`, with `templates/voice` set up); set `SHORTS_REPO=/path/to/claude-animated-shorts` if it is not found.

## The workflow

1. **Facts and promise.** Collect true, sourced facts (the user's "data"); decide the one question or promise the whole video answers; list 4-6 sections, each a self-contained idea with its own facts and one everyday analogy. Sources go at the top of `SCRIPT.md`.
2. **Draft** section by section with the formula in A. Spoken words only.
3. **Check:** `python skills/_shared/script_check.py script.txt --format long`.
4. **Plan the delivery:** `python skills/_shared/delivery_plan.py script.txt --format long --out <workspace>` (long scripts are split into takes of up to 4 sentences / 70 words).
5. **Build the voice:** `python skills/_shared/build_voice.py <workspace>` (Qwen3-TTS 1.7B). Long scripts take time on a CPU (about 16x real time): generate section by section and keep finished takes (they are cached per take).
6. **Music** (C) and **mix**: voice about 12 dB above the bed (10-13), master -12.4 LUFS, true peak <= -1.2 dBTP.
7. **You cannot hear audio.** Never claim the voice sounds good: export layers, report measured numbers, ask the user to listen.

## A. The script structure (what the 4 long videos do)

**Length and pace.** 3.6-17.5 minutes in the sample (median 13.4 min), 935-2,508 words at 2.4-2.7 words per second over the whole video (median 2.5) - about 0.68 times the pace of a short, because the pauses are longer (see B).

**Voice of the text.** First person is present: "I / we / my / our" 1.1-3.1 per 100 words (median 2.3), "you / your" 0.9-5.1 (median 2.2). Slightly harder than a short: words average 4.7 letters, reading grade about 8 (7.6-9.1). Fewer contractions (1.5-2.2 per 100 words) and fewer numbers (0.8-2.4 per 100). Questions about 3% of sentences. Sentences: mean 13.6-16.6 words (median 14.7), about 17% are <= 6 words and about 26% are >= 20 words; a short line follows a long one in about 15% of cases. Only about 3% of sentences open with "And" or "So" (vs 15% in shorts); common openers are "this is", "if you", "we don't", "the", "but the", "stress is" (the subject word), "in the".

**The hook is short and talks to the viewer.** First sentence 3-10 words (median 8, about 2-4.5 s), spoken slowly. In all 4 videos **tension and the viewer appear immediately**: the first "you" lands within the first 1-2% of the video and the first but / yet / however within the first 2-5%. Hook kinds: addresses "you" 2 of 4, plain statement 2 of 4, tension word 1 of 4. The first number lands about 7% in (0-20%), the first question about 11% in (3 of 4 videos), the first explanation marker (because / turns out / here's) about 29% in.

**Sections.** About 5-7 sections of roughly 2.5 minutes each (145 s average; the 3.6-minute video had 2). This was detected from topic shifts in 40-second windows, so treat it as approximate. Each section: a claim, the evidence, one analogy or example, a hand-off line to the next. Every section opens with the viewer's question, not a recap.

**The arc** (five equal parts of the running time):

| part | words/sentence | % but/yet | % "you" | % numbers | sentence speed (words/s) |
|---|---|---|---|---|---|
| 1 | 14.8 | 20 | 15 | 17 | 3.2 |
| 2 | 15.6 | 10 | 11 | 18 | 3.1 |
| 3 | 16.1 | 15 | 36 | 11 | 3.1 |
| 4 | 15.5 | 17 | 28 | 17 | 3.7 |
| 5 | 13.2 | 5 | 40 | 16 | 3.4 |

Tension words are densest at the start (20%) and thin out toward the end (5%); address to "you" **rises** through the video (15% to 40%) as the argument turns into advice; numbers stay even.

**Calls to action and sign-off.** The channel / subscribe style line comes at the very end (about 96% of the way) in 2-3 of 4 videos; one video mentions a sponsor at about 46%; one asks to follow at about 24% and one at about 80%. Allow 4-17 s of music-only tail after the last word (end screen).

## B. How to talk: the delivery map

Ratios are to the same video's own median sentence. `delivery_plan.py` writes a per-sentence plan.

**Speed.** Whole video 2.3-2.7 words/s. Sentence by sentence: p10 2.4, median 3.0, p90 3.8 words/s (the fastest sentences are 1.6x the slowest). Faster: any sentence <= 6 words (about x1.8) and a short punch after a long sentence (about x1.9; short lines are *tossed away* quickly); questions x1.10; sentences starting "But" x1.13. Slower: the hook (x0.77, spoken carefully), the last sentence x0.87. Across the video: even for the first half, a little faster in parts 5-9 of 10 (x1.03-1.08), then a **strong slowdown in the last tenth (x0.74)**.

**Pauses.** Much longer and more varied than a short. After a sentence: median 0.76 s (p90 1.12 s, up to 5.6 s at a topic change). After a comma: 0.40 s (p90 0.66). After the hook: 0.62 s. Before "but / yet": 0.68 s. Before a number: 0.68 s. After a question: 0.75 s. About 2.6 pauses per 10 s. Use the long pause (1.1 s or more) where the topic turns, not in the middle of an idea.

**Loudness.** -13.0 to -12.1 LUFS (median -12.4), loudness range 2.4-2.7 LU: still heavily compressed, about 1.3 LU quieter than shorts. Word-to-word range inside a sentence 9.8-11.9 dB (shorts: about 13). Short lines are 1-1.5 dB quieter. The last sentence is about 6 dB quieter and the hook about 4 dB quieter than the middle (small sample: n = 4).

**Pitch** (least reliable): the voices in the sample sit around 91-106 Hz; pitch moves 6.3-7.4 semitones inside a sentence (shorts: 7.5-9.4), so the delivery is a little flatter and calmer. Short punch lines fall about 3 semitones and sit about 1.9 below average. The last sentence falls about 6 semitones (a clear settle). Sentences fall slightly at the end (about -0.5 semitone on average; much less than shorts).

**Which words are pushed.** About 10.5% of words get extra stress (shorts 15.5%). Most likely: extremes (only, every, first, last, ever; lift 1.9, 1.3x longer), numbers (lift 1.9, 2.3x longer), question words (why, how, what; lift 1.4), contrast words (but, yet, however; lift 1.3, 1.6x longer - unlike shorts) and names (lift 1.3). The last word of a sentence is almost never pushed (2%) and falls about 1.8 semitones. "you / your" is under-stressed (lift 0.66).

**Turning it into a voice (Qwen3-TTS 1.7B).** Same rules as the short-form skill: one instruction per mood, speed by stretching each take to its target words/s (at most 1.35x), pauses cut or padded to the plan, pushed words raised in the mix, pitch only requested in the instruction text, two candidates per take, keep the clean one. Long-form instructions are warmer and calmer (see `delivery_plan.py`).

## C. Music

Measured from the **separated music stems** of the first 2 minutes of each of 4 long videos (full tables: [references/MUSIC.md](references/MUSIC.md)). Very small sample; tempo and key are estimates.

- **A warm, spacious bed under the whole video**, closer to the voice than in a short: voice 10-13 dB above it (median 12), with a slight dip of about 2-3 dB while the voice speaks.
- **Sound:** about 100-108 bpm (estimate; one video 129), a soft pulse in two of four, about 3 note onsets per second, very sustained (almost no percussion), dark and warm (spectral centre about 1.1 kHz, bass-heavy, soft top), wider stereo than a short; major and minor both occur.
- **Over the video:** level stays within about +-0.7 dB, then fades about 4 dB in the last tenth; music starts with or just before the first word (median 0.2 s) and ends 0.4-0.9 s after the last word (in two videos the bed ends in silence). Allow a longer tail if there is an end screen.
- **Build it** as a slow pad with a few soft plucks (`templates/audio/instruments.py`) or a licensed track; master -12.4 LUFS, true peak <= -1.2 dBTP.

## D. Converting between formats

**Long form from a short concept** (the user says "make a long-form video using the short concept"):
1. Treat each short as **one section** and its five-part arc as the section's skeleton; a 10-minute video is 4-5 such sections (each about 145 s, about 360 words at 2.5 words/s) plus an intro and an outro.
2. Add the intro: a 3-10 word hook that addresses "you" and states the tension in the first 2-5% (first "you" by 1-2%, first "but / yet" by 2-5%), then a one-sentence promise of what the video will answer.
3. Move from third person to first person plural and "you" ("we", "I", "you"); raise the reading level a little (words 4.7 letters, grade 8); fewer contractions and numbers than a short; keep the numbers precise.
4. Slow down: 2.5 words/s whole-video, pauses 0.76 s after sentences, 0.40 s at commas, longer pauses (1.1 s+) at section changes; master -12.4 LUFS.
5. Let "you" rise toward the end (15% to 40% of sentences) and let the tension words thin out; close with a short, slow, quiet last line and one end line (subscribe / channel) about 96% in.
6. Between sections: one hand-off sentence, a long pause, then the next section's own question.

**Short from a long-form idea:** use [../short-form-narrative/SKILL.md](../short-form-narrative/SKILL.md), section D.

## E. Limits
- **4 videos, probably more than one creator**: weak evidence. Add more long videos to `style-study` and re-run the analysis to tighten every range.
- Section boundaries are approximate; the first/last-sentence delivery numbers rest on 4 sentences.
- Pitch is the weakest measurement; timing and loudness are the strongest.
- Music: read from separated stems of only the first 2 minutes of each of 4 videos (see C).
- The voice model can follow timing, pauses and pushes, not pitch melody or real emotion. The user's ear decides.
