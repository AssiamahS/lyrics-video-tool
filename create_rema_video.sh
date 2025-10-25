#!/bin/bash
# Create the Rema - Calm Down lyrics video

cd ~/code/lyrics-video-tool

echo "=============================================="
echo "Creating Rema - Calm Down Lyrics Video"
echo "=============================================="

# Check if files exist
if [ ! -f "rema_calm_down.mp3" ]; then
    echo "❌ Audio file not found: rema_calm_down.mp3"
    echo "   Run: bash setup_rema_project.sh first"
    exit 1
fi

if [ ! -f "rema_calm_down.lrc" ]; then
    echo "❌ LRC file not found: rema_calm_down.lrc"
    echo ""
    echo "Please download it manually:"
    echo "1. Visit: https://www.megalobiz.com/lrc/maker/Rema+-+Calm+Down+(Official+Music+Video)(MP3_320K).55643056"
    echo "2. Click 'Download LRC'"
    echo "3. Save as: rema_calm_down.lrc in this folder"
    exit 1
fi

echo "✅ Found audio file"
echo "✅ Found LRC file"
echo ""
echo "Creating video with centered lyrics..."
echo ""

python3 create_video.py \
  --audio rema_calm_down.mp3 \
  --lrc rema_calm_down.lrc \
  --output rema_calm_down_lyrics.mp4 \
  --style center \
  --font-size 70 \
  --fade 0.3

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Video created: rema_calm_down_lyrics.mp4"
    echo ""
    echo "To view it:"
    echo "   open rema_calm_down_lyrics.mp4"
else
    echo ""
    echo "❌ Error creating video. Make sure dependencies are installed:"
    echo "   pip install moviepy pillow"
fi

echo "=============================================="
