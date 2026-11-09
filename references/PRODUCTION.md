# Production workspaces and local narration

Keep the skill checkout as a source library. Put each short in its own sibling production tree and share one Qwen3-TTS installation across them.

```text
videoes/
  claude-animated-shorts/       skill, templates, voice config and setup
  shorts-runtime/              Python, dependencies and model cache
  shorts-production/
    first-short/
      SCRIPT.md                facts, sources and approved script
      narration.txt            spoken text only, in UTF-8
      voice/                   voice.wav and words.json
      audio/                   copied mix scripts, caches and stems
      remotion/                host project, props, shot source and dependencies
      out/                     stills, QA sheets and final MP4
```

## One-time Windows setup

From the skill checkout, run the following with PowerShell and a working `py` launcher. The script installs Python 3.12 and the CPU dependencies under `shorts-runtime`, downloads the checkpoint into the shared cache, and loads it once to validate the model and speaker. Use the same setup for every short.

```powershell
.\templates\voice\setup-qwen.ps1
```

The default is the Apache-2.0 Qwen3-TTS **1.7B** CustomVoice checkpoint with the English speaker Ryan (the 0.6B models were dropped: they ignore style instructions and sound flatter). The CPU setup uses PyTorch SDPA. Use the same speaker and language across episodes for a consistent channel voice. The configuration is in `templates/voice/qwen.json`. [Qwen3-TTS model card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice) · [Qwen3-TTS setup and speaker list](https://github.com/QwenLM/Qwen3-TTS#quickstart)

## One-time macOS / Linux setup

Install Homebrew, then from the skill checkout run the following. It creates `../shorts-runtime/tts-venv` (Python 3.12), installs the dependencies and downloads the 1.7B CustomVoice (preset voices + style instructions) and 1.7B Base (voice cloning) checkpoints, about 9 GB once. Each needs about 9 GB of free RAM in float32, so use a Mac with 16 GB or more. ffmpeg from Homebrew includes the Rubber Band filter used for clean pace and pitch changes.

```bash
brew install ffmpeg node python@3.12 uv git
bash templates/voice/setup-qwen.sh            # add --no-clone to skip the 1.7B Base (voice cloning) model
bash templates/voice/open-narration-studio.sh # the Narration Studio, same as the Windows launcher
```

Apple silicon runs the CPU path by default. `export QWEN_DEVICE=mps PYTORCH_ENABLE_MPS_FALLBACK=1` tries the Apple GPU for generation (not verified here, so compare a short line against the CPU result first).

## Styled delivery with the 1.7B model

The 0.6B CustomVoice model ignores style text (the library says so: "for 0b6 model, instruct is not supported"). The **1.7B CustomVoice** model takes a plain-English instruction per beat for tone, speaking rate and emotion. Add an `instruct` key to a beat in `delivery.json`; `qwen_narrate.py` then loads the 1.7B model (`style_model` in `qwen.json`).

```json
[
  {"instruct": "Serious, hushed documentary narrator. Slow and deliberate, low in pitch. Lean on 'almost three days', then stop.", "pause_ms": 300},
  {"instruct": "Tense and urgent, getting faster and louder as the storm hits, with a hard punch on 'flips'."}
]
```

What was learned making the Okene short:

- **Fewer, longer beats.** One take per sentence group flows; four tiny takes sound chopped because every take starts and ends the same way. Group by mood, not by comma.
- **The model follows instructions loosely.** It ignored "quiet" and read a date louder than the action. Fix levels afterwards in the mix with a per-word gain table keyed to `words.json` (see `audio/okene_mix.py`, `LEVELS`).
- **It sometimes stumbles** ("a ... huge" with a pause mid-phrase). `candidates.py` generates several takes of one beat, scores each for silent gaps inside the phrase and keeps the cleanest.
- **Takes are cached per beat** in `voice/beats/` (keyed by text + instruction + voice), so changing one beat regenerates only that beat.
- **Full precision on CPU.** `style_dtype` is `float32`: bfloat16 has no hardware support on older CPUs and ran more than ten times slower. The 1.7B model needs about 9 GB of RAM in float32.
- **Pace and pitch:** `pace` / `pitch_semitones` use Rubber Band through ffmpeg (formant preserving) when ffmpeg is available, which avoids the hollow, tube-like smear of a phase vocoder.
- **Voice EQ:** TTS voices come out boxy (a hump at 150-400 Hz) and dull above 3 kHz. A cut around 260 Hz, a presence boost near 3.5 kHz, light compression and a touch of air fixed that in `okene_mix.py`.

## What this repository knows about how to talk

Very little, and it is worth being clear about it. `STYLE_BIBLE.md` records the reference narrator as one male voice, "fast and steady", 3.5-4.1 words/s with almost no pauses, mixed at -14 LUFS. `delivery.json` can nudge pace, pitch and level "modestly". There are no recordings or transcripts of the reference narrator here (they are private study material), no pitch contours and no emphasis rules, so nothing in the repository can teach a text-to-speech model to perform. Expressive delivery comes from the 1.7B instructions above, from a recording you make yourself, or from cloning a voice that already reads the way you want.

## Narration Studio

Double-click `Open Narration Studio.cmd` in Windows Explorer. It opens a browser tab on this computer. Leave the launcher window open while using the studio.

1. Pick **Preset narrator** and select a voice, or pick **Clone a voice** and upload a WAV, FLAC or MP3 recording up to 25 MB. A clean clip of one person speaking for several seconds works best. Use your own voice or a recording you have permission to use.
2. For cloning, optionally paste the exact words spoken in the recording. If the screen shows **Set up cloning**, click it once to download Qwen3-TTS 1.7B Base. [Qwen3-TTS cloning model](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base)
3. Choose the narration language, enter a short line, and click **Test voice** to listen to your current selection. Click **Save narrator** when you want the production command to use that voice on future shorts.

The studio runs on localhost. It stores the saved profile and its reference recording under `shorts-runtime/narrator/`, outside the Git checkout.

## Start a short

From the skill checkout, create an external folder and prepare its script. The workspace can be on a separate drive. Keep the source notes and stage directions in `SCRIPT.md`. Put only the words the voice should read in `narration.txt`. Use blank lines between short groups of sentences where a pause belongs.

```powershell
$short = New-Item -ItemType Directory -Force '..\shorts-production\first-short'
```

Once the script is approved, the production agent splits the spoken text into beats separated by blank lines and writes `delivery.json` in the short folder. Use one object per beat in script order. Omit keys to keep the model's pitch and pace, unity gain, and the configured paragraph pause. A two-beat example follows.

```json
[
  {"pace": 0.92, "pitch_semitones": -0.5, "gain_db": -2, "pause_ms": 320},
  {"pace": 1.08, "pitch_semitones": 0.7, "gain_db": 2}
]
```

Keep changes tied to the story. Give a reveal room to land, pick up pace when the action builds, and emphasize a key line with a modest level or pitch change. Phrasing and punctuation guide Qwen's natural inflection. The numeric controls adjust the rendered beat, and the pause applies before the next one. Generate the voice track with the saved narrator.

```powershell
$python = '..\shorts-runtime\tts-venv\Scripts\python.exe'
& $python .\templates\voice\qwen_narrate.py --workspace $short.FullName
```

The command uses the cached checkpoint offline and writes `voice/voice.wav` as 48 kHz PCM for the existing mixer. It refuses a workspace in the skill checkout and preserves existing takes. Archive an old take before retrying. Without a saved narrator, the command uses the default speaker and language in `qwen.json`.

Run word-level speech alignment on the final WAV, review the timestamps, and save them to `voice/words.json` as an array of word records with `s` and `e` in seconds. Re-align when the WAV changes. The GSAP shot cues and the audio mixer both depend on the recorded timings.

## Build and export

- Keep a Remotion project under the short's `remotion/` directory. Install its Three.js and GSAP dependencies there and copy the bridge template into that project's `src/videos/<name>/`. Keep assets in that project's `public/`.
- Copy `templates/audio/` to the short's `audio/` directory before adapting or running the mix scripts. The mixer finds narration relative to this copy. Copy any render and QA helpers into the external workspace before using them.
- Run Remotion from the external host project. Point its output paths to the short's `out/` and set `REMOTION_TMP` to an external directory when using the stills helper. Keep delivery exports and intermediate render files in the short's workspace.
