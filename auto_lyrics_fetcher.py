#!/usr/bin/env python3
"""
Automated Lyrics Fetcher - Production System
Fetches synced lyrics from multiple sources automatically
"""

import re
import requests
import json
import os
from typing import Optional, List, Dict

class AutoLyricsFetcher:
    """Automatically fetch synced lyrics from multiple APIs"""

    last_duration = None

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
        Fetch synced lyrics from LRCLIB (free, no API key).
        Tries several queries, since filenames rarely match the catalog exactly:
          1. artist + title   2. free-text "artist title"   3. title only
        and keeps the synced result whose length is closest to the audio file.
        """
        url = "https://lrclib.net/api/search"
        queries = [{'artist_name': artist, 'track_name': title},
                   {'q': f"{artist} {title}".strip()},
                   {'track_name': title}]
        seen, candidates = set(), []
        for params in queries:
            if not any(v for v in params.values()):
                continue
            try:
                response = requests.get(url, params=params, timeout=10)
                results = response.json() if response.status_code == 200 else []
            except Exception as e:
                print(f"❌ LRCLIB error: {e}")
                continue
            for r in results:
                if r.get('id') in seen or not r.get('syncedLyrics'):
                    continue
                seen.add(r.get('id'))
                candidates.append(r)
            if candidates and params is queries[0]:
                break  # exact artist+title hit, no need to widen the search

        if not candidates:
            print("❌ No synced lyrics on LRCLIB")
            return None

        stop = {"a", "the", "da", "de", "and", "x", "dj", "mc", "lil", "big", "wit", "with", "of"}
        want = {w for w in re.findall(r"[a-z0-9]+", artist.lower()) if w not in stop} if artist else set()

        def artist_ok(r):
            have = set(re.findall(r"[a-z0-9]+", (r.get('artistName') or '').lower()))
            return not want or bool(want & have)

        # a title-only hit by somebody else ("Body Dirty" -> an R. Kelly song) is a different song
        candidates = [r for r in candidates if artist_ok(r)]
        if not candidates:
            print("❌ No synced lyrics on LRCLIB for this artist")
            return None

        def score(r):
            off = abs((r.get('duration') or 0) - duration) if duration else 0
            return (off > 4, off)

        best = min(candidates, key=score)
        self.last_duration = best.get('duration')
        print(f"✅ Synced lyrics: {best.get('artistName')} - {best.get('trackName')} ({best.get('duration')}s)")
        return best['syncedLyrics']

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
