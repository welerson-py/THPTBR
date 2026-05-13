"""TTS for Haitian Creole via Meta MMS-TTS-hat, and Portuguese via pyttsx3 (Windows SAPI).

Both are offline. Kreyol TTS is the valuable one (volunteers can read PT themselves).
"""
import os
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import io
from functools import lru_cache

import numpy as np
import torch
from transformers import VitsModel, AutoTokenizer


from pathlib import Path
TTS_HAT_REPO = "facebook/mms-tts-hat"
TTS_LOCAL = Path(__file__).resolve().parent.parent / "models" / "mms-tts-hat"


@lru_cache(maxsize=1)
def get_tts_hat():
    src = str(TTS_LOCAL) if TTS_LOCAL.exists() else TTS_HAT_REPO
    tok = AutoTokenizer.from_pretrained(src)
    model = VitsModel.from_pretrained(src)
    model.eval()
    return tok, model, model.config.sampling_rate


def synth_kreyol(text: str) -> tuple[np.ndarray, int]:
    """Generate kreyol speech. Returns (audio_array_float32, sample_rate)."""
    text = text.strip()
    if not text:
        return np.zeros(1, dtype=np.float32), 16000
    tok, model, sr = get_tts_hat()
    inputs = tok(text, return_tensors="pt")
    with torch.no_grad():
        waveform = model(**inputs).waveform
    audio = waveform.squeeze().cpu().numpy().astype(np.float32)
    # Normalize to avoid clipping
    peak = np.abs(audio).max()
    if peak > 0:
        audio = audio / peak * 0.95
    return audio, sr


def synth_kreyol_wav_bytes(text: str) -> bytes:
    """Same as synth_kreyol but returns WAV bytes (for Streamlit st.audio)."""
    audio, sr = synth_kreyol(text)
    # Convert to int16 WAV
    import wave
    int16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16.tobytes())
    return buf.getvalue()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    test_text = "Bonjou, kijan ou ye? Mwen kontan rankontre ou."
    print(f"Synthesizing: {test_text!r}")
    audio, sr = synth_kreyol(test_text)
    print(f"Generated {len(audio)} samples at {sr} Hz ({len(audio)/sr:.1f}s)")
    # Save for listening
    from pathlib import Path
    out = Path(r"C:\Users\ResTIC55\oficina-imigrantes-ai\data\tts_test.wav")
    out.write_bytes(synth_kreyol_wav_bytes(test_text))
    print(f"Saved to {out}")
