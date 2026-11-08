"""Generate narration for a short in an external production workspace."""
import argparse
import json
from math import gcd
import os
from pathlib import Path
import re
from shutil import copyfile
from tempfile import NamedTemporaryFile
from uuid import uuid4


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RUNTIME = REPO.parent / "shorts-runtime"


def outside_repo(path):
    resolved = path.resolve()
    if resolved.is_relative_to(REPO):
        raise ValueError(f"Use a location outside the skill repository: {resolved}")
    return resolved


def profile_file():
    return outside_repo(RUNTIME / "narrator" / "profile.json")


def read_profile():
    path = profile_file()
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_profile(speaker, language, cloning, reference=None, transcript=""):
    path = profile_file()
    profile = read_profile()
    profile.update(speaker=speaker, language=language, mode="clone" if cloning else "preset")
    if cloning:
        filename = profile.get("reference")
        if not reference and (not filename or not (path.parent / filename).is_file()):
            raise ValueError("Upload a WAV, FLAC or MP3 recording first.")
        if reference:
            suffix = Path(reference).suffix.lower()
            if suffix not in {".wav", ".flac", ".mp3"}:
                raise ValueError("Use a WAV, FLAC or MP3 recording.")
            filename = f"reference-{uuid4().hex}{suffix}"
            path.parent.mkdir(parents=True, exist_ok=True)
            copyfile(reference, path.parent / filename)
        profile.update(reference=filename, transcript=(transcript or "").strip())
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
        staging = Path(file.name)
        json.dump(profile, file, indent=2)
    try:
        staging.replace(path)
    finally:
        staging.unlink(missing_ok=True)


def workspace_file(workspace, relative_path):
    workspace = outside_repo(workspace)
    if REPO.is_relative_to(workspace):
        raise ValueError("Choose a dedicated folder for this short.")
    path = outside_repo(workspace / relative_path)
    if not path.is_relative_to(workspace):
        raise ValueError("Narration input and output must stay inside the short workspace.")
    return path


def configure_cache():
    cache = outside_repo(RUNTIME / "huggingface")
    os.environ["HF_HOME"] = str(cache)
    os.environ["HF_HUB_CACHE"] = str(cache / "hub")
    os.environ["HF_XET_CACHE"] = str(cache / "xet")
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")


def load_model(model_id, revision, *, download=False):
    configure_cache()

    import torch
    from huggingface_hub import snapshot_download
    from qwen_tts import Qwen3TTSModel

    snapshot = snapshot_download(model_id, revision=revision, local_files_only=not download)
    return Qwen3TTSModel.from_pretrained(
        snapshot, device_map="cpu", dtype=torch.float32, attn_implementation="sdpa",
        local_files_only=True,
    )


def narration_paragraphs(text):
    paragraphs = re.split(r"\n[ \t]*\n", text.strip())
    if not paragraphs[0]:
        raise ValueError("Enter the text you want narrated.")
    return paragraphs


def delivery_plan(workspace, count):
    path = workspace_file(workspace, "delivery.json")
    if not path.exists():
        return [{} for _ in range(count)]
    beats = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(beats, list) or len(beats) != count:
        raise ValueError("delivery.json needs one object per narration paragraph.")
    limits = {"pace": (0.8, 1.25), "pitch_semitones": (-3, 3),
              "gain_db": (-12, 6), "pause_ms": (0, 2000)}
    for beat in beats:
        if not isinstance(beat, dict) or beat.keys() - limits.keys():
            raise ValueError("Use pace, pitch_semitones, gain_db and pause_ms in delivery.json.")
        for key, value in beat.items():
            low, high = limits[key]
            if type(value) not in (int, float) or not low <= value <= high:
                raise ValueError(f"{key} must be between {low} and {high}.")
    return beats


def shape_beat(audio, rate, beat):
    pitch = beat.get("pitch_semitones", 0)
    pace = beat.get("pace", 1)
    if pitch or pace != 1:
        from librosa import effects

        if pitch:
            audio = effects.pitch_shift(audio, sr=rate, n_steps=pitch)
        if pace != 1:
            audio = effects.time_stretch(audio, rate=pace)
    return audio * 10 ** (beat.get("gain_db", 0) / 20)


