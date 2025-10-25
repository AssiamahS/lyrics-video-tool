# Quick Start Guide - Lyrics Video Tool

## Step-by-Step: Create Your First Lyrics Video

### Step 1: Get an LRC File

Visit one of these sites and download the LRC file for your song:

**Option A: Megalobiz (Recommended)**
1. Go to https://www.megalobiz.com/lrc/
2. Search for your song (e.g., "Rema Calm Down")
3. Click on the result
4. Click "Download LRC" button
5. Save to `~/code/lyrics-video-tool/`

**Option B: LRCLib**
1. Go to https://lrclib.net/
2. Search for your song
3. Download the .lrc file

### Step 2: Prepare Your Audio/Video

Make sure you have:
- The audio file (MP3, WAV, etc.) OR
- A background video file (MP4, MOV, etc.)

Example: If you downloaded a song to `~/Music/song.mp3`

### Step 3: Install Dependencies

```bash
cd ~/code/lyrics-video-tool
pip install -r requirements.txt
```

### Step 4: Create Your Video

```bash
# Basic example (black background + lyrics)
python create_video.py \
  --audio ~/Music/song.mp3 \
  --lrc song.lrc \
  --output my_lyrics_video.mp4

# With custom styling
python create_video.py \
  --audio ~/Music/song.mp3 \
  --lrc song.lrc \
  --output my_lyrics_video.mp4 \
  --style center \
  --font-size 70 \
  --fade 0.4
```

### Step 5: Watch Your Video!

```bash
open my_lyrics_video.mp4
```

## Testing with Demo Data

Want to test first? Run the demo:

```bash
python demo.py
```

This creates a sample video with placeholder text so you can see how it works.

## Troubleshooting

**"No module named 'moviepy'"**
```bash
pip install moviepy pillow
```

**LRC file not found**
Make sure the .lrc file is in the same directory, or use full path:
```bash
--lrc /full/path/to/song.lrc
```

**Need help with timing?**
If your LRC file timing is off, you can edit it manually. LRC format is simple:
```
[00:12.50]First line
[00:15.80]Second line
```

Times are [MM:SS.CS] where CS is centiseconds.

---

🎵 Remember: Only use songs you have rights to or for personal/educational use!
