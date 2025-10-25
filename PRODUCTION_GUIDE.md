# Production Lyrics Video System
**Automated bulk lyrics video creation for social media**

## 🚀 Quick Start - One Song

**Single command to create a lyrics video:**

```bash
cd ~/code/lyrics-video-tool

python3 one_click_creator.py \
  --artist "Rema" \
  --song "Calm Down"
```

That's it! The script will:
1. ✅ Search YouTube and download audio
2. ✅ Fetch synced lyrics from LRCLIB API
3. ✅ Create professional lyrics video
4. ✅ Output ready for social media

**Output:** `output/Rema_Calm_Down_lyrics_video.mp4`

---

## 📦 Batch Processing - Entire Albums

### Step 1: Create your songs list

Edit `songs_template.json`:

```json
[
  {
    "artist": "Rema",
    "song": "Calm Down",
    "youtube": "https://www.youtube.com/watch?v=WcIcVapfqXw",
    "style": "center"
  },
  {
    "artist": "Rema",
    "song": "Another Song",
    "style": "center"
  }
]
```

### Step 2: Process the entire album

```bash
python3 batch_processor.py --songs-file songs_template.json
```

This will process all songs automatically and give you a summary report.

---

## 🎨 Video Styles

Change the `--style` parameter:

- `center` - Centered text (default, best for most content)
- `bottom` - Subtitle style at bottom
- `karaoke` - Word-by-word highlighting
- `slide` - Sliding text animation

---

## ⚙️ Installation

```bash
cd ~/code/lyrics-video-tool

# Install Python dependencies
pip install moviepy pillow requests

# Test the system
python3 demo.py
```

---

## 📱 Social Media Optimization

Videos are created at:
- **Resolution:** 1920x1080 (Full HD)
- **Format:** MP4 (H.264)
- **Audio:** AAC
- **FPS:** 30

Perfect for:
- Instagram Reels
- TikTok
- YouTube
- Facebook
- Twitter/X

---

## 🔧 Advanced Options

### Custom YouTube URL

```bash
python3 one_click_creator.py \
  --artist "Rema" \
  --song "Calm Down" \
  --youtube "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Change output directory

```bash
python3 one_click_creator.py \
  --artist "Rema" \
  --song "Calm Down" \
  --output-dir "rema_album_videos"
```

### Different video style

```bash
python3 one_click_creator.py \
  --artist "Rema" \
  --song "Calm Down" \
  --style bottom
```

---

## 🎯 Workflow for 100+ Songs

1. **Prepare the song list**
   - Create `rema_album.json` with all tracks
   - Include YouTube URLs if available (faster)

2. **Run batch processor**
   ```bash
   python3 batch_processor.py --songs-file rema_album.json --output-dir rema_videos
   ```

3. **Review results**
   - Check the summary report
   - All videos in `rema_videos/` folder
   - Failed songs will be listed

4. **Re-run failed songs**
   - Some songs might not have synced lyrics on LRCLIB
   - For these, manually download LRC from Megalobiz
   - Use: `python create_video.py --audio song.mp3 --lrc song.lrc`

---

## 📊 Success Rate

**Estimated success rate:**
- Popular songs: ~80% (synced lyrics available on LRCLIB)
- New releases: ~50% (may not have lyrics synced yet)
- Very new/unreleased: May need manual LRC files

**For songs without auto-synced lyrics:**
1. Visit https://www.megalobiz.com/lrc/
2. Download the LRC file
3. Run: `python create_video.py --audio song.mp3 --lrc song.lrc --output video.mp4`

---

## 🚨 Troubleshooting

**"Module not found"**
```bash
pip install moviepy pillow requests
```

**"No lyrics found"**
- Try Megalobiz.com for manual LRC download
- Check spelling of artist/song name
- Some songs may not have synced lyrics available

**"YouTube download failed"**
- Provide direct YouTube URL with `--youtube`
- Check internet connection
- Video may be region-restricted

**Video rendering slow**
- Normal for first render (MoviePy compilation)
- Subsequent renders are faster
- Processing time: ~1-2 minutes per song

---

## 📁 File Structure

```
lyrics-video-tool/
├── one_click_creator.py      # Main one-click tool
├── batch_processor.py         # Bulk processing
├── create_video.py           # Manual video creation
├── lyrics_fetcher.py         # LRC parsing
├── video_renderer.py         # Video rendering engine
├── songs_template.json       # Song list template
└── output/                   # All generated videos
```

---

## ✅ Quality Checklist

Before uploading to social media:
- [ ] Audio is clear and synced
- [ ] Lyrics appear at correct time
- [ ] Text is readable (good contrast)
- [ ] No timing issues
- [ ] Proper song credits in filename

---

## 💡 Pro Tips

1. **Process overnight** - For 100+ songs, let it run overnight
2. **Check first 5** - Test with 5 songs first to verify quality
3. **Backup originals** - Keep your audio files backed up
4. **Organize output** - Use separate folders per album/project
5. **Version control** - Keep track of which videos you've uploaded

---

## 🎵 Example: Full Album Workflow

```bash
# 1. Create song list
cat > rema_album.json << 'EOF'
[
  {"artist": "Rema", "song": "Track 1"},
  {"artist": "Rema", "song": "Track 2"},
  {"artist": "Rema", "song": "Track 3"}
]
EOF

# 2. Process all songs
python3 batch_processor.py --songs-file rema_album.json --output-dir rema_rave_roses

# 3. Check results
ls -lh rema_rave_roses/

# 4. Upload to social media!
```

---

**Ready to create hundreds of professional lyrics videos! 🎬**
