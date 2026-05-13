"""Live conversation pipeline: microphone audio -> ASR -> translation -> output.

Two directions:
- PT (voluntario fala) -> KR (display + TTS for the Haitian)
- KR (imigrante fala)  -> PT (display for the volunteer)

PT direction uses Whisper (fast, accurate PT).
KR direction uses MMS-1B (much better than Whisper on kreyol).
"""
import os
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import tempfile
from pathlib import Path
from functools import lru_cache

import numpy as np
import librosa

from translate import pt_to_kr, kr_to_pt


TARGET_SR = 16000


def _save_audio_to_tempfile(audio_bytes: bytes) -> Path:
    """Streamlit's audio_input returns bytes (WAV). Save to temp for ASR loading."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(audio_bytes)
    tmp.close()
    return Path(tmp.name)


def _load_16k_mono(path: Path) -> np.ndarray:
    audio, _ = librosa.load(str(path), sr=TARGET_SR, mono=True)
    return audio.astype(np.float32)


@lru_cache(maxsize=1)
def _whisper_pt():
    from faster_whisper import WhisperModel
    return WhisperModel("small", device="cpu", compute_type="int8")


def transcribe_pt(audio_path: Path) -> str:
    """Volunteer speaking Portuguese."""
    model = _whisper_pt()
    segments, _info = model.transcribe(
        str(audio_path),
        beam_size=1,
        vad_filter=True,
        language="pt",
    )
    return " ".join(s.text.strip() for s in segments).strip()


def transcribe_kr(audio_path: Path) -> str:
    """Immigrant speaking kreyol — uses MMS-1B which is much better than Whisper here."""
    from transcribe_mms import transcribe_audio_array
    audio = _load_16k_mono(audio_path)
    return transcribe_audio_array(audio)


def pt_says_to_kr(audio_bytes: bytes) -> dict:
    """Volunteer's PT audio -> kreyol output."""
    path = _save_audio_to_tempfile(audio_bytes)
    try:
        pt_text = transcribe_pt(path)
        kr_text = pt_to_kr(pt_text) if pt_text else ""
        return {"pt": pt_text, "kr": kr_text}
    finally:
        path.unlink(missing_ok=True)


def kr_says_to_pt(audio_bytes: bytes) -> dict:
    """Immigrant's kreyol audio -> PT output."""
    path = _save_audio_to_tempfile(audio_bytes)
    try:
        kr_text = transcribe_kr(path)
        pt_text = kr_to_pt(kr_text) if kr_text else ""
        return {"kr": kr_text, "pt": pt_text}
    finally:
        path.unlink(missing_ok=True)
