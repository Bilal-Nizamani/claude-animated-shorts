"""Download the Qwen3-TTS checkpoints into the shared cache (shorts-runtime/huggingface, outside Git).
usage: python download_models.py [--no-style] [--clone]
  default      0.6B CustomVoice (fast preset voices) + 1.7B CustomVoice (style instructions: tone, pace, emotion)
  --no-style   skip the 1.7B model (about 4.5 GB)
  --clone      also fetch the 0.6B Base model used for voice cloning"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parents[1].parent / "shorts-runtime"
os.environ["HF_HOME"] = str(RUNTIME / "huggingface")
os.environ["HF_HUB_CACHE"] = str(RUNTIME / "huggingface" / "hub")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")

from huggingface_hub import snapshot_download  # noqa: E402

config = json.loads((HERE / "qwen.json").read_text(encoding="utf-8-sig"))
jobs = [(config["model"], config["revision"], "0.6B CustomVoice (fast preset voices)")]
if config.get("style_model") and "--no-style" not in sys.argv:
    jobs.append((config["style_model"], config["style_revision"], "1.7B CustomVoice (style instructions)"))
if "--clone" in sys.argv:
    jobs.append((config["clone_model"], config["clone_revision"], "0.6B Base (voice cloning)"))

for model_id, revision, label in jobs:
    print(f"Downloading {label}: {model_id}", flush=True)
    print("  ->", snapshot_download(model_id, revision=revision), flush=True)
print("Models ready in", RUNTIME / "huggingface")
