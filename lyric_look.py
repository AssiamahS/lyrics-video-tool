"""
Lyric look - scrolling, word-filling lyrics video renderer.

Frames are drawn with Pillow and piped straight into ffmpeg, so there is no
moviepy / ImageMagick dependency. The look:
  - blurred, slowly drifting background (cover art or generated gradient)
  - lines stacked and scrolled so the active line sits at the anchor
  - active line fills word by word across its duration
  - soft glow on the active line that pulses with the audio level
  - intro title card + thin progress bar
"""

import math
import os
import re
import shutil
import subprocess
import tempfile
import multiprocessing as mp
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEFAULT_FONTS = [
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

PALETTES = {
    "dusk": [(38, 18, 74), (196, 54, 112), (255, 140, 66)],
    "ocean": [(6, 22, 54), (18, 92, 140), (64, 200, 196)],
    "ember": [(24, 6, 6), (140, 24, 30), (240, 120, 40)],
    "mono": [(10, 10, 12), (48, 48, 56), (110, 110, 124)],
}


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def load_font(path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    for candidate in ([path] if path else []) + DEFAULT_FONTS:
        try:
            font = ImageFont.truetype(candidate, size)
            try:
                font.set_variation_by_name("Bold")
            except Exception:
                pass
            return font
        except (OSError, TypeError):
            continue
    return ImageFont.load_default(size)


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def audio_envelope(path: str, fps: int, frames: int) -> np.ndarray:
    """Per-frame loudness in 0..1, smoothed so the glow breathes, not flickers."""
    rate = 22050
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(rate),
         "-f", "s16le", "-"],
        capture_output=True, check=True,
    ).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    hop = rate / fps
    env = np.zeros(frames, dtype=np.float32)
    for i in range(frames):
        chunk = pcm[int(i * hop):int((i + 1) * hop)]
        if chunk.size:
            env[i] = math.sqrt(float(np.mean(chunk * chunk)))
    peak = np.percentile(env, 98) or 1.0
    env = np.clip(env / peak, 0, 1)
    for i in range(1, frames):  # fast attack, slow release
        if env[i] < env[i - 1]:
            env[i] = env[i - 1] * 0.88 + env[i] * 0.12
    return env


def audio_bands(path: str, fps: int, frames: int, bands: int = 48) -> np.ndarray:
    """Per-frame log-spaced spectrum (frames x bands) in 0..1 for the visualizer bars."""
    rate = 22050
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(rate),
         "-f", "s16le", "-"],
        capture_output=True, check=True,
    ).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    win = 2048
    hop = rate / fps
    edges = np.geomspace(40, 10000, bands + 1)
    freqs = np.fft.rfftfreq(win, 1 / rate)
    idx = [np.where((freqs >= edges[b]) & (freqs < edges[b + 1]))[0] for b in range(bands)]
    idx = [i if i.size else np.array([np.argmin(abs(freqs - edges[b]))]) for b, i in enumerate(idx)]
    window = np.hanning(win).astype(np.float32)
    out = np.zeros((frames, bands), dtype=np.float32)
    for f in range(frames):
        a = int(f * hop)
        chunk = pcm[a:a + win]
        if chunk.size < win:
            chunk = np.pad(chunk, (0, win - chunk.size))
        mag = np.abs(np.fft.rfft(chunk * window))
        out[f] = [np.log1p(mag[i].mean()) for i in idx]
    out /= np.percentile(out, 99, axis=0) + 1e-6
    out = np.clip(out, 0, 1)
    for f in range(1, frames):  # bars fall slowly, jump instantly
        out[f] = np.maximum(out[f], out[f - 1] * 0.85)
    return out


@dataclass
class LineArt:
    start: float
    end: float
    dim: Image.Image
    bright: Image.Image
    glow: Image.Image
    words: List[Tuple[int, int, int, int, int]]  # x0, y0, x1, y1, chars
    height: int


