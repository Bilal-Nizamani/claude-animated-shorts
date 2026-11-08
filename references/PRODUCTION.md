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

The default is the Apache-2.0 Qwen3-TTS 0.6B CustomVoice checkpoint with the English speaker Ryan. The CPU setup uses PyTorch SDPA. Use the same speaker and language across episodes for a consistent channel voice. The configuration is in `templates/voice/qwen.json`. [Qwen3-TTS model card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice) · [Qwen3-TTS setup and speaker list](https://github.com/QwenLM/Qwen3-TTS#quickstart)

## Narration Studio

Double-click `Open Narration Studio.cmd` in Windows Explorer. It opens a browser tab on this computer. Leave the launcher window open while using the studio.

1. Pick **Preset narrator** and select a voice, or pick **Clone a voice** and upload a WAV, FLAC or MP3 recording up to 25 MB. A clean clip of one person speaking for several seconds works best. Use your own voice or a recording you have permission to use.
2. For cloning, optionally paste the exact words spoken in the recording. If the screen shows **Set up cloning**, click it once to download Qwen3-TTS 0.6B Base. [Qwen3-TTS cloning model](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base)
3. Choose the narration language and click **Save narrator**. The production command uses this voice on future shorts. Reopen the studio whenever you want to change it.

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
