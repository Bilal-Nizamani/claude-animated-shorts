# Claude Animated Shorts

The free Claude skill from the video **"How to Make Viral Animated Shorts Using Claude (Full Workflow)"**.

It makes 55-70 s vertical animated story shorts with 2D characters in a colourful 3D world, ink outlines, a painted town, lens blur, gliding cameras, a march score and sound effects. GSAP timelines drive motion in the Three.js scene, and Remotion samples them at the requested frame for export.

Proven on **The Bridge That Fell for a Song**, a 67 s short about the 1831 Broughton bridge.

## What's inside
| Path | What it is |
|---|---|
| `SKILL.md` | The skill: the full pipeline, every rule, every fix, and the final look values |
| `templates/bridge/` | The full source of the bridge short: world, characters, ink, lens blur, grade, story/camera |
| `templates/audio/` | The synthesized sound: SFX, march music, the mix with ducking and loudness |
| `templates/scripts/` | Stills, side-by-side sheets, shot merge and frame-by-frame QA helpers |
| `references/STYLE_BIBLE.md` | The script and visual formula measured from 20 reference shorts |
| `references/GSAP_MOTION.md` | Reusable frame-driven animation patterns and motion checks |
| `references/PRODUCTION.md` | External production workspaces and Windows setup for local Qwen3-TTS |
| `templates/voice/` | Voice model configuration, setup and narration command |
| `Open Narration Studio.cmd` | Windows launcher for selecting a narrator or cloning a voice |
| `references/reports/` | Seven measured reports: motion, depth, textures, characters, lighting, outlines, grade |

## Install
1. Copy this folder to `~/.claude/skills/cartoon-3d-short/` (clone it there, or download the ZIP).
2. Follow the [production setup](references/PRODUCTION.md) to install Qwen3-TTS and create a separate folder for each short.
3. In the short's [Remotion](https://www.remotion.dev/) project with `@remotion/three`, run `npm install gsap`. The workflow also uses Node, Python 3 and ffmpeg.
4. In Claude Code, say: *"Use the cartoon short skill and make a short about …"*.

Claude then follows `SKILL.md`: topic and facts, then script, then voice, then the shot plan in `story.ts`, then stills, then renders. Agents check your frames against the reports and the frames, and you get the final 2K render and sound mix.

## Notes
- Keep finished shorts, voice recordings, model weights and render outputs in the sibling production and runtime folders. In a fresh clone, run `git config --local core.hooksPath .githooks` to enable the push check for ignored files.
- Set `REMOTION_TMP` to a folder on a big drive. Every Remotion bundle copies `public/` (~1.3 GB) into the temp folder.
- Story, characters and voice should always be your own. Use the references for the look, not the content.

## License
The code and docs are MIT (see `LICENSE`). Keep private reference media in local study folders.
