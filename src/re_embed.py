"""Re-embed all stored records with a new embedder (e.g., after upgrading to LaBSE).

Strategy: wipe ChromaDB collection, then re-load all transcript JSONs and upsert.
The transcripts already have kreyòl text + portuguese translation — no re-transcription needed.
This runs in ~minutes instead of hours.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import chromadb
from config import CHROMA_DIR, CHROMA_COLLECTION, TRANSCRIPT_DIR
from embed_store import upsert, get_embedder


def main():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(CHROMA_COLLECTION)
        print(f"deletado collection {CHROMA_COLLECTION}", flush=True)
    except Exception:
        pass
    client.create_collection(name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"})
    print(f"collection recriada (vazia)", flush=True)

    print(f"\nVerificando embedder atual...", flush=True)
    emb = get_embedder()
    print(f"  modelo: {emb._model_card_text[:50] if hasattr(emb, '_model_card_text') else type(emb).__name__}", flush=True)
    print(f"  dim:    {emb.get_sentence_embedding_dimension()}", flush=True)

    transcripts = sorted(TRANSCRIPT_DIR.glob("*.json"))
    transcripts = [t for t in transcripts if t.name != "test_compare.json"]
    print(f"\nRe-embedando {len(transcripts)} videos...\n", flush=True)
    total = 0
    for tf in transcripts:
        try:
            data = json.loads(tf.read_text(encoding="utf-8"))
            segs = data.get("segments", [])
            if not segs:
                print(f"[skip] {tf.name}: sem segments", flush=True)
                continue
            upsert(segs)
            total += len(segs)
            print(f"[ok] {tf.name}: {len(segs)} records (total: {total})", flush=True)
        except Exception as e:
            print(f"[ERR] {tf.name}: {e}", flush=True)

    print(f"\n[done] {total} records re-embedados")


if __name__ == "__main__":
    main()
