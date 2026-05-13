"""Embed text and store in ChromaDB."""
from functools import lru_cache
from typing import Iterable

import chromadb
from sentence_transformers import SentenceTransformer

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


def search(query: str, n: int = 5) -> list[dict]:
    emb = embed([query])[0]
    res = get_collection().query(query_embeddings=[emb], n_results=n)
    out = []
    for i in range(len(res["ids"][0])):
        m = res["metadatas"][0][i]
        out.append({
            "score": 1 - res["distances"][0][i],
            "kreyol": m["kreyol"],
            "portuguese": m["portuguese"],
            "video_id": m["video_id"],
            "start": m["start"],
            "end": m["end"],
            "context": m.get("context", ""),
        })
    return out


def count() -> int:
    return get_collection().count()
