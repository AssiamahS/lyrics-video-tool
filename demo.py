#!/usr/bin/env python3
"""
Demo script - Shows how the lyrics video tool works
Uses placeholder text for demonstration
"""

from lyrics_fetcher import LRCCreator
import os

def create_demo():
    """Create a demo LRC file and show usage"""

    print("=" * 60)
    print("LYRICS VIDEO TOOL - DEMO")
    print("=" * 60)

    # Create sample LRC file with placeholder text
    demo_lyrics = [
        {'timestamp': 0.5, 'text': 'This is a demo line one'},
        {'timestamp': 3.0, 'text': 'This is a demo line two'},
        {'timestamp': 6.0, 'text': 'This is a demo line three'},
        {'timestamp': 9.0, 'text': 'Demo text continues here'},
        {'timestamp': 12.0, 'text': 'Final demo line example'},
    ]

    creator = LRCCreator()
    demo_lrc_path = 'demo.lrc'
    creator.create_from_timestamps(demo_lyrics, demo_lrc_path)

    print(f"\n✅ Created demo LRC file: {demo_lrc_path}")
    print("\n📄 Contents:")
    with open(demo_lrc_path, 'r') as f:
        print(f.read())

    print("\n" + "=" * 60)
    print("TO CREATE A VIDEO:")
    print("=" * 60)
    print("\n1. Get your song's LRC file from:")
    print("   - https://www.megalobiz.com/lrc/")
    print("   - https://lrclib.net/")
    print("   - Or create manually")

    print("\n2. Run the tool:")
    print("   python create_video.py \\")
    print("     --audio your_song.mp3 \\")
    print("     --lrc your_song.lrc \\")
    print("     --output result.mp4")

    print("\n3. The tool will:")
    print("   ✅ Parse the timing data")
    print("   ✅ Sync text to audio")
    print("   ✅ Render professional video")

    print("\n" + "=" * 60)
    print("\n💡 TIP: You can test with this demo.lrc file")
    print("   Just provide a short audio clip to see it work!")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    create_demo()
