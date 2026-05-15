"""Empacota o banco vetorial + transcricoes + correcoes num zip pra compartilhar com a equipe.

Quem receber esse zip extrai dentro da pasta do projeto e ja tem todas as 7000+
frases prontas, sem precisar rodar daemon do zero (que demora ~6h).
"""
import sys
import zipfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import ROOT, DATA, CHROMA_DIR, TRANSCRIPT_DIR, PROCESSED_FILE, FAILED_FILE


def main():
    out_zip = ROOT / f"oficina-bundle-{time.strftime('%Y%m%d-%H%M')}.zip"
    print(f"Gerando bundle: {out_zip.name}\n", flush=True)

    items_to_zip = []
    # 1. ChromaDB (banco vetorial completo)
    if CHROMA_DIR.exists():
        for f in CHROMA_DIR.rglob("*"):
            if f.is_file():
                items_to_zip.append((f, f.relative_to(ROOT)))
    # 2. Transcripts (JSONs de cada video)
    if TRANSCRIPT_DIR.exists():
        for f in TRANSCRIPT_DIR.glob("*.json"):
            if f.name != "test_compare.json":
                items_to_zip.append((f, f.relative_to(ROOT)))
    # 3. Correções manuais
    correcoes = DATA / "correcoes.json"
    if correcoes.exists():
        items_to_zip.append((correcoes, correcoes.relative_to(ROOT)))
    # 4. Listas de status
    for f in (PROCESSED_FILE, FAILED_FILE):
        if f.exists():
            items_to_zip.append((f, f.relative_to(ROOT)))
    # 5. TTS cache (frases ja sintetizadas)
    tts_cache = DATA / "tts_cache"
    if tts_cache.exists():
        for f in tts_cache.glob("*.wav"):
            items_to_zip.append((f, f.relative_to(ROOT)))

    print(f"Empacotando {len(items_to_zip)} arquivos...\n", flush=True)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, dst in items_to_zip:
            zf.write(src, str(dst))

    size_mb = out_zip.stat().st_size / 1024 / 1024
    print(f"[done] {out_zip} ({size_mb:.1f} MB)")
    print(f"\nComo usar do outro lado:")
    print(f"  1. git clone https://github.com/welerson-py/THPTBR")
    print(f"  2. cd THPTBR")
    print(f"  3. unzip {out_zip.name}")
    print(f"  4. py -m venv .venv && .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
    print(f"  5. iniciar_ui.bat   (modelos baixam automaticamente na 1a vez)")


if __name__ == "__main__":
    main()
