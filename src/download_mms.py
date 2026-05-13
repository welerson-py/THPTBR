"""Download MMS models (ASR + TTS for kreyol). Avoids HF symlink issues on Windows."""
import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from huggingface_hub import snapshot_download
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS = PROJECT_ROOT / "models"
MODELS.mkdir(exist_ok=True)


def download_asr():
    target = MODELS / "mms-1b-all"
    target.mkdir(exist_ok=True)
    print(f"\n[ASR] Downloading MMS-1B base + hat adapter to {target}...")
    snapshot_download(
        repo_id="facebook/mms-1b-all",
        local_dir=str(target),
        allow_patterns=[
            "config.json", "preprocessor_config.json", "tokenizer_config.json",
            "special_tokens_map.json", "vocab.json", "*.model",
            "model.safetensors", "adapter*hat*",
        ],
    )
    print("[ASR] done.")


def download_tts():
    target = MODELS / "mms-tts-hat"
    target.mkdir(exist_ok=True)
    print(f"\n[TTS] Downloading MMS-TTS-hat to {target}...")
    snapshot_download(
        repo_id="facebook/mms-tts-hat",
        local_dir=str(target),
    )
    print("[TTS] done.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or "asr" in args:
        download_asr()
    if not args or "tts" in args:
        download_tts()
    print("\nALL DONE")
