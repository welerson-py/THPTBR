"""Transcribe audio with Meta MMS-1B (multilingual, with adapter for kreyol haitiano).

MMS handles low-resource languages much better than Whisper. We force lang='hat'.
Audio is segmented externally (Whisper VAD timestamps) and each segment fed to MMS.
"""
import os
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from functools import lru_cache
from pathlib import Path

import torch
import numpy as np
import librosa
from transformers import AutoModelForCTC, AutoProcessor

from config import ROOT

MMS_LOCAL = ROOT / "models" / "mms-1b-all"
TARGET_LANG = "hat"
TARGET_SR = 16000


@lru_cache(maxsize=1)
def get_mms():
    # Load from local snapshot (avoids HF symlink issues on Windows)
    src = str(MMS_LOCAL) if MMS_LOCAL.exists() else "facebook/mms-1b-all"
    processor = AutoProcessor.from_pretrained(src)
    processor.tokenizer.set_target_lang(TARGET_LANG)
    model = AutoModelForCTC.from_pretrained(src, target_lang=TARGET_LANG, ignore_mismatched_sizes=True)
    model.eval()
    return processor, model


def _load_audio_16k_mono(path: Path) -> np.ndarray:
    audio, _ = librosa.load(str(path), sr=TARGET_SR, mono=True)
    return audio.astype(np.float32)


def transcribe_audio_array(audio: np.ndarray) -> str:
    processor, model = get_mms()
    inputs = processor(audio, sampling_rate=TARGET_SR, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    pred_ids = torch.argmax(logits, dim=-1)
    text = processor.batch_decode(pred_ids)[0]
    return text.strip()


def transcribe_segments(audio_path: Path, segments: list[dict]) -> list[dict]:
    """For each Whisper-derived segment {start, end}, run MMS on that slice and replace text."""
    audio = _load_audio_16k_mono(audio_path)
    out = []
    for seg in segments:
        s = int(seg["start"] * TARGET_SR)
        e = int(seg["end"] * TARGET_SR)
        clip = audio[s:e]
        if len(clip) < TARGET_SR // 4:  # skip <0.25s
            continue
        text = transcribe_audio_array(clip)
        if not text:
            continue
        out.append({"start": seg["start"], "end": seg["end"], "text": text})
    return out


def transcribe_full(audio_path: Path) -> str:
    """Transcribe whole audio file at once (no segmentation)."""
    audio = _load_audio_16k_mono(audio_path)
    return transcribe_audio_array(audio)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from config import AUDIO_DIR
    test_file = next(AUDIO_DIR.glob("*.mp3"))
    print(f"Testing MMS on {test_file.name}...")
    text = transcribe_full(test_file)
    print(f"\nFull transcription:\n{text[:1000]}")
