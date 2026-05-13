"""Embed text and store in ChromaDB."""
from functools import lru_cache
from typing import Iterable

import chromadb
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz

from config import EMBED_MODEL, CHROMA_DIR, CHROMA_COLLECTION


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=1)
def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"})


def embed(texts: list[str]) -> list[list[float]]:
    emb = get_embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return emb.tolist()


def upsert(records: Iterable[dict]):
    """Each record needs id, kreyol, portuguese, video_id, start, end, context."""
    records = list(records)
    if not records:
        return
    ids = [r["id"] for r in records]
    docs = [f"{r['kreyol']} | {r['portuguese']}" for r in records]
    metas = [
        {
            "kreyol": r["kreyol"],
            "portuguese": r["portuguese"],
            "video_id": r["video_id"],
            "start": r["start"],
            "end": r["end"],
            "context": r.get("context", r["kreyol"]),
        }
        for r in records
    ]
    embs = embed(docs)
    get_collection().upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embs)


def search(query: str, n: int = 5, alpha: float = 0.55) -> list[dict]:
    """Hybrid search: vector similarity + fuzzy text match on kreyol/portuguese fields.

    alpha = weight of vector score vs fuzzy score (0.55 = slightly favor vector).
    Pulls top 30 vector candidates, re-ranks with fuzzy boost on kr+pt fields."""
    q = query.strip()
    if not q:
        return []
    emb = embed([q])[0]
    pool = max(n * 6, 30)
    res = get_collection().query(query_embeddings=[emb], n_results=pool)
    if not res["ids"] or not res["ids"][0]:
        return []
    out = []
    for i in range(len(res["ids"][0])):
        m = res["metadatas"][0][i]
        vec = 1 - res["distances"][0][i]
        kr_fuzzy = fuzz.WRatio(q, m["kreyol"]) / 100.0
        pt_fuzzy = fuzz.WRatio(q, m["portuguese"]) / 100.0
        fuzzy = max(kr_fuzzy, pt_fuzzy)
        combined = alpha * vec + (1 - alpha) * fuzzy
        out.append({
            "score": round(combined, 3),
            "vec_score": round(vec, 3),
            "fuzzy_score": round(fuzzy, 3),
            "kreyol": m["kreyol"],
            "portuguese": m["portuguese"],
            "video_id": m["video_id"],
            "start": m["start"],
            "end": m["end"],
            "context": m.get("context", ""),
        })
    out.sort(key=lambda r: -r["score"])
    return out[:n]


def count() -> int:
    return get_collection().count()
