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
    parser.add_argument('--lrc', help='LRC file with timed lyrics (auto-fetched with --song)')
    parser.add_argument('--song', help='Search your yt-dlp library, e.g. --song "artist title"')
    parser.add_argument('--list', action='store_true', help='With --song: show matches and exit')
    parser.add_argument('--visualizer', action='store_true',
                       help='No lyrics: title + audio-reactive bars (instrumentals, mixes)')

    # Output
    parser.add_argument('--output', default='output.mp4', help='Output video file')

    # Style options
    parser.add_argument('--style', default='look',
                       choices=['look', 'center', 'bottom', 'karaoke', 'slide'],
                       help="Text animation style ('look' = scrolling word-fill, no moviepy)")
    parser.add_argument('--font-size', type=int, default=None, help='Font size (look: auto)')

    # 'look' style options
    parser.add_argument('--vertical', action='store_true', help='1080x1920 for reels/shorts')
    parser.add_argument('--cover', help='Cover art image for the blurred background')
    parser.add_argument('--palette', default='dusk', choices=['dusk', 'ocean', 'ember', 'mono'],
                       help='Gradient background when no --cover is given')
    parser.add_argument('--title', help='Song title for the intro card')
    parser.add_argument('--artist', help='Artist name for the intro card')
    parser.add_argument('--align', default='left', choices=['left', 'center'])
    parser.add_argument('--font', help='Path to a .ttf/.ttc font')
    parser.add_argument('--fps', type=int, default=30)
    parser.add_argument('--fade', type=float, default=0.3, help='Fade duration (seconds)')

    args = parser.parse_args()

    if args.song:
        import library
        hits = library.search(args.song)
        if not hits:
            print(f"❌ Nothing in the library matches: {args.song}")
            return
        if args.list:
            for i, (_, p) in enumerate(hits):
                print(f"{i}: {p.name}")
            return
        song = hits[0][1]
        print(f"🎧 Library pick: {song.name}")
        args.audio = str(song)
        artist, title = library.split_artist_title(song)
        args.artist = args.artist or artist
        args.title = args.title or title
        if not args.lrc and not args.visualizer:
            args.lrc = library.lrc_for(song, args.artist, args.title)
            if not args.lrc:
                print("❌ No synced lyrics found; pass --lrc yourself")
                return
        if args.output == 'output.mp4':
            safe = library._norm(f"{artist} {title}").strip().replace(' ', '_')
            args.output = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output',
                                       f"{safe or 'song'}{'_reel' if args.vertical else ''}.mp4")

    # any audio file (e.g. dropped into the app): fetch lyrics, else fall back to the visualizer
    if args.audio and not args.song and not args.lrc and not args.visualizer:
        import library
        from pathlib import Path
        artist, title = library.split_artist_title(Path(args.audio))
        args.artist = args.artist or artist
        args.title = args.title or title
        args.lrc = library.lrc_for(Path(args.audio), args.artist, args.title)
        if not args.lrc:
            print("ℹ️  No synced lyrics found, rendering visualizer instead", flush=True)
            print("MODE visualizer", flush=True)
            args.visualizer = True
        else:
            print("MODE lyrics", flush=True)

    if args.visualizer:
        if not args.audio:
            print("❌ Error: --visualizer needs --audio or --song")
            return
        from lyric_look import LyricLookRenderer
        print("\n🎨 Rendering visualizer...")
        LyricLookRenderer(
            audio_path=args.audio,
            size=(1080, 1920) if args.vertical else (1920, 1080),
            fps=args.fps, font_path=args.font, font_size=args.font_size,
            cover_path=args.cover, palette=args.palette,
            title=args.title, artist=args.artist, align=args.align,
        ).render([], args.output)
        print(f"\n✅ SUCCESS! Video created: {args.output}")
        return

    if not args.lrc:
        print("❌ Error: --lrc is required (or use --song / --visualizer)")
        return

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

    if args.style == 'look':
        if not args.audio:
            print("❌ Error: the 'look' style needs --audio")
            return
        from lyric_look import LyricLookRenderer
        print(f"\n🎨 Rendering 'look' style ({'vertical' if args.vertical else 'landscape'})...")
        LyricLookRenderer(
            audio_path=args.audio,
            size=(1080, 1920) if args.vertical else (1920, 1080),
            fps=args.fps,
            font_path=args.font,
            font_size=args.font_size,
            cover_path=args.cover,
            palette=args.palette,
            title=args.title,
            artist=args.artist,
            align=args.align,
        ).render(lyrics_data, args.output)
        print(f"\n✅ SUCCESS! Video created: {args.output}")
        return

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
        font_size=args.font_size or 60,
        fade_duration=args.fade
    )

    print(f"\n✅ SUCCESS! Video created: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
