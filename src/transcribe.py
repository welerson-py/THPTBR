"""Transcribe audio with faster-whisper or MMS-1B (Meta), depending on ASR_BACKEND.

- "whisper": fast, OK quality for kreyol
- "mms": Meta MMS-1B, much better kreyol but no native segmentation
- "hybrid" (default): Whisper segments the audio (VAD timestamps),
  MMS-1B transcribes each segment — best of both
"""
from pathlib import Path
from functools import lru_cache

from faster_whisper import WhisperModel
from config import WHISPER_MODEL, WHISPER_COMPUTE, WHISPER_LANG, ASR_BACKEND


@lru_cache(maxsize=1)
def get_whisper() -> WhisperModel:
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE)


def _whisper_segments(audio_path: Path) -> list[dict]:
    model = get_whisper()
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


def transcribe(audio_path: Path) -> list[dict]:
    """Returns list of {start, end, text} segments using configured backend."""
    backend = ASR_BACKEND
    if backend == "whisper":
        return _whisper_segments(audio_path)

    # Both "mms" and "hybrid" use Whisper for VAD timestamps
    segs = _whisper_segments(audio_path)
    if not segs:
        return []

    # Replace text with MMS transcription per segment
    from transcribe_mms import transcribe_segments as mms_transcribe_segments
    mms_segs = mms_transcribe_segments(audio_path, segs)
    return [
        {"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()}
        for s in mms_segs
        if s["text"].strip()
    ]
