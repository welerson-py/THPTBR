"""Pre-download all pending audio files. Needs internet but NO ML models — fast."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from daemon import get_pending_urls
from download import download_audio, video_id


def main():
    urls = get_pending_urls()
    print(f"[download_all] {len(urls)} videos pendentes\n", flush=True)
    ok, fail = 0, 0
    for i, url in enumerate(urls, 1):
        vid = video_id(url)
        print(f"[{i}/{len(urls)}] {vid} ...", end="", flush=True)
        try:
            result = download_audio(url)
            if result:
                size_mb = result.stat().st_size / 1024 / 1024
                print(f" OK ({size_mb:.1f} MB)", flush=True)
                ok += 1
            else:
                print(" FAIL", flush=True)
                fail += 1
        except Exception as e:
            print(f" ERR: {e}", flush=True)
            fail += 1
    print(f"\n[done] {ok} baixados, {fail} falharam", flush=True)


if __name__ == "__main__":
    main()
