"""End-to-end pipeline for one URL: download -> transcribe -> translate -> embed -> store."""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from download import download_audio, video_id
from transcribe import transcribe
from translate import translate, batch_kr_to_pt
from embed_store import upsert
from config import TRANSCRIPT_DIR


_PT_ENDINGS = ("ar", "er", "ir", "or")
_PT_CHARS = set("çãáâàéêíóôõú")


def _pt_score(words: list[str]) -> float:
    """Heuristic 'how Portuguese-looking' is a set of words. Returns 0..2 per word, averaged."""
    if not words:
        return 0.0
    total = 0
    for w in words:
        wl = w.lower()
        if len(w) >= 4 and wl.endswith(_PT_ENDINGS):
            total += 1
        if any(c in _PT_CHARS for c in wl):
            total += 1
    return total / len(words)


_KR_HINT_CHARS = set("èòáä")


def _kr_score(words: list[str]) -> float:
    """Higher score = more kreyol-looking (short words, kreyol accents)."""
    if not words:
        return 0.0
    total = 0
    for w in words:
        wl = w.lower()
        if any(c in _KR_HINT_CHARS for c in wl):
            total += 1
        if len(w) <= 4:
            total += 0.4
    return total / len(words)


def _detect_pairing(pieces: list[str]) -> tuple[bool, bool]:
    """Returns (should_pair, kr_first).

    Strategy:
    - Need 6+ items, even count.
    - Compute PT-leaning and KR-leaning score for both alternating sets.
    - If one set is clearly PT and the other clearly KR (opposite profiles), pair.
    - Default direction: KR first (dominant pattern in haitian PT-teaching videos).
    - Switch to PT first only when even-indexed set is clearly more PT than odd-indexed."""
    if len(pieces) < 6 or len(pieces) % 2 != 0:
        return False, False
    evens, odds = pieces[0::2], pieces[1::2]
    even_pt, odd_pt = _pt_score(evens), _pt_score(odds)
    even_kr, odd_kr = _kr_score(evens), _kr_score(odds)
    # Overall language lean per set (+ = PT, - = KR)
    even_lean = even_pt - even_kr
    odd_lean = odd_pt - odd_kr
    # If both sets lean same way strongly → uniform language list, don't pair
    if even_lean > 0.4 and odd_lean > 0.4:
        return False, False
    if even_lean < -0.2 and odd_lean < -0.2:
        return False, False
    # Pair, with direction by which set is more PT
    return True, odd_lean >= even_lean


def _split_pieces(text: str) -> tuple[list[str], list[str]]:
    """Return (preferred_pieces, comma_pieces). Tries comma split first (Whisper style),
    falls back to space split if it looks like a paired word list (MMS style)."""
    comma = [p.strip(" .") for p in re.split(r"[,;]", text) if p.strip(" .")]
    if len(comma) >= 6:
        return comma, comma
    spaces = [p.strip(" .") for p in text.split() if p.strip(" .")]
    if len(spaces) >= 6 and len(spaces) % 2 == 0:
        provisional, _ = _detect_pairing(spaces)
        if provisional:
            return spaces, comma
    return comma, comma


def expand_segment(seg: dict, vid: str, seg_idx: int) -> list[dict]:
    """Three behaviors:
    1. Real paired list (alternating languages): pair them, skip NLLB.
    2. Long unpaired list (comma-separated): one record per piece + NLLB.
    3. Normal sentence: whole segment as one record + NLLB."""
    text = seg["text"].strip(" .")
    pieces, comma_pieces = _split_pieces(text)
    duration = seg["end"] - seg["start"]
    records = []

    should_pair = False
    kr_first = False
    if len(pieces) >= 6 and len(pieces) % 2 == 0:
        should_pair, kr_first = _detect_pairing(pieces)

    if should_pair:
        n_pairs = len(pieces) // 2
        per_pair = duration / n_pairs
        for j in range(n_pairs):
            a, b = pieces[2 * j], pieces[2 * j + 1]
            kr, pt = (a, b) if kr_first else (b, a)
            records.append({
                "id": f"{vid}_{seg_idx:04d}_{j:02d}",
                "video_id": vid,
                "kreyol": kr,
                "portuguese": pt,
                "start": round(seg["start"] + j * per_pair, 2),
                "end": round(seg["start"] + (j + 1) * per_pair, 2),
                "context": text,
                "_skip_nllb": True,
            })
    elif len(comma_pieces) >= 5:
        per_piece = duration / len(comma_pieces)
        for j, p in enumerate(comma_pieces):
            records.append({
                "id": f"{vid}_{seg_idx:04d}_{j:02d}",
                "video_id": vid,
                "kreyol": p,
                "portuguese": "",
                "start": round(seg["start"] + j * per_piece, 2),
                "end": round(seg["start"] + (j + 1) * per_piece, 2),
                "context": text,
                "_skip_nllb": False,
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
            "_skip_nllb": False,
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

    print(f"[3/4] expand + batch-translate to Portuguese (NLLB)")
    records = []
    pending_translate_idx: list[int] = []
    pending_translate_txt: list[str] = []
    paired_count = 0
    for i, seg in enumerate(segments):
        for r in expand_segment(seg, vid, i):
            if r.pop("_skip_nllb", False):
                paired_count += 1
                records.append(r)
            else:
                # Marca pra batch
                records.append(r)
                pending_translate_idx.append(len(records) - 1)
                pending_translate_txt.append(r["kreyol"])
    # Tradução em batch (muito mais rápido que serial)
    if pending_translate_txt:
        translations = batch_kr_to_pt(pending_translate_txt, batch_size=8)
        for idx, pt in zip(pending_translate_idx, translations):
            records[idx]["portuguese"] = pt
    print(f"      {len(records)} records  ({paired_count} pareados pela professora, {len(pending_translate_idx)} via NLLB batch)")
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
