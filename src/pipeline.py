"""End-to-end pipeline for one URL: download -> transcribe -> translate -> embed -> store."""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from download import download_audio, video_id
from transcribe import transcribe
from translate import translate
from embed_store import upsert
from config import TRANSCRIPT_DIR


def expand_segment(seg: dict, vid: str, seg_idx: int) -> list[dict]:
    """Split comma-separated word lists into one record per item.
    For normal sentences, returns the full segment as one record."""
    text = seg["text"].strip(" .")
    pieces = [p.strip(" .") for p in re.split(r"[,;]", text) if p.strip(" .")]
    duration = seg["end"] - seg["start"]
    records = []
    if len(pieces) >= 5:  # word list pattern
        per_piece = duration / len(pieces)
        for j, p in enumerate(pieces):
            records.append({
                "id": f"{vid}_{seg_idx:04d}_{j:02d}",
                "video_id": vid,
                "kreyol": p,
                "portuguese": "",  # filled in by translate step
                "start": round(seg["start"] + j * per_piece, 2),
                "end": round(seg["start"] + (j + 1) * per_piece, 2),
                "context": text,
            })
    else:
        records.append({
            "id": f"{vid}_{seg_idx:04d}",
            "video_id": vid,
            "kreyol": text,
            "portuguese": "",
            "start": seg["start"],
            "end": seg["end"],
            "context": text,
        })
    return records


def process_url(url: str, redo: bool = False) -> dict:
    vid = video_id(url)
    transcript_file = TRANSCRIPT_DIR / f"{vid}.json"
    if transcript_file.exists() and not redo:
        print(f"[skip] {vid} already processed")
        return json.loads(transcript_file.read_text(encoding="utf-8"))

    print(f"[1/4] download {vid}")
    audio = download_audio(url)
    if not audio:
        return {"video_id": vid, "status": "download_failed"}

    print(f"[2/4] transcribe (Whisper kreyol)")
    segments = transcribe(audio)
    print(f"      {len(segments)} segments")

    print(f"[3/4] expand + translate to Portuguese (NLLB)")
    records = []
    for i, seg in enumerate(segments):
        for r in expand_segment(seg, vid, i):
            r["portuguese"] = translate(r["kreyol"])
            records.append(r)
    print(f"      {len(records)} records after expansion")
    for r in records[:8]:
        print(f"      [{r['start']:6.1f}] KR: {r['kreyol'][:40]:40s} | PT: {r['portuguese'][:40]}")

    print(f"[4/4] embed + upsert to ChromaDB")
    upsert(records)

    result = {"video_id": vid, "status": "ok", "segments": records}
    transcript_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] saved {transcript_file.name} ({len(records)} records)")
    return result


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=qo-n2AiGzTA"
    redo = "--redo" in sys.argv
    process_url(url, redo=redo)
