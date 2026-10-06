"""
Pick a song straight out of the local yt-dlp library and get its synced lyrics.

    find_song("calm down")  -> best-matching audio path
    lrc_for(path)           -> cached .lrc next to output/, fetched from LRCLIB on first use
"""

import os
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import List, Optional, Tuple

LIBRARY_DIRS = [Path.home() / "Music" / "yt-dlp", Path.home() / "Music"]
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".flac", ".aac", ".ogg", ".opus", ".aif", ".aiff"}
NOISE = re.compile(
    r"\((official|lyric|lyrics|audio|video|visualizer|music video|hd|hq)[^)]*\)|"
    r"\[(official|lyric|lyrics|audio|video|visualizer|music video|hd|hq)[^\]]*\]",
    re.I,
)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[^\w\s]", " ", s)


def _walk() -> List[Path]:
    seen, files = set(), []
    for root in LIBRARY_DIRS:
        if not root.exists():
            continue
        for dirpath, _, names in os.walk(root):
            for n in names:
                p = Path(dirpath) / n
                if p.suffix.lower() in AUDIO_EXT and p.name not in seen:
                    seen.add(p.name)
                    files.append(p)
    return files


def search(query: str, limit: int = 10) -> List[Tuple[int, Path]]:
    words = _norm(query).split()
    hits = []
    for p in _walk():
        name = _norm(p.stem)
        if all(w in name for w in words):
            # prefer clean originals over slowed / sped / edits / mixes
            penalty = sum(k in name for k in ("slowed", "sped", "edit", "remix", "mix", "reverb", "loop"))
            hits.append((penalty * 10 + len(name), p))
    hits.sort(key=lambda h: h[0])
    return hits[:limit]


def find_song(query: str) -> Optional[Path]:
    hits = search(query)
    return hits[0][1] if hits else None


def split_artist_title(path: Path) -> Tuple[str, str]:
    stem = NOISE.sub("", unicodedata.normalize("NFKC", path.stem)).strip()
    for sep in (" - ", " – ", " — ", "-"):
        if sep in stem:
            artist, title = stem.split(sep, 1)
            return _strip_feat(artist), _strip_feat(title)
    return "", stem


def _strip_feat(s: str) -> str:
    """'A Boogie Wit Da Hoodie ft. Cash Cobain' -> 'A Boogie Wit Da Hoodie' (also feat./featuring/with/x/&/,)."""
    s = re.sub(r"\s*[\(\[]?\s*(ft|feat|featuring|with)\.?\s.*$", "", s, flags=re.I)
    s = re.split(r"\s+(?:x|&)\s+|,\s*", s, maxsplit=1)[0]
    return s.strip(" -")


def duration_of(path: Path) -> int:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    try:
        return int(float(out.stdout.strip()))
    except ValueError:
        return 0


def lrc_for(path: Path, artist: str = "", title: str = "", cache_dir: str = str(Path(__file__).resolve().parent / "output" / "lrc")) -> Optional[str]:
    """Return a path to synced lyrics for this track, fetching from LRCLIB once."""
    if not (artist and title):
        a, t = split_artist_title(path)
        artist, title = artist or a, title or t
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    lrc_path = cache / f"{_norm(artist + ' ' + title).strip().replace(' ', '_') or 'track'}.lrc"
    if lrc_path.exists():
        return str(lrc_path)
    from auto_lyrics_fetcher import AutoLyricsFetcher
    fetcher = AutoLyricsFetcher()
    length = duration_of(path) or None
    content = fetcher.auto_fetch(artist, title, length)
    if not content:
        # not in any lyrics database: transcribe this exact file so the timing is exact too
        print("MODE transcribed", flush=True)
        print("PROGRESS 0.00 transcribing vocals", flush=True)
        from align import transcribe
        content = transcribe(str(path))
        if not content:
            return None
        lrc_path.write_text(content, encoding="utf-8")
        return str(lrc_path)
    # a different cut of the song (radio/DJ edit, YouTube rip) needs the lines re-timed
    if length and fetcher.last_duration and abs(fetcher.last_duration - length) > 2:
        print(f"PROGRESS 0.00 aligning ({fetcher.last_duration:.0f}s lyrics vs {length}s audio)", flush=True)
        from align import align
        content = align(content, str(path))
        if not content:
            print("❌ Lyrics found, but couldn't line them up with this edit of the song")
            return None
    lrc_path.write_text(content, encoding="utf-8")
    return str(lrc_path)