class LyricLookRenderer:
    def __init__(
        self,
        audio_path: str,
        size: Tuple[int, int] = (1920, 1080),
        fps: int = 30,
        font_path: Optional[str] = None,
        font_size: Optional[int] = None,
        cover_path: Optional[str] = None,
        palette: str = "dusk",
        title: Optional[str] = None,
        artist: Optional[str] = None,
        align: str = "left",
    ):
        self.audio_path = audio_path
        self.w, self.h = size
        self.fps = fps
        self.vertical = self.h > self.w
        base = min(self.w, self.h)
        self.font_path = font_path
        self.font = load_font(font_path, font_size or int(base * 0.075))
        self.small_font = load_font(font_path, int(base * 0.032))
        self.title_font = load_font(font_path, int(base * 0.07))
        self.cover_path = cover_path
        self.palette = PALETTES.get(palette, PALETTES["dusk"])
        self.title = title
        self.artist = artist
        self.align = align
        self.margin = int(self.w * (0.08 if self.vertical else 0.1))
        self.max_text_w = self.w - 2 * self.margin
        self.line_gap = int(self.font.size * 0.55)
        self.anchor_y = int(self.h * (0.42 if self.vertical else 0.4))

    # ---------- background ----------

    def _background_source(self) -> Image.Image:
        """Oversized blurred plate; per-frame we crop a drifting window."""
        bw, bh = int(self.w * 1.25), int(self.h * 1.25)
        if self.cover_path:
            img = Image.open(self.cover_path).convert("RGB")
            scale = max(bw / img.width, bh / img.height)
            img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1))
            left, top = (img.width - bw) // 2, (img.height - bh) // 2
            img = img.crop((left, top, left + bw, top + bh))
            img = img.filter(ImageFilter.GaussianBlur(max(bw, bh) // 25))
            img = Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.45)
            return img
        small = Image.new("RGB", (64, 64))
        px = small.load()
        c0, c1, c2 = self.palette
        for y in range(64):
            for x in range(64):
                a = math.hypot(x - 10, y - 54) / 80
                b = math.hypot(x - 54, y - 12) / 70
                r = [c0[i] * (1 - min(a, 1)) * 0.2 + c0[i] * 0.8 for i in range(3)]
                r = [r[i] * min(b, 1) + c1[i] * (1 - min(b, 1)) for i in range(3)]
                glow = max(0.0, 1 - math.hypot(x - 46, y - 46) / 30) * 0.55
                r = [r[i] * (1 - glow) + c2[i] * glow for i in range(3)]
                px[x, y] = tuple(int(v) for v in r)
        return small.resize((bw, bh), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))

    def _background_frame(self, plate: Image.Image, t: float, level: float) -> Image.Image:
        dx = (plate.width - self.w) / 2
        dy = (plate.height - self.h) / 2
        x = int(dx + math.sin(t * 0.07) * dx * 0.9)
        y = int(dy + math.cos(t * 0.05) * dy * 0.9)
        frame = plate.crop((x, y, x + self.w, y + self.h))
        if level > 0.01:
            frame = Image.blend(frame, Image.new("RGB", frame.size, (255, 255, 255)), 0.05 * level)
        return frame

    # ---------- text layout ----------

    def _split_long(self, word: str) -> List[str]:
        """A token wider than the column gets broken at hyphens, then by characters."""
        if self.font.getlength(word) <= self.max_text_w:
            return [word]
        pieces, cur = [], ""
        parts = re.split(r"(?<=-)", word)  # keep the hyphen on the left piece
        for part in parts:
            if cur and self.font.getlength(cur + part) > self.max_text_w:
                pieces.append(cur)
                cur = part
            else:
                cur += part
        if cur:
            pieces.append(cur)
        out = []
        for piece in pieces:  # still too wide (no hyphens): split by characters
            while self.font.getlength(piece) > self.max_text_w:
                cut = len(piece)
                while cut > 1 and self.font.getlength(piece[:cut]) > self.max_text_w:
                    cut -= 1
                out.append(piece[:cut])
                piece = piece[cut:]
            if piece:
                out.append(piece)
        return out

    def _wrap(self, text: str) -> List[List[str]]:
        rows, row = [], []
        tokens = [p for w in text.split() for p in self._split_long(w)]
        for word in tokens:
            trial = " ".join(row + [word])
            if row and self.font.getlength(trial) > self.max_text_w:
                rows.append(row)
                row = [word]
            else:
                row.append(word)
        if row:
            rows.append(row)
        return _balance(rows, self.font) or [[""]]

    def _render_line(self, text: str, start: float, end: float) -> LineArt:
        rows = self._wrap(text)
        ascent, descent = self.font.getmetrics()
        row_h = int((ascent + descent) * 1.05)
        pad = int(self.font.size * 0.5)
        width = self.max_text_w + 2 * pad
        height = row_h * len(rows) + 2 * pad
        space = self.font.getlength(" ")

        bright = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(bright)
        words = []
        for r, row in enumerate(rows):
            row_w = self.font.getlength(" ".join(row))
            if self.align == "center":
                x = pad + (self.max_text_w - row_w) / 2
            else:
                x = pad
            y = pad + r * row_h
            for word in row:
                wlen = self.font.getlength(word)
                draw.text((x, y), word, font=self.font, fill=(255, 255, 255, 255))
                words.append((int(x), y, int(x + wlen + space * 0.5), y + row_h, max(len(word), 1)))
                x += wlen + space

        alpha = bright.getchannel("A")
        dim = Image.new("RGBA", bright.size, (255, 255, 255, 0))
        dim.putalpha(alpha.point(lambda a: int(a * 0.32)))
        glow = Image.new("RGBA", bright.size, (255, 255, 255, 0))
        glow.putalpha(alpha.filter(ImageFilter.GaussianBlur(self.font.size * 0.22)))
        return LineArt(start, end, dim, bright, glow, words, height)

    def _fill_mask(self, art: LineArt, progress: float) -> Image.Image:
        mask = Image.new("L", art.bright.size, 0)
        draw = ImageDraw.Draw(mask)
        total = sum(w[4] for w in art.words)
        budget = progress * total
        feather = max(6, int(self.font.size * 0.25))
        for x0, y0, x1, y1, n in art.words:
            if budget <= 0:
                break
            frac = min(1.0, budget / n)
            fx = x0 + (x1 - x0) * frac
            draw.rectangle((x0 - 2, y0, fx, y1), fill=255)
            budget -= n
        return mask.filter(ImageFilter.GaussianBlur(feather / 3))

    # ---------- frame ----------

    SCROLL_TIME = 0.55  # seconds to glide to the next line

    def _prepare(self, lyrics: List[Dict], intro: float):
        self.duration = probe_duration(self.audio_path)
        self.frames = int(self.duration * self.fps)
        self.intro = intro
        self.env = audio_envelope(self.audio_path, self.fps, self.frames)
        self.plate = self._background_source()
        self.spectrum = None if lyrics else audio_bands(self.audio_path, self.fps, self.frames)
        lines = [l for l in lyrics if l["text"].strip()]
        self.arts = []
        for i, l in enumerate(lines):
            end = lines[i + 1]["timestamp"] if i + 1 < len(lines) else self.duration
            # fill finishes a little early so the line reads complete before it moves on
            fill_end = l["timestamp"] + max(0.4, (end - l["timestamp"]) * 0.85)
            self.arts.append(self._render_line(l["text"], l["timestamp"], min(fill_end, end)))
        self.offsets, y = [], 0
        for art in self.arts:
            self.offsets.append(y + art.height / 2)
            y += art.height + self.line_gap
        self.pad = int(self.font.size * 0.5)
        self.title_layer = self._title_layer() if self.spectrum is not None else None

    def _active(self, t: float) -> int:
        active = -1
        for i, art in enumerate(self.arts):
            if art.start <= t:
                active = i
            else:
                break
        return active

    def _scroll_at(self, t: float, active: int) -> float:
        """Pure function of t, so any frame can be rendered independently."""
        if not self.arts:
            return 0.0
        if active <= 0:
            return self.offsets[0]
        k = ease((t - self.arts[active].start) / self.SCROLL_TIME)
        a, b = self.offsets[active - 1], self.offsets[active]
        return a + (b - a) * k

    def frame_at(self, f: int) -> Image.Image:
        t = f / self.fps
        level = float(self.env[f])
        frame = self._background_frame(self.plate, t, level).convert("RGBA")
        has_title = t < self.intro and (self.title or self.artist) and self.spectrum is None
        show = 1 - self._title_alpha(t, self.intro) if has_title else 1.0
        active = self._active(t)
        scroll = self._scroll_at(t, active)
        for i, art in enumerate(self.arts):
            top = self.anchor_y + self.offsets[i] - scroll - art.height / 2
            if top > self.h or top + art.height < 0:
                continue
            dist = abs(self.offsets[i] - scroll) / (self.h * 0.5)
            fade = max(0.0, 1 - dist ** 1.6) * show
            if fade <= 0.01:
                continue
            pos = (self.margin - self.pad, int(top))
            frame.alpha_composite(art.dim if fade >= 0.999 else _scale_alpha(art.dim, fade), pos)
            if i == active:
                prog = ease((t - art.start) / max(art.end - art.start, 0.01))
                frame.alpha_composite(_scale_alpha(art.glow, (0.25 + 0.55 * level) * fade), pos)
                lit = art.bright.copy()
                lit.putalpha(_mul(art.bright.getchannel("A"), self._fill_mask(art, prog)))
                if fade < 0.999:
                    lit = _scale_alpha(lit, fade)
                frame.alpha_composite(lit, pos)
            elif i < active:
                frame.alpha_composite(_scale_alpha(art.bright, 0.55 * fade), pos)
        if self.spectrum is not None:
            self._draw_visualizer(frame, self.spectrum[f], level)
        elif has_title:
            self._draw_title(frame, t, self.intro)
        self._draw_progress(frame, t / self.duration)
        return frame.convert("RGB")

    def _encode_chunk(self, job):
        start, stop, path = job
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.w}x{self.h}",
            "-r", str(self.fps), "-i", "-",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-threads", "1", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(start, stop):
            proc.stdin.write(self.frame_at(f).tobytes())
        proc.stdin.close()
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg chunk {start}-{stop} exited {proc.returncode}")
        return stop - start

    def render(self, lyrics: List[Dict], output_path: str, intro: float = 3.0, workers: int = 0):
        print("PROGRESS 0.00 analyzing", flush=True)
        self._prepare(lyrics, intro)
        workers = workers or max(1, (os.cpu_count() or 2) - 1)
        tmp = tempfile.mkdtemp(prefix="lyriclook_")
        chunk = self.fps * 4
        jobs = [(a, min(a + chunk, self.frames), os.path.join(tmp, f"seg_{i:05d}.mp4"))
                for i, a in enumerate(range(0, self.frames, chunk))]
        global _ACTIVE
        _ACTIVE = self
        done = 0
        try:
            # fork shares the prepared state (images, spectrum) with every worker for free
            with mp.get_context("fork").Pool(workers) as pool:
                for n in pool.imap_unordered(_encode_job, jobs):
                    done += n
                    print(f"PROGRESS {done / self.frames:.3f} rendering", flush=True)
            listing = os.path.join(tmp, "list.txt")
            with open(listing, "w") as fh:
                fh.writelines(f"file '{j[2]}'\n" for j in jobs)
            print("PROGRESS 0.99 muxing", flush=True)
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", listing,
                "-i", self.audio_path, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
                output_path,
            ], check=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print("PROGRESS 1.00 done", flush=True)

    @staticmethod
    def _title_alpha(t: float, intro: float) -> float:
        return ease(t / 0.6) * (1 - ease((t - (intro - 0.8)) / 0.8))

    def _draw_title(self, frame: Image.Image, t: float, intro: float):
        a = self._title_alpha(t, intro)
        if a <= 0:
            return
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, int(90 * a)))
        d = ImageDraw.Draw(overlay)
        cy = self.h // 2
        if self.title:
            d.text((self.w / 2, cy - 10), self.title, font=self.title_font,
                   fill=(255, 255, 255, int(255 * a)), anchor="md")
        if self.artist:
            d.text((self.w / 2, cy + 18), self.artist.upper(), font=self.small_font,
                   fill=(255, 255, 255, int(170 * a)), anchor="ma")
        frame.alpha_composite(overlay)

    def _title_layer(self):
        text = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        td = ImageDraw.Draw(text)
        ty = int(self.h * (0.36 if self.vertical else 0.34))
        title_font = self.title_font
        while self.title and title_font.getlength(self.title) > self.max_text_w and title_font.size > 24:
            title_font = load_font(self.font_path, int(title_font.size * 0.9))
        if self.title:
            td.text((self.w / 2, ty), self.title, font=title_font,
                    fill=(255, 255, 255, 255), anchor="md")
        if self.artist:
            td.text((self.w / 2, ty + 24), self.artist.upper(), font=self.small_font,
                    fill=(255, 255, 255, 190), anchor="ma")
        return text, text.filter(ImageFilter.GaussianBlur(10))

    def _draw_visualizer(self, frame: Image.Image, bands: np.ndarray, level: float):
        """No lyrics: title stays up, mirrored spectrum bars breathe under it."""
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        n = len(bands)
        x0, x1 = self.margin, self.w - self.margin
        slot = (x1 - x0) / n
        bar_w = max(2, int(slot * 0.62))
        mid = int(self.h * (0.62 if self.vertical else 0.66))
        max_h = self.h * (0.16 if self.vertical else 0.22)
        for b, v in enumerate(bands):
            h = max(3, v * max_h)
            x = x0 + b * slot + (slot - bar_w) / 2
            d.rounded_rectangle((x, mid - h, x + bar_w, mid), radius=bar_w // 2,
                                fill=(255, 255, 255, int(150 + 105 * v)))
            d.rounded_rectangle((x, mid + 6, x + bar_w, mid + 6 + h * 0.35), radius=bar_w // 2,
                                fill=(255, 255, 255, int(40 * v + 15)))
        small = overlay.resize((self.w // 4, self.h // 4), Image.BILINEAR)
        glow = small.filter(ImageFilter.GaussianBlur(3)).resize(frame.size, Image.BILINEAR)
        frame.alpha_composite(glow)
        frame.alpha_composite(overlay)
        text, tglow = self.title_layer
        frame.alpha_composite(_scale_alpha(tglow, 0.3 + 0.6 * level))
        frame.alpha_composite(text)

    def _draw_progress(self, frame: Image.Image, p: float):
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        y = self.h - int(self.h * 0.05)
        x0, x1 = self.margin, self.w - self.margin
        d.rounded_rectangle((x0, y, x1, y + 4), radius=2, fill=(255, 255, 255, 50))
        d.rounded_rectangle((x0, y, x0 + (x1 - x0) * min(p, 1), y + 4), radius=2,
                            fill=(255, 255, 255, 200))
        frame.alpha_composite(overlay)


def _scale_alpha(img: Image.Image, k: float) -> Image.Image:
    out = img.copy()
    out.putalpha(img.getchannel("A").point(lambda a: int(a * k)))
    return out


def _mul(a: Image.Image, b: Image.Image) -> Image.Image:
    from PIL import ImageChops
    return ImageChops.multiply(a, b)


_ACTIVE: Optional["LyricLookRenderer"] = None


def _encode_job(job):
    return _ACTIVE._encode_chunk(job)


def _balance(rows: List[List[str]], font) -> List[List[str]]:
    """Even out a two-row wrap so the last row isn't a lonely word (Spotify-style)."""
    if len(rows) != 2:
        return rows
    words = rows[0] + rows[1]
    best, best_diff = rows, abs(font.getlength(" ".join(rows[0])) - font.getlength(" ".join(rows[1])))
    for cut in range(1, len(words)):
        a, b = words[:cut], words[cut:]
        wa, wb = font.getlength(" ".join(a)), font.getlength(" ".join(b))
        if wa <= font.getlength(" ".join(rows[0])) and abs(wa - wb) < best_diff:
            best, best_diff = [a, b], abs(wa - wb)
    return best
