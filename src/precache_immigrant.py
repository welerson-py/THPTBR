"""Pre-warm NLLB cache for common immigrant phrases (KR → PT direction).

These are things a haitian immigrant might say during the workshop.
Running this populates the @lru_cache in translate.kr_to_pt so subsequent calls are instant.
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from translate import kr_to_pt

PHRASES_KR = [
    # Comprehension / asking for help
    "Mwen pa konprann",
    "Èske w ka repete?",
    "Èske w ka repete tanpri?",
    "Mwen pa konnen",
    "Pale pi dousman tanpri",
    "Mwen pa konn pale pòtigè byen",
    "Èd mwen tanpri",
    "Mwen bezwen èd",
    "Mwen pèdi",
    "Kòman?",
    # Learning
    "Mwen vle aprann",
    "Kijan yo di sa nan pòtigè?",
    "Kisa sa vle di?",
    "Repete tanpri",
    "Montre m",
    # Computer interactions
    "Klike kote?",
    "Mwen klike isit la?",
    "Ki bouton mwen peze?",
    "Mwen pa wè li",
    "Òdinatè a pa mache",
    # Identification / greetings
    "Mwen rele",
    "Kòman ou rele?",
    "Bonjou",
    "Bonswa",
    "Kijan ou ye?",
    "Mwen byen",
    "Mwen kontan",
    "Orevwa",
    # Yes/no/thanks
    "Wi",
    "Non",
    "Mèsi",
    "Mèsi anpil",
    "Tanpri",
    "Padon",
    "Eskize m",
    # Basic needs
    "Mwen grangou",
    "Mwen swaf",
    "Mwen vle dlo",
    "Mwen fatige",
    "Ki kote twalèt la ye?",
    "Ki lè li ye?",
    # Confirmation
    "Mwen konprann",
    "Mwen pare",
    "Sa bon",
    "Sa pa bon",
    "Ankò",
]


def main():
    print(f"Pre-aquecendo NLLB com {len(PHRASES_KR)} frases comuns de imigrante...\n", flush=True)
    t0 = time.time()
    ok = 0
    for i, kr in enumerate(PHRASES_KR, 1):
        try:
            t = time.time()
            pt = kr_to_pt(kr)
            dt = time.time() - t
            print(f"[{i:2d}/{len(PHRASES_KR)}] {dt:5.1f}s | KR: {kr:35s} -> PT: {pt}", flush=True)
            ok += 1
        except Exception as e:
            print(f"[{i:2d}/{len(PHRASES_KR)}] ERR: {e}", flush=True)
    print(f"\n[done] {ok}/{len(PHRASES_KR)} em {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
