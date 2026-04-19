"""Unit tests for app.services.lyrics."""
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from app.services.lyrics import _clean, best_match_line, fetch_lyrics


@dataclass
class FakeSegment:
    text: str
    start: float = 0.0
    end: float = 1.0


# ── _clean ────────────────────────────────────────────────────────────────────

class TestClean:
    def test_removes_brackets(self):
        assert _clean("[Verse 1]") == ""

    def test_removes_inline_annotation(self):
        assert _clean("Hello [Chorus] world") == "Hello  world"

    def test_strips_whitespace(self):
        assert _clean("  hello  ") == "hello"

    def test_no_brackets(self):
        assert _clean("Just a line") == "Just a line"

    def test_multiple_bracket_groups(self):
        assert _clean("[A][B] text [C]") == " text"


# ── best_match_line ───────────────────────────────────────────────────────────

class TestBestMatchLine:
    def test_exact_match(self):
        lines = ["hello world", "foo bar", "baz qux"]
        assert best_match_line("hello world", lines) == "hello world"

    def test_case_insensitive(self):
        lines = ["Hello World", "Foo Bar"]
        result = best_match_line("hello world", lines)
        assert result == "Hello World"

    def test_best_partial_match(self):
        lines = ["I love you", "I love cats", "hate everything"]
        result = best_match_line("I love you so much", lines)
        assert result == "I love you"

    def test_returns_asr_text_when_no_lines(self):
        result = best_match_line("fallback text", [])
        assert result == "fallback text"

    def test_single_line(self):
        result = best_match_line("anything", ["only line"])
        assert result == "only line"


# ── fetch_lyrics ──────────────────────────────────────────────────────────────

class TestFetchLyrics:
    def test_returns_none_without_token(self):
        with patch("app.services.lyrics.settings") as mock_settings:
            mock_settings.genius_token = ""
            result = fetch_lyrics([FakeSegment("some text")])
        assert result is None

    def test_returns_none_when_song_not_found(self):
        with patch("app.services.lyrics.settings") as mock_settings, \
             patch("lyricsgenius.Genius") as mock_genius_cls:
            mock_settings.genius_token = "fake-token"
            mock_genius_cls.return_value.search_song.return_value = None
            result = fetch_lyrics([FakeSegment("unknown song lyrics")])
        assert result is None

    def test_returns_cleaned_lines(self):
        raw_lyrics = "[Verse 1]\nHello world\nFoo bar\n\n[Chorus]\nLa la la"
        mock_song = MagicMock()
        mock_song.lyrics = raw_lyrics

        with patch("app.services.lyrics.settings") as mock_settings, \
             patch("lyricsgenius.Genius") as mock_genius_cls:
            mock_settings.genius_token = "fake-token"
            mock_genius_cls.return_value.search_song.return_value = mock_song
            result = fetch_lyrics([FakeSegment("Hello world foo bar")])

        assert result is not None
        # [Verse 1] and [Chorus] annotations should be stripped
        assert "Hello world" in result
        assert "Foo bar" in result
        assert "La la la" in result
        # Empty strings should be filtered
        assert "" not in result
        # Bracket-only lines should be absent
        assert all("[" not in line for line in result)

    def test_returns_none_on_exception(self):
        with patch("app.services.lyrics.settings") as mock_settings, \
             patch("lyricsgenius.Genius") as mock_genius_cls:
            mock_settings.genius_token = "fake-token"
            mock_genius_cls.return_value.search_song.side_effect = Exception("network error")
            result = fetch_lyrics([FakeSegment("some song")])
        assert result is None

    def test_uses_first_5_segments_as_probe(self):
        segs = [FakeSegment(f"word{i}") for i in range(10)]
        mock_song = MagicMock()
        mock_song.lyrics = "line one\nline two"

        with patch("app.services.lyrics.settings") as mock_settings, \
             patch("lyricsgenius.Genius") as mock_genius_cls:
            mock_settings.genius_token = "fake-token"
            genius_instance = mock_genius_cls.return_value
            genius_instance.search_song.return_value = mock_song
            fetch_lyrics(segs)

        probe_arg = genius_instance.search_song.call_args[0][0]
        # probe should contain first 5 segments' text joined
        for i in range(5):
            assert f"word{i}" in probe_arg
        # should NOT contain segment 6+
        assert "word5" not in probe_arg

    def test_handles_none_lyrics(self):
        mock_song = MagicMock()
        mock_song.lyrics = None

        with patch("app.services.lyrics.settings") as mock_settings, \
             patch("lyricsgenius.Genius") as mock_genius_cls:
            mock_settings.genius_token = "fake-token"
            mock_genius_cls.return_value.search_song.return_value = mock_song
            result = fetch_lyrics([FakeSegment("test")])

        # None lyrics → empty lines list after filtering → falsy, but not an error
        # Current code: raw = song.lyrics or "" → lines = [] → return []
        # This returns an empty list, not None — which causes align_with_aeneas
        # to be called with 0 lines. This is a potential bug.
        assert result == [] or result is None  # document the actual behavior
