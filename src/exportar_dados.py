"""Exporta TODO o banco vetorial pra arquivos versionaveis no git.

Saida:
  data/banco_frases.json    — metadata legivel (kreyol, portugues, video, timestamps)
  data/banco_embeddings.npy — vetores LaBSE em float16 (compacto)

Permite que quem clona o repo tenha as frases prontas sem rodar o daemon do zero.
Auto-import em embed_store.py popula ChromaDB na primeira execucao se estiver vazio.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import chromadb
from config import CHROMA_DIR, CHROMA_COLLECTION, DATA


def main():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(name=CHROMA_COLLECTION)
    n = col.count()
    print(f"Exportando {n} frases do ChromaDB...", flush=True)

    # Pega tudo (em batches pra nao explodir memoria)
    batch = 1000
    all_ids = []
    all_docs = []
    all_metas = []
    all_embs = []
    for offset in range(0, n, batch):
        chunk = col.get(
            limit=batch,
            offset=offset,
            include=["embeddings", "documents", "metadatas"],
        )
        all_ids.extend(chunk["ids"])
        all_docs.extend(chunk["documents"])
        all_metas.extend(chunk["metadatas"])
        all_embs.extend(chunk["embeddings"])
        print(f"  ... {len(all_ids)}/{n}", flush=True)

    # Salva metadata como JSON (legivel)
    out_json = DATA / "banco_frases.json"
    payload = {
        "version": 1,
        "embedder": "sentence-transformers/LaBSE",
        "dim": len(all_embs[0]) if all_embs else 0,
        "count": len(all_ids),
        "ids": all_ids,
        "documents": all_docs,
        "metadatas": all_metas,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"[ok] {out_json.name}: {out_json.stat().st_size / 1024 / 1024:.1f} MB", flush=True)

    # Salva embeddings como numpy float16 (50% menor que float32, qualidade igual pra cosine)
    embs_arr = np.array(all_embs, dtype=np.float16)
    out_npy = DATA / "banco_embeddings.npy"
    np.save(out_npy, embs_arr)
    print(f"[ok] {out_npy.name}: {out_npy.stat().st_size / 1024 / 1024:.1f} MB | shape={embs_arr.shape}", flush=True)

    total_mb = (out_json.stat().st_size + out_npy.stat().st_size) / 1024 / 1024
    print(f"\nTotal: {total_mb:.1f} MB versionaveis no git")
    print(f"Quem clonar + rodar UI -> banco populado automaticamente em ~5s")


if __name__ == "__main__":
    main()
