"""Tests for render module — formatting helpers."""

from birdview.render import _format_count


class TestFormatCount:
    def test_small_numbers(self):
        assert _format_count(0) == "0"
        assert _format_count(42) == "42"
        assert _format_count(999) == "999"

    def test_thousands(self):
        assert _format_count(1000) == "1.0K"
        assert _format_count(1200) == "1.2K"
        assert _format_count(15000) == "15.0K"
        assert _format_count(999999) == "1000.0K"

    def test_millions(self):
        assert _format_count(1_000_000) == "1.0M"
        assert _format_count(1_500_000) == "1.5M"
        assert _format_count(234_900_000) == "234.9M"
