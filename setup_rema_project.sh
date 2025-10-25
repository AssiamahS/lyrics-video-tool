#!/bin/bash
# Complete setup for Rema - Calm Down lyrics video

echo "=============================================="
echo "Rema - Calm Down Lyrics Video Setup"
echo "=============================================="
echo ""

# Step 1: Download audio from YouTube
echo "STEP 1: Downloading audio..."
echo "-------------------------------------------"
yt-dlp -x --audio-format mp3 \
  --output "~/code/lyrics-video-tool/rema_calm_down.mp3" \
  "https://www.youtube.com/watch?v=WcIcVapfqXw"

echo ""
echo "STEP 2: Get the LRC file"
echo "-------------------------------------------"
echo "You need to manually download the LRC file:"
echo ""
echo "1. Open this URL in your browser:"
echo "   https://www.megalobiz.com/lrc/maker/Rema+-+Calm+Down+(Official+Music+Video)(MP3_320K).55643056"
echo ""
echo "2. Click 'Download LRC' button on the page"
echo ""
echo "3. Save it as: rema_calm_down.lrc"
echo "   In this folder: ~/code/lyrics-video-tool/"
echo ""
echo "Once you've downloaded the LRC file, run:"
echo "   bash create_rema_video.sh"
echo ""
echo "=============================================="
