"""Continuous processor: reads queue.txt and runs the pipeline on each URL."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pipeline import process_url
from download import video_id, expand_playlist
from config import QUEUE_FILE, PROCESSED_FILE, FAILED_FILE


def read_set(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip().split("\t")[0]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def append_line(path: Path, line: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_pending_urls() -> list[str]:
    if not QUEUE_FILE.exists():
        return []
    raw = [
        line.strip()
        for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    expanded: list[str] = []
    seen_ids: set[str] = set()
    for url in raw:
        if "list=" in url:
            for vu in expand_playlist(url):
                vid = video_id(vu)
                if vid not in seen_ids:
                    seen_ids.add(vid)
                    expanded.append(vu)
        else:
            vid = video_id(url)
            if vid not in seen_ids:
                seen_ids.add(vid)
                expanded.append(url)
    processed = read_set(PROCESSED_FILE)
    failed = read_set(FAILED_FILE)
    return [u for u in expanded if video_id(u) not in processed and video_id(u) not in failed]


def run_once() -> int:
    pending = get_pending_urls()
    print(f"[daemon] {len(pending)} URLs pendentes")
    done = 0
    for url in pending:
        vid = video_id(url)
        print(f"\n[daemon] >>> {vid}")
        try:
            r = process_url(url)
            if r.get("status") == "ok":
                append_line(PROCESSED_FILE, vid)
                done += 1
            else:
                append_line(FAILED_FILE, f"{vid}\t{r.get('status', 'unknown')}")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[daemon] ERRO em {vid}: {e}")
            append_line(FAILED_FILE, f"{vid}\tEXCEPTION: {e}")
    return done


def run_forever(interval_sec: int = 300):
    print(f"[daemon] iniciado, intervalo {interval_sec}s entre varreduras")
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            print("[daemon] interrompido pelo usuário")
            break
        print(f"[daemon] aguardando {interval_sec}s antes da próxima varredura...")
        time.sleep(interval_sec)


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        run_forever(int(sys.argv[1]) if len(sys.argv) > 1 else 300)
