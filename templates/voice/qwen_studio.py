"""Save the narrator used by the local short-production workflow."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from qwen_narrate import (
    HERE, REPO, RUNTIME, configure_cache, load_model, narrator_synthesizer,
    outside_repo, profile_file, read_profile, save_profile,
)


SPEAKERS = ["Ryan", "Aiden", "Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ono_Anna", "Sohee"]
LANGUAGES = ["English", "Chinese", "Japanese", "Korean", "German", "French",
             "Russian", "Portuguese", "Spanish", "Italian"]
PRESET = "Preset narrator"
CLONE = "Clone a voice"
AUDITION_LINE = "A ship's cook spent almost three days at the bottom of the ocean, and lived to tell about it."


def audition_clip(text, language, name):
    """Where the saved audition clip for this line, language and narrator lives (outside the repo)."""
    key = hashlib.sha1(f"{language}\n{text.strip()}".encode("utf-8")).hexdigest()[:12]
    return outside_repo(RUNTIME / "auditions" / key / f"{name}.wav")


def build_studio():
    configure_cache()
    os.environ["GRADIO_TEMP_DIR"] = str(outside_repo(RUNTIME / "studio-temp"))
    import gradio as gr

    config = json.loads((HERE / "qwen.json").read_text(encoding="utf-8-sig"))
    profile = read_profile()
    cloning = profile.get("mode") == "clone"
    clone_cache = (
        RUNTIME / "huggingface" / "hub" / f"models--{config['clone_model'].replace('/', '--')}"
        / "snapshots" / config["clone_revision"]
    )
    clone_ready = all((clone_cache / path).is_file() for path in (
        "config.json", "model.safetensors", "speech_tokenizer/model.safetensors",
    ))
    model = None
    model_key = None

    def get_model(cloning, *, download=False):
        nonlocal model, model_key
        key, revision = ("clone_model", "clone_revision") if cloning else ("model", "revision")
        if key != model_key:
            model, model_key = None, None
            model = load_model(config[key], config[revision], download=download)
            model_key = key
        return model

    def install_cloning():
        try:
            get_model(True, download=True)
            return gr.update(visible=False), "Cloning model is ready."
        except (OSError, ValueError) as exc:
            raise gr.Error(str(exc)) from exc

    def save(mode, speaker, language, reference, transcript):
        try:
            save_profile(speaker, language, mode == CLONE, reference, transcript)
        except (OSError, ValueError) as exc:
            raise gr.Error(str(exc)) from exc
        label = "your reference voice" if mode == CLONE else speaker
        return f"Saved {label} as the narrator for future shorts."

    def preview(text, mode, speaker, language, reference, transcript):
        try:
            text = (text or "").strip()
            if not 1 <= len(text) <= 280:
                raise ValueError("Enter a test line of up to 280 characters.")
            cloning = mode == CLONE
            sample = None
            if cloning:
                saved_reference = read_profile().get("reference")
                if reference:
                    sample = Path(reference)
                elif saved_reference:
                    sample = profile_file().parent / saved_reference
                if sample is None or not sample.is_file():
                    raise ValueError("Upload a recording or save a reference voice first.")
            synthesize = narrator_synthesizer(
                get_model(cloning), speaker=speaker, language=language,
                reference=sample, transcript=transcript,
            )
            audio, rate = synthesize(text)
            return rate, audio[0]
        except (OSError, ValueError) as exc:
            raise gr.Error(str(exc)) from exc

    def saved_clips(text, language):
        paths = [audition_clip(text, language, name) for name in SPEAKERS]
        return [str(path) if path.is_file() else None for path in paths]

    def audition(text, language, regenerate, progress=gr.Progress()):
        """Speak one line with every preset narrator. Saved clips load instantly; only missing ones are made."""
        text = (text or "").strip()
        if not 1 <= len(text) <= 280:
            raise gr.Error("Enter an audition line of up to 280 characters.")
        import soundfile

        clips = [None if regenerate else clip for clip in saved_clips(text, language)]
        missing = [i for i, clip in enumerate(clips) if clip is None]
        reused = len(SPEAKERS) - len(missing)
        yield [*clips, f"{reused} saved clip(s) loaded. {len(missing)} to generate. "
                       "Loading the voice model first (can take a minute)..."]
        if missing:
            progress(0, desc="Loading the voice model...")
            try:
                preset_model = get_model(False)
            except (OSError, ValueError) as exc:
                raise gr.Error(str(exc)) from exc
        for done, index in enumerate(missing, start=1):
            name = SPEAKERS[index]
            progress((done - 1) / len(missing), desc=f"Generating {name} ({done}/{len(missing)})")
            yield [*clips, f"Generating {name} ({done}/{len(missing)}), about 20-60 s on CPU..."]
            audio, rate = narrator_synthesizer(preset_model, speaker=name, language=language)(text)
            path = audition_clip(text, language, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            soundfile.write(path, audio[0], rate)
            clips[index] = str(path)
            yield [*clips, f"{done}/{len(missing)} generated and saved. Last: {name}."]
        yield [*clips, "All narrators ready and saved. Press play on each, then press its Use button."]

    def use_narrator(name):
        def choose(language):
            try:
                save_profile(name, language, False)
            except (OSError, ValueError) as exc:
                raise gr.Error(str(exc)) from exc
            return f"Saved {name} as the narrator for future shorts."
        return choose

    with gr.Blocks(title="Narration Studio", analytics_enabled=False) as studio:
        gr.Markdown("# Narrator setup\nChoose the voice to use for future shorts and save it once.")
        mode = gr.Radio([PRESET, CLONE], value=CLONE if cloning else PRESET, label="Voice source")
        with gr.Row():
            speaker = gr.Dropdown(SPEAKERS, value=profile.get("speaker", config["speaker"]),
                                  label="Narrator", visible=not cloning)
            language = gr.Dropdown(LANGUAGES, value=profile.get("language", config["language"]),
                                   label="Narration language")
        with gr.Group(visible=cloning) as clone_fields:
            install = gr.Button("Set up cloning (one-time download)", visible=not clone_ready)
            clone_status = gr.Markdown("Cloning model is ready." if clone_ready else "")
            reference = gr.File(label="Reference recording (WAV, FLAC or MP3)",
                                file_types=[".wav", ".flac", ".mp3"])
            if profile.get("reference"):
                gr.Markdown("A reference recording is saved. Upload a new file to replace it.")
            transcript = gr.Textbox(label="Words spoken in the recording (optional)", lines=2,
                                    value=profile.get("transcript", ""))
        save_button = gr.Button("Save narrator", variant="primary")
        status = gr.Textbox(label="Status", interactive=False,
                            value="Saved narrator loaded." if profile else "")
        gr.Markdown("### Test this voice\nTry the current selection before saving it.")
        test_text = gr.Textbox(label="Test line", lines=2, max_lines=4,
                               placeholder="Type a short line in the selected language.")
        test_button = gr.Button("Test voice")
        test_audio = gr.Audio(label="Voice preview", format="wav", interactive=False)
        gr.Markdown("### Audition all narrators\nHear one line in every preset voice, then save your favourite.")
        audition_text = gr.Textbox(label="Audition line", lines=2, max_lines=4, value=AUDITION_LINE)
        regenerate = gr.Checkbox(label="Make new takes (ignore saved clips)", value=False)
        audition_button = gr.Button("Generate all narrators", variant="primary")
        first_clips = saved_clips(AUDITION_LINE, language.value)
        audition_status = gr.Textbox(
            label="Audition progress", interactive=False,
            value=f"{sum(clip is not None for clip in first_clips)}/{len(SPEAKERS)} clips saved for this line.")
        audition_clips = []
        for name, clip in zip(SPEAKERS, first_clips):
            with gr.Row():
                gr.Markdown(f"**{name}**")
                audition_clips.append(gr.Audio(value=clip, show_label=False, format="wav", interactive=False))
                gr.Button(f"Use {name}").click(use_narrator(name), inputs=language, outputs=status,
                                               concurrency_limit=1)
        audition_button.click(audition, inputs=[audition_text, language, regenerate],
                              outputs=[*audition_clips, audition_status],
                              concurrency_id="voice-model", concurrency_limit=1)
        mode.change(lambda value: (gr.update(visible=value == PRESET), gr.update(visible=value == CLONE)),
                    inputs=mode, outputs=[speaker, clone_fields], queue=False)
        install.click(install_cloning, outputs=[install, clone_status],
                      concurrency_id="voice-model", concurrency_limit=1)
        save_button.click(save, inputs=[mode, speaker, language, reference, transcript],
                          outputs=status, concurrency_limit=1)
        test_button.click(preview, inputs=[test_text, mode, speaker, language, reference, transcript],
                          outputs=test_audio, concurrency_id="voice-model", concurrency_limit=1)
    return studio


def prepare_auditions(text, language):
    """Generate and save any missing audition clips without opening the studio."""
    import soundfile

    config = json.loads((HERE / "qwen.json").read_text(encoding="utf-8-sig"))
    model = None
    for number, name in enumerate(SPEAKERS, start=1):
        path = audition_clip(text, language, name)
        if path.is_file():
            print(f"[{number}/{len(SPEAKERS)}] {name}: already saved", flush=True)
            continue
        if model is None:
            print("Loading the voice model...", flush=True)
            model = load_model(config["model"], config["revision"])
        print(f"[{number}/{len(SPEAKERS)}] {name}: generating...", flush=True)
        audio, rate = narrator_synthesizer(model, speaker=name, language=language)(text)
        path.parent.mkdir(parents=True, exist_ok=True)
        soundfile.write(path, audio[0], rate)
        print(f"[{number}/{len(SPEAKERS)}] {name}: saved", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--prepare", action="store_true",
                        help="Generate the saved audition clips for the default line, then exit")
    args = parser.parse_args()
    if args.prepare:
        configure_cache()
        prepare_auditions(AUDITION_LINE, read_profile().get("language", "English"))
        raise SystemExit(0)
    build_studio().launch(
        server_name="127.0.0.1", share=False, inbrowser=not args.no_browser,
        max_file_size="25mb", blocked_paths=[str(REPO)],
        allowed_paths=[str(outside_repo(RUNTIME / "auditions"))],
    )
