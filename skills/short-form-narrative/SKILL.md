---
name: short-form-narrative
description: Write, voice and score a 40-80 second narrated short (YouTube Shorts style) from a topic and facts, using numbers measured from 16 real narrated shorts - the script formula, a sentence-by-sentence delivery plan (speed, pauses, pushed words, instruction text for the voice model) and the music bed. Also converts a long-form idea into a short. Use when asked to create a short, write a short script, plan how a short should be spoken, or to use the "short-form style" for any topic or format.
---

# Short-form narrative: script, voice, music

Everything below is **measured, not guessed**: 16 narrated shorts (15.0 min, 3,326 words, 213 sentences), analysed for how the script is built, how the narrator speaks and what the music does. Only numbers and structure were kept. No script, wording or voice was copied, and none may be: topics, wording and characters are always your own, and a voice is a preset narrator or one you have permission to clone.

Full tables: [references/SHORT_FORM_DATA.md](references/SHORT_FORM_DATA.md). Machine-readable numbers: [../_shared/style_profiles.json](../_shared/style_profiles.json). Long-form counterpart: [../long-form-narrative/SKILL.md](../long-form-narrative/SKILL.md).

> **Paths.** `_shared` is the folder next to this skill: `skills/_shared` in the repo, `~/.claude/skills/_shared` when installed. `build_voice.py` also needs the tooling checkout (`claude-animated-shorts`, with `templates/voice` set up); set `SHORTS_REPO=/path/to/claude-animated-shorts` if it is not found.

## The workflow (do it in this order)

