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


def load_model(model_id, revision, *, download=False, dtype="float32"):
    configure_cache()

    import torch
    from huggingface_hub import snapshot_download
    from qwen_tts import Qwen3TTSModel

    snapshot = snapshot_download(model_id, revision=revision, local_files_only=not download)
    return Qwen3TTSModel.from_pretrained(
        snapshot, device_map=os.environ.get("QWEN_DEVICE", "cpu"), dtype=getattr(torch, dtype), attn_implementation="sdpa",
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
        if not isinstance(beat, dict) or beat.keys() - limits.keys() - {"instruct"}:
            raise ValueError("Use instruct, pace, pitch_semitones, gain_db and pause_ms in delivery.json.")
        if "instruct" in beat and (not isinstance(beat["instruct"], str) or len(beat["instruct"]) > 400):
            raise ValueError("instruct must be a short text (up to 400 characters).")
        for key, value in beat.items():
            if key == "instruct":
                continue
            low, high = limits[key]
            if type(value) not in (int, float) or not low <= value <= high:
                raise ValueError(f"{key} must be between {low} and {high}.")
    return beats


def find_ffmpeg():
    """ffmpeg from FFMPEG, the PATH, or a winget install (used for high-quality time-stretch / pitch-shift)"""
    from glob import glob
    from shutil import which

    exe = os.environ.get("FFMPEG") or which("ffmpeg")
    if exe:
        return exe
    hits = glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe"))
    return hits[0] if hits else None


def rubberband(audio, rate, pace, pitch_semitones):
    """Rubber Band (formant-preserving) via ffmpeg: far cleaner than a phase vocoder, no hollow 'in a tube' smear"""
    exe = find_ffmpeg()
    if not exe:
        return None
    import subprocess
    import tempfile

    import soundfile

    with tempfile.TemporaryDirectory() as folder:
        src, dst = Path(folder) / "in.wav", Path(folder) / "out.wav"
        soundfile.write(src, audio, rate, subtype="FLOAT")
        chain = (f"rubberband=tempo={pace}:pitch={2 ** (pitch_semitones / 12)}:formant=preserved:transients=mixed:"
                 "pitchq=quality:phase=laminar:window=standard:smoothing=off")
        run = subprocess.run([exe, "-v", "error", "-y", "-i", str(src), "-af", chain, "-c:a", "pcm_f32le", str(dst)],
                             capture_output=True, text=True)
        if run.returncode:
            return None
        shaped, _ = soundfile.read(dst, dtype="float32")
    return shaped


def shape_beat(audio, rate, beat):
    pitch = beat.get("pitch_semitones", 0)
    pace = beat.get("pace", 1)
    if pitch or pace != 1:
        shaped = rubberband(audio, rate, pace, pitch)
        if shaped is None:  # no ffmpeg / rubberband available: fall back to the phase vocoder
            from librosa import effects

            shaped = audio
            if pitch:
                shaped = effects.pitch_shift(shaped, sr=rate, n_steps=pitch)
            if pace != 1:
                shaped = effects.time_stretch(shaped, rate=pace)
        audio = shaped
    return audio * 10 ** (beat.get("gain_db", 0) / 20)


def beat_cache_path(cache_dir, paragraph, instruct, extra=""):
    """one cached raw take per (text, instruction, voice): change one beat and only that beat is generated again"""
    import hashlib

    key = hashlib.sha1(f"{paragraph.strip()}|{instruct or ''}|{extra}".encode("utf-8")).hexdigest()[:12]
    return Path(cache_dir) / f"beat-{key}.npz"


def write_narration(paragraphs, output, config, synthesize, beats, cache_dir=None, cache_extra=""):
    import numpy as np
    from scipy.signal import resample_poly
    import soundfile

    rate = config["sample_rate"]
    takes = []
    for index, (paragraph, beat) in enumerate(zip(paragraphs, beats, strict=True), start=1):
        cached = beat_cache_path(cache_dir, paragraph, beat.get("instruct"), cache_extra) if cache_dir else None
        if cached is not None and cached.is_file():
            print(f"Reusing saved take for paragraph {index}/{len(paragraphs)}", flush=True)
            saved = np.load(cached)
            audio, source_rate = saved["audio"][None, :], int(saved["rate"])
        else:
            print(f"Synthesizing paragraph {index}/{len(paragraphs)}", flush=True)
            audio, source_rate = synthesize(paragraph, beat.get("instruct"))
            if cached is not None:
                cached.parent.mkdir(parents=True, exist_ok=True)
                np.savez(cached, audio=np.asarray(audio[0], dtype=np.float32), rate=source_rate)
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


def narrator_synthesizer(model, *, speaker, language, reference=None, transcript=None):
    """returns synthesize(text, instruct=None); instruct (tone / pace / emotion in plain words) needs the 1.7B CustomVoice model"""
    if reference is None:
        return lambda text, instruct=None: model.generate_custom_voice(
            text=text, language=language, speaker=speaker, instruct=(instruct or None))
    transcript = (transcript or "").strip()
    prompt = model.create_voice_clone_prompt(
        ref_audio=str(reference), ref_text=transcript or None, x_vector_only_mode=not transcript,
    )
    return lambda text, instruct=None: model.generate_voice_clone(
        text=text, language=language, voice_clone_prompt=prompt,
    )


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

    reference = None
    if profile.get("mode") == "clone":
        reference = profile_file().parent / profile["reference"]
        if not reference.is_file():
            parser.error("The saved reference recording is missing. Save it again in Narration Studio.")
        model = load_model(config["clone_model"], config["clone_revision"])
    elif args.workspace and any("instruct" in beat for beat in beats) and config.get("style_model"):
        # style instructions (tone, pace, emotion) are only understood by the 1.7B CustomVoice model
        print(f"Loading {config['style_model']} for styled delivery (slower on CPU)...", flush=True)
        model = load_model(config["style_model"], config["style_revision"], dtype=config.get("style_dtype", "float32"))
    else:
        model = load_model(config["model"], config["revision"])

    synthesize = narrator_synthesizer(
        model, speaker=profile.get("speaker", config["speaker"]),
        language=profile.get("language", config["language"]),
        reference=reference, transcript=profile.get("transcript"),
    )
    write_narration(paragraphs, output, config, synthesize, beats,
                    cache_dir=workspace_file(args.workspace, "voice/beats"),
                    cache_extra=f"{profile.get('mode')}|{profile.get('speaker', config['speaker'])}|{profile.get('language', config['language'])}")
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
