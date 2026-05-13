"""Transcribe audio with faster-whisper, forced to Haitian Creole."""
from pathlib import Path
from functools import lru_cache

from faster_whisper import WhisperModel
from config import WHISPER_MODEL, WHISPER_COMPUTE, WHISPER_LANG


@lru_cache(maxsize=1)
def get_model() -> WhisperModel:
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE)


def transcribe(audio_path: Path) -> list[dict]:
    """Returns list of {start, end, text} segments."""
    model = get_model()
    segments, _info = model.transcribe(
        str(audio_path),
        beam_size=1,
        vad_filter=True,
        language=WHISPER_LANG,
        word_timestamps=False,
    )
    return [
        {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        for s in segments
        if s.text.strip()
    ]
