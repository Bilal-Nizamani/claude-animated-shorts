"""Download the Qwen3-TTS checkpoints into the shared cache (shorts-runtime/huggingface, outside Git).
usage: python download_models.py [--no-clone]
  default      1.7B CustomVoice (preset voices + style instructions: tone, pace, emotion), about 4.5 GB
               1.7B Base (voice cloning from a short reference clip), about 4.5 GB
  --no-clone   skip the 1.7B Base model
The 0.6B models were dropped: they ignore style instructions and sound flatter. Each 1.7B model needs about 9 GB of free RAM in float32."""
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
jobs = [(config["model"], config["revision"], "1.7B CustomVoice (preset voices + style instructions)")]
if "--no-clone" not in sys.argv:
    jobs.append((config["clone_model"], config["clone_revision"], "1.7B Base (voice cloning)"))

for model_id, revision, label in jobs:
    print(f"Downloading {label}: {model_id}", flush=True)
    print("  ->", snapshot_download(model_id, revision=revision), flush=True)
print("Models ready in", RUNTIME / "huggingface")
