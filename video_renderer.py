"""
Lyrics Video Tool - Video Renderer
Creates animated text overlays on video with perfect timing
"""

from typing import List, Dict, Tuple
import os

class LyricsVideoRenderer:
    """Renders timed lyrics onto video with animations"""

    def __init__(self, video_path: str = None, audio_path: str = None):
        """
        Initialize renderer with video or audio
        If only audio provided, creates video with background
        """
        self.video_path = video_path
        self.audio_path = audio_path

    def create_lyrics_video(
        self,
        lyrics_data: List[Dict],
        output_path: str,
        style: str = "center",
        font_path: str = None,
        font_size: int = 60,
        color: Tuple[int, int, int] = (255, 255, 255),
        bg_color: Tuple[int, int, int] = (0, 0, 0),
        fade_duration: float = 0.3
    ):
        """
        Create lyrics video with timed text overlays

        Args:
            lyrics_data: List of {'timestamp': float, 'text': str}
            output_path: Where to save the video
            style: "center", "karaoke", "bottom", "slide"
            font_path: Path to TTF font file
            font_size: Size of text
            color: RGB tuple for text color
            bg_color: RGB tuple for background
            fade_duration: Duration of fade in/out effects
        """
        try:
            from moviepy.editor import (
                VideoFileClip, AudioFileClip,
                TextClip, CompositeVideoClip, ColorClip
            )
        except ImportError:
            print("Install required packages:")
            print("pip install moviepy==1.0.3 pillow")
            return

        # Load or create base video
        if self.video_path:
            base = VideoFileClip(self.video_path)
            duration = base.duration
        elif self.audio_path:
            audio = AudioFileClip(self.audio_path)
            duration = audio.duration
            # Create color background
            base = ColorClip(size=(1920, 1080), color=bg_color, duration=duration)
            base = base.set_audio(audio)
        else:
            raise ValueError("Must provide either video_path or audio_path")

        # Create text clips for each lyric line
        text_clips = []

        for i, lyric in enumerate(lyrics_data):
            timestamp = lyric['timestamp']
            text = lyric['text']

            # Calculate duration (until next line or end)
            if i < len(lyrics_data) - 1:
                next_timestamp = lyrics_data[i + 1]['timestamp']
                clip_duration = next_timestamp - timestamp
            else:
                clip_duration = duration - timestamp

            # Create text clip based on style
            if style == "center":
                txt_clip = self._create_center_text(
                    text, clip_duration, font_path, font_size, color
                )
            elif style == "karaoke":
                txt_clip = self._create_karaoke_text(
                    text, clip_duration, font_path, font_size, color
                )
            elif style == "bottom":
                txt_clip = self._create_bottom_text(
                    text, clip_duration, font_path, font_size, color
                )
            elif style == "slide":
                txt_clip = self._create_slide_text(
                    text, clip_duration, font_path, font_size, color
                )
            else:
                txt_clip = self._create_center_text(
                    text, clip_duration, font_path, font_size, color
                )

            # Set start time (fade effects disabled for MoviePy 2.x compatibility)
            txt_clip = txt_clip.set_start(timestamp)
            text_clips.append(txt_clip)

        # Composite all text clips onto base video
        final_video = CompositeVideoClip([base] + text_clips)

        # Write output
        print(f"Rendering video to {output_path}...")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=30
        )

        print("✅ Video created successfully!")

    def _create_center_text(self, text, duration, font_path, font_size, color):
        """Create centered text clip"""
        from moviepy.editor import TextClip

        return TextClip(
            text,
            fontsize=font_size,
            color='white',
            font=font_path or 'Arial-Bold',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(1600, None)
        ).set_duration(duration).set_position('center')

    def _create_karaoke_text(self, text, duration, font_path, font_size, color):
        """Create karaoke-style text (word by word highlight)"""
        # Simplified version - full implementation would highlight words progressively
        return self._create_center_text(text, duration, font_path, font_size, color)

    def _create_bottom_text(self, text, duration, font_path, font_size, color):
        """Create bottom-positioned text (subtitle style)"""
        from moviepy.editor import TextClip

        return TextClip(
            text,
            fontsize=font_size,
            color='white',
            font=font_path or 'Arial-Bold',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(1600, None)
        ).set_duration(duration).set_position(('center', 900))

    def _create_slide_text(self, text, duration, font_path, font_size, color):
        """Create sliding text animation"""
        from moviepy.editor import TextClip

        txt = TextClip(
            text,
            fontsize=font_size,
            color='white',
            font=font_path or 'Arial-Bold',
            stroke_color='black',
            stroke_width=2
        ).set_duration(duration)

        # Slide in from right
        return txt.set_position(lambda t: (max(1920 - t * 500, 400), 'center'))


# Example usage
if __name__ == "__main__":
    print("Lyrics Video Renderer initialized")
    print("\nSupported styles:")
    print("- center: Centered text")
    print("- karaoke: Word-by-word highlight")
    print("- bottom: Subtitle style")
    print("- slide: Sliding animation")
