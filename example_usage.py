"""
Lyrics Video Tool - Example Usage
Shows how to create a lyrics video from timing data
"""

from lyrics_fetcher import LyricsFetcher, LRCCreator
from video_renderer import LyricsVideoRenderer
import os

# ============================================
# STEP 1: Get Lyrics Timing Data
# ============================================

def example_using_lrc_file():
    """
    Example: Using an existing LRC file
    LRC files can be found at:
    - https://lrclib.net/
    - https://www.megalobiz.com/lrc/
    - Or create manually using Aegisub subtitle editor
    """

    # Initialize fetcher
    fetcher = LyricsFetcher()

    # Parse LRC file (you provide this)
    # lyrics_data = fetcher.parse_lrc_file('path/to/song.lrc')

    # For demonstration, here's the structure you need:
    # (Replace with actual timing data from LRC file or API)
    lyrics_data = [
        {'timestamp': 0.5, 'text': 'Example lyric line 1'},
        {'timestamp': 3.2, 'text': 'Example lyric line 2'},
        {'timestamp': 6.8, 'text': 'Example lyric line 3'},
        # ... add all timed lyrics
    ]

    return lyrics_data


def example_create_lrc_manually():
    """
    Example: Creating an LRC file manually
    Useful if you have timestamps but need to create the file
    """

    creator = LRCCreator()

    # Your timing data (get this from audio analysis or manual timing)
    timing_data = [
        {'timestamp': 0.5, 'text': 'First line'},
        {'timestamp': 3.2, 'text': 'Second line'},
        {'timestamp': 6.8, 'text': 'Third line'},
    ]

    # Save as LRC file
    creator.create_from_timestamps(timing_data, 'output.lrc')
    print("✅ LRC file created: output.lrc")


# ============================================
# STEP 2: Create Video with Timed Lyrics
# ============================================

def create_lyrics_video_from_audio():
    """
    Example: Create lyrics video from audio file
    Creates a simple background with animated text
    """

    # Get your timing data (from LRC file or API)
    lyrics_data = example_using_lrc_file()

    # Initialize renderer with audio
    renderer = LyricsVideoRenderer(
        audio_path='path/to/your/song.mp3'  # Your audio file
    )

    # Create video with different styles:

    # Style 1: Center (like most lyrics videos)
    renderer.create_lyrics_video(
        lyrics_data=lyrics_data,
        output_path='output_center.mp4',
        style='center',
        font_size=70,
        color=(255, 255, 255),  # White text
        bg_color=(0, 0, 0),      # Black background
        fade_duration=0.3
    )

    print("✅ Created: output_center.mp4")


def create_lyrics_video_with_background():
    """
    Example: Overlay lyrics on existing video
    """

    lyrics_data = example_using_lrc_file()

    # Use existing video as background
    renderer = LyricsVideoRenderer(
        video_path='path/to/background_video.mp4'
    )

    renderer.create_lyrics_video(
        lyrics_data=lyrics_data,
        output_path='output_with_bg.mp4',
        style='bottom',  # Subtitle style at bottom
        font_size=50,
        fade_duration=0.2
    )

    print("✅ Created: output_with_bg.mp4")


# ============================================
# STEP 3: Where to Get Timing Data
# ============================================

def get_timing_data_sources():
    """
    Legitimate sources for lyrics timing data:
    """

    sources = """
    📝 LEGITIMATE SOURCES FOR LYRICS TIMING:

    1. LRC FILE DATABASES:
       - https://lrclib.net/ (free LRC files)
       - https://www.megalobiz.com/lrc/
       - Community-contributed timing data

    2. APIS (Require registration):
       - Musixmatch API (https://developer.musixmatch.com/)
       - Spotify API (has some synchronized lyrics)
       - Genius API (lyrics text, timing varies)

    3. MANUAL TIMING TOOLS:
       - Aegisub (subtitle editor - can time to audio)
       - Subtitle Edit (free timing tool)
       - Record timestamps while listening

    4. FOR YOUR OWN MUSIC:
       - Time manually as you record
       - Use DAW markers
       - Audio analysis tools

    ⚖️ IMPORTANT LEGAL NOTE:
    - Only use lyrics you have rights to
    - For copyrighted songs, you need licenses
    - This tool is for personal use, educational purposes,
      or content you own/have licensed
    """

    print(sources)


# ============================================
# MAIN EXAMPLE
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("LYRICS VIDEO TOOL - Example Usage")
    print("=" * 60)

    # Show where to get timing data
    get_timing_data_sources()

    print("\n" + "=" * 60)
    print("USAGE EXAMPLES:")
    print("=" * 60)

    print("\n1. Create video from audio + LRC file:")
    print("   python example_usage.py --audio song.mp3 --lrc song.lrc")

    print("\n2. Overlay lyrics on existing video:")
    print("   python example_usage.py --video bg.mp4 --lrc song.lrc")

    print("\n3. Different text styles:")
    print("   --style center   (default, centered)")
    print("   --style bottom   (subtitle style)")
    print("   --style karaoke  (word highlighting)")
    print("   --style slide    (sliding animation)")

    print("\n" + "=" * 60)
    print("\n📌 TO USE THIS TOOL:")
    print("1. Install dependencies: pip install moviepy pillow")
    print("2. Get LRC file for your song (see sources above)")
    print("3. Run: python create_video.py")
    print("\n" + "=" * 60)
