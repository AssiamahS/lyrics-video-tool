#!/usr/bin/env python3
"""
BATCH PROCESSOR - Process entire albums/playlists
For bulk lyrics video creation
"""

import json
import sys
from pathlib import Path
from one_click_creator import OneClickCreator

class BatchProcessor:
    """Process multiple songs from a list/album"""

    def __init__(self, output_dir='output'):
        self.creator = OneClickCreator(output_dir=output_dir)
        self.results = {
            'success': [],
            'failed': []
        }

    def process_from_file(self, songs_file):
        """
        Process songs from JSON file

        Format:
        [
            {"artist": "Rema", "song": "Calm Down", "youtube": "optional_url"},
            {"artist": "Rema", "song": "Song 2"},
            ...
        ]
        """
        try:
            with open(songs_file, 'r') as f:
                songs = json.load(f)

            total = len(songs)
            print(f"\n📋 Processing {total} songs from {songs_file}")
            print("=" * 70)

            for i, song_data in enumerate(songs, 1):
                artist = song_data.get('artist')
                song = song_data.get('song')
                youtube = song_data.get('youtube')
                style = song_data.get('style', 'center')

                print(f"\n[{i}/{total}] Processing: {artist} - {song}")
                print("-" * 70)

                try:
                    success = self.creator.create(artist, song, youtube, style)

                    if success:
                        self.results['success'].append(f"{artist} - {song}")
                    else:
                        self.results['failed'].append(f"{artist} - {song}")

                except Exception as e:
                    print(f"❌ Error: {e}")
                    self.results['failed'].append(f"{artist} - {song} (Error: {e})")

            self.print_summary()

        except Exception as e:
            print(f"❌ Error reading songs file: {e}")
            return False

    def process_from_list(self, songs_list):
        """Process from Python list"""
        total = len(songs_list)
        print(f"\n📋 Processing {total} songs")
        print("=" * 70)

        for i, (artist, song) in enumerate(songs_list, 1):
            print(f"\n[{i}/{total}] Processing: {artist} - {song}")
            print("-" * 70)

            try:
                success = self.creator.create(artist, song)

                if success:
                    self.results['success'].append(f"{artist} - {song}")
                else:
                    self.results['failed'].append(f"{artist} - {song}")

            except Exception as e:
                print(f"❌ Error: {e}")
                self.results['failed'].append(f"{artist} - {song}")

        self.print_summary()

    def print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 70)
        print("📊 BATCH PROCESSING SUMMARY")
        print("=" * 70)

        print(f"\n✅ Successful: {len(self.results['success'])}")
        for song in self.results['success']:
            print(f"   • {song}")

        if self.results['failed']:
            print(f"\n❌ Failed: {len(self.results['failed'])}")
            for song in self.results['failed']:
                print(f"   • {song}")

        print("\n" + "=" * 70)


# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Batch lyrics video processor')
    parser.add_argument('--songs-file', required=True, help='JSON file with songs list')
    parser.add_argument('--output-dir', default='output', help='Output directory')

    args = parser.parse_args()

    processor = BatchProcessor(output_dir=args.output_dir)
    processor.process_from_file(args.songs_file)
