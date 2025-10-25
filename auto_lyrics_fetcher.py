#!/usr/bin/env python3
"""
Automated Lyrics Fetcher - Production System
Fetches synced lyrics from multiple sources automatically
"""

import requests
import json
import os
from typing import Optional, List, Dict

class AutoLyricsFetcher:
    """Automatically fetch synced lyrics from multiple APIs"""

    def __init__(self, config_file='config.json'):
        """Load API keys from config"""
        self.config = self.load_config(config_file)

    def load_config(self, config_file):
        """Load API configuration"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}

    def fetch_from_lrclib(self, artist: str, title: str, duration: int = None) -> Optional[str]:
        """
        Fetch from LRCLIB (free, no API key needed!)
        https://lrclib.net/api
        """
        try:
            url = "https://lrclib.net/api/search"
            params = {
                'artist_name': artist,
                'track_name': title
            }
            if duration:
                params['duration'] = duration

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    # Get the best match
                    best = results[0]
                    if 'syncedLyrics' in best and best['syncedLyrics']:
                        print(f"✅ Found synced lyrics from LRCLIB")
                        return best['syncedLyrics']
                    elif 'plainLyrics' in best:
                        print(f"⚠️ Found plain lyrics (no timing) from LRCLIB")
                        return None

            print(f"❌ No results from LRCLIB")
            return None

        except Exception as e:
            print(f"❌ LRCLIB error: {e}")
            return None

    def fetch_from_musixmatch(self, artist: str, title: str) -> Optional[str]:
        """
        Fetch from Musixmatch API
        Requires API key from https://developer.musixmatch.com/
        """
        api_key = self.config.get('musixmatch_api_key')
        if not api_key:
            print("⚠️ No Musixmatch API key configured")
            return None

        try:
            # Search for track
            search_url = "https://api.musixmatch.com/ws/1.1/track.search"
            search_params = {
                'q_artist': artist,
                'q_track': title,
                'apikey': api_key
            }

            response = requests.get(search_url, params=search_params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                tracks = data.get('message', {}).get('body', {}).get('track_list', [])

                if tracks:
                    track_id = tracks[0]['track']['track_id']

                    # Get synced lyrics
                    lyrics_url = "https://api.musixmatch.com/ws/1.1/track.subtitle.get"
                    lyrics_params = {
                        'track_id': track_id,
                        'apikey': api_key
                    }

                    lyrics_response = requests.get(lyrics_url, params=lyrics_params, timeout=10)
                    if lyrics_response.status_code == 200:
                        lyrics_data = lyrics_response.json()
                        subtitle = lyrics_data.get('message', {}).get('body', {}).get('subtitle', {})

                        if subtitle and 'subtitle_body' in subtitle:
                            print(f"✅ Found synced lyrics from Musixmatch")
                            return subtitle['subtitle_body']

            print(f"❌ No results from Musixmatch")
            return None

        except Exception as e:
            print(f"❌ Musixmatch error: {e}")
            return None

    def auto_fetch(self, artist: str, title: str, duration: int = None) -> Optional[str]:
        """
        Automatically fetch from multiple sources (priority order)
        Returns LRC format string
        """
        print(f"\n🔍 Searching for: {artist} - {title}")
        print("=" * 60)

        # Try LRCLIB first (free, no key needed)
        lrc_content = self.fetch_from_lrclib(artist, title, duration)
        if lrc_content:
            return lrc_content

        # Try Musixmatch (if API key available)
        lrc_content = self.fetch_from_musixmatch(artist, title)
        if lrc_content:
            return lrc_content

        print("\n❌ Could not find synced lyrics from any source")
        print("💡 Options:")
        print("   1. Check song title/artist spelling")
        print("   2. Add Musixmatch API key to config.json")
        print("   3. Manually download LRC from https://www.megalobiz.com/lrc/")

        return None


# Test/Example
if __name__ == "__main__":
    fetcher = AutoLyricsFetcher()

    # Test with a song
    result = fetcher.auto_fetch("Rema", "Calm Down")

    if result:
        print("\n✅ Successfully fetched lyrics!")
        print(f"Length: {len(result)} characters")
    else:
        print("\n❌ Could not fetch lyrics automatically")
