"""Central configuration for the pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AUDIO_DIR = DATA / "audio"
TRANSCRIPT_DIR = DATA / "transcripts"
CHROMA_DIR = DATA / "chroma"
TTS_CACHE_DIR = DATA / "tts_cache"
QUEUE_FILE = DATA / "queue.txt"
PROCESSED_FILE = DATA / "processed.txt"
FAILED_FILE = DATA / "failed.txt"

for d in (AUDIO_DIR, TRANSCRIPT_DIR, CHROMA_DIR, TTS_CACHE_DIR):
    d.mkdir(parents=True, exist_ok=True)

WHISPER_MODEL = "small"
WHISPER_COMPUTE = "int8"
WHISPER_LANG = "ht"

# ASR backend for batch: "whisper" (rápido) | "mms" (qualidade) | "hybrid" (Whisper segmenta, MMS transcreve)
ASR_BACKEND = "hybrid"

NLLB_MODEL = "facebook/nllb-200-distilled-600M"
NLLB_SRC = "hat_Latn"
NLLB_TGT = "por_Latn"

EMBED_MODEL = "sentence-transformers/LaBSE"
CHROMA_COLLECTION = "kreyol_pt"
