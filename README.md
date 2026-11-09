# first-short: "The Cook Who Survived 3 Days Underwater"

A 10 s vertical animated short (1440x2560, 30 fps): Qwen3-TTS narration, a Three.js world drawn with an ink-outline look, GSAP-driven animation, Remotion rendering, and synthesized ambience / effects / a light score. This branch holds **only the code and the script**. Models, voice takes, renders and caches are never committed (see `.gitignore` and the `pre-push` hook).

It is built on the tooling in `main` of this repository (`claude-animated-shorts`: voice scripts, templates, setup).

## Set up a Mac (one command)

Needs [Homebrew](https://brew.sh) and a GitHub login (`gh auth login`). **This repository is public unless you switch it to private in GitHub settings. Do that before adding anything personal, and never commit voice recordings.**

```bash
mkdir -p ~/shorts/shorts-production && cd ~/shorts/shorts-production \
  && git clone --branch first-short --single-branch https://github.com/Bilal-Nizamani/claude-animated-shorts.git first-short \
  && bash first-short/scripts/setup-mac.sh
```

That installs ffmpeg, Node, Python 3.12 and uv, clones the tooling next to this folder, creates the Python environment, downloads the Qwen3-TTS 1.7B CustomVoice (preset voices + style instructions) and 1.7B Base (voice cloning) models (about 9 GB, once) and installs the Remotion dependencies plus its headless Chrome. Layout afterwards:

```
~/shorts/
  claude-animated-shorts/        tooling (branch main)
  shorts-runtime/                Python env + model weights      (not in Git)
  shorts-production/first-short/ this branch
```

## Make the short

```bash
cd ~/shorts/shorts-production/first-short
bash scripts/make-short.sh voice     # narration + word timings        (Qwen 1.7B, styled by delivery.json)
bash scripts/make-short.sh mix       # voice + ambience + SFX + score  -> audio/mix.wav, -14 LUFS
bash scripts/make-short.sh render    # 1440x2560 render + sound + QA   -> out/okene_final.mp4
bash scripts/make-short.sh all       # everything
```

On a Mac with a real GPU the render should take a few minutes (`CONC=3` parallel tabs by default; lower it if memory is tight). Narration is the slow part: each 1.7B model runs on the CPU in float32 and needs about 9 GB of free RAM (use a Mac with 16 GB or more).

## Voice cloning (optional, local only)
Put a clean 15-30 s WAV of a voice you have permission to clone, plus the EXACT words spoken, in `voice/reference/`. That folder is git-ignored on purpose because the repository is public. The clone uses `Qwen/Qwen3-TTS-12Hz-1.7B-Base` with the transcript in in-context mode. It copies the timbre but often not the speaker's delivery, so compare it with Aiden by ear.

## What to edit

| File | What it controls |
|---|---|
| `narration.txt` | the words the voice reads; blank line = a new take |
| `delivery.json` | one entry per take: an `instruct` text (tone, pace, emotion), optional `pace` / `pitch_semitones` / `gain_db` / `pause_ms` |
| `audio/okene_mix.py` | the mix: voice EQ, per-word level table `LEVELS`, ambience, effects, the light score, loudness |
| `remotion/src/videos/okene/story.ts` | shots and camera, keyed to the word timings |
| `remotion/src/videos/okene/world.ts` | the three places (seabed, air pocket, surface) and the characters |

Every cut, camera move and sound cue is keyed to `words.json`, so after the voice changes always run `voice` again, then `mix`, then `render`. Beats whose text and instruction did not change are reused from `voice/beats/`, so retrying one line is cheap. `python candidates.py 2 3` generates three takes of beat 2 and keeps the one with no mid-phrase gap.

## Things that bit us (read before debugging)

- **Blank 3D frames:** `@react-three/postprocessing` is pinned to **3.0.4**. Newer versions create their composer a render too late, and Remotion draws each frame once, so every frame comes out empty. Do not upgrade it.
- **Remotion's own browser:** the scripts use Remotion's headless Chrome, not your desktop Chrome. Reuse one browser for many frames (the scripts do); starting a new one per frame is very slow.
- **bfloat16 is slow on CPUs without hardware support.** Keep `style_dtype` at `float32`. On Apple silicon you can try `export QWEN_DEVICE=mps PYTORCH_ENABLE_MPS_FALLBACK=1` for generation (untested; compare against the CPU result).
- **Voice delivery is the weak spot.** The model follows style text loosely (it read a date louder than the action and sometimes stumbles). Levels are corrected in the mix, stumbles are filtered by `candidates.py`, but expressive storytelling may still need a recorded or cloned human voice. The repository's own guidance on narration is thin: the reference narrator is described as "fast and steady".
- **Word timings:** Whisper starts words early after a pause; `retime.py` snaps them to the real speech edges. Check `voice/words.json` if a cut looks off.
