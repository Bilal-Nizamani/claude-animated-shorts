# CLAUDE.md - first-short (read this first)

A 10 s vertical animated short, "The Cook Who Survived 3 Days Underwater" (Harrison Okene, tug Jascon-4, May 2013). Qwen3-TTS narration + Three.js/GSAP scenes rendered by Remotion + a synthesized sound mix. This branch is code and script only.

## First-time setup on this Mac (do this, in order)
1. Layout must be siblings: `<parent>/shorts-production/first-short` (this repo, branch `first-short`), `<parent>/claude-animated-shorts` (tooling, branch `main`), `<parent>/shorts-runtime` (env + models, never in Git). `qwen_narrate.py` refuses a workspace inside the tooling checkout.
2. Run `bash scripts/setup-mac.sh` from this folder. It needs Homebrew and a GitHub login that can read the private tooling repo (`gh auth login`). It installs ffmpeg/node/python@3.12/uv, clones the tooling, builds the Python env, downloads the Qwen3-TTS 0.6B and 1.7B models (~6 GB), saves narrator Aiden, runs `npm ci` and fetches Remotion's headless Chrome.
3. Verify: `ffmpeg -filters | grep rubberband` (needed for clean pace/pitch edits), then time one sentence: generate a ~4 s line with the 1.7B model on CPU (float32, ~9 GB RAM) and note seconds per second of speech. Then, optionally, repeat with `QWEN_DEVICE=mps PYTORCH_ENABLE_MPS_FALLBACK=1` and compare speed and quality (never verified).
4. Build: `bash scripts/make-short.sh all` (or `voice`, `mix`, `render`). Output: `out/okene_final.mp4` (1440x2560, 30 fps, 10-11 s).
Nothing here has been run on a Mac yet. Fix what breaks, and tell the user exactly what you changed.

## Rules from the user (keep following them)
- Serious tone: eleven people died. No jokes, no comedic sound.
- English only. No captions or on-screen text. Final export 2K vertical 1440x2560.
- Narrator: Aiden (Qwen3-TTS). Music must be LIGHT: about 14 dB under the voice, ducked while speaking (an earlier version was "too much").
- The voice must sound like someone telling a story: pace, loudness and pauses should follow the picture. The user said the last version was "one tone", and that is **still the open problem**.
- You cannot hear audio. Never claim the voice sounds good. Export layers as WAV files, measure what you can, and ask the user to listen. (Frame-level pitch metrics were tried and were misleading.)
- The hook line "A man breathed at the bottom of the ocean for almost three days." was chosen by the assistant, not confirmed by the user. Facts and sources are in SCRIPT.md (60 h, 2 mattresses, 12 aboard, 11 died; sardines/cola claims were dropped as unsupported).
- Never commit media, models, voice takes, renders or caches (`.gitignore` + `.githooks/pre-push` enforce it). Do not put the user's email or personal paths in the repo.

## How the pipeline works
`narration.txt` (blank line = a take) + `delivery.json` (per take: `instruct` text for the 1.7B model; optional pace/pitch_semitones/gain_db/pause_ms) -> `voice/voice.wav` -> `finish_voice.py` (silence cuts only) -> `align.py` (faster-whisper words) -> `retime.py` (snap word times to real speech edges) -> `remotion/src/videos/okene/words.json`. Every cut, camera move and sound cue is keyed to those word times, so after any voice change run `voice`, `mix`, `render` again. `audio/okene_mix.py` builds the mix (voice EQ, per-word `LEVELS`, ambience, SFX, light score) to -14 LUFS. `candidates.py <beat> <n>` makes several takes of one beat and keeps the one without a mid-phrase gap. Per-beat takes are cached in `voice/beats/` (keyed by text + instruction + voice).

## Gotchas that cost hours
- `@react-three/postprocessing` is pinned to 3.0.4. Newer versions create their composer one render late, so every Remotion frame is blank. Do not upgrade.
- Use one browser for many frames (the scripts do). Starting a browser per frame was ~2 min each on Windows. Remotion's own headless Chrome is used, not desktop Chrome.
- The 1.7B model in bfloat16 on a CPU without bf16 hardware was >10x slower than float32. Keep `style_dtype` "float32".
- The 0.6B CustomVoice model ignores `instruct`; only 1.7B uses it. The 1.7B follows instructions loosely (read the date louder than the action; sometimes stumbles "a ... huge").
- Whisper starts words 0.1-0.4 s early after a pause; `retime.py` fixes that. `faster-whisper` 1.2.1 fails to decode files with `av` 19, so `align.py` passes a numpy array instead of a path.
- `short_qa.py` needs ffmpeg/ffprobe on PATH plus numpy and pillow (installed in the venv).

## Ideas for the voice, in the order I would try them
1. One `instruct` per sentence with strong, concrete wording; generate 3-5 candidates and pick by ear (the user), not by metric.
2. Fix level and pace per word in the mix (already done for the date/sentence: `LEVELS` in `okene_mix.py`).
3. A recorded or cloned human voice (Qwen3-TTS 0.6B Base cloning, via the Narration Studio) - the most likely way to get a natural storyteller.

## Voice cloning experiment (reference clip)
- `voice/reference/reference_50s_center.wav` (+ `.txt` transcript, `NOTICE.md`) is a 50 s clip of the YouTube creator Dani, used by the repo owner's statement of his permission for **private experiments only**. Read `NOTICE.md`: never publish the clip, never use the clone in a published video without Dani's explicit permission, label AI voices. Keep the repository private.
- The transcript is an automatic Whisper pass and has errors. Qwen's in-context cloning needs the EXACT words, so listen and correct the `.txt` first (ask the user to confirm).
- Plan: use `Qwen/Qwen3-TTS-12Hz-1.7B-Base` (the `clone_model` in `claude-animated-shorts/templates/voice/qwen.json`; the 0.6B models were removed). Clone from this clip with `ref_text` set (not x-vector-only), say the same test sentence in Aiden and in the clone, and ask the user to compare by ear.
- Set expectations: Qwen's clone copies the timbre but often not the speaker's delivery, so it can sound like "its own voice from the provided audio". The user already saw this with their own voice. If it is not close enough, the next step to evaluate is fine-tuning (e.g. GPT-SoVITS on CPU on the Mac), which needs more clean audio and the same permission.
