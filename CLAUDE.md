# CLAUDE.md - first-short (read this first)

A 10 s vertical animated short, "The Cook Who Survived 3 Days Underwater" (Harrison Okene, tug Jascon-4, May 2013). Qwen3-TTS narration + Three.js/GSAP scenes rendered by Remotion + a synthesized sound mix. This branch is code and script only.

## First-time setup on this Mac (do this, in order)
1. Layout must be siblings: `<parent>/shorts-production/first-short` (this repo, branch `first-short`), `<parent>/claude-animated-shorts` (tooling, branch `main`), `<parent>/shorts-runtime` (env + models, never in Git). `qwen_narrate.py` refuses a workspace inside the tooling checkout.
2. Run `bash scripts/setup-mac.sh` from this folder. It needs Homebrew and a GitHub login (`gh auth login`). It installs ffmpeg/node/python@3.12/uv, clones the tooling, builds the Python env, downloads the Qwen3-TTS 1.7B CustomVoice and 1.7B Base (cloning) models (~9 GB; the 0.6B models were dropped), saves narrator Aiden, runs `npm ci` and fetches Remotion's headless Chrome.
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
- Never commit media, models, voice takes, renders, caches or VOICE SAMPLES (`.gitignore` + `.githooks/pre-push` enforce it). **This GitHub repository is PUBLIC** unless the user has switched it to private: before every push check with an unauthenticated `curl https://api.github.com/repos/<owner>/<repo>` (look at "private"). Do not put the user's email or personal paths in the repo.

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

## Voice cloning experiment (the reference clip is NOT in Git)
- The user wants to try cloning a creator's voice (Dani) for a private experiment. They say Dani agreed (unverified). The 50 s reference WAV is NOT in this repository: it was pushed once by mistake to a public repo and removed. Ask the user to copy it to `voice/reference/` by other means (AirDrop, USB, cloud drive) together with the exact transcript. That folder is git-ignored.
- The transcript must be exact (in-context cloning). Listen and correct any automatic Whisper transcript with the user first.
- Use `Qwen/Qwen3-TTS-12Hz-1.7B-Base` (the `clone_model` in `claude-animated-shorts/templates/voice/qwen.json`) with `ref_text` set (not x-vector-only). Say the same test sentence in Aiden and in the clone and ask the user to compare by ear. Never publish the clone or use it in a published video without the creator's explicit permission; label AI voices.
- Set expectations: the clone copies timbre, often not delivery, so it can sound like "its own voice from the provided audio". If not close enough, evaluate fine-tuning (e.g. GPT-SoVITS on CPU), which needs more clean audio and the same permission.
