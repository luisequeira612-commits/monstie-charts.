"""Pruebas unitarias para los límites de validación de datos."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_data as validator


class NumericValidationTests(unittest.TestCase):
    def test_accepts_zero_and_positive_numbers(self):
        validator.nonnegative(0, "test")
        validator.nonnegative(12, "test")
        validator.nonnegative(0.5, "test")

    def test_rejects_negative_numbers(self):
        with self.assertRaises(SystemExit):
            validator.nonnegative(-1, "test")

    def test_rejects_boolean_even_though_bool_is_an_int(self):
        with self.assertRaises(SystemExit):
            validator.nonnegative(True, "test")

    def test_rejects_non_finite_numbers(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit):
                    validator.nonnegative(value, "test")


class HistoryValidationTests(unittest.TestCase):
    def test_accepts_empty_history(self):
        validator.validate_history([])

    def test_accepts_well_formed_snapshot(self):
        validator.validate_history([{
            "date": "2026-10-29",
            "spotify": {"track_count": 43, "daily_streams": 123},
            "youtube": {"video_count": 6, "total_views": 456},
        }])

    def test_rejects_invalid_date(self):
        with self.assertRaises(SystemExit):
            validator.validate_history([{
                "date": "29-10-2026",
                "spotify": {},
                "youtube": {},
            }])

    def test_rejects_duplicate_dates(self):
        snapshot = {
            "date": "2026-10-29",
            "spotify": {},
            "youtube": {},
        }
        with self.assertRaises(SystemExit):
            validator.validate_history([snapshot, snapshot.copy()])

    def test_rejects_unsorted_dates(self):
        def snapshot(day):
            return {"date": day, "spotify": {}, "youtube": {}}
        with self.assertRaises(SystemExit):
            validator.validate_history([
                snapshot("2026-10-29"),
                snapshot("2026-10-28"),
            ])

    def test_rejects_negative_historical_metrics(self):
        with self.assertRaises(SystemExit):
            validator.validate_history([{
                "date": "2026-10-29",
                "spotify": {"daily_streams": -10},
                "youtube": {},
            }])


class YouTubeUrlTests(unittest.TestCase):
    def test_accepts_realistic_video_url(self):
        self.assertIsNotNone(
            validator.YOUTUBE_URL.fullmatch("https://www.youtube.com/watch?v=x3eqqoZPV_E")
        )

    def test_rejects_invalid_video_ids_and_domains(self):
        for url in (
            "https://www.youtube.com/watch?v=short",
            "https://youtube.example/watch?v=x3eqqoZPV_E",
            "https://www.youtube.com/watch?v=x3eqqoZPV_E&other=1",
        ):
            with self.subTest(url=url):
                self.assertIsNone(validator.YOUTUBE_URL.fullmatch(url))


if __name__ == "__main__":
    unittest.main()