def write_narration(paragraphs, output, config, synthesize, beats):
    import numpy as np
    from scipy.signal import resample_poly
    import soundfile

    rate = config["sample_rate"]
    takes = []
    for index, (paragraph, beat) in enumerate(zip(paragraphs, beats, strict=True), start=1):
        print(f"Synthesizing paragraph {index}/{len(paragraphs)}", flush=True)
        audio, source_rate = synthesize(paragraph)
        divisor = gcd(rate, source_rate)
        takes.append(resample_poly(shape_beat(audio[0], source_rate, beat),
                                   rate // divisor, source_rate // divisor))
        if index < len(paragraphs):
            pause_ms = beat.get("pause_ms", config["paragraph_pause_ms"])
            takes.append(np.zeros(round(rate * pause_ms / 1000), dtype=np.float32))

    waveform = np.concatenate(takes)
    peak = float(np.max(np.abs(waveform)))
    if peak > 0.98:
        waveform *= 0.98 / peak

    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=output.parent, suffix=".wav", delete=False) as temporary:
        staging = Path(temporary.name)
    try:
        soundfile.write(staging, waveform, rate, subtype="PCM_24")
        # Publish the finished file without replacing an existing take, even on concurrent runs.
        os.link(staging, output)
    finally:
        staging.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Download and load the model without synthesizing")
    mode.add_argument("--check-clone", action="store_true", help="Download and load the cloning model")
    mode.add_argument("--workspace", type=Path, help="External short folder containing narration.txt")
    parser.add_argument("--config", type=Path, default=HERE / "qwen.json")
    args = parser.parse_args()

    try:
        if args.workspace:
            source = workspace_file(args.workspace, "narration.txt")
            output = workspace_file(args.workspace, "voice/voice.wav")
            if output.exists():
                raise ValueError(f"Archive the previous take before generating again: {output}")
            paragraphs = narration_paragraphs(source.read_text(encoding="utf-8-sig"))
            beats = delivery_plan(args.workspace, len(paragraphs))
            profile = read_profile()

        config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.check_clone:
        model = load_model(config["clone_model"], config["clone_revision"], download=True)
        if model.model.tts_model_type != "base":
            parser.error("The configured clone model must be a Qwen3-TTS Base checkpoint.")
        print(f"Loaded {config['clone_model']} on CPU.")
        return

    if args.check:
        model = load_model(config["model"], config["revision"], download=True)
        speakers = model.get_supported_speakers() or []
        languages = model.get_supported_languages() or []
        if config["speaker"].lower() not in [speaker.lower() for speaker in speakers]:
            parser.error(f"Speaker is unavailable: {config['speaker']}")
        if config["language"].lower() not in [language.lower() for language in languages]:
            parser.error(f"Language is unavailable: {config['language']}")
        print(f"Loaded {config['model']} on CPU with {config['speaker']} ({config['language']}).")
        return

    language = profile.get("language", config["language"])
    if profile.get("mode") == "clone":
        reference = profile_file().parent / profile["reference"]
        if not reference.is_file():
            parser.error("The saved reference recording is missing. Save it again in Narration Studio.")
        model = load_model(config["clone_model"], config["clone_revision"])
        transcript = profile.get("transcript")
        prompt = model.create_voice_clone_prompt(
            ref_audio=str(reference), ref_text=transcript or None, x_vector_only_mode=not transcript,
        )

        def synthesize(text):
            return model.generate_voice_clone(text=text, language=language, voice_clone_prompt=prompt)
    else:
        model = load_model(config["model"], config["revision"])
        speaker = profile.get("speaker", config["speaker"])

        def synthesize(text):
            return model.generate_custom_voice(text=text, language=language, speaker=speaker)

    write_narration(paragraphs, output, config, synthesize, beats)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
