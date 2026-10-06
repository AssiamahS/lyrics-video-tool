"""
Re-time an LRC to a different cut of the song (radio edit, DJ edit, sped/slowed upload).

Whisper transcribes the actual audio with word timestamps; the LRC's words are aligned to
Whisper's words with difflib; each line takes the time of its first matched word. Lines whose
words never appear in the audio (sections cut from this edit) are dropped, and lines with only
a few matches are interpolated between their neighbours.
"""

import difflib
import json
import os
import re
import subprocess
import tempfile
from typing import List, Optional, Tuple

WHISPER_CLI = os.path.expanduser("~/.local/bin/mlx_whisper")
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
TS = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower())


def parse_lrc(text: str) -> List[Tuple[float, str]]:
    out = []
    for raw in text.splitlines():
        stamps = TS.findall(raw)
        body = TS.sub("", raw).strip()
        for m, s in stamps:
            out.append((int(m) * 60 + float(s), body))
    return sorted(out)


def to_lrc(lines: List[Tuple[float, str]]) -> str:
    return "\n".join(f"[{int(t // 60):02d}:{t % 60:05.2f}]{txt}" for t, txt in lines) + "\n"


def whisper_words(audio: str) -> List[Tuple[float, str]]:
    tmp = tempfile.mkdtemp(prefix="align_")
    subprocess.run([WHISPER_CLI, audio, "--model", WHISPER_MODEL, "-f", "json",
                    "--word-timestamps", "True", "--condition-on-previous-text", "False",
                    "--hallucination-silence-threshold", "2", "--output-dir", tmp,
                    "--output-name", "w"], check=True, capture_output=True)
    data = json.load(open(os.path.join(tmp, "w.json")))
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            n = _norm(w.get("word", ""))
            if n:
                words.append((float(w["start"]), n))
    return words


def align(lrc_text: str, audio: str, min_ratio: float = 0.34) -> Optional[str]:
    lines = [(t, txt) for t, txt in parse_lrc(lrc_text) if txt]
    if not lines:
        return None
    heard = whisper_words(audio)
    if len(heard) < 10:
        return None  # nothing usable came back (instrumental / heavy noise)

    lrc_words, owner = [], []
    for i, (_, txt) in enumerate(lines):
        for w in txt.split():
            n = _norm(w)
            if n:
                lrc_words.append(n)
                owner.append(i)
    sm = difflib.SequenceMatcher(a=lrc_words, b=[w for _, w in heard], autojunk=False)
    hit_time = {}
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            hit_time[a + k] = heard[b + k][0]

    per_line = {}
    for idx, i in enumerate(owner):
        per_line.setdefault(i, []).append(idx)
    timed = []
    for i, (_, txt) in enumerate(lines):
        idxs = per_line.get(i, [])
        hits = [hit_time[x] for x in idxs if x in hit_time]
        ratio = len(hits) / max(len(idxs), 1)
        start = min(hits) if hits else None
        timed.append([start if ratio >= min_ratio else None, txt, ratio])

    # keep lines in order: a "match" earlier than the previous line is a repeated chorus
    # matched to the wrong pass, treat it as unknown
    last = -1.0
    for row in timed:
        if row[0] is not None and row[0] <= last:
            row[0] = None
        elif row[0] is not None:
            last = row[0]

    # interpolate a short run of unknowns between two anchors; drop long runs (cut sections)
    out, i = [], 0
    while i < len(timed):
        if timed[i][0] is not None:
            out.append((timed[i][0], timed[i][1]))
            i += 1
            continue
        j = i
        while j < len(timed) and timed[j][0] is None:
            j += 1
        prev_t = out[-1][0] if out else None
        next_t = timed[j][0] if j < len(timed) else None
        run = j - i
        if prev_t is not None and next_t is not None and run <= 2 and next_t - prev_t > 1.5 * (run + 1):
            step = (next_t - prev_t) / (run + 1)
            for k in range(run):
                out.append((prev_t + step * (k + 1), timed[i + k][1]))
        i = j
    return to_lrc(out) if len(out) >= max(3, len(lines) // 4) else None


def transcribe(audio: str, max_words: int = 9) -> Optional[str]:
    """No lyrics anywhere: write timed lines straight from what Whisper hears in the file."""
    tmp = tempfile.mkdtemp(prefix="transcribe_")
    subprocess.run([WHISPER_CLI, audio, "--model", WHISPER_MODEL, "-f", "json",
                    "--word-timestamps", "True", "--condition-on-previous-text", "False",
                    "--hallucination-silence-threshold", "2", "--output-dir", tmp,
                    "--output-name", "t"], check=True, capture_output=True)
    data = json.load(open(os.path.join(tmp, "t.json")))
    lines, prev = [], None
    for seg in data.get("segments", []):
        words = [w for w in seg.get("words", []) if w.get("word", "").strip()]
        text = " ".join(w["word"].strip() for w in words)
        if not words or text == prev:  # whisper loops repeat the same segment
            continue
        prev = text
        # long segments become several lines, broken at punctuation when possible
        chunk = []
        for w in words:
            chunk.append(w)
            end_punct = w["word"].strip()[-1:] in ",.?!"
            if len(chunk) >= max_words or (end_punct and len(chunk) >= 4):
                lines.append((float(chunk[0]["start"]), " ".join(x["word"].strip() for x in chunk)))
                chunk = []
        if chunk:
            lines.append((float(chunk[0]["start"]), " ".join(x["word"].strip() for x in chunk)))
    lines = [(t, txt.strip(" ,")) for t, txt in lines if txt.strip(" ,")]
    return to_lrc(lines) if len(lines) >= 3 else None
