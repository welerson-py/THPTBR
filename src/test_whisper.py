"""Test Whisper on the sample audio, comparing language=ht vs auto-detect."""
import sys
import json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from faster_whisper import WhisperModel

AUDIO = Path(r"C:\Users\ResTIC55\oficina-imigrantes-ai\data\audio\qo-n2AiGzTA.mp3")
OUT = Path(r"C:\Users\ResTIC55\oficina-imigrantes-ai\data\transcripts\test_compare.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

print("Loading Whisper small (int8, CPU)...")
model = WhisperModel("small", device="cpu", compute_type="int8")

results = {}

for lang_label, lang_arg in [("auto", None), ("forced_ht", "ht"), ("forced_fr", "fr")]:
    print(f"\n=== Transcribing with language={lang_arg} ===")
    segments, info = model.transcribe(
        str(AUDIO),
        beam_size=1,
        vad_filter=True,
        language=lang_arg,
    )
    segs = []
    for seg in segments:
        segs.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
    results[lang_label] = {
        "detected_language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration": round(info.duration, 1),
        "segments": segs,
    }
    print(f"Detected: {info.language} (prob {info.language_probability:.2f})  segments: {len(segs)}")
    # Print first 5 for quick eye-check
    for s in segs[:5]:
        print(f"  [{s['start']:6.1f}-{s['end']:6.1f}] {s['text']}")

OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nFull comparison saved to: {OUT}")