1. **Facts first.** Collect true, sourced facts for the topic (the user's "data"): one surprising cause-and-effect with a physical or human mechanism, numbers and names, and one everyday analogy that explains it. Write them with sources at the top of `SCRIPT.md`. Drop any claim the sources do not support.
2. **Draft the script** with the formula in section A. Spoken words only, plain English, one voice.
3. **Check it:** `python skills/_shared/script_check.py script.txt --format short`. It says OK / EDGE / OUT for every measure against the measured shorts and gives a fix list. Fix, re-run, until the list is empty or you can defend each remaining difference.
4. **Plan the delivery:** `python skills/_shared/delivery_plan.py script.txt --format short --out <workspace>`. It writes `narration.txt` (takes), `delivery.json` (instruction per take), `plan.json` and a readable `delivery_plan.md`: per sentence the speed, level, pitch guidance, pause after it and the word to push.
5. **Build the voice:** `python skills/_shared/build_voice.py <workspace>` (needs the venv from `templates/voice/setup-qwen.sh`, Qwen3-TTS 1.7B). It generates two candidates per take, keeps the clean one, stretches each take to its target words/s, sets the sentence pauses, pushes the planned words, applies EQ and compression and masters to -11 LUFS. It also writes the word timings for syncing pictures.
6. **Music:** section C. **Mix:** voice first, bed about 11 dB under it, -11 LUFS master, true peak <= -1.2 dBTP.
7. **You cannot hear audio.** Never claim the voice sounds good. Export the layers as WAV, report the measured numbers and ask the user to listen. The user's ear decides; then adjust the plan (not the rules) and rebuild only the takes that changed.

## A. The script formula (what the 16 shorts do)

**Length.** 40-65 s (p10-p90; median 61, range 31-78 s) = 145-247 words (median 220) at 3.7 words per second. Aim for 55-65 s / about 215 words.

**Voice of the text.** Third-person storytelling about a person, event or thing ("he sold...", "the town..."): "I / we" are almost absent (0.0-0.5 per 100 words) and "you" is occasional (median 1.5, up to 7 per 100 words). Plain, short words: average word length 4.1 letters, reading grade about 6. Spoken English: 2-4 contractions per 100 words. Concrete numbers: 0.7-5.9 per 100 words (median 2.3) and **every** measured short has a number; the first one appears on average 20% into the story.

**Hook = sentence 1.** 9-20 words (median 14), about 2.5-5 seconds, spoken immediately (no greeting, no title, no channel name). Hook kinds in the 16 shorts: plain statement of an odd fact 50%; a number inside the first 8 words 31%; a tension word (but, yet, never, only, just, without, despite, impossible, illegal) 31%; addresses "you" 19%; "if / imagine" 6%. **None of the 16 hooks was a question.** Write the hook as a precise, slightly absurd fact with a stake, then go straight on.

**Sentence rhythm.** Mean 12.6-20.7 words (median 15). About 12% of sentences are very short (<= 6 words, the punch lines; up to 38% in some) and about 30% are long (>= 20 words). Pattern: a short line (<= 7 words) follows a long one (>= 16) in about 20% of cases - use short lines to land a fact after a long build-up.

**Devices and where they land** (fraction of the story; 0 = start):

| device | average position | range | used by |
|---|---|---|---|
| first number | 0.20 | 0.00-0.93 | 16 of 16 |
| first "you" | 0.21 | 0.00-0.80 | 14 of 16 |
| first explanation marker (because / turns out / you see / here's) | 0.27 | 0.00-0.79 | 15 of 16 |
| first but / yet / however | 0.33 | 0.00-0.71 | 14 of 16 |
| first question | 0.44 | 0.27-0.62 | 7 of 16 (3.7% of sentences) |
| first "because" | 0.44 | 0.05-0.75 | 6 of 16 |

**The pivot is "You see,"**: the most common two-word sentence opener (9 times in 16 shorts). It introduces the mechanism, usually with an everyday analogy. Contrast sentences (but / yet / however) are 17% of all sentences (11-30% per short).

**How sentences start** (share of all sentences): So 10%, The 10%, He 9%, You 7.5%, But 7%, And 4%, Then 4%. About 15% of sentences open with "So" or "And".

**The arc**, five equal parts of the running time:

| part | job | words/sentence | % with but/yet | % with "you" | % with a number | speed (words/s) |
|---|---|---|---|---|---|---|
| 1 | hook and setting | 18 | 13 | 36 | 40 | 3.8 |
| 2 | escalation (the only place questions cluster: 8%) | 15 | 12 | 22 | 35 | 3.8 |
| 3 | complication: longest sentences | 23 | 27 | 24 | 32 | 3.8 |
| 4 | the turn and the explanation ("You see,") | 16 | 29 | 35 | 28 | 4.0 |
| 5 | payoff: fastest, fewest reversals | 16 | 7 | 27 | 31 | 4.25 |

**The ending.** No sign-off, no "follow", no "part 2" teaser in the measured shorts (only 2 of 16 even say "follow", and mid-story). The last sentence is long (median 15 words, often the explanatory twist or irony), delivered slightly slower and lower. End on the payoff sentence and stop; the audio tail is only 0.1-0.5 s.

## B. How to talk: the delivery map

Measured as ratios to the same video's own median sentence, so they transfer to any voice. `delivery_plan.py` turns these into a per-sentence plan.

**Speed.** Whole video 3.4-3.9 words/s (mean 3.7). Sentence by sentence: p10 3.2, median 3.9, p90 4.5 words/s (the fastest sentences are 1.4x the slowest). It is **fast and even**, not dramatic.
- Faster: a short punch after a long sentence x1.20; any sentence <= 6 words x1.12; questions x1.10; sentences containing a number x1.07; sentences starting So / And x1.05.
- Slower: the second sentence x0.96; explanation sentences (because / turns out / you see) x0.97; the last sentence x0.96; the end of the video x0.93.
- Across the story: flat, a little faster in parts 7-8 of 10 (x1.03-1.04), slowing at the very end.

**Pauses.** Almost none. Sentence end: median 0.30 s (p90 0.42, longest 0.54). After a comma: 0.28 s. About 1.5 pauses per 10 s in total. **After the hook only 0.15 s** (it runs straight into sentence 2). Before "but / yet": 0.31 s. After a question: 0.29 s. No dramatic silences. Lead-in before the first word 0.04-0.2 s; tail after the last word 0.1-0.5 s.

**Loudness.** Constant. -12.1 to -11.0 LUFS (median -11.1), loudness range 1.7-2.8 LU: heavily compressed, no quiet passages. Inside a sentence, words vary about 13 dB; short lines (<= 6 words) are about 1 dB quieter with a narrower range (6.6 dB); exclamations about 1 dB louder.

**Pitch** (least reliable measurement; the voice model cannot set it): the first sentence sits about 1.7 semitones above the narrator's average; every sentence ends by **falling about 2.6 semitones** (the hook about 4.7, the last sentence about 3.7); even questions fall (-2.2 semitones). Short punch lines sit lower (about 1 semitone below average) and are flatter (pitch range 5.7-6.6 vs 8.3 for normal sentences). Over the whole story the pitch drifts down about 2 semitones from start to end.

**Which words are pushed** (louder and longer, or clearly higher). About 15% of words get some extra stress. Most likely: numbers (27% of them; spoken 2.0x longer, 2.1 semitones above their sentence), extremes - only, every, first, last, ever, never (26%; 1.5x longer, +2.3 semitones), names (23%), long content words (19%). Least likely: but / yet / however (2.5%), question words (4.7%), "you" (9%), the last word of a sentence (11%; it falls). Rule: **stress the facts, not the grammar, and let the sentence fall at the end.**

**Turning it into a voice (Qwen3-TTS 1.7B).** The voice model cannot be told "faster" or "quieter"; it reads the style loosely and ignores speed words. So the plan uses: one instruction per mood (written into `delivery.json`), the speed set afterwards by stretching each take to its target words/s (at most 1.35x), the pauses set by cutting or padding silence, the pushed words raised by +2.5 to +3.5 dB in the mix, and the pitch fall requested in the instruction text only. Group 2-3 sentences of one mood into one take so the voice flows; a take per sentence sounds chopped. Generate two candidates per take and keep the one without a stumble (a silence inside a phrase).

## C. Music

**Provisional (v1, read from the mixed audio, so tempo and key are estimates):**
- It is a **steady bed under the whole story**: starts at the first word (0.1 s) and ends at the last (0.1-0.5 s), no intro, no outro tail, no swells (the level moves +-0.5 dB over the running time) and no measurable ducking.
- **Level:** the voice sits about 11 dB above the bed (p10-p90 9.6-12.6 dB).
- **Character:** no strong drum pulse (beat strength near zero in 14 of 16); the tempo estimates cluster at 83-136 bpm (median 107) but are weak; mostly minor-leaning, D minor the most frequent where the key estimate was confident; bright-ish bed (spectral centre 3.5-5.3 kHz).
- A separated-music analysis (v2) is in [references/MUSIC.md](references/MUSIC.md) when present; prefer its numbers.

**What to put under a short:** a soft, steady, loop-friendly bed in a minor key at about 90-110 bpm, no big drums, constant level, starting with the first word, voice 11 dB above it, no ducking needed. Build it with the repo's synthesizer (`templates/audio/instruments.py`: `pad`, `pluck`, `musicbox`, `vibes`) or any licensed track; keep it quieter than the voice and constant.

## D. Converting between formats

**Short from a long-form idea or script** (the user says "make a short using the long-form style"):
1. Pick **one** surprising claim and its mechanism from the long piece. A short is one story, not a summary.
2. Cut to about 215 words; sentence 1 is the hook (9-20 words, a fact with a stake, no greeting).
3. Rewrite in third person; swap "I / we" for the person or thing; lower the reading level (words about 4.1 letters, grade about 6); raise contractions to 2-4 per 100 words and numbers to about 2-3 per 100.
4. Keep one "You see," pivot and one or two short punch lines after long sentences. Remove sections, recaps, sponsor lines and calls to action.
5. Speak it 1.5x faster than the long form (3.7 vs 2.5 words/s), with pauses of 0.3 s instead of 0.76 s, and master 1.3 dB louder (-11 vs -12.4 LUFS).

**Long form from a short concept:** use [../long-form-narrative/SKILL.md](../long-form-narrative/SKILL.md): treat the short's arc as **one section** and build 4-6 sections.

## E. Limits, so nobody overtrusts this
- 16 shorts from what look like one or a few channels: this is *a* measured house style, not a law of the medium.
- Sentence boundaries come from Whisper punctuation; a few shorts were transcribed with long run-on sentences, which blurs the sentence-length numbers.
- Pitch is the weakest measurement. Timing and loudness are the strongest.
- Music was read from the mixed audio (see section C).
- The voice model can follow the plan's timing, pauses and pushes; it cannot follow pitch melody or real emotion. Judge by ear, keep the user in the loop.
