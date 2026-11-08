"""Save the narrator used by the local short-production workflow."""
import argparse
import json
import os

from qwen_narrate import HERE, REPO, RUNTIME, configure_cache, load_model, outside_repo, read_profile, save_profile


SPEAKERS = ["Ryan", "Aiden", "Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ono_Anna", "Sohee"]
LANGUAGES = ["English", "Chinese", "Japanese", "Korean", "German", "French",
             "Russian", "Portuguese", "Spanish", "Italian"]
PRESET = "Preset narrator"
CLONE = "Clone a voice"


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

    def install_cloning():
        try:
            load_model(config["clone_model"], config["clone_revision"], download=True)
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
        mode.change(lambda value: (gr.update(visible=value == PRESET), gr.update(visible=value == CLONE)),
                    inputs=mode, outputs=[speaker, clone_fields], queue=False)
        install.click(install_cloning, outputs=[install, clone_status], concurrency_limit=1)
        save_button.click(save, inputs=[mode, speaker, language, reference, transcript],
                          outputs=status, concurrency_limit=1)
    return studio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    build_studio().launch(
        server_name="127.0.0.1", share=False, inbrowser=not args.no_browser,
        max_file_size="25mb", blocked_paths=[str(REPO)],
    )
