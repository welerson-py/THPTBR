"""Test vector search quality with PT and kreyol queries."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from embed_store import search

queries = [
    ("PT", "comprar"),
    ("PT", "comer"),
    ("PT", "beber"),
    ("PT", "trabalhar"),
    ("PT", "perguntar"),
    ("KR", "manje"),       # = comer
    ("KR", "achte"),       # = comprar
    ("KR", "travay"),      # = trabalhar
    ("KR", "bwè"),         # = beber
]

for kind, q in queries:
    print(f"\n=== {kind} query: '{q}' ===")
    results = search(q, n=3)
    for r in results:
        print(f"  [{r['score']:.2f}] KR: {r['kreyol'][:60]}")
        print(f"         PT: {r['portuguese'][:60]}")
        print(f"         @ {r['video_id']} {r['start']}s")
