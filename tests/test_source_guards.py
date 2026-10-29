"""Regression tests for source ingestion safeguards."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_kworb
import fetch_youtube

class SpotifyGuardTests(unittest.TestCase):
    def test_empty_tracks_rejected(self):
        with self.assertRaises(RuntimeError):
            fetch_kworb.validate_tracks([])
    def test_duplicate_titles_rejected(self):
        tracks = [{"title": "Song", "streams": 1}, {"title": "song", "streams": 2}]
        with self.assertRaises(RuntimeError):
            fetch_kworb.validate_tracks(tracks)
    def test_suspicious_drop_rejected(self):
        tracks = [{"title": str(i), "streams": 1} for i in range(5)]
        with self.assertRaises(RuntimeError):
            fetch_kworb.validate_tracks(tracks, 20, 100)

class YouTubeGuardTests(unittest.TestCase):
    def test_accepts_official_music_video(self):
        self.assertTrue(fetch_youtube.is_official_music_video("BABYMONSTER - CHOOM M/V"))
    def test_rejects_korean_behind_the_scenes(self):
        self.assertFalse(fetch_youtube.is_official_music_video("베몬 매거진 EP.1 로라의 춤 M/V 비하인드"))
    def test_rejects_english_dance_practice(self):
        self.assertFalse(fetch_youtube.is_official_music_video("BABYMONSTER - DANCE PRACTICE"))
    def test_rejects_non_video_title(self):
        self.assertFalse(fetch_youtube.is_official_music_video("BABYMONSTER interview"))
    def test_empty_candidates_rejected(self):
        with self.assertRaises(RuntimeError):
            fetch_youtube.validate_tracks([], 0, 6)
    def test_duplicate_ids_rejected(self):
        tracks = [{"id": "abcdefghijk", "views": 1}, {"id": "abcdefghijk", "views": 2}]
        with self.assertRaises(RuntimeError):
            fetch_youtube.validate_tracks(tracks, 2)
    def test_invalid_views_rejected(self):
        with self.assertRaises(RuntimeError):
            fetch_youtube.validate_tracks([{"id": "abcdefghijk", "views": -1}], 1)

if __name__ == "__main__":
    unittest.main()
