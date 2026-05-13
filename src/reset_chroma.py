"""Wipe and recreate the ChromaDB collection (for re-indexing experiments)."""
import chromadb
from config import CHROMA_DIR, CHROMA_COLLECTION

client = chromadb.PersistentClient(path=str(CHROMA_DIR))
try:
    client.delete_collection(CHROMA_COLLECTION)
    print(f"deleted collection {CHROMA_COLLECTION}")
except Exception as e:
    print(f"no existing collection: {e}")
client.create_collection(name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"})
print("recreated empty collection")
