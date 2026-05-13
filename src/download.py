"""Download YouTube audio as mp3 using yt-dlp."""
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from config import AUDIO_DIR, ROOT

YT_DLP = ROOT / ".venv" / "Scripts" / "yt-dlp.exe"


def _find_ffmpeg_dir() -> str | None:
    """Locate ffmpeg.exe directory, falling back to FFMPEG_LOCATION env var."""
    env = os.environ.get("FFMPEG_LOCATION")
    if env and Path(env).exists():
        return env
    found = shutil.which("ffmpeg")
    if found:
        return str(Path(found).parent)
    # Fallback: common winget install path on Windows
    winget = Path(os.path.expandvars(
        r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"
    ))
    if winget.exists():
        for d in winget.glob("Gyan.FFmpeg*/ffmpeg-*/bin"):
            if (d / "ffmpeg.exe").exists():
                return str(d)
    return None


FFMPEG_DIR = _find_ffmpeg_dir()


def video_id(url: str) -> str:
    """Extract YouTube video ID from any url form."""
    p = urlparse(url)
    if p.hostname in ("youtu.be",):
        return p.path.lstrip("/")
    q = parse_qs(p.query)
    if "v" in q:
        return q["v"][0]
    return p.path.rstrip("/").split("/")[-1]


def download_audio(url: str) -> Path | None:
    """Download a single video as mp3. Returns path to mp3 or None on failure."""
    vid = video_id(url)
    out = AUDIO_DIR / f"{vid}.mp3"
    if out.exists() and out.stat().st_size > 1024:
        return out
    cmd = [
        str(YT_DLP),
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "4",
        "--no-playlist",
    ]
    if FFMPEG_DIR:
        cmd.extend(["--ffmpeg-location", FFMPEG_DIR])
    cmd.extend([
        "-o", str(AUDIO_DIR / "%(id)s.%(ext)s"),
        url,
    ])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"yt-dlp failed for {url}:\n{r.stderr[-500:]}")
        return None
    return out if out.exists() else None


def expand_playlist(url: str) -> list[str]:
    """Return list of individual video URLs from a playlist URL."""
    cmd = [str(YT_DLP), "--flat-playlist", "--print", "%(id)s", url]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ids = [line.strip() for line in r.stdout.splitlines() if line.strip() and line.strip() != "NA"]
    seen = set()
    out = []
    for vid in ids:
        if vid in seen:
            continue
        seen.add(vid)
        out.append(f"https://www.youtube.com/watch?v={vid}")
    return out
