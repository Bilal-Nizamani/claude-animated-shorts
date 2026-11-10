# Narrated-video skills: short-form and long-form

Two skills built from **measurements of real narrated videos** (16 shorts, 4 long-form videos: 63 minutes of audio). They cover three things for each format: how the **script** is built, how the **narration is delivered** (where it is slow, fast, high, low, loud, quiet, where the pauses and pushed words are) and what the **music bed** does. Only numbers and structure were kept: no script, wording or voice from any video is stored or reused.

| skill | use it when you say |
|---|---|
| [short-form-narrative](short-form-narrative/SKILL.md) | "create a short about ...", "write a short script", "plan the delivery of this short", "make a short using the long-form style" |
| [long-form-narrative](long-form-narrative/SKILL.md) | "create a long-form video about ...", "write a video essay", "turn this short concept into a long video" |

Each skill ends with **conversion rules** (short from a long idea; long form from a short concept), so either direction works.

## Tools (in `_shared/`, plain Python)

| tool | what it does |
|---|---|
| `script_check.py script.txt --format short\|long` | compares a draft script with the measured style: length, hook, sentence rhythm, devices and where they land; gives a fix list |
| `delivery_plan.py script.txt --format short\|long --out DIR` | marks up every sentence: speed, level, pitch guidance, pause after it, the word to push; writes `narration.txt`, `delivery.json`, `plan.json`, `delivery_plan.md` |
| `build_voice.py DIR` | builds the narration from that plan with Qwen3-TTS 1.7B: two candidates per take, stretch to target speed, sentence pauses, pushed words, EQ, loudness; writes the wav and word timings |
| `style_profiles.json` | the measured numbers the tools use (statistics only) |

## Install

Skills are read from `~/.claude/skills/`. Copy the three folders there (keep `_shared` next to the skills):

- macOS / Linux: `bash skills/install.sh`
- Windows: `powershell -File skills/install.ps1`

`build_voice.py` also needs this repository's voice setup (`templates/voice/setup-qwen.sh`) and finds the checkout itself; set `SHORTS_REPO` if it cannot.

## Honest limits
- Small samples (the long-form numbers rest on 4 videos, likely from different creators): treat ranges as starting points.
- Timing and loudness are measured well; pitch is the weakest measurement; the music was first read from the mixed audio and then from separated music stems (see each skill's music section).
- The voice model follows the timing, pauses and pushed words; it cannot follow pitch melody or real emotion, and Claude cannot hear audio: the user's ear decides.
- Never clone or imitate a real person's voice without their permission. This repository is public unless switched to private: never put recordings or transcripts of other people's videos here.
