#!/usr/bin/env python3
"""
ONE-CLICK LYRICS VIDEO CREATOR
Complete automation: Just provide artist + song name
"""

import subprocess
import sys
import os
import json
import requests
from pathlib import Path

class OneClickCreator:
    """Complete automated lyrics video creation"""

    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        Path(output_dir).mkdir(exist_ok=True)

    def sanitize_filename(self, name):
        """Create safe filename"""
        return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()

    def search_youtube(self, artist, song):
        """Search YouTube and get video ID"""
        try:
            search_query = f"{artist} {song} official audio"
            cmd = [
                'yt-dlp',
                '--get-id',
                '--default-search', 'ytsearch1',
                search_query
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                video_id = result.stdout.strip()
                print(f"✅ Found YouTube video: {video_id}")
                return video_id
            return None
        except Exception as e:
            print(f"❌ YouTube search error: {e}")
            return None

    def download_audio(self, video_id, output_path):
        """Download audio from YouTube"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"\n⬇️ Downloading audio from YouTube...")

            cmd = [
                'yt-dlp',
                '-x',
                '--audio-format', 'mp3',
                '--extractor-args', 'youtube:player_client=android',
                '--output', output_path,
                url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # Check if MP3 file was created
            mp3_path = output_path.replace('.%(ext)s', '.mp3')
            if os.path.exists(mp3_path):
                print(f"✅ Audio downloaded: {mp3_path}")
                return mp3_path

            print(f"❌ Download failed")
            return None

        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

    def fetch_lyrics_lrclib(self, artist, song):
        """Fetch synced lyrics from LRCLIB (free API)"""
        try:
            print(f"\n🔍 Fetching synced lyrics from LRCLIB...")

            url = "https://lrclib.net/api/search"
            params = {
                'artist_name': artist,
                'track_name': song
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    best = results[0]

                    # Prefer synced lyrics
                    if 'syncedLyrics' in best and best['syncedLyrics']:
                        print(f"✅ Found synced lyrics!")
                        return best['syncedLyrics']

                    # Fallback to plain lyrics (we'll need to sync manually)
                    if 'plainLyrics' in best and best['plainLyrics']:
                        print(f"⚠️ Found plain lyrics (no timing)")
                        return None

            print(f"❌ No lyrics found on LRCLIB")
            return None

        except Exception as e:
            print(f"❌ LRCLIB error: {e}")
            return None

    def save_lrc(self, lyrics_content, output_path):
        """Save LRC content to file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(lyrics_content)
            print(f"✅ Saved lyrics: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving LRC: {e}")
            return False

    def create_video(self, audio_path, lrc_path, output_path, style='center', font_size=70):
        """Create lyrics video"""
        try:
            print(f"\n🎬 Creating lyrics video...")

            cmd = [
                'python3',
                'create_video.py',
                '--audio', audio_path,
                '--lrc', lrc_path,
                '--output', output_path,
                '--style', style,
                '--font-size', str(font_size)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0 and os.path.exists(output_path):
                print(f"✅ Video created: {output_path}")
                return True
            else:
                print(f"❌ Video creation failed")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Video creation error: {e}")
            return False

    def create(self, artist, song, youtube_url=None, style='center'):
        """
        ONE-CLICK: Create complete lyrics video

        Args:
            artist: Artist name
            song: Song title
            youtube_url: Optional direct YouTube URL (otherwise will search)
            style: Video style (center, bottom, karaoke, slide)
        """
        print("=" * 70)
        print(f"🎵 ONE-CLICK LYRICS VIDEO CREATOR")
        print("=" * 70)
        print(f"Artist: {artist}")
        print(f"Song: {song}")
        print("=" * 70)

        # Create safe filenames
        safe_name = self.sanitize_filename(f"{artist}_{song}")
        audio_path = f"{self.output_dir}/{safe_name}.%(ext)s"
        lrc_path = f"{self.output_dir}/{safe_name}.lrc"
        video_path = f"{self.output_dir}/{safe_name}_lyrics_video.mp4"

        # Step 1: Get YouTube video
        if youtube_url:
            video_id = youtube_url.split('v=')[-1].split('&')[0]
        else:
            video_id = self.search_youtube(artist, song)

        if not video_id:
            print("❌ Could not find YouTube video")
            return False

        # Step 2: Download audio
        final_audio = self.download_audio(video_id, audio_path)
        if not final_audio:
            print("❌ Audio download failed")
            return False

        # Step 3: Fetch lyrics
        lyrics = self.fetch_lyrics_lrclib(artist, song)
        if not lyrics:
            print("\n❌ Could not fetch synced lyrics automatically")
            print("💡 Try:")
            print(f"   1. Download LRC manually from https://www.megalobiz.com/lrc/")
            print(f"   2. Save as: {lrc_path}")
            print(f"   3. Run: python create_video.py --audio {final_audio} --lrc {lrc_path} --output {video_path}")
            return False

        # Step 4: Save LRC
        if not self.save_lrc(lyrics, lrc_path):
            return False

        # Step 5: Create video
        if not self.create_video(final_audio, lrc_path, video_path, style):
            return False

        print("\n" + "=" * 70)
        print("🎉 SUCCESS! Lyrics video created!")
        print("=" * 70)
        print(f"📁 Video: {video_path}")
        print(f"🎵 Audio: {final_audio}")
        print(f"📝 Lyrics: {lrc_path}")
        print("\n🚀 Ready to upload to social media!")
        print("=" * 70)

        return True


# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='One-click lyrics video creator')
    parser.add_argument('--artist', required=True, help='Artist name')
    parser.add_argument('--song', required=True, help='Song title')
    parser.add_argument('--youtube', help='YouTube URL (optional, will search if not provided)')
    parser.add_argument('--style', default='center', choices=['center', 'bottom', 'karaoke', 'slide'])
    parser.add_argument('--output-dir', default='output', help='Output directory')

    args = parser.parse_args()

    creator = OneClickCreator(output_dir=args.output_dir)
    success = creator.create(args.artist, args.song, args.youtube, args.style)

    sys.exit(0 if success else 1)
