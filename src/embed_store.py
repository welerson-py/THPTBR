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


def _search_single(query: str, n: int, alpha: float) -> list[dict]:
    """One pass of vector + fuzzy search for a given query string."""
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
            "id": f"{m['video_id']}_{m['start']}",
        })
    return out


def _looks_portuguese(q: str) -> bool:
    """Cheap heuristic: does this query look like Portuguese or kreyol?"""
    ql = q.lower().strip()
    if any(c in ql for c in "çãáâàéêíóôõú"):
        return True
    # Common short PT words
    if ql in {"sim", "não", "muito", "obrigado", "com", "para", "que", "isso", "esse", "essa", "como", "onde", "quando", "porque"}:
        return True
    # PT infinitives
    if len(ql) >= 4 and ql.endswith(("ar", "er", "ir", "ção")):
        return True
    # KR signals
    if any(c in ql for c in "èòìù"):
        return False
    if ql.startswith(("ki ", "èske", "mwen ", "ou ", "li ", "kòm", "ou pa")):
        return False
    if ql in {"wi", "non", "mèsi", "mesi", "tanpri", "manje", "bwè", "ale", "achte", "konprann"}:
        return False
    return True  # default to PT (most common)


def search(query: str, n: int = 5, alpha: float = 0.55, bidirectional: bool = True) -> list[dict]:
    """Hybrid search: vector + fuzzy match. If bidirectional, also tries the
    NLLB-translated query in the other language and merges results.

    This is critical for kreyol queries — the embedder doesn't know kreyol well,
    but if we translate 'achte' -> 'comprar' first, search hits much harder."""
    q = query.strip()
    if not q:
        return []

    results_map = {}
    for r in _search_single(q, n, alpha):
        results_map[r["id"]] = r

    if bidirectional:
        try:
            from translate import kr_to_pt, pt_to_kr
            if _looks_portuguese(q):
                translated = pt_to_kr(q)
            else:
                translated = kr_to_pt(q)
            if translated and translated.strip().lower() != q.lower():
                for r in _search_single(translated, n, alpha):
                    # If same record found again, keep the higher score
                    if r["id"] in results_map:
                        if r["score"] > results_map[r["id"]]["score"]:
                            results_map[r["id"]] = r
                    else:
                        results_map[r["id"]] = r
        except Exception:
            pass  # if translation fails for any reason, fall back to single-side search

    out = list(results_map.values())
    out.sort(key=lambda r: -r["score"])
    return out[:n]


def count() -> int:
    return get_collection().count()
