#!/usr/bin/env python3
"""
Lyrics Video Creator - Main CLI Tool
Create professional lyrics videos with perfect timing
"""

import argparse
import os
from lyrics_fetcher import LyricsFetcher
from video_renderer import LyricsVideoRenderer


def main():
    parser = argparse.ArgumentParser(
        description='Create lyrics videos with timed text overlays'
    )

    # Input files
    parser.add_argument('--audio', help='Audio file (MP3, WAV, etc.)')
    parser.add_argument('--video', help='Video file (MP4, MOV, etc.) - optional background')
    parser.add_argument('--lrc', required=True, help='LRC file with timed lyrics')

    # Output
    parser.add_argument('--output', default='output.mp4', help='Output video file')

    # Style options
    parser.add_argument('--style', default='center',
                       choices=['center', 'bottom', 'karaoke', 'slide'],
                       help='Text animation style')
    parser.add_argument('--font-size', type=int, default=60, help='Font size')
    parser.add_argument('--fade', type=float, default=0.3, help='Fade duration (seconds)')

    args = parser.parse_args()

    # Validate inputs
    if not args.audio and not args.video:
        print("❌ Error: Must provide either --audio or --video")
        return

    if not os.path.exists(args.lrc):
        print(f"❌ Error: LRC file not found: {args.lrc}")
        return

    print("=" * 60)
    print("🎵 LYRICS VIDEO CREATOR")
    print("=" * 60)

    # Step 1: Load lyrics timing data
    print(f"\n📝 Loading lyrics from: {args.lrc}")
    fetcher = LyricsFetcher()
    lyrics_data = fetcher.parse_lrc_file(args.lrc)

    if not lyrics_data:
        print("❌ No lyrics found in LRC file")
        return

    print(f"✅ Loaded {len(lyrics_data)} timed lyrics lines")

    # Step 2: Initialize renderer
    print(f"\n🎬 Initializing video renderer...")
    if args.video:
        print(f"   Using background video: {args.video}")
        renderer = LyricsVideoRenderer(video_path=args.video)
    else:
        print(f"   Using audio file: {args.audio}")
        renderer = LyricsVideoRenderer(audio_path=args.audio)

    # Step 3: Create video
    print(f"\n🎨 Rendering video with '{args.style}' style...")
    print(f"   Font size: {args.font_size}")
    print(f"   Fade duration: {args.fade}s")

    renderer.create_lyrics_video(
        lyrics_data=lyrics_data,
        output_path=args.output,
        style=args.style,
        font_size=args.font_size,
        fade_duration=args.fade
    )

    print(f"\n✅ SUCCESS! Video created: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
