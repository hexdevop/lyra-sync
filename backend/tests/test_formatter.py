"""Unit tests for app.services.formatter — pure functions, no mocks needed."""
import pytest

from app.services.alignment import AlignedLine
from app.services.formatter import _ts_lrc, _ts_srt, build_result, to_json, to_lrc, to_srt


# ── Timestamp helpers ─────────────────────────────────────────────────────────

class TestTsLrc:
    def test_zero(self):
        assert _ts_lrc(0.0) == "00:00.00"

    def test_under_minute(self):
        assert _ts_lrc(5.5) == "00:05.50"

    def test_over_minute(self):
        assert _ts_lrc(65.75) == "01:05.75"

    def test_two_digits_minutes(self):
        assert _ts_lrc(125.0) == "02:05.00"

    def test_fractional_precision(self):
        result = _ts_lrc(1.234)
        # Should round to 2 decimal places
        assert result == "00:01.23"


class TestTsSrt:
    def test_zero(self):
        assert _ts_srt(0.0) == "00:00:00,000"

    def test_seconds_only(self):
        assert _ts_srt(5.5) == "00:00:05,500"

    def test_minutes_and_seconds(self):
        assert _ts_srt(65.75) == "00:01:05,750"

    def test_hours(self):
        assert _ts_srt(3661.0) == "01:01:01,000"

    def test_millisecond_precision(self):
        assert _ts_srt(1.001) == "00:00:01,001"

    def test_millisecond_truncation(self):
        # Should truncate (int), not round
        assert _ts_srt(1.9999) == "00:00:01,999"


# ── Conversion functions ──────────────────────────────────────────────────────

@pytest.fixture
def sample_lines():
    return [
        AlignedLine(start=0.0,  end=2.5,  text="Hello world"),
        AlignedLine(start=2.5,  end=5.0,  text="Foo bar"),
        AlignedLine(start=65.0, end=67.5, text="Over a minute"),
    ]


class TestToJson:
    def test_structure(self, sample_lines):
        result = to_json(sample_lines)
        assert len(result) == 3
        assert result[0] == {"start": 0.0, "end": 2.5, "text": "Hello world"}

    def test_all_fields_present(self, sample_lines):
        for item in to_json(sample_lines):
            assert "start" in item and "end" in item and "text" in item

    def test_empty(self):
        assert to_json([]) == []


class TestToLrc:
    def test_format(self, sample_lines):
        lrc = to_lrc(sample_lines)
        lines = lrc.splitlines()
        assert lines[0] == "[00:00.00] Hello world"
        assert lines[1] == "[00:02.50] Foo bar"
        assert lines[2] == "[01:05.00] Over a minute"

    def test_empty(self):
        assert to_lrc([]) == ""


class TestToSrt:
    def test_format(self, sample_lines):
        srt = to_srt(sample_lines)
        assert "00:00:00,000 --> 00:00:02,500" in srt
        assert "Hello world" in srt
        assert "1\n" in srt
        assert "2\n" in srt

    def test_sequence_numbers(self, sample_lines):
        srt = to_srt(sample_lines)
        assert srt.count("\n1\n") == 0  # no "1" in middle
        assert "1\n00:00:00,000" in srt
        assert "2\n00:00:02,500" in srt

    def test_empty(self):
        assert to_srt([]) == ""


class TestBuildResult:
    def test_keys(self, sample_lines):
        result = build_result(sample_lines)
        assert set(result.keys()) == {"lines", "lrc", "srt"}

    def test_lines_is_list_of_dicts(self, sample_lines):
        result = build_result(sample_lines)
        assert isinstance(result["lines"], list)
        assert isinstance(result["lines"][0], dict)

    def test_lrc_is_string(self, sample_lines):
        assert isinstance(build_result(sample_lines)["lrc"], str)

    def test_srt_is_string(self, sample_lines):
        assert isinstance(build_result(sample_lines)["srt"], str)

    def test_empty_input(self):
        result = build_result([])
        assert result["lines"] == []
        assert result["lrc"] == ""
        assert result["srt"] == ""
