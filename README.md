# Lyrics Video Creator 🎵

Professional lyrics video generator with perfect timing synchronization.

## Features
- ✅ Parse LRC format timed lyrics
- ✅ Multiple text animation styles (center, bottom, karaoke, slide)
- ✅ Create videos from audio or overlay on existing video
- ✅ Customizable fonts, colors, and animations
- ✅ Professional fade in/out effects

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x create_video.py
```

## Quick Start

### 1. Get Timed Lyrics (LRC file)

**Free LRC Sources:**
- https://lrclib.net/
- https://www.megalobiz.com/lrc/
- Create manually with Aegisub

**LRC Format Example:**
```
[00:12.50]First line of lyrics
[00:15.80]Second line of lyrics
[00:19.20]Third line continues
```

### 2. Create Your Video

**From audio file:**
```bash
python create_video.py \
  --audio song.mp3 \
  --lrc song.lrc \
  --output result.mp4 \
  --style center
```

**Overlay on video:**
```bash
python create_video.py \
  --video background.mp4 \
  --lrc song.lrc \
  --output result.mp4 \
  --style bottom
```

## Styles

- `center` - Centered text (default)
- `bottom` - Subtitle style at bottom
- `karaoke` - Word-by-word highlighting
- `slide` - Sliding text animation

## Advanced Options

```bash
python create_video.py \
  --audio song.mp3 \
  --lrc song.lrc \
  --output result.mp4 \
  --style center \
  --font-size 70 \
  --fade 0.5
```

## How to Get Timing Data

### Option 1: Download LRC Files
Many songs have community-created LRC files available online.

### Option 2: Manual Timing
Use tools like Aegisub to time lyrics while listening to the audio.

### Option 3: API Integration
- Musixmatch API (requires API key)
- Spotify API (some songs have synced lyrics)

See `example_usage.py` for API integration examples.

## Legal Notice

⚖️ **Important:** Only use lyrics you have rights to use. For copyrighted songs, you need proper licenses. This tool is intended for:
- Personal use
- Educational purposes
- Your own original music
- Licensed content

## Project Structure

```
lyrics-video-tool/
├── create_video.py       # Main CLI tool
├── lyrics_fetcher.py     # Parse LRC files and fetch from APIs
├── video_renderer.py     # Render text overlays on video
├── example_usage.py      # Usage examples
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Examples

Check `example_usage.py` for detailed code examples and API integration guides.

## Troubleshooting

**"Module not found" errors:**
```bash
pip install moviepy pillow
```

**Font issues:**
Specify custom font with `--font-path /path/to/font.ttf`

**Video rendering slow:**
Lower resolution or use simpler styles for faster rendering.

---

Created for educational and personal use. Respect copyright laws! 🎵
